cd /d %~dp0
cd ..

set GAE_BIN_DIR=%ProgramFiles(x86)%\Google\Cloud SDK\google-cloud-sdk\bin
set PY2="%ProgramFiles(x86)%\Google\Cloud SDK\google-cloud-sdk\platform\bundledpython2\python.exe"

%PY2% "%GAE_BIN_DIR%\dev_appserver.py" app.yaml -A skojjt --port 8080 --admin_port 8000 --api_port 56035 --enable_console --skip_sdk_update_check

rem datastore location: %temp%\appengine.skojjt\datastore.db