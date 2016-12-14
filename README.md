#Skojjt
##Närvarorapportering för scouter. 

*av Martin Green/Tynnereds scoutkår.*

https://skojjt.appspot.com
Prova skojjt.appspot.com, säg till martin@famgreen.se för att få access.

Målet med skojjt är en enkel närvaroregistrering som kan används av alla på avdelning. Samt att göra rapporteringen enkel (ingen excel).
Alternativen verkar så undermåliga för vår verksamhet, så ett eget system var den bästa möjligheten.
Man ska kunna göra sin registering direkt när man har mötet.
Det finns en direktkoppling till vårt eget medlemsregister, scoutnet. Vi kan synkronisera nya medlemmar direkt från scoutnet med en knapptryckning.
Det är en web-site som fungerar i mobiltelefon, inget behov av en app. Det ser ut som en app i telefonens browser.
Den hostas på Google app engine. Vilket ger följande fördelar:
* Google står för säkerheten. Användarna loggar in med sina google konton. Administratören sätter access i skojjt, sen kan dom registrera.
* google står för SSL certifikatet. All trafik går via https.
* Driftsäkerheten är god.
* Det är gratis upp till en viss gräns för trafik och datamängd (mer memcache behövs, för att begränsa data läsningar).
* Om det skulle bli många användare så klarar googles servrar det.

Det finns rapportering av närvaro per grupp (avdelning) som Göteborgs kommun kräver.
Vi har även möjlighet att koppla denna närvaro till andra partners, t ex Sensus studieförbund.

Skojjt implementerar DAK för redovisning till Göteborgs kommun:
http://www.sverigesforeningssystem.se/dak-formatet/vad-ar-dak/

###Dokumentation
[Wiki](/martin-green/skojjt/wiki)

###Hur man testar/utvecklar
Klona git-repon till lokal dator.
Installera Python 2.7 och Google App Engine SDK (GAE). 
Starta GAE. Lägg till skojjt med File|Add existing application...
Markera skojjt i listan kicka start, sen browse.
Man kan också köra Visual Studio Code för att få brytpunkter i koden.

Om du kör på windows och får felet:
"ImportError: cannot import name RAND_egd"
Editera:
C:\Prgram Files (x86)\Google\google_appengine\google\appengine\dist27\socket.py
ta bort: RAND_egd from line 73:
from _ssl import RAND_add, RAND_egd, RAND_status, SSL_ERROR_ZERO_RETURN, SSL_ERROR_WANT_READ, SSL_ERROR_WANT_WRITE, SSL_ERROR_WANT_X509_LOOKUP, SSL_ERROR_SYSCALL, SSL_ERROR_SSL, SSL_ERROR_WANT_CONNECT, SSL_ERROR_EOF, SSL_ERROR_INVALID_ERROR_CODE
