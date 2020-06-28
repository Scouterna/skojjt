/// <reference path="./script.d.ts" />

document.addEventListener("DOMContentLoaded", () => {
    const localStorageTokenKey = 'ScoutID-JWT-Token';
    const main = document.getElementById('main') as HTMLDivElement;
    const whoamiElement = document.getElementById("whoami") as HTMLInputElement;
    const whoamiErrorTest = 'Inte inloggad';
    const apiBaseUrl = location.origin + '/api/';

    let config = null;
    let isLoggedIn = false;
    let isAdmin = false;

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
    const apiPost = async (urlSufix: string, data: any) => {
        return apiFetch(
            urlSufix,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            }
        );
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
        isAdmin = response.admin;
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
            if (!config) {
                console.error('Loggin failed, as no config was received');
                return false;
            }
            if (!config.jwturl) {
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

    const setSection = (section: string) => {
        main.setAttribute('data-section', section);
    };
    const showMenu = () => setSection('mainmenu');
    const reset = () => {
        document.body.classList.toggle('guest', !isLoggedIn);
        document.body.classList.toggle('admin', isAdmin);
        setSection('');
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

            case '#!/import':
                setSection('import');
                break;

            case '#!/logout':
                localStorage.removeItem(localStorageTokenKey);
                isLoggedIn = false;
                whoamiElement.innerText = whoamiErrorTest;
                location.hash = '#!/';
                return;
        }
    };
    window.addEventListener('hashchange', navigate);

    const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
    const showAjaxContent = async (contentInfo: any) => {
        if (!contentInfo.ok) {
            throw contentInfo;
        }
        const contentElement = document.getElementById('ajax-content') as HTMLDivElement;
        contentElement.innerHTML = contentInfo.html;
        setSection('ajax-loaded');
        if (contentInfo.refrechUrl) {
            let lastInfo = contentInfo;
            while (lastInfo.refrechUrl) {
                if(lastInfo.delay) {
                    await sleep(lastInfo.delay * 1000);
                }
                lastInfo = await apiFetch(lastInfo.refrechUrl);
                if (!lastInfo.ok) {
                    throw lastInfo;
                }
                if (lastInfo.html) {
                    contentElement.innerHTML = lastInfo.html;
                } else if (lastInfo.append) {
                    const appendDiv = document.createElement('div');
                    appendDiv.innerHTML = lastInfo.append;
                    contentElement.append(appendDiv);
                }
            }
        }
    };

    const doImport = async () => {
        const karIdInput = document.getElementById('import_kar_id') as HTMLInputElement;
        const apiKeyInput = document.getElementById('import_kar_api_key') as HTMLInputElement;
        let karId = +karIdInput.value;
        let apiKey = apiKeyInput.value.trim();
        if (apiKey.substr(0, 8) === 'https://') {
            let matches = null;
            const regexps = [
                new RegExp('^https://([1-9][0-9]*):([0-9a-f]+)@www\.scoutnet\.se/api/group/memberlist$'),
                new RegExp('^https://www\.scoutnet\.se/api/group/memberlist\?id=([1-9][0-9]*)&(?:amp;)?key=([0-9a-f]+)(?:&|$)')
            ];
            for (const regexp of regexps) {
                matches = regexp.exec(apiKey);
                if (matches) {
                    break;
                }
            }
            if (matches) {
                if (karId > 0) {
                    if (karId !== +matches[1]) {
                        alert('Du angav kar-id: ' + karId + ', men urln innehåll kår-id: ' + matches[1]);
                        return;
                    }
                }
                karId = +matches[1];
                apiKey = matches[2];
            }
        }
        if (karId < 1) {
            alert('Kår-id saknas');
            return;
        }
        if (apiKey.length < 1) {
            alert('Api-nyckel saknas');
            return;
        }
        setSection('loading');
        const importPromise = apiPost('import', {karId, apiKey});
        try {
            await importPromise
        } catch (e) {
            console.error(e);
            alert(e.error || e);
            setSection('import');
        }
        const importInfo = await importPromise;
        try {
            await showAjaxContent(importInfo);
        } catch (e) {
            if (e.ok === false && e.error) {
                console.error(e.error);
                alert(e.error)
                setSection('import');
            } else {
                console.error(e);
            }
        }
        location.hash = '!#/kar/' + karId;
    };

    (async () => {
        const loginButton = document.getElementById('login-button') as HTMLAnchorElement;
        loginButton.addEventListener('click', (event: Event) => {
            if (location.hash.length > 3 && location.hash.substr(0, 3) === '#!/') {
                event.preventDefault();
                location.hash = '#!/login/' + location.hash.substr(3);
            }
        });

        const importKarButton = document.getElementById('import_kar_button') as HTMLInputElement;
        importKarButton.addEventListener('click', doImport);

        /// TODO: replace with live hostname
        if (location.hostname !== 'skojjt.webservices.scouterna.net') {
            if (location.hostname === 'skojjt-staging.webservices.scouterna.net') {
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
