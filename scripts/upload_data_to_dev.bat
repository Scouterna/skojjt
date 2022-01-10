rem this file uploads data to your dev server
rem use download_data_from_prod.bat to download data from production

set GAE_TOOLS_DIR=%ProgramFiles(x86)%\Google\Cloud SDK\google-cloud-sdk\platform\google_appengine
set PY2="%ProgramFiles(x86)%\Google\Cloud SDK\google-cloud-sdk\platform\bundledpython2\python.exe"

%PY2% "%GAE_TOOLS_DIR%\appcfg.py" upload_data --num_threads=1 --batch_size=100 --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --filename=semester_data.sql3 --kind=Semester
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" upload_data --num_threads=1 --batch_size=100 --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --filename=ScoutGroup_data.sql3 --kind=ScoutGroup
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" upload_data --num_threads=1 --batch_size=50  --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --filename=Troop_data.sql3 --kind=Troop
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" upload_data --num_threads=1 --batch_size=5   --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --filename=Person_data.sql3 --kind=Person
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" upload_data --num_threads=1 --batch_size=50  --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --filename=Meeting_data.sql3 --kind=Meeting
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" upload_data --num_threads=1 --batch_size=50  --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --filename=TroopPerson_data.sql3 --kind=TroopPerson
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" upload_data --num_threads=1 --batch_size=50  --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --filename=UserPrefs_data.sql3 --kind=UserPrefs
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" upload_data --num_threads=1 --batch_size=100 --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --kind=Badge --filename=Badge_data.sql3
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" upload_data --num_threads=1 --batch_size=100 --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --kind=BadgeCompleted --filename=BadgeCompleted_data.sql3
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" upload_data --num_threads=1 --batch_size=100 --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --kind=BadgePartDone --filename=BadgePartDone_data.sql3
%PY2% "%GAE_TOOLS_DIR%\appcfg.py" upload_data --num_threads=1 --batch_size=100 --bandwidth_limit=25000000 --rps_limit=1000000 --http_limit=80 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --kind=BadgeTemplate --filename=BadgeTemplate_data.sql3
