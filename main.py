# -*- coding: utf-8 -*-
import datetime
import logging
import scoutnet
import sys
import time
from data import Meeting, Person, ScoutGroup, Semester, TaskProgress, Troop, TroopPerson, UserPrefs
from flask import Flask, make_response, redirect, render_template, request
from dataimport import dosettroopsemester, GetBackupXML, UpdateSchemas
from imports import import_page, progress
from google.appengine.ext import deferred
from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.ext import ndb
from groupsummary import groupsummary
from persons import persons
from scoutgroupinfo import scoutgroupinfo
from start import start
import traceback
from badges import badges

app = Flask(__name__)
app.debug = True
# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.

reload(sys)
sys.setdefaultencoding('utf8')


@app.route('/')
def home():
    breadcrumbs = [{'link':'/', 'text':'Hem'}]
    user = UserPrefs.current()
    user.attemptAutoGroupAccess()
    starturl = '/start/'
    personsurl = '/persons/'
    badgesurl = '/badges/'
    if user.groupaccess != None:
        starturl += user.groupaccess.urlsafe() + '/'
        personsurl += user.groupaccess.urlsafe() + '/'
        badgesurl += user.groupaccess.urlsafe() + '/'
    return render_template('start.html',
                           heading='Hem',
                           items=[],
                           breadcrumbs=breadcrumbs,
                           user=user,
                           starturl=starturl,
                           personsurl=personsurl,
                           badgesurl=badgesurl,
                           logouturl=users.create_logout_url('/')
                           )

app.register_blueprint(start, url_prefix='/start')
app.register_blueprint(persons, url_prefix='/persons')
app.register_blueprint(badges, url_prefix='/badges')
app.register_blueprint(scoutgroupinfo, url_prefix='/scoutgroupinfo')
app.register_blueprint(groupsummary, url_prefix='/groupsummary')
app.register_blueprint(import_page, url_prefix='/import')
app.register_blueprint(progress, url_prefix='/progress')

@app.route('/getaccess/', methods = ['POST', 'GET'])
def getaccess():
    user = UserPrefs.current()
    breadcrumbs = [{'link':'/', 'text':'Hem'}]
    baselink = "/getaccess/"
    section_title = "Access"
    breadcrumbs.append({'link':baselink, 'text':section_title})
    if request.method == "POST":
        adminEmails = [u.email for u in UserPrefs.query(UserPrefs.hasadminaccess==True).fetch()]
        if len(adminEmails) > 0:
            scoutgroup_name = request.form.get('sg').strip()
            mail.send_mail(sender=user.email,
            to=','.join(adminEmails),
            subject="Användren: " + user.getname() + " vill ha access.\nKår: " + scoutgroup_name,
            body="""""")
        return redirect('/')
    else:
        return render_template('getaccess.html',
            baselink=baselink,
            breadcrumbs=breadcrumbs)


@app.route('/admin')
@app.route('/admin/')
def admin():
    user = UserPrefs.current()
    if not user.isAdmin():
        return "denied", 403

    breadcrumbs = [{'link':'/', 'text':'Hem'},
                   {'link':'/admin', 'text':'Admin'}]
    return render_template('admin.html', heading="Admin", breadcrumbs=breadcrumbs, username=user.getname())


@app.route('/admin/access/')
@app.route('/admin/access/<userprefs_url>')
@app.route('/admin/access/<userprefs_url>/', methods = ['POST', 'GET'])
def adminaccess(userprefs_url=None):
    user = UserPrefs.current()
    if not user.isAdmin():
        return "denied", 403

    section_title = u'Hem'
    baselink = '/'
    breadcrumbs = [{'link':baselink, 'text':section_title}]

    section_title = u'Admin'
    baselink += 'admin/'
    breadcrumbs.append({'link':baselink, 'text':section_title})

    section_title = u'Access'
    baselink += 'access/'
    breadcrumbs.append({'link':baselink, 'text':section_title})

    if userprefs_url != None:
        userprefs = ndb.Key(urlsafe=userprefs_url).get()
        if request.method == 'POST':
            userprefs.hasaccess = request.form.get('hasAccess') == 'on'
            userprefs.hasadminaccess = request.form.get('hasAdminAccess') == 'on'
            userprefs.groupadmin = request.form.get('groupadmin') == 'on'
            userprefs.canimport = request.form.get('canImport') == 'on'
            sgroup_key = None
            if len(request.form.get('groupaccess')) != 0:
                sgroup_key = ndb.Key(urlsafe=request.form.get('groupaccess'))
            userprefs.groupaccess = sgroup_key
            userprefs.put()
        else:
            section_title = userprefs.getname()
            baselink += userprefs_url + '/'
            breadcrumbs.append({'link':baselink, 'text':section_title})
            return render_template('userprefs.html',
                heading=section_title,
                baselink=baselink,
                userprefs=userprefs,
                breadcrumbs=breadcrumbs,
                scoutgroups=ScoutGroup.query().fetch())

    users = UserPrefs().query().fetch()
    return render_template('userlist.html',
        heading=section_title,
        baselink=baselink,
        users=users,
        breadcrumbs=breadcrumbs)


@app.route('/groupaccess')
@app.route('/groupaccess/')
@app.route('/groupaccess/<userprefs_url>')
def groupaccess(userprefs_url=None):
    user = UserPrefs.current()
    if not user.isGroupAdmin():
        return "denied", 403

    section_title = u'Hem'
    baselink = '/'
    breadcrumbs = [{'link':baselink, 'text':section_title}]

    section_title = u'Kåraccess'
    baselink += 'groupaccess/'
    breadcrumbs.append({'link':baselink, 'text':section_title})

    if userprefs_url != None:
        userprefs = ndb.Key(urlsafe=userprefs_url).get()
        groupaccessurl = request.args["setgroupaccess"]
        if groupaccessurl == 'None':
            userprefs.groupaccess = None
        else:
            userprefs.groupaccess = ndb.Key(urlsafe=groupaccessurl)
            userprefs.hasaccess = True
        userprefs.put()

    users = UserPrefs().query(UserPrefs.groupaccess == None).fetch()
    users.extend(UserPrefs().query(UserPrefs.groupaccess == user.groupaccess).fetch())
    return render_template('groupaccess.html',
        heading=section_title,
        baselink=baselink,
        users=users,
        breadcrumbs=breadcrumbs,
        mygroupurl=user.groupaccess.urlsafe(),
        mygroupname=user.groupaccess.get().getname())


# merge scoutgroups with different names (renamed in scoutnet):
@app.route('/admin/merge_sg/', methods = ['POST', 'GET'])
def adminMergeScoutGroups():
    user = UserPrefs.current()
    if not user.isAdmin():
        return "denied", 403

    section_title = u'Hem'
    baselink = '/'
    breadcrumbs = [{'link':baselink, 'text':section_title}]

    section_title = u'Admin'
    baselink += 'admin/'
    breadcrumbs.append({'link':baselink, 'text':section_title})

    section_title = u'Merge SG'
    baselink += 'merge_sg/'
    breadcrumbs.append({'link':baselink, 'text':section_title})

    if request.method == 'POST':
        oldname = request.form.get('oldname').strip()
        newname = request.form.get('newname').strip()
        commit = request.form.get('commit') == 'on'
        move_users = request.form.get('move_users') == 'on'
        move_persons = request.form.get('move_persons') == 'on'
        move_troops = request.form.get('move_troops') == 'on'
        delete_sg = request.form.get('delete_sg') == 'on'
        semester_id =  request.form.get('semester')
        return startAsyncMergeSG(oldname, newname, commit, user, move_users, move_persons, move_troops, delete_sg, semester_id)
    else:
        return render_template('merge_sg.html',
            heading=section_title,
            baselink=baselink,
            breadcrumbs=breadcrumbs,
            semesters=Semester.query().fetch())

"""
How to handle tasks 
List all tasks:
> gcloud tasks list --queue=default

Delete a task:
> gcloud tasks delete <task-name> --queue=default
"""
def startAsyncMergeSG(oldname, newname, commit, user, move_users, move_persons, move_troops, delete_sg, semester_id):
    """
    :type oldname: str
    :type newname: str
    :type commit: Boolean
    :type user: data.UserPrefs
    :type move_users Boolean
    :type move_persons Boolean
    :type move_troops Boolean
    :type delete_sg Boolean
    :type semester_id str
    """
    taskProgress = TaskProgress(name='MergeSG', return_url=request.url)
    taskProgress.put()
    deferred.defer(merge_sg_deferred, oldname, newname, commit, taskProgress.key, user.key, move_users, move_persons, move_troops, delete_sg, semester_id, _queue="admin")
    return redirect('/progress/' + taskProgress.key.urlsafe())

def merge_sg_deferred(oldname, newname, commit, taskProgress_key, user_key, move_users, move_persons, move_troops, delete_sg, semester_id):
    try:
        user = user_key.get()  # type: data.UserPrefs
        taskProgress = None
        for i in range(1, 3):
            taskProgress = taskProgress_key.get()  # type: data.TaskProgress
            if taskProgress is not None:
                break
            time.sleep(1) # wait for the eventual consistency

        merge_scout_group(oldname, newname, commit, taskProgress, user, move_users, move_persons, move_troops, delete_sg, semester_id)

    except Exception as e:
        # catch all exceptions so that defer stops running it again (automatic retry)
        taskProgress.error(str(e) + "CS:" + traceback.format_exc())

    try:
        taskProgress.done()
    except Exception as e:
        pass

def merge_scout_group(oldname, newname, commit, taskProgress, user, move_users, move_persons, move_troops, delete_sg, semester_id):
    start_time = time.time()
    oldsg = ScoutGroup.getbyname(oldname)
    if oldsg is None:
        raise RuntimeError("Old sg name:%s not found" % oldname)

    newsg = ScoutGroup.getbyname(newname)
    if newsg is None:
        raise RuntimeError("New sg name:%s not found" % newname)

    if not commit:
        taskProgress.info("*** testmode ***")

    keys_to_delete = []
    entities_to_put_first = []
    entities_to_put = []

    taskProgress.info("termin: %s" % semester_id)
    
    convertsemester = Semester.getbyId(semester_id)
    if convertsemester is None:
        taskProgress.error("termin: %s does not exist" % semester_id)

    currentsemester = Semester.getOrCreateCurrent()

    if move_users:
        taskProgress.info("Update all users to the new scoutgroup")
        for u in UserPrefs.query(UserPrefs.groupaccess == oldsg.key).fetch():
            logging.info(" * * moving user for %s" % (u.getname()))
            u.groupaccess = newsg.key
            u.activeSemester = currentsemester.key
            entities_to_put.append(u)

    if move_persons:
        taskProgress.info("Moving all persons to the new ScoutGroup:%s" % newsg.getname())
        for oldp in Person.query(Person.scoutgroup == oldsg.key).fetch():
            oldp.scoutgroup = newsg.key
            entities_to_put.append(oldp)

    if move_troops:
        taskProgress.info("Move all troops to the new ScoutGroup:%s, semester: %s" % (newsg.getname(), convertsemester.getname()))
        for oldt in Troop.query(Troop.scoutgroup == oldsg.key, Troop.semester_key == convertsemester.key).fetch():
            taskProgress.info(" * found old troop for %s, semester=%s" % (str(oldt.key.id()), oldt.semester_key.get().getname()))
            keys_to_delete.append(oldt.key)
            newt = Troop.get_by_id(Troop.getid(oldt.scoutnetID, newsg.key, oldt.semester_key), use_memcache=True)
            if newt is None:
                taskProgress.info(" * * creating new troop for %s, semester=%s" % (str(oldt.key.id()), oldt.semester_key.get().getname()))
                newt = Troop.create(oldt.name, oldt.scoutnetID, newsg.key, oldt.semester_key)
                entities_to_put_first.append(newt) # put first to be able to reference it
            else:
                taskProgress.info(" * * already has new troop for %s, semester=%s" % (str(newt.key.id()), newt.semester_key.get().getname()))

            taskProgress.info(" * Move all trooppersons to the new group")
            for oldtp in TroopPerson.query(TroopPerson.troop == oldt.key).fetch():
                keys_to_delete.append(oldtp.key)
                newtp = TroopPerson.get_by_id(TroopPerson.getid(newt.key, oldtp.person), use_memcache=True)
                if newtp is None:
                    logging.info(" * * creating new TroopPerson for %s:%s" % (newt.getname(), oldtp.getname()))
                    newtp = TroopPerson.create(newt.key, oldtp.person, oldtp.leader)
                    entities_to_put.append(newtp)
                else:
                    logging.info(" * * already has TroopPerson for %s:%s" % (newt.getname(), oldtp.getname()))

            taskProgress.info(" * Move all old meetings to the new troop")
            for oldm in Meeting.query(Meeting.troop==oldt.key).fetch():
                keys_to_delete.append(oldm.key)
                newm = Meeting.get_by_id(Meeting.getId(oldm.datetime, newt.key), use_memcache=True)
                if newm is None:
                    logging.info(" * * creating new Meeting for %s:%s" % (newt.getname(), oldm.datetime.strftime("%Y-%m-%d %H:%M")))
                    newm = Meeting(id=Meeting.getId(oldm.datetime, newt.key),
                                        datetime=oldm.datetime,
                                        name=oldm.name,
                                        troop=newt.key,
                                        duration=oldm.duration,
                                        ishike=oldm.ishike)
                    newm.attendingPersons = oldm.attendingPersons
                    entities_to_put.append(newm)
                else:
                    logging.info(" * * merging Meeting %s->%s :%s" % (oldm.getname(), newm.getname(), oldm.datetime.strftime("%Y-%m-%d %H:%M")))
                    need_to_put = False
                    if len(oldm.name) > len(newm.name): # take the longer name.
                        newm.name = oldm.name
                        need_to_put = True
                    
                    for oldattendingpersonkey in oldm.attendingPersons:
                        if oldattendingpersonkey not in newm.attendingPersons:
                            newm.attendingPersons.append(oldattendingpersonkey)
                            need_to_put = True
                    
                    if need_to_put:
                        entities_to_put.append(newm)

        if delete_sg:
            keys_to_delete.append(oldsg.key)

    taskProgress.info("time before put: %s s" % str(time.time() - start_time))

    logging.info("Putting %d entities first" % len(entities_to_put_first))
    if commit: ndb.put_multi(entities_to_put_first)
    logging.info("Putting %d entities" % len(entities_to_put))
    if commit: ndb.put_multi(entities_to_put)
    logging.info("Deleting %d keys" % len(keys_to_delete))
    if commit: ndb.delete_multi(keys_to_delete)
    logging.info("clear memcache")
    if commit: ndb.get_context().clear_cache()

    taskProgress.info("Done! time: %s s" % str(time.time() - start_time))


# cron job:
@app.route('/tasks/cleanup')
@app.route('/tasks/cleanup/')
def tasksCleanup():
    TaskProgress.cleanup()
    return "", 200


@app.route('/admin/deleteall/')
def dodelete():
    user = UserPrefs.current()
    if not user.isAdmin():
        return "denied", 403

    # DeleteAllData() # uncomment to enable this
    return redirect('/admin/')


@app.route('/admin/settroopsemester/')
def settroopsemester():
    user = UserPrefs.current()
    if not user.isAdmin():
        return "denied", 403

    dosettroopsemester()
    return redirect('/admin/')

@app.route('/admin/updateschemas')
def doupdateschemas():
    user = UserPrefs.current()
    if not user.isAdmin():
        return "denied", 403

    UpdateSchemas()
    return redirect('/admin/')

@app.route('/admin/setcurrentsemester')
def setcurrentsemester():
    user = UserPrefs.current()
    if not user.isAdmin():
        return "denied", 403

    semester = Semester.getOrCreateCurrent()
    for u in UserPrefs.query().fetch():
        u.activeSemester = semester.key
        u.put()

    return redirect('/admin/')

@app.route('/admin/autoGroupAccess')
def autoGroupAccess():
    user = UserPrefs.current()
    if not user.isAdmin():
        return "denied", 403
    users = UserPrefs().query().fetch()
    for u in users:
        u.attemptAutoGroupAccess()

    return "done"


@app.route('/admin/backup')
@app.route('/admin/backup/')
def dobackup():
    user = UserPrefs.current()
    if not user.isAdmin():
        return "denied", 403

    response = make_response(GetBackupXML())
    response.headers['Content-Type'] = 'application/xml'
    thisdate = datetime.datetime.now()
    response.headers['Content-Disposition'] = 'attachment; filename=skojjt-backup-' + str(thisdate.isoformat()) + '.xml'
    return response

@app.route('/admin/test_email')
@app.route('/admin/test_email/')
def adminTestEmail():
    user = UserPrefs.current()
    scoutnet.sendRegistrationQueueInformationEmail(user.groupaccess.get())
    return "ok"

@app.errorhandler(404)
def page_not_found(e):
    return render_template('notfound.html'), 404

@app.errorhandler(403)
def access_denied(e):
    return render_template('403.html'), 403

@app.errorhandler(500)
def serverError(e):
    logging.error("Error 500:%s", str(e))
    return render_template('error.html', error=str(e)), 500

#@app.errorhandler(Exception)
#def defaultHandler(e):
#    logging.error("Error:%s", str(e))
#    return render_template('error.html', error=str(e)), 500
