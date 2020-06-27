/// <reference path="./script.d.ts" />

document.addEventListener("DOMContentLoaded", () => {
    const localStorageTokenKey = 'ScoutID-JWT-Token';
    const whoamiElement = document.getElementById("whoami") as HTMLInputElement;
    const whoamiErrorTest = 'Inte inloggad';
    const apiBaseUrl = location.origin + '/api/';
    let config = null;
    let isLoggedIn = false;

    const fetchJson = async (url: string, fetchOptions?: RequestInit) => {
        const response = await fetch(url, fetchOptions);
        if (!response.ok) {
            throw response;
        }
        return await response.json();
    };

    const apiFetch = async (urlSufix: string, fetchOptions?: RequestInit, token?: string) => {
        const url = apiBaseUrl + urlSufix;

        if (!fetchOptions) {
            fetchOptions = {};
        }
        if (!fetchOptions.headers) {
            fetchOptions.headers = {};
        }
        fetchOptions.headers["Authorization"] = 'Bearer ' + (token || localStorage.getItem(localStorageTokenKey));

        const response = await fetch(url, fetchOptions);

        if (response.ok) {
            return await response.json();
        }

        // Other errors then token expired
        if (response.status !== 498) {
            throw response;
        }

        // if we are not logged in, this was just a token test, then we are done here
        if (token) {
            throw response;
        }

        // Try to re-login
        if (!await login(false)) {
            throw response;
        }

        // Update Authorization-header
        fetchOptions.headers["Authorization"] = 'Bearer ' + localStorage.getItem(localStorageTokenKey);
        const response2 = await fetch(url, fetchOptions);

        if (!response2.ok) {
            throw response2;
        }

        return await response2.json();
    };

    const verifyToken = async (token: string) => {
        isLoggedIn = false;
        whoamiElement.innerText = whoamiErrorTest;
        const verifyPromise = apiFetch('jwt/verify_token', {}, token);
        try {
            await verifyPromise;
        } catch (e) {
            console.error(e);
            throw e;
        }

        /// TODO Skojjt.whoamiResponse
        const response = await verifyPromise as ScoutId.whoamiResponse;
        if (response.user === false) {
            throw new Error('No user');
        }

        const karer = response.data.karer ? Object.values(response.data.karer) : [];
        let kar = null;
        if (karer.length > 2) {
            kar = karer.slice(0, karer.length - 1).join(', ') + ' och ' + karer[karer.length - 1]
        } else if (karer.length > 0) {
            kar = karer.join(' och ');
        }

        whoamiElement.innerText = "Inloggad som " + response.data.name + (kar ? " från " + kar : "");
        isLoggedIn = true;
        return true;
    };

    const login = async (byUser: boolean): Promise<boolean> => {
        const oldToken = localStorage.getItem(localStorageTokenKey);
        if (oldToken) {
            try {
                await verifyToken(oldToken);
            } catch (e) {
                localStorage.removeItem(localStorageTokenKey);
            }
        }
        if (!isLoggedIn) {
            if(!config) {
                console.error('Loggin failed, as no config was received');
                return false;
            }
            if(!config.jwturl) {
                console.error('Loggin failed, as there is no jwturl in the received config');
                return false;
            }
            let jwtPromise = fetchJson(config.jwturl, {credentials: 'include'});
            try {
                await jwtPromise;
            } catch (e) {
                if (!e.json) {
                    console.error(e);
                    whoamiElement.innerText = whoamiErrorTest;
                    return false;
                }
                jwtPromise = e.json();
                try {
                    await jwtPromise;
                } catch (e) {
                    console.error(e);
                    whoamiElement.innerText = whoamiErrorTest;
                    return false;
                }
            }
            const jwtResponse = await jwtPromise as ScoutId.jwtResponse;
            if (jwtResponse.ok) {
                try {
                    await verifyToken(jwtResponse.token);
                } catch (e) {
                    console.error(e);
                    whoamiElement.innerText = whoamiErrorTest;
                    return false;
                }
                localStorage.setItem(localStorageTokenKey, jwtResponse.token);
            }
            if (!isLoggedIn && byUser) {
                location.href = (jwtResponse as ScoutId.jwtBadResponse).url;
            }
        }
        if (isLoggedIn) {
            if (location.hash.substr(0, 9) === '#!/login/') {
                location.hash = '#!/' + location.hash.substr(9);
            } else if (location.hash === '#!/login') {
                location.hash = '#!/';
            } else if (byUser) {
                navigate();
            }
        }

        return isLoggedIn;
    };
    const showMenu = () => {
    };
    const reset = () => {
        document.body.classList.toggle('guest', !isLoggedIn);
    };
    const navigate = async () => {
        reset();
        if (!isLoggedIn) {
            switch (location.hash) {
                case '#!/login':
                    return login(true);
                case '#!/':
                case '':
                    return showMenu();
            }
            if (location.hash.substr(0, 9) === '#!/login/') {
                return login(true);
            }
            return showMenu();
        }
        switch (location.hash) {
            case '#!/':
            case '':
                return showMenu();

            case '#!/logout':
                localStorage.removeItem(localStorageTokenKey);
                isLoggedIn = false;
                whoamiElement.innerText = whoamiErrorTest;
                location.hash = '#!/';
                return;
        }
    };
    window.addEventListener('hashchange', navigate);

    (async () => {
        const loginButton = document.getElementById('login-button') as HTMLAnchorElement;
        loginButton.addEventListener('click', (event: Event) => {
            if (location.hash.length > 3 && location.hash.substr(0, 3) === '#!/') {
                event.preventDefault();
                location.hash = '#!/login/' + location.hash.substr(3);
            }
        });

        /// TODO: replace with live hostname
        if(location.hostname !== 'skojjt.webservices.scouterna.net') {
            if(location.hostname === 'skojjt-staging.webservices.scouterna.net') {
                document.title += ' Stage';
            } else {
                document.title += ' Dev';
            }
        }

        config = await fetchJson("/api/config");
        await login(false);
        await navigate();
    })();
});
