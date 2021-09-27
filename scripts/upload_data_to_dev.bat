rem this file uploads data to your dev server
rem use download_data_from_prod.bat to download data from production

c:\python27\python "c:\Program Files (x86)\Google\google_appengine\appcfg.py" upload_data --num_threads=5 --batch_size=100 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --filename=semester_data.sql3 --kind=Semester
c:\python27\python "c:\Program Files (x86)\Google\google_appengine\appcfg.py" upload_data --num_threads=5 --batch_size=100 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --filename=ScoutGroup_data.sql3 --kind=ScoutGroup
c:\python27\python "c:\Program Files (x86)\Google\google_appengine\appcfg.py" upload_data --num_threads=1 --batch_size=50 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --filename=Troop_data.sql3 --kind=Troop
c:\python27\python "c:\Program Files (x86)\Google\google_appengine\appcfg.py" upload_data --num_threads=1 --batch_size=20 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --filename=Person_data.sql3 --kind=Person
c:\python27\python "c:\Program Files (x86)\Google\google_appengine\appcfg.py" upload_data --num_threads=1 --batch_size=50 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --filename=Meeting_data.sql3 --kind=Meeting
c:\python27\python "c:\Program Files (x86)\Google\google_appengine\appcfg.py" upload_data --num_threads=1 --batch_size=50 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --filename=TroopPerson_data.sql3 --kind=TroopPerson
c:\python27\python "c:\Program Files (x86)\Google\google_appengine\appcfg.py" upload_data --num_threads=1 --batch_size=50 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --filename=UserPrefs_data.sql3 --kind=UserPrefs

c:\python27\python "c:\Program Files (x86)\Google\google_appengine\appcfg.py" upload_data --num_threads=1 --batch_size=100 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --kind=Badge --filename=Badge_data.sql3
c:\python27\python "c:\Program Files (x86)\Google\google_appengine\appcfg.py" upload_data --num_threads=1 --batch_size=100 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --kind=BadgeCompleted --filename=BadgeCompleted_data.sql3
c:\python27\python "c:\Program Files (x86)\Google\google_appengine\appcfg.py" upload_data --num_threads=1 --batch_size=100 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --kind=BadgePartDone --filename=BadgePartDone_data.sql3
c:\python27\python "c:\Program Files (x86)\Google\google_appengine\appcfg.py" upload_data --num_threads=1 --batch_size=100 --application=dev~skojjt --url=http://localhost:56035/_ah/remote_api --kind=BadgeTemplate --filename=BadgeTemplate_data.sql3
