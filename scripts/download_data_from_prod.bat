rem this file downloads data from prod
rem you need to get the service account's key for this.
rem see here:
rem https://console.cloud.google.com/iam-admin/serviceaccounts
set GOOGLE_APPLICATION_CREDENTIALS=skojjt-e86c432553a1.json

c:\python27\python "c:\Program Files (x86)\Google\google_appengine\appcfg.py" download_data --num_threads=5 --batch_size=100 --application=s~skojjt --url=https://skojjt.appspot.com/_ah/remote_api --kind=Semester --filename=semester_data.sql3
c:\python27\python "c:\Program Files (x86)\Google\google_appengine\appcfg.py" download_data --num_threads=5 --batch_size=100 --application=s~skojjt --url=https://skojjt.appspot.com/_ah/remote_api --kind=ScoutGroup --filename=ScoutGroup_data.sql3
c:\python27\python "c:\Program Files (x86)\Google\google_appengine\appcfg.py" download_data --num_threads=5 --batch_size=100 --application=s~skojjt --url=https://skojjt.appspot.com/_ah/remote_api --kind=Troop --filename=Troop_data.sql3
c:\python27\python "c:\Program Files (x86)\Google\google_appengine\appcfg.py" download_data --num_threads=1 --batch_size=20  --application=s~skojjt --url=https://skojjt.appspot.com/_ah/remote_api --kind=Person --filename=Person_data.sql3
c:\python27\python "c:\Program Files (x86)\Google\google_appengine\appcfg.py" download_data --num_threads=1 --batch_size=100 --application=s~skojjt --url=https://skojjt.appspot.com/_ah/remote_api --kind=Meeting --filename=Meeting_data.sql3
c:\python27\python "c:\Program Files (x86)\Google\google_appengine\appcfg.py" download_data --num_threads=1 --batch_size=20  --application=s~skojjt --url=https://skojjt.appspot.com/_ah/remote_api --kind=TroopPerson --filename=TroopPerson_data.sql3
c:\python27\python "c:\Program Files (x86)\Google\google_appengine\appcfg.py" download_data --num_threads=5 --batch_size=100 --application=s~skojjt --url=https://skojjt.appspot.com/_ah/remote_api --kind=UserPrefs --filename=UserPrefs_data.sql3
