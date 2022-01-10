rem this file downloads data from prod
rem you need to get the service account's key for this.
rem see here:
rem https://console.cloud.google.com/iam-admin/serviceaccounts
set GOOGLE_APPLICATION_CREDENTIALS=skojjt-e86c432553a1.json

set GAE_TOOLS_DIR=%ProgramFiles(x86)%\Google\Cloud SDK\google-cloud-sdk\platform\google_appengine
set PY2="%ProgramFiles(x86)%\Google\Cloud SDK\google-cloud-sdk\platform\bundledpython2\python.exe"

%PY2% "%GAE_TOOLS_DIR%\appcfg.py" download_data --num_threads=1 --batch_size=100 --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=s~skojjt --url=https://skojjt.appspot.com/_ah/remote_api --kind=Semester --filename=semester_data.sql3
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" download_data --num_threads=1 --batch_size=10  --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=s~skojjt --url=https://skojjt.appspot.com/_ah/remote_api --kind=ScoutGroup --filename=ScoutGroup_data.sql3
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" download_data --num_threads=5 --batch_size=100 --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=s~skojjt --url=https://skojjt.appspot.com/_ah/remote_api --kind=Troop --filename=Troop_data.sql3
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" download_data --num_threads=1 --batch_size=5   --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=s~skojjt --url=https://skojjt.appspot.com/_ah/remote_api --kind=Person --filename=Person_data.sql3
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" download_data --num_threads=1 --batch_size=100 --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=s~skojjt --url=https://skojjt.appspot.com/_ah/remote_api --kind=Meeting --filename=Meeting_data.sql3
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" download_data --num_threads=1 --batch_size=20  --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=s~skojjt --url=https://skojjt.appspot.com/_ah/remote_api --kind=TroopPerson --filename=TroopPerson_data.sql3
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" download_data --num_threads=5 --batch_size=100 --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=s~skojjt --url=https://skojjt.appspot.com/_ah/remote_api --kind=UserPrefs --filename=UserPrefs_data.sql3
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" download_data --num_threads=5 --batch_size=100 --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=s~skojjt --url=https://skojjt.appspot.com/_ah/remote_api --kind=Badge --filename=Badge_data.sql3
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" download_data --num_threads=5 --batch_size=100 --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=s~skojjt --url=https://skojjt.appspot.com/_ah/remote_api --kind=BadgeCompleted --filename=BadgeCompleted_data.sql3
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" download_data --num_threads=5 --batch_size=100 --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=s~skojjt --url=https://skojjt.appspot.com/_ah/remote_api --kind=BadgePartDone --filename=BadgePartDone_data.sql3
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" download_data --num_threads=5 --batch_size=100 --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=s~skojjt --url=https://skojjt.appspot.com/_ah/remote_api --kind=BadgeTemplate --filename=BadgeTemplate_data.sql3
