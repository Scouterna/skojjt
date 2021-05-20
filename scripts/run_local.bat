cd /d %~dp0
cd ..
c:\Python27\python "c:\Program Files (x86)\Google\google_appengine\dev_appserver.py" app.yaml -A skojjt --port 8080 --admin_port 8000 --api_port 56035 --enable_console

rem datastore location: %temp%\appengine.skojjt\datastore.db