# Changelog

Ändringslogg för Skojjt

## [2.0.0]

Skojjt kör nu på Python 3.11!

Tanken med uppdateringen är att gå till Python 3 utan att det märks för användare.

### Viktiga ändringar från Python 2.7 Google App Engine till Python 3

Google insåg sitt misstag att ta bort alla bra hjälpsystem när man byter till Py3. Så det finns ett hjälp-bibliotek på github:
https://github.com/GoogleCloudPlatform/appengine-python-standard/network

Då får man tillbaka: 
* google.appengine.api.memcache
* google.appengine.api.users
* google.appengine.ext.ndb
* google.appengine.api.mail
* google.appengine.api.app_identity
* google.appengine.runtime.apiproxy_errors

Pga en bugg i appengine-python-standard används nu en patchad version:
https://github.com/martin-green/appengine-python-standard

Däremot verkar deferred inte fungera, den kräver en handler url _ah/queue/deferred som måste vara utan inloggning. Nu kan man bara ha en handler i app.yaml och den måste ha inloggning. 
Men python trådning fungerar, så vi behöver inte deferred längre. Alla deferred är ersatta med Threading.thread.

Alla filer måste servas från /static på servern flask mappar om den katalogen till /. Så resultatet är samma men filerna har flyttat ner i /static.

Ett stort problem är att det inte går att köra lokalt längre, memcache mm fungerar inte. dev_appserver.py kör en instans av Python 2.7 men springer ändå in i python 3 kod, så den krashar. 
Man får print debugga på en server.

#### Python 2.7 - Python 3

Ändringar:

urllib2 blir urllib.error, urllib.parse, urllib.request

urllib.urlencode -> urllib.parse.urlencode

list.sort() måste använda functools.cmp_to_key för att sortera med jämförelse a,b

dict.iteritems() blir dict.items()

zip(a,b) -> list(zip(a,b)) ger en lista i py3.

