# -*- coding: utf-8 -*-
from data import Meeting, Person, ScoutGroup, Semester, Troop, TroopPerson, UserPrefs, PendingPersonKeyChange
from data_badge import TroopBadge, Badge
from flask import Blueprint, render_template, request, make_response, redirect
from progress import TaskProgress
from google.appengine.ext import deferred
from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext.ndb import metadata
from datetime import datetime
import htmlform
import logging
import scoutnet
import time
import traceback


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
    deferred.defer(merge_sg_deferred, oldname, newname, commit, taskProgress.key, user.key, move_users, move_persons, move_troops, delete_sg, semester_id, _queue="admin")
    return redirect('/progress/' + taskProgress.key.urlsafe())

def merge_sg_deferred(oldname, newname, commit, taskProgress_key, user_key, move_users, move_persons, move_troops, delete_sg, semester_id):
    try:
        user = user_key.get()  # type: data.UserPrefs
        taskProgress = TaskProgress.getTaskProgress(taskProgress_key)

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


"""
How to handle tasks 
List all tasks:
> gcloud tasks list --queue=admin

Delete a task:
> gcloud tasks delete <task-name> --queue=admin
"""
def startAsyncUpdatePersonIds(commit, sgroup_key):
    taskProgress = TaskProgress(name='Update Person IDs', return_url=request.url)
    taskProgress.put()
    taskProgress.info("Startar Person id uppdatering")
    if not commit:
        taskProgress.info("** Test mode **")

    if sgroup_key is None:
        taskProgress.error("Missing sgroup_key")
        return redirect('/progress/' + taskProgress.key.urlsafe())

    deferred.defer(update_person_ids_deferred, commit, sgroup_key, None, 0, taskProgress.key, _queue="admin")
    return redirect('/progress/' + taskProgress.key.urlsafe())

def update_person_ids_deferred(commit, sgroup_key, cursor, stage, taskProgress_key):
    there_is_more = True
    try:
        taskProgress = TaskProgress.getTaskProgress(taskProgress_key)

        cursor, there_is_more, stage = update_person_ids(commit, sgroup_key, cursor, stage, taskProgress)

        if there_is_more:
            deferred.defer(update_person_ids_deferred, commit, sgroup_key, cursor, stage, taskProgress_key, _queue="admin")

    except Exception as e:
        # catch all exceptions so that defer stops running it again (automatic retry)
        taskProgress.error(str(e) + "CS:" + traceback.format_exc())

    try:
        if not there_is_more:
            taskProgress.done()
    except Exception as e:
        pass

max_time_seconds = 7*60
PAGE_SIZE = 100
def update_person_ids(commit, sgroup_key, start_cursor, stage, taskProgress):
    start_time = time.time()
    time_is_out = False
    there_is_more = True
    oldToNewDict = {}

    # --- Stage 0 ---
    if stage == 0:
        while there_is_more:

            if time.time() - start_time > max_time_seconds:
                time_is_out = True
                break # time out

            person_keys, start_cursor, there_is_more = Person.query(Person.scoutgroup ==sgroup_key) \
                                                        .fetch_page(page_size=PAGE_SIZE, start_cursor=start_cursor, keys_only=True)
            for person_key in person_keys:
                if len(str(person_key.id())) < 12: # cannot be a personnr if shorter than 12 chars
                    taskProgress.info("Not updating id=%s" % (str(person_key.id())))
                    continue
                person = person_key.get()
                if person.version == 1 or person.version == 2:
                    taskProgress.info("Already updated id=%s" % (str(person_key.id())))
                    continue
                if person.member_no is None:
                    taskProgress.warning("Cannot update, member_no is None id=%s, %s" % (str(person_key.id()), person.getname()))
                    continue

                taskProgress.info("Updating Person: id=%s, pnr=%s, no=%s, %s" % (str(person.key.id()), person.personnr, str(person.member_no), person.getname()))

                newPerson, pendingKeyChange = person.updateKey()

                if newPerson is not None:
                    if commit and newPerson._dirty:
                        k = newPerson.put()
                        assert(k == newPerson.key)
                if commit and person._dirty:
                    person.put()
                if pendingKeyChange is not None:
                    if pendingKeyChange._dirty:
                        pendingKeyChange.put() # safe to put, to be able to test the rest of the method

        if there_is_more:
            return start_cursor, there_is_more, stage
        else:
            taskProgress.info("Updated all persons Persons")
            stage = 1
            start_cursor = None
            there_is_more = True
            return start_cursor, there_is_more, stage # restart to start fresh and let datastore catch up


    taskProgress.info("Loading PendingPersonKeyChange records")
    ppkc_more = True
    ppkc_start_cursor = None
    while ppkc_more:
        ppkcs, ppkc_start_cursor, ppkc_more = PendingPersonKeyChange.query().fetch_page(page_size=1000, start_cursor=ppkc_start_cursor)
        for ppkc in ppkcs:
            oldToNewDict[ppkc.old_key] = ppkc.new_key
        
        taskProgress.info("Loaded persons to convert %d" % (len(oldToNewDict)))

    taskProgress.info("Number of persons to convert %d" % (len(oldToNewDict)))

    # --- Stage 1 ---
    if stage == 1:
        num_meetings_updated = 0
        troop_count = 0
        there_is_more = True
        taskProgress.info("Updating Meetings")
        while there_is_more:
            if time.time() - start_time > max_time_seconds:
                return start_cursor, there_is_more, stage

            troop_keys, start_cursor, there_is_more = Troop.query(Troop.scoutgroup == sgroup_key) \
                                                    .fetch_page(page_size=5, start_cursor=start_cursor, keys_only=True)
            for troop_key in troop_keys:
                troop_count += 1
                meetings = Meeting.query(Meeting.troop == troop_key).fetch()
                for meeting in meetings:
                    if meeting.uppdateOldPersonKeys(oldToNewDict):
                        num_meetings_updated += 1
                        if commit:
                            meeting.put()

            if num_meetings_updated % 10 == 0:
                taskProgress.info("Updated %d meetings, %d troop_count" % (num_meetings_updated, troop_count))

        if there_is_more:
            return start_cursor, there_is_more, stage
        else:
            taskProgress.info("Updated all meetings, time taken: %s s" % (str(time.time() - start_time)))
            stage = 2
            there_is_more = True
            start_cursor = None
            return start_cursor, there_is_more, stage

    # --- Stage 2 ---
    if stage == 2:
        update_counter = 0
        if start_cursor == None:
            start_cursor = 0

        taskProgress.info("Updating TroopPersons")
        for index, (old_person_key, new_person_key) in enumerate(oldToNewDict.items()):
            if index < start_cursor:
                continue

            for troopPerson in TroopPerson.query(TroopPerson.person==old_person_key).fetch():
                troopPerson.person = new_person_key
                update_counter += 1
                if commit:
                    troopPerson.put()
                if update_counter % 10 == 0:
                    taskProgress.info("Updated %d TroopPersons" % (update_counter))

            if time.time() - start_time > max_time_seconds:
                start_cursor = index
                there_is_more = True
                return start_cursor, there_is_more, stage

        taskProgress.info("Updated all TroopPersons")
        there_is_more = True
        stage = 3
        start_cursor = None
        return start_cursor, there_is_more, stage # restart to start fresh and let datastore catch up

    # --- Stage 3 ---
    if stage == 3:
        taskProgress.info("Deleting old persons")
        if commit and len(oldToNewDict) != 0:
            old_person_keys = [old_person_key for index, (old_person_key, new_person_key) in enumerate(oldToNewDict.items())]
            ndb.delete_multi(old_person_keys)
            taskProgress.info("Deleted %d old persons" % (len(old_person_keys)))

        there_is_more = False
        start_cursor = None
        stage = 4

    taskProgress.info("Done updating Person keys!")
    return None, False, stage


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
