# -*- coding: utf-8 -*-
import time
import logging
from google.appengine.api import memcache
from data import Semester, UserPrefs
from dataimport import RunScoutnetImport
from threading import Thread
from flask import Blueprint, render_template, request, redirect
from progress import TaskProgress
import traceback

import_page = Blueprint('import_page', __name__, template_folder='templates')

@import_page.route('/', methods = ['POST', 'GET'])
def import_():
    user = UserPrefs.current()
    if not user.canImport():
        return "denied", 403

    breadcrumbs = [{'link':'/', 'text':'Hem'},
                   {'link':'/import', 'text':'Import'}]

    groupid = ""
    apikey = ""
    if user.groupaccess is not None:
        scoutgroup = user.groupaccess.get()
        apikey = scoutgroup.apikey_all_members
        groupid = scoutgroup.scoutnetID

    if request.method == 'POST':
        apikey = request.form.get('apikey').strip()
        groupid = request.form.get('groupid').strip()
        semester_key = Semester.getOrCreateCurrent().key
        return startAsyncImport(apikey, groupid, semester_key, user, request)

    return render_template('updatefromscoutnetform.html',
                            heading="Import",
                            breadcrumbs=breadcrumbs,
                            user=user,
                            groupid=groupid,
                            apikey=apikey)


def startAsyncImport(api_key, groupid, semester_key, user, request):
    """
    :type api_key: str
    :type groupid: str
    :type semester_key: google.appengine.ext.ndb.Key
    :type user: data.UserPrefs
    :type request: werkzeug.local.LocalProxy
    :rtype werkzeug.wrappers.response.Response
    """
    taskProgress = TaskProgress(name='Import', return_url=request.url)
    logging.info(f"Starting import thread for progress={taskProgress.urlsafe()}")
    t = Thread(target=importTask, args=[api_key, groupid, semester_key, taskProgress.key, user.key])
    t.start()
    logging.info(f"Started import thread for progress={taskProgress.urlsafe()}")
    return redirect('/progress/' + taskProgress.urlsafe())

def importTask(api_key, groupid, semester_key, taskProgress_key, user_key):
    """
    :type api_key: str
    :type groupid: str
    :type semester_key: google.appengine.ext.ndb.Key
    :type taskProgress_key: google.appengine.ext.ndb.Key
    :type user_key: google.appengine.ext.ndb.Key
    """
    logging.info(f"importTask thread running for progress={taskProgress_key}")

    start_time = time.time()
    semester = semester_key.get()  # type: data.Semester
    user = user_key.get()  # type: data.UserPrefs
    progress = TaskProgress.getTaskProgress(taskProgress_key)
    import_task_mutex = "import_task:" + groupid
    if not memcache.add(import_task_mutex, True): # add returns false if the key already exist
        progress.error(f"Import already running for group: {groupid}")
        return

    try:
        success = RunScoutnetImport(groupid, api_key, user, semester, progress)
        if not success:
            progress.info("Importen misslyckades")
            progress.failed = True
        else:
            progress.info("Import klar")
            if user.groupaccess is not None:
                progress.info('<a href="/start/%s/">Gå till scoutkåren</a>' % (user.groupaccess.urlsafe()))
    except Exception as e: # catch all exceptions so that defer stops running it again (automatic retry)
        logging.error("Importfel: " + str(e) + "CS:" + traceback.format_exc())
        progress.error("Importfel: " + str(e) + "CS:" + traceback.format_exc())
    finally:
        memcache.delete(import_task_mutex)

    end_time = time.time()
    time_taken = end_time - start_time
    progress.info("Tid: %s s" % str(time_taken))

    progress.done()
    logging.info("import klar!")
