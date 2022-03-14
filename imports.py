# -*- coding: utf-8 -*-
import time
from data import Semester, UserPrefs, dbcontext
from dataimport import RunScoutnetImport
from google.appengine.ext import deferred, ndb
from flask import Blueprint, render_template, request, make_response, redirect
from progress import TaskProgress
import traceback
import access

import_page = Blueprint('import_page', __name__, template_folder='templates')

@import_page.route('/', methods = ['POST', 'GET'])
@dbcontext
@access.canImport
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

    semesters = Semester.getAllSemestersSorted()
    if request.method == 'POST':
        apikey = request.form.get('apikey').strip()
        groupid = request.form.get('groupid').strip()
        semester_key=ndb.Key(urlsafe=request.form.get('semester'))
        return startAsyncImport(apikey, groupid, semester_key, user, request)

    return render_template('updatefromscoutnetform.html',
                            heading="Import",
                            breadcrumbs=breadcrumbs,
                            user=user,
                            semesters=semesters,
                            groupid=groupid,
                            apikey=apikey)


@dbcontext
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
    taskProgress.put()
    deferred.defer(importTask, api_key, groupid, semester_key, taskProgress.key, user.key, _queue="import")
    return redirect('/progress/' + taskProgress.key.urlsafe())

@dbcontext
def importTask(api_key, groupid, semester_key, taskProgress_key, user_key):
    """
    :type api_key: str
    :type groupid: str
    :type semester_key: google.appengine.ext.ndb.Key
    :type taskProgress_key: google.appengine.ext.ndb.Key
    :type user_key: google.appengine.ext.ndb.Key
    """
    start_time = time.time()
    semester = semester_key.get()  # type: data.Semester
    user = user_key.get()  # type: data.UserPrefs
    progress = TaskProgress.getTaskProgress(taskProgress_key)
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
        progress.error("Importfel: " + str(e) + "CS:" + traceback.format_exc())

    end_time = time.time()
    time_taken = end_time - start_time
    progress.info("Tid: %s s" % str(time_taken))

    progress.done()
