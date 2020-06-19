/// <reference path="./script.d.ts" />

document.addEventListener("DOMContentLoaded", async () => {
    console.log("script.ts loaded");
    const pingElement = document.getElementById("ping") as HTMLParagraphElement;
    const dbCheckElement = document.getElementById("dbcheck") as HTMLParagraphElement;

    const fetchPromise = fetch("/ping");
    try {
        await fetchPromise;
    } catch (e) {
        console.error(e);
        pingElement.innerText = "Rest-API no respondse.";
        return;
    }
    const response = await fetchPromise;
    if(!response.ok) {
        pingElement.innerText = "Rest-API bad response status.";
        return;
    }
    const jsonPromise = response.json();
    try {
        await jsonPromise;
    } catch (e) {
        console.error(e);
        pingElement.innerText = "Rest-API invalid response.";
        return;
    }
    const json = await jsonPromise;
    if(json.ping !== "pong") {
        pingElement.innerText = "Rest-API bad response.";
        return;
    }

    pingElement.innerText = "Rest-API is working";
    dbCheckElement.innerText = "Testing db-connection?";

    const fetchPromise2 = fetch("/api/dbtest");
    try {
        await fetchPromise2;
    } catch (e) {
        console.error(e);
        dbCheckElement.innerText = "DB-test no response";
        return;
    }
    const response2 = await fetchPromise2;
    if(!response2.ok) {
        dbCheckElement.innerText = "DB-test bad response status.";
        return;
    }
    const jsonPromise2 = response2.json();
    try {
        await jsonPromise2;
    } catch (e) {
        console.error(e);
        dbCheckElement.innerText = "DB-test invalid response";
        return;
    }
    const json2 = await jsonPromise2;
    if(!json2.ok || isNaN(json2.count)) {
        dbCheckElement.innerText = "DB-test bad response";
        return;
    }

    dbCheckElement.innerText = "Database connection is working, counter = " + json2.count + ".";
});
