# Skojjt
Närvarorapportering för scouter.

Det här är en utvecklings branch för konverteringen av Skojjt från GAE till Azure.

Fil Structur:
 * i k8s-mappen ligger configurationen av azure och kubernets
 * i config-mappen ligger inställningar för docker-containern, inklusive requirements.txt med vilka python paket som ska installeras.
 * i app-mappen ligger backend: python flask med flast_rest, varav app.py innehåller mappningen av url:r till klasser/funktioner.
 * i src-mappen ligger frontend: html, less och typescript. Kompileras med gulp. (npm install , sudo npm install gulp -g, gulp)
 * i build-mappen ligger den kompilerade frontenden
 
URL Structur:
  * / -> /build/index.html
  * /favicon.ico -> /build/favicon.png
  * /src/* -> statiska filer från /src/ (för att .map-filerna ska fungera)
  * /* -> statiska filer från /build/
  * /* -> dynamiskt content enligt /app/app.py
  * (ovan är konfigurerat i /config/nginx.server.conf, se även COPY-raderna i /Dockerfile)


Använd följande kommando för att bygga och starta servern:
```
docker-compose up --build
```

Du kommer åt servern på [http://localhost:8080](http://localhost:8080)
