"use strict";var __awaiter=function(e,t,o,n){return new(o||(o=Promise))((function(i,r){function a(e){try{l(n.next(e))}catch(e){r(e)}}function c(e){try{l(n.throw(e))}catch(e){r(e)}}function l(e){var t;e.done?i(e.value):(t=e.value,t instanceof o?t:new o((function(e){e(t)}))).then(a,c)}l((n=n.apply(e,t||[])).next())}))};document.addEventListener("DOMContentLoaded",()=>{const e=document.getElementById("whoami"),t=location.origin+"/api/";let o=null,n=!1;const i=(e,t)=>__awaiter(void 0,void 0,void 0,(function*(){const o=yield fetch(e,t);if(!o.ok)throw o;return yield o.json()})),r=o=>__awaiter(void 0,void 0,void 0,(function*(){n=!1,e.innerText="Inte inloggad";const i=((e,o,n)=>__awaiter(void 0,void 0,void 0,(function*(){const i=t+e;o||(o={}),o.headers||(o.headers={}),o.headers.Authorization="Bearer "+(n||localStorage.getItem("ScoutID-JWT-Token"));const r=yield fetch(i,o);if(r.ok)return yield r.json();if(498!==r.status)throw r;if(n)throw r;if(!(yield a(!1)))throw r;o.headers.Authorization="Bearer "+localStorage.getItem("ScoutID-JWT-Token");const c=yield fetch(i,o);if(!c.ok)throw c;return yield c.json()})))("jwt/verify_token",{},o);try{yield i}catch(e){throw console.error(e),e}const r=yield i;if(!1===r.user)throw new Error("No user");const c=r.data.karer?Object.values(r.data.karer):[];let l=null;return c.length>2?l=c.slice(0,c.length-1).join(", ")+" och "+c[c.length-1]:c.length>0&&(l=c.join(" och ")),e.innerText="Inloggad som "+r.data.name+(l?" från "+l:""),n=!0,!0})),a=t=>__awaiter(void 0,void 0,void 0,(function*(){const a=localStorage.getItem("ScoutID-JWT-Token");if(a)try{yield r(a)}catch(e){localStorage.removeItem("ScoutID-JWT-Token")}if(!n){if(!o)return console.error("Loggin failed, as no config was received"),!1;if(!o.jwturl)return console.error("Loggin failed, as there is no jwturl in the received config"),!1;let a=i(o.jwturl,{credentials:"include"});try{yield a}catch(t){if(!t.json)return console.error(t),e.innerText="Inte inloggad",!1;a=t.json();try{yield a}catch(t){return console.error(t),e.innerText="Inte inloggad",!1}}const c=yield a;if(c.ok){try{yield r(c.token)}catch(t){return console.error(t),e.innerText="Inte inloggad",!1}localStorage.setItem("ScoutID-JWT-Token",c.token)}!n&&t&&(location.href=c.url)}return n&&("#!/login/"===location.hash.substr(0,9)?location.hash="#!/"+location.hash.substr(9):"#!/login"===location.hash?location.hash="#!/":t&&c()),n})),c=()=>__awaiter(void 0,void 0,void 0,(function*(){if(document.body.classList.toggle("guest",!n),!n){switch(location.hash){case"#!/login":return a(!0);case"#!/":case"":return}return"#!/login/"===location.hash.substr(0,9)?a(!0):void 0}switch(location.hash){case"#!/":case"":return;case"#!/logout":return localStorage.removeItem("ScoutID-JWT-Token"),n=!1,e.innerText="Inte inloggad",void(location.hash="#!/")}}));window.addEventListener("hashchange",c),__awaiter(void 0,void 0,void 0,(function*(){document.getElementById("login-button").addEventListener("click",e=>{location.hash.length>3&&"#!/"===location.hash.substr(0,3)&&(e.preventDefault(),location.hash="#!/login/"+location.hash.substr(3))}),"skojjt.webservices.scouterna.net"!==location.hostname&&("skojjt-staging.webservices.scouterna.net"===location.hostname?document.title+=" Stage":document.title+=" Dev"),o=yield i("/api/config"),yield a(!1),yield c()}))});
//# sourceMappingURL=es6.js.map
