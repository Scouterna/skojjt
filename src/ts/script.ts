/// <reference path="./script.d.ts" />

document.addEventListener("DOMContentLoaded", async () => {
    console.log('script.ts loaded');
    const pingElement = document.getElementById("ping") as HTMLParagraphElement;

    const fetchPromise = fetch("/ping");
    try {
        await fetchPromise;
    } catch (e) {
        console.error(e);
        return;
    }
    const response = await fetchPromise;
    const jsonPromise = response.json();
    try {
        await jsonPromise;
    } catch (e) {
        console.error(e);
        return;
    }
    const json = await jsonPromise;
    pingElement.innerText = json.ping;
});
