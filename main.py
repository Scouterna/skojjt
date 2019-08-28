# -*- coding: utf-8 -*-
from data import *
from dataimport import *
import datetime
import urllib
import json
import scoutnet
import time
import htmlform
from dakdata import *
import sensus
from google.appengine.api import users
from google.appengine.api import app_identity
from google.appengine.api import mail
from google.appengine.api import taskqueue
import random

from imports import import_page, progress
from groupsummary import groupsummary
from scoutgroupinfo import scoutgroupinfo
from persons import persons
from start import start

from flask import Flask, render_template, abort, redirect, url_for, request, make_response
import sys

app = Flask(__name__)
app.debug = True
# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.


reload(sys)
sys.setdefaultencoding('utf8')


@app.route('/')
def home():
	breadcrumbs = [{'link':'/', 'text':'Hem'}]
	user=UserPrefs.current()
	user.attemptAutoGroupAccess()
	starturl = '/start/'
	personsurl = '/persons/'
	if user.groupaccess != None:
		starturl += user.groupaccess.urlsafe() + '/'
		personsurl += user.groupaccess.urlsafe() + '/'
	return render_template('start.html',
						   heading='Hem',
						   items=[],
						   breadcrumbs=breadcrumbs,
						   user=user,
						   starturl=starturl,
						   personsurl=personsurl,
						   logouturl=users.create_logout_url('/')
						   )

app.register_blueprint(start, url_prefix='/start')
app.register_blueprint(persons, url_prefix='/persons')
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
		merge_sg(oldname, newname, commit)

	return render_template('merge_sg.html',
		heading=section_title,
		baselink=baselink,
		breadcrumbs=breadcrumbs)


def merge_sg(oldname, newname, commit):
	oldsg = ScoutGroup.getbyname(oldname)
	if oldsg is None:
		raise RuntimeError("Old sg name:%s not found" % oldname)
	
	newsg = ScoutGroup.getbyname(newname)
	if newsg is None:
		raise RuntimeError("New sg name:%s not found" % newname)
	
	if not commit: logging.info("*** testmode ***")

	keys_to_delete = []
	entities_to_put_first = []
	entities_to_put = []
	semester = Semester.getOrCreateCurrent()

	keys_to_delete.append(oldsg.key)

	logging.info("Update all users to the new scoutgroup")
	for u in UserPrefs.query(UserPrefs.groupaccess == oldsg.key).fetch():
		u.groupaccess = newsg.key
		u.activeSemester = semester.key
		entities_to_put.append(u)

	logging.info("Moving all persons to the new ScoutGroup:%s", newsg.getname())
	for oldp in Person.query(Person.scoutgroup == oldsg.key).fetch():
		logging.info(" * Moving %s %s", oldp.getname(), oldp.personnr)
		oldp.scoutgroup = newsg.key
		entities_to_put.append(oldp)

	logging.info("Move all troops to the new ScoutGroup:%s", newsg.getname())
	for oldt in Troop.query(Troop.scoutgroup == oldsg.key).fetch():
		logging.info(" * found old troop for %s, semester=%s", str(oldt.key.id()), oldt.semester_key.get().getname())
		keys_to_delete.append(oldt.key)
		newt = Troop.get_by_id(Troop.getid(oldt.scoutnetID, newsg.key, oldt.semester_key), use_memcache=True)
		if newt is None:
			logging.info(" * * creating new troop for %s, semester=%s", str(oldt.key.id()), oldt.semester_key.get().getname())
			newt = Troop.create(oldt.name, oldt.scoutnetID, newsg.key, oldt.semester_key)
			entities_to_put_first.append(newt) # put first to be able to reference it
		else:
			logging.info(" * * already has new troop for %s, semester=%s", str(newt.key.id()), newt.semester_key.get().getname())

		logging.info(" * Move all trooppersons to the new group (it they don't already exist there)")
		for oldtp in TroopPerson.query(TroopPerson.troop == oldt.key).fetch():
			keys_to_delete.append(oldtp.key)
			newtp = TroopPerson.get_by_id(TroopPerson.getid(newt.key, oldtp.person), use_memcache=True)
			if newtp is None:
				logging.info(" * * creating new TroopPerson for %s:%s", newt.getname(), oldtp.getname())
				newtp = TroopPerson.create(newt.key, oldtp.person, oldtp.leader)
				entities_to_put.append(newtp)
			else:
				logging.info(" * * already has TroopPerson for %s:%s", newt.getname(), oldtp.getname())

		logging.info(" * Move all old meetings to the new troop")
		for oldm in Meeting.query(Meeting.troop==oldt.key).fetch():
			keys_to_delete.append(oldm.key)
			newm = Meeting.get_by_id(Meeting.getId(oldm.datetime, newt.key), use_memcache=True)
			if newm is None:
				logging.info(" * * creating new Meeting for %s:%s", newt.getname(), oldm.datetime.strftime("%Y-%m-%d %H:%M"))
				newm = Meeting.getOrCreate(newt.key, oldm.name, oldm.datetime, oldm.duration, oldm.ishike)
				newm.attendingPersons = oldm.attendingPersons
				entities_to_put.append(newm)
			else:
				logging.info(" * * already has Meeting for %s:%s", newt.getname(), newt.datetime.strftime("%Y-%m-%d %H:%M"))
	
	logging.info("Putting %d entities first", len(entities_to_put_first))
	if commit: ndb.put_multi(entities_to_put_first)
	logging.info("Putting %d entities", len(entities_to_put))
	if commit: ndb.put_multi(entities_to_put)
	logging.info("Deleting %d keys", len(keys_to_delete))
	if commit: ndb.delete_multi(keys_to_delete)
	logging.info("clear memcache")
	if commit: ndb.get_context().clear_cache()
	logging.info("Done!")


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
	
@app.route('/admin/fixsgroupids/')
def fixsgroupids():
	user = UserPrefs.current()
	if not user.isAdmin():
		return "denied", 403

	dofixsgroupids()
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
#	logging.error("Error:%s", str(e))
#	return render_template('error.html', error=str(e)), 500
