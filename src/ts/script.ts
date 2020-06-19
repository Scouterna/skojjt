/// <reference path="./script.d.ts" />

document.addEventListener("DOMContentLoaded", async () => {
    console.log("script.ts loaded");
    const pingElement = document.getElementById("ping") as HTMLParagraphElement;
    const dbCheckElement = document.getElementById("dbcheck") as HTMLParagraphElement;

    const fetchJson = async (url: string, fetchOptions?: RequestInit) => {
        const response = await fetch(url, fetchOptions);
        if (!response.ok) {
            throw response;
        }
        return await response.json();
    };

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
});
