
import time

from dataimport import TaskProgress, RunScoutnetImport

from google.appengine.ext import deferred

from flask import redirect

def startAsyncImport(api_key, groupid, semester_key, user, request):
	taskProgress = TaskProgress(name='Import', return_url=request.url)
	taskProgress.put()
	deferred.defer(importTask, api_key, groupid, semester_key, taskProgress.key, user.key)
	return redirect('/progress/' + taskProgress.key.urlsafe())

def importTask(api_key, groupid, semester_key, taskProgress_key, user_key):
	semester=semester_key.get()
	user = user_key.get()
	progress = None
	for i in range(1, 3):
		progress = taskProgress_key.get()
		if progress is not None:
			break
		time.sleep(1) # wait for the eventual consistency
	try:
		success = RunScoutnetImport(groupid, api_key, user, semester, progress)
		if not success:
			progress.info("Importen misslyckades")
			progress.failed = True
		else:
			progress.info("Import klar")
	except Exception as e: # catch all exceptions so that defer stops running it again (automatic retry)
		progress.info("Importfel: " + str(e))
	progress.done()
