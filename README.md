# Skojjt
## Närvarorapportering för scouter. 

*av Martin Green/Tynnereds scoutkår.*

https://skojjt.appspot.com
Prova skojjt.appspot.com, säg till martin@famgreen.se för att få access.

Målet med skojjt är en enkel närvaroregistrering som kan används av alla på avdelning.
Alternativen verkar så undermåliga för vår verksamhet, så ett eget system var den bästa möjligheten.
Man ska kunna göra sin registering direkt när man har mötet.
Det finns en direktkoppling till vårt eget medlemsregister, scoutnet. Vi kan synkronisera nya medlemmar direkt från scoutnet med en knapptryckning.
Det är en web-site som fungerar i mobiltelefon, inget behov av en app. Det ser ut som en app i telefonens browser.
Den hostas på Google app engine. Vilket ger följande fördelar:
* Google står för säkerheten. Användarna loggar in med sina google konton. Administratören sätter access i skojjt, sen kan dom registrera.
* Google står för SSL certifikatet. All trafik går via https.
* Driftsäkerheten är god.
* Det är gratis upp till en viss gräns för trafik och datamängd.
* Om det skulle bli många användare så klarar googles servrar det.

Det finns rapportering av närvaro per grupp (avdelning) som Göteborgs kommun kräver.
Vi har även möjlighet att koppla denna närvaro till andra partners, t ex Sensus studieförbund.

Skojjt implementerar APN/DAK för redovisning till Göteborgs kommun:
http://www.sverigesforeningssystem.se/dak-formatet/vad-ar-dak/
http://ukf.umea.se/aktivitetskort

### [Dokumentation](https://github.com/martin-green/skojjt/wiki)

### Hur man testar/utvecklar i Windows:
* Klona git-repon till lokal dator.
* Installera Python 2.7 och Google App Engine SDK (GAE). 
	https://storage.googleapis.com/appengine-sdks/featured/GoogleAppEngine-1.9.73.msi
* Starta GAE. Lägg till skojjt med File|Add existing application...
* Markera skojjt i listan kicka start, sen browse.
* Man kan också köra Visual Studio Code för att få brytpunkter i koden.

### Hur man testar/utvecklar i Linux:
* Klona git-repon till lokal dator.
* Installera Python 2.7 och Google App Engine SDK (GAE). 
* Konfigurera GAE `gcloud init
* Deploy kod `gcloud app deploy` från git mappen
* Testa appen `gcloud app browse`
