/// <reference path="./script.d.ts" />

document.addEventListener("DOMContentLoaded", () => {
    const localStorageTokenKey = 'ScoutID-JWT-Token';
    const whoamiElement = document.getElementById("whoami") as HTMLInputElement;

    const fetchJson = async (url: string, fetchOptions?: RequestInit) => {
        const response = await fetch(url, fetchOptions);
        if (!response.ok) {
            throw response;
        }
        return await response.json();
    };

    const verifyToken = async (token: string) => {
        whoamiElement.innerText = "Logged in as ??? from ???";
        return true;
    };
    const login = async (byUser: boolean): Promise<boolean> => {
        let jwtPromise = fetchJson("https://beta.scoutid.se/jwt/jwt.php", {credentials: 'include'});
        try {
            await jwtPromise;
        } catch (e) {
            if (!e.json) {
                console.error(e);
                whoamiElement.innerText = "Not logged in";
                return false;
            }
            jwtPromise = e.json();
            try {
                await jwtPromise;
            } catch (e) {
                console.error(e);
                whoamiElement.innerText = "Not logged in";
                return false;
            }
        }
        const jwtResponse = await jwtPromise as ScoutId.jwtResponse;
        if (jwtResponse.ok) {
            try {
                await verifyToken(jwtResponse.token);
            } catch (e) {
                console.error(e);
                whoamiElement.innerText = "Not logged in";
                return false;
            }
            localStorage.setItem(localStorageTokenKey, jwtResponse.token);
            return true;
        }

        if (byUser) {
            location.href = (jwtResponse as ScoutId.jwtBadResponse).url;
        }

        return false;
    };


    //<editor-fold desc="Ping & db-test">
    (async () => {
        const pingElement = document.getElementById("ping") as HTMLParagraphElement;
        const dbCheckElement = document.getElementById("dbcheck") as HTMLParagraphElement;
        const pingPromise = fetchJson("/ping");
        try {
            await pingPromise;
        } catch (e) {
            console.error(e);
            pingElement.innerText = "Rest-API failed: " + (e.statusText || e);
            return;
        }
        const ping = await pingPromise;
        if (ping.ping !== "pong") {
            pingElement.innerText = "Rest-API bad response.";
            return;
        }

        pingElement.innerText = "Rest-API is working";
        dbCheckElement.innerText = "Testing db-connection?";

        const dbTestPromise = fetchJson("/api/dbtest");
        try {
            await dbTestPromise;
        } catch (e) {
            console.error(e);
            dbCheckElement.innerText = "DB-test failed: " + (e.statusText || e);
            return;
        }
        const dbTest = await dbTestPromise;
        if (!dbTest.ok || isNaN(dbTest.count)) {
            dbCheckElement.innerText = "DB-test bad response";
            return;
        }

        dbCheckElement.innerText = "Database connection is working, counter = " + dbTest.count + ".";
    })();
    //</editor-fold>

    (() => {
        const loginForm = document.getElementById("login") as HTMLFormElement;

        loginForm.addEventListener("submit", async (event: Event) => {
            event.preventDefault();
            loginForm.hidden = true;
            await login(true);
        });
        return login(false);
    })();
});
