# -*- coding: utf-8 -*-
import time
from data import Semester, TaskProgress, UserPrefs
from dataimport import RunScoutnetImport
from google.appengine.ext import deferred, ndb
from flask import Blueprint, render_template, request, make_response, redirect


import_page = Blueprint('import_page', __name__, template_folder='templates')

@import_page.route('/', methods = ['POST', 'GET'])
def import_():
    user = UserPrefs.current()
    if not user.canImport():
        return "denied", 403

    breadcrumbs = [{'link':'/', 'text':'Hem'},
                   {'link':'/import', 'text':'Import'}]

    currentSemester = Semester.getOrCreateCurrent()
    semesters=[currentSemester]
    semesters.extend(Semester.query(Semester.key!=currentSemester.key))
    if request.method != 'POST':
        return render_template('updatefromscoutnetform.html', heading="Import", breadcrumbs=breadcrumbs, user=user, semesters=semesters)

    api_key = request.form.get('apikey').strip()
    groupid = request.form.get('groupid').strip()
    semester_key=ndb.Key(urlsafe=request.form.get('semester'))
    return startAsyncImport(api_key, groupid, semester_key, user, request)

progress = Blueprint('progress_page', 'progress', template_folder='templates')

@progress.route('/<progress_url>')
@progress.route('/<progress_url>/')
@progress.route('/<progress_url>/<update>')
@progress.route('/<progress_url>/<update>/')
def importProgress(progress_url, update=None):
    if update is not None:
        taskProgress = None
        for i in range(1, 2):
            taskProgress = ndb.Key(urlsafe=progress_url).get()
            if taskProgress is not None:
                break
            time.sleep(1)

        if taskProgress is not None:
            s = taskProgress.toJson()
        else:
            s = '{"messages": ["Error: Hittar inte uppgiften"], "failed": "true", "running": "false"}'

        response = make_response(s)
        response.headers['Content-Type'] = 'application/json'
        return response

    breadcrumbs = [{'link':'/', 'text':'Hem'}, {'link':'/import', 'text':'Import'}]
    return render_template('importresult.html', tabletitle="Importresultat", rowtitle='Result', breadcrumbs=breadcrumbs)

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
    deferred.defer(importTask, api_key, groupid, semester_key, taskProgress.key, user.key)
    return redirect('/progress/' + taskProgress.key.urlsafe())

def importTask(api_key, groupid, semester_key, taskProgress_key, user_key):
    """
    :type api_key: str
    :type groupid: str
    :type semester_key: google.appengine.ext.ndb.Key
    :type taskProgress_key: google.appengine.ext.ndb.Key
    :type user_key: google.appengine.ext.ndb.Key
    """
    semester = semester_key.get()  # type: data.Semester
    user = user_key.get()  # type: data.UserPrefs
    progress = None
    for i in range(1, 3):
        progress = taskProgress_key.get()  # type: data.TaskProgress
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
