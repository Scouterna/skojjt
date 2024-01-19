# -*- coding: utf-8 -*-
from datetime import datetime
import logging
import time
import traceback
from threading import Thread
from flask import Blueprint, render_template, request, make_response, redirect
from google.appengine.ext import ndb
from google.appengine.ext.ndb import metadata
from data import Meeting, Person, ScoutGroup, Semester, Troop, TroopPerson, UserPrefs
from data_badge import TroopBadge, Badge
from progress import TaskProgress
import htmlform
import scoutnet


admin = Blueprint('admin_page', __name__, template_folder='templates')


@admin.route('/')
def admin_():
    user = UserPrefs.current()
    if not user.isAdmin():
        return "denied", 403

    breadcrumbs = [{'link':'/', 'text':'Hem'},
                   {'link':'/admin', 'text':'Admin'}]
    return render_template('admin.html', heading="Admin", breadcrumbs=breadcrumbs, username=user.getname())


@admin.route('/access/')
@admin.route('/access/<userprefs_url>')
@admin.route('/access/<userprefs_url>/', methods = ['POST', 'GET'])
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


# merge scoutgroups with different names (renamed in scoutnet):
@admin.route('/merge_sg/', methods = ['POST', 'GET'])
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
            semesters=Semester.getAllSemestersSorted())

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
    t = Thread(target=merge_sg_deferred, args=[oldname, newname, commit, taskProgress.key, user.key, move_users, move_persons, move_troops, delete_sg, semester_id])
    t.start()
    return redirect('/progress/' + taskProgress.key.urlsafe())

def merge_sg_deferred(oldname, newname, commit, taskProgress_key, user_key, move_users, move_persons, move_troops, delete_sg, semester_id):
    try:
        user = user_key.get()  # type: data.UserPrefs
        taskProgress = TaskProgress.getTaskProgress(taskProgress_key)

        merge_scout_group(oldname, newname, commit, taskProgress, user, move_users, move_persons, move_troops, delete_sg, semester_id)

    except Exception as e:
        # catch all exceptions so that defer stops running it again (automatic retry)
        if taskProgress:
            taskProgress.error(str(e) + "CS:" + traceback.format_exc())

    try:
        if taskProgress:
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
                    newtp = TroopPerson.create_or_update(newt.key, oldtp.person, oldtp.leader)
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

# update person ids to member_no
@admin.route('/update_person_ids/', methods = ['POST', 'GET'])
def adminUpdateUpdatePersonIds():
    user = UserPrefs.current()
    if not user.isAdmin():
        return "denied", 403

    section_title = u'Hem'
    baselink = '/'
    breadcrumbs = [{'link':baselink, 'text':section_title}]

    section_title = u'Admin'
    baselink += 'admin/'
    breadcrumbs.append({'link':baselink, 'text':section_title})

    section_title = u'Update Person Ids'
    baselink += 'update_person_ids/'
    breadcrumbs.append({'link':baselink, 'text':section_title})

    if request.method == 'POST':
        sgroup_key = None
        if len(request.form.get('groupaccess')) != 0:
            sgroup_key = ndb.Key(urlsafe=request.form.get('groupaccess'))

        commit = request.form.get('commit') == 'on'
        return startAsyncUpdatePersonIds(commit, sgroup_key)
    else:
        return render_template('update_person_ids.html',
            heading=section_title,
            baselink=baselink,
            breadcrumbs=breadcrumbs,
            scoutgroups=ScoutGroup.query().fetch())



# cleanup of bad database records
@admin.route('/cleanup/', methods = ['POST', 'GET'])
def cleanup():
    user = UserPrefs.current()
    if not user.isGroupAdmin():
        return "", 403

    heading="Cleanup"
    baselink="/admin/cleanup/"
    breadcrumbs = [{'link':'/', 'text':'Hem'},
                   {'link':'/admin', 'text':'Admin'},
                   {'link':'/admin/cleanup', 'text':'Cleanup'}]

    if request.method == 'POST' and request.form is not None:
        commit = "commit" in request.form and request.form['commit'] == 'on'

        tps = TroopBadge.query().fetch()
        tp_keys_to_remove = []
        items = []
        if not commit:
            items.append('testmode')
        for tp in tps:
            badge = Badge.get_by_id(tp.badge_key.id())
            if badge is None:
                tp_keys_to_remove.append(tp.key)
                items.append(str(tp.key))

        if commit:
            ndb.delete_multi(tp_keys_to_remove)

        return render_template('table.html',
                                heading=heading,
                                baselink=baselink,
                                tabletitle="Items to remove",
                                items=items,
                                breadcrumbs=breadcrumbs)
    else:
        form = htmlform.HtmlForm('cleanup', submittext="Radera", buttonType="btn-danger",
                                    descriptionText=u"Cleanup of bad TroopBadge records")
        form.AddField('commit', 'on', u'Commit to database', 'checkbox', False)
        return render_template('form.html',
                                heading=heading,
                                baselink=baselink,
                                form=str(form),
                                breadcrumbs=breadcrumbs)



def flushPendingDatabaseOperations():
    ndb.get_context().flush().wait()
    while ndb.eventloop.get_event_loop().run_idle():
        pass


@admin.route('/deleteall/')
def dodelete():
    user = UserPrefs.current()
    if not user.isAdmin():
        return "denied", 403

    # DeleteAllData() # uncomment to enable this
    return redirect('/admin/')


@admin.route('/settroopsemester/')
def settroopsemester():
    user = UserPrefs.current()
    if not user.isAdmin():
        return "denied", 403

    dosettroopsemester()
    return redirect('/admin/')

@admin.route('/updateschemas')
def doupdateschemas():
    user = UserPrefs.current()
    if not user.isAdmin():
        return "denied", 403

    UpdateSchemas()
    return redirect('/admin/')

@admin.route('/setcurrentsemester')
def setcurrentsemester():
    user = UserPrefs.current()
    if not user.isAdmin():
        return "denied", 403

    semester = Semester.getOrCreateCurrent()
    for u in UserPrefs.query().fetch():
        u.activeSemester = semester.key
        u.put()

    return redirect('/admin/')

@admin.route('/autoGroupAccess')
def autoGroupAccess():
    user = UserPrefs.current()
    if not user.isAdmin():
        return "denied", 403
    users = UserPrefs().query().fetch()
    for u in users:
        u.attemptAutoGroupAccess()

    return "done"


@admin.route('/backup')
@admin.route('/backup/')
def dobackup():
    user = UserPrefs.current()
    if not user.isAdmin():
        return "denied", 403

    response = make_response(GetBackupXML())
    response.headers['Content-Type'] = 'application/xml'
    thisdate = datetime.datetime.now()
    response.headers['Content-Disposition'] = 'attachment; filename=skojjt-backup-' + str(thisdate.isoformat()) + '.xml'
    return response

@admin.route('/test_email')
@admin.route('/test_email/')
def adminTestEmail():
    user = UserPrefs.current()
    scoutnet.sendRegistrationQueueInformationEmail(user.groupaccess.get())
    return "ok"



def GetBackupXML():
    thisdate = datetime.now()
    xml = '<?xml version="1.0" encoding="utf-8"?>\r\n<data date="' + thisdate.isoformat() + '">\r\n'
    kinds = metadata.get_kinds()
    for kind in kinds:
        if kind.startswith('_'):
            pass  # Ignore kinds that begin with _, they are internal to GAE
        else:
            q = ndb.Query(kind=kind)
            all = q.fetch()
            for e in all:
                xml += '<' + kind + ' id=' + e.key.id() + '>\r\n'
                for n, v in e._properties.items():
                    xml += '  <' + n + '>' + str(v) + '</' + n + '>\r\n'
                xml += '</' + kind + '>\r\n'

    xml += '</data>'
    return xml



def DeleteAllData():
    entries = []
    entries.extend(Person.query().fetch(keys_only=True))
    entries.extend(Troop.query().fetch(keys_only=True))
    entries.extend(ScoutGroup.query().fetch(keys_only=True))
    entries.extend(Meeting.query().fetch(keys_only=True))
    entries.extend(TroopPerson.query().fetch(keys_only=True))
    entries.extend(Semester.query().fetch(keys_only=True))
    entries.extend(TaskProgress.query().fetch(keys_only=True))
    entries.extend(TaskProgressMessage.query().fetch(keys_only=True))
    entries.extend(UserPrefs.query().fetch(keys_only=True))
    ndb.delete_multi(entries)
    ndb.get_context().clear_cache() # clear memcache


def dosettroopsemester():
    semester_key = Semester.getOrCreateCurrent().key
    troops = Troop.query().fetch()
    for troop in troops:
        #if troop.semester_key != semester_key:
        troop.semester_key = semester_key
        logging.info("updating semester for: %s", troop.getname())
        troop.put()


def UpdateSchemaTroopPerson():
    entries = TroopPerson().query().fetch()
    for e in entries:
        e.put()


def UpdateSchemas():
    UpdateSchemaTroopPerson()
