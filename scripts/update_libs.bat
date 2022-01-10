cd /d %~dp0
cd ..

set PY2="%ProgramFiles(x86)%\Google\Cloud SDK\google-cloud-sdk\platform\bundledpython2\python.exe"
%PY2% -m pip install -r requirements.txt -t lib
