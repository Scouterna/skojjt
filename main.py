﻿# -*- coding: utf-8 -*-
from data import *
from dataimport import *
import datetime
import urllib
import json
import scoutnet
from google.appengine.api import users

from flask import Flask, render_template, abort, redirect, url_for, request, make_response
from werkzeug import secure_filename
import sys

app = Flask(__name__)
app.debug = True
# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.


reload(sys)  
sys.setdefaultencoding('utf8')


@app.route('/')
def home():
	user = users.get_current_user()
	breadcrumbs = [{'link':'/', 'text':'Hem'}]
	return render_template('index.html',
						   heading='Hem',
						   items=[],
						   breadcrumbs=breadcrumbs,
						   showstart=True,
						   username=user.nickname(),
						   signout_url=users.create_logout_url('/'))

@app.route('/start')
@app.route('/start/')
@app.route('/start/<sgroup_url>')
@app.route('/start/<sgroup_url>/')
@app.route('/start/<sgroup_url>/<troop_url>', methods = ['POST', 'GET'])
@app.route('/start/<sgroup_url>/<troop_url>/', methods = ['POST', 'GET'])
@app.route('/start/<sgroup_url>/<troop_url>/<key_url>', methods = ['POST', 'GET'])
@app.route('/start/<sgroup_url>/<troop_url>/<key_url>/', methods = ['POST', 'GET'])
def start(sgroup_url=None, troop_url=None, key_url=None):
	user = users.get_current_user()
	if not UserPrefs.checkandcreate(user):
		abort(403)
		return "denied"
		
	breadcrumbs = [{'link':'/', 'text':'Hem'}]
	section_title = u'Kårer'
	breadcrumbs.append({'link':'/start', 'text':section_title})
	baselink='/start/'

	scoutgroup = None
	if sgroup_url!=None:
		sgroup_key = ndb.Key(urlsafe=sgroup_url)
		scoutgroup = sgroup_key.get()
		baselink+=sgroup_url+"/"
		breadcrumbs.append({'link':baselink, 'text':scoutgroup.getname()})

	troop = None
	if troop_url!=None:
		baselink+=troop_url+"/"
		troop_key = ndb.Key(urlsafe=troop_url)
		troop = troop_key.get()
		breadcrumbs.append({'link':baselink, 'text':troop.getname()})
		
	if key_url == "newperson":
		section_title = "Ny person"
		baselink += key_url + "/"
		breadcrumbs.append({'link':baselink, 'text':section_title})
		if request.method == "GET":
			return render_template('person.html',
				heading=section_title,
				baselink=baselink,
				breadcrumbs=breadcrumbs)				
		elif request.method == "POST":
			person = Person.createlocal(request.form['firstname'], request.form['lastname'], request.form['birthdate'].replace('-',''), request.form['sex'] == "female")
			person.scoutgroup = sgroup_key
			logging.info("created local person %s", person.getname());
			person.put()
			troopperson = TroopPerson.create(troop_key, person.key, False)
			troopperson.commit()
			return redirect(breadcrumbs[-2]['link'])
	
	if request.method == "GET" and len(request.args) > 0:
		action =""
		if "action" in request.args:
			action = request.args["action"]
		logging.debug("action %s", action)
		if action == "lookupperson":
			if scoutgroup == None:
				raise ValueError('Missing group')
			name = request.args['name'].lower()
			if len(name) < 2:
				return "[]"
			jsonstr='['
			personCounter = 0
			for person in Person().query(Person.scoutgroup == sgroup_key):
				if person.getname().lower().find(name) != -1 and not person.removed:
					if personCounter != 0:
						jsonstr += ', '
					jsonstr += '{"name": "'+person.getname()+'", "url": "' + person.key.urlsafe() + '"}'
					personCounter += 1
					if personCounter == 8:
						break;
			jsonstr+=']'
			return jsonstr
		elif action == "addperson":
			if troop == None or key_url == None:
				raise ValueError('Missing troop or person')
			person_key = ndb.Key(urlsafe=key_url)
			person = person_key.get()
			logging.debug("adding person=%s to troop=%d", person.getname(), troop.getname())
			troopperson = TroopPerson.create(troop_key, person_key, False)
			troopperson.commit()
			return redirect(breadcrumbs[-1]['link'])
		else:
			logging.error('unknown action=' + action)
			abort(404)
			return ""
		
	if request.method == "POST" and len(request.form) > 0:
		action=request.form["action"]
		if action == "saveattendance":
			if troop == None or scoutgroup == None or key_url == None:
				raise ValueError('Missing troop or group')

			meeting_key = ndb.Key(urlsafe=key_url)
			oldattendance = Attendance.query(Attendance.meeting==meeting_key).fetch(keys_only=True)
			ndb.delete_multi(oldattendance)
			for person_url in request.form["persons"].split(","):
				#logging.debug("person_url=%s", person_url)
				if len(person_url) > 0:
					person_key = ndb.Key(urlsafe=person_url)
					attendance = Attendance.create(person_key, meeting_key).put()
			return "ok"
		elif action == "addmeeting" or action == "updatemeeting":
			mname = request.form['name']
			mdate = request.form['date']
			mtime = request.form['starttime'].replace('.', ':')
			dtstring = mdate + "T" + mtime
			mduration = request.form['duration']
			dt = datetime.datetime.strptime(dtstring, "%Y-%m-%dT%H:%M")
			if action == "addmeeting":
				meeting = Meeting.create(troop_key, 
					mname,
					dt,
					int(mduration),
					scoutgroup.activeSemester)
			else:
				meeting = ndb.Key(urlsafe=key_url).get()
				meeting.name = mname
				meeting.datetime = dt
				meeting.duration = int(mduration)

			meeting.commit()
			return redirect(breadcrumbs[-1]['link'])
		elif action == "deletemeeting":
			meeting = ndb.Key(urlsafe=key_url).get()
			logging.debug("deleting meeting=%s", meeting.getname())
			oldattendance = Attendance.query(Attendance.meeting==meeting.key).fetch(keys_only=True)
			ndb.delete_multi(oldattendance)
			meeting.key.delete()
			return redirect(breadcrumbs[-1]['link'])
		else:
			logging.error('unknown action=' + action)
			abort(404)
			return ""

	# render main pages
	if scoutgroup==None:
		return render_template('index.html', 
			heading=section_title, 
			baselink=baselink,
			addlink=True,
			items=ScoutGroup.query().fetch(100),
			breadcrumbs=breadcrumbs)
	elif troop==None:
		section_title = 'Avdelningar'
		return render_template('index.html',
			heading=section_title,
			baselink=baselink,
			addlink=True,
			items=Troop.query(Troop.scoutgroup==sgroup_key).fetch(100),
			breadcrumbs=breadcrumbs)
	elif key_url!=None: # assuming this is a meeting for now
		meeting = ndb.Key(urlsafe=key_url).get()
		section_title = meeting.getname()
		baselink += key_url + "/"
		breadcrumbs.append({'link':baselink, 'text':section_title})

		return render_template('meeting.html',
			heading=section_title,
			baselink=baselink,
			attendances=Attendance.query(Attendance.meeting==meeting.key).fetch(),
			existingmeeting=meeting,
			breadcrumbs=breadcrumbs)				
	else:
		meetingCount = 0
		sumMaleAttendenceCount = 0
		sumFemaleAttendenceCount = 0
		sumMaleLeadersAttendenceCount = 0
		sumFemaleLeadersAttendenceCount = 0
		noLeaderMeetingCount = 0
		tooSmallGroupMeetingCount = 0
		ageProblemCount = 0
		ageProblemDesc = []

		section_title = troop.getname()
		trooppersons = TroopPerson.query(TroopPerson.troop==troop_key).order(TroopPerson.sortname).fetch()
		meetings = Meeting.gettroopmeetings(troop_key)
		
		attendances = [] # [meeting][person]
		persons = []
		personsDict = {}
		for troopperson in trooppersons:
			personKey = troopperson.person
			person = troopperson.person.get()
			persons.append(person)
			personsDict[personKey] = person
		
		for meeting in meetings:
			maleAttendenceCount = 0
			femaleAttendenceCount = 0
			maleLeadersAttendenceCount = 0
			femaleLeadersAttendenceCount = 0
			meetingattendance = []
			for troopperson in trooppersons:
				att = Attendance.query(Attendance.meeting==meeting.key, Attendance.person==troopperson.person).fetch(keys_only=True)
				isAttending = len(att) != 0
				meetingattendance.append(isAttending)
				if isAttending:
					person = personsDict[troopperson.person]
					age = person.getyearsold()
					if troopperson.leader:
						if age >= 13 and age <= 100:
							if femaleLeadersAttendenceCount+maleLeadersAttendenceCount < 2:
								if person.female:
									femaleLeadersAttendenceCount += 1
								else:
									maleLeadersAttendenceCount += 1
						else:
							ageProblemCount += 1
							ageProblemDesc.append(person.getname() + ": " + str(age))
					else:
						if age >= 7 and age <= 25:
							if person.female:
								femaleAttendenceCount += 1
							else:
								maleAttendenceCount += 1
						else:
							ageProblemCount += 1
							ageProblemDesc.append(person.getname() + ": " + str(age))
					
			attendances.append(meetingattendance)

			if maleAttendenceCount+femaleAttendenceCount < 5:
				tooSmallGroupMeetingCount += 1
			else:
				if femaleLeadersAttendenceCount+maleLeadersAttendenceCount == 0:
					noLeaderMeetingCount += 1
				else:
					meetingCount += 1
					sumMaleAttendenceCount += maleAttendenceCount
					sumFemaleAttendenceCount += femaleAttendenceCount
					sumMaleLeadersAttendenceCount += maleLeadersAttendenceCount
					sumFemaleLeadersAttendenceCount += femaleLeadersAttendenceCount

		if key_url == "kommunal":
			result = render_template('gbgkommun.xml', meetings=meetings, troop=troop, trooppersons=trooppersons)
			response = make_response(result)
			response.headers['Content-Type'] = 'application/xml'
			response.headers['Content-Disposition'] = 'attachment; filename=gbgkommun-' + troop.getname() + '.xml'
			return response
		else:
			allowance = []
			allowance.append({'name':'Antal möten:', 'value':meetingCount})
			allowance.append({'name':'Deltagartillfällen', 'value':''})
			allowance.append({'name':'Kvinnor:', 'value':sumFemaleAttendenceCount})
			allowance.append({'name':'Män:', 'value':sumMaleAttendenceCount})
			allowance.append({'name':'Ledare Kvinnor:', 'value':sumFemaleLeadersAttendenceCount})
			allowance.append({'name':'Ledare Män:', 'value':sumMaleLeadersAttendenceCount})
			if noLeaderMeetingCount > 0:
				allowance.append({'name':'Antal möten utan ledare', 'value':noLeaderMeetingCount})
			if tooSmallGroupMeetingCount > 0:
				allowance.append({'name':'Antal möten med för få deltagare', 'value':tooSmallGroupMeetingCount})
			if ageProblemCount > 0:
				allowance.append({'name':'Ålder utanför intervall:', 'value':ageProblemCount})
			if len(ageProblemDesc) > 0:
				ageProblemDescStr = ','.join(ageProblemDesc[:3])
				if len(ageProblemDesc) > 3:
					ageProblemDescStr += "..."
				allowance.append({'name':'', 'value':ageProblemDescStr})
				
			return render_template('troop.html',
				heading=section_title,
				baselink='/persons/' + scoutgroup.key.urlsafe() + '/',
				addlink=True,
				items=persons,
				meetings=meetings,
				attendances=attendances,
				showaddmeetings=True,
				showaddmember=True,
				breadcrumbs=breadcrumbs,
				allowance=allowance)

@app.route('/persons')
@app.route('/persons/')
@app.route('/persons/<sgroup_url>')
@app.route('/persons/<sgroup_url>/')
@app.route('/persons/<sgroup_url>/<person_url>')
@app.route('/persons/<sgroup_url>/<person_url>/')
@app.route('/persons/<sgroup_url>/<person_url>/<action>')
def persons(sgroup_url=None, person_url=None, action=None):
	user = users.get_current_user()
	if not UserPrefs.checkandcreate(user):
		abort(403)
		return "denied"

	breadcrumbs = [{'link':'/', 'text':'Hem'}]
	
	section_title = u'Personer'
	breadcrumbs.append({'link':'/persons', 'text':section_title})
	baselink='/persons/'

	scoutgroup = None
	if sgroup_url!=None:
		sgroup_key = ndb.Key(urlsafe=sgroup_url)
		scoutgroup = sgroup_key.get()
		baselink+=sgroup_url+"/"
		breadcrumbs.append({'link':baselink, 'text':scoutgroup.getname()})

	person = None
	if person_url!=None:
		person_key = ndb.Key(urlsafe=person_url)
		person = person_key.get()
		baselink+=person_url+"/"
		section_title = person.getname()
		breadcrumbs.append({'link':baselink, 'text':section_title})
	
	if action != None:
		if action == "deleteperson" or action == "addbackperson":
			person.removed = action == "deleteperson"
			person.put() # we only mark the person as removed
			if person.removed:
				tpkeys = TroopPerson.query(TroopPerson.person==person.key).fetch(keys_only=True)
				ndb.delete_multi(tpkeys)
			return redirect(breadcrumbs[-1]['link'])
		if action == "removefromtroop" or action == "setasleader" or action == "removeasleader":
			troop_key = ndb.Key(urlsafe=request.args["troop"])
			tp = TroopPerson.query(TroopPerson.person==person.key, TroopPerson.troop == troop_key).fetch(1)[0]
			if action == "removefromtroop":
				tp.key.delete()
			else:
				tp.leader = (action == "setasleader")
				tp.put()
			return redirect(breadcrumbs[-1]['link'])
		else:
			logging.error('unknown action=' + action)
			abort(404)
			return ""
		
		
	# render main pages
	if scoutgroup==None:
		return render_template('index.html', 
			heading=section_title, 
			baselink=baselink,
			addlink=True,
			items=ScoutGroup.query().fetch(),
			breadcrumbs=breadcrumbs,
			username=user.nickname())
	elif person==None:
		section_title = 'Personer'
		return render_template('index.html',
			heading=section_title,
			baselink=baselink,
			addlink=True,
			items=Person.query(Person.scoutgroup==sgroup_key).order(Person.firstname, Person.lastname).fetch(),
			breadcrumbs=breadcrumbs,
			username=user.nickname())
	else:
		return render_template('person.html',
			heading=section_title,
			baselink='/persons/' + scoutgroup.key.urlsafe() + '/',
			addlink=True,
			trooppersons=TroopPerson.query(TroopPerson.person==person.key).fetch(),
			ep=person,
			attendances=Attendance.query(Attendance.person==person.key).fetch(), # todo: filter by semester
			breadcrumbs=breadcrumbs,
			username=user.nickname())
	

@app.route('/admin')
@app.route('/admin/')
def admin():
	user = users.get_current_user()
	if not UserPrefs.checkandcreate(user):
		abort(403)
		return "denied"

	breadcrumbs = [{'link':'/', 'text':'Hem'},
				   {'link':'/admin', 'text':'Admin'}]
	return render_template('admin.html', heading="Admin", breadcrumbs=breadcrumbs, showstart=True, username=user.nickname())

@app.route('/admin/access/')
@app.route('/admin/access/<userprefs_url>')
@app.route('/admin/access/<userprefs_url>/', methods = ['POST', 'GET'])
def adminaccess(userprefs_url=None):
	user = users.get_current_user()
	if not UserPrefs.checkandcreate(user, True):
		abort(403)
		return "denied"

	section_title = u'Hem'
	baselink = '/'
	breadcrumbs = [{'link':baselink, 'text':section_title}]
	
	section_title = u'Admin'
	baselink += 'admin/'
	breadcrumbs.append({'link':baselink, 'text':section_title})

	section_title = u'Access'
	baselink += 'access/'
	breadcrumbs.append({'link':baselink, 'text':section_title})

	if userprefs_url == None:
		return render_template('index.html',
			heading=section_title,
			baselink=baselink,
			addlink=True,
			items=UserPrefs().query().fetch(),
			breadcrumbs=breadcrumbs)
	else:
		userprefs = ndb.Key(urlsafe=userprefs_url).get()
		if request.method == 'POST':
			logging.info('request.form=%s', str(request.form))
			userprefs.hasaccess = request.form.get('hasAccess') == 'on'
			userprefs.hasadminaccess = request.form.get('hasAdminAccess') == 'on'
			userprefs.put()
			return redirect(breadcrumbs[-1]['link'])
		else:
			section_title = userprefs.getname()
			baselink += userprefs_url + '/' 
			breadcrumbs.append({'link':baselink, 'text':section_title})
			return render_template('userprefs.html',
				heading=section_title,
				baselink=baselink,
				addlink=True,
				userprefs=userprefs,
				breadcrumbs=breadcrumbs)
	
	abort(404)
	
@app.route('/admin/import')
def doimport():
	user = users.get_current_user()
	if not UserPrefs.checkandcreate(user, True):
		abort(403)
		return "denied"

	ImportData()
	return redirect('/admin')

@app.route('/admin/reimport')
def doreimport():
	user = users.get_current_user()
	if not UserPrefs.checkandcreate(user, True):
		abort(403)
		return "denied"

	ReimportData()
	return redirect('/admin')
	
@app.route('/admin/delete')
def dodelete():
	user = users.get_current_user()
	if not UserPrefs.checkandcreate(user, True):
		abort(403)
		return "denied"

	DeleteAllData()
	return redirect('/admin')
	

@app.route('/admin/updateschemas')
def doupdateschemas():
	user = users.get_current_user()
	if not UserPrefs.checkandcreate(user, True):
		abort(403)
		return "denied"

	UpdateSchemas()
	return redirect('/admin')

@app.route('/admin/backup')
@app.route('/admin/backup/')
def dobackup():
	user = users.get_current_user()
	if not UserPrefs.checkandcreate(user, True):
		abort(403)
		return "denied"

	response = make_response(GetBackupXML())
	response.headers['Content-Type'] = 'application/xml'
	thisdate = datetime.datetime.now()
	response.headers['Content-Disposition'] = 'attachment; filename=skojjt-backup-' + str(thisdate.isoformat()) + '.xml'
	return response
	
	
@app.route('/admin/reimportcsv/', methods=['GET', 'POST'])
def reimportcsv():
	user = users.get_current_user()
	if not UserPrefs.checkandcreate(user, True):
		abort(403)
		return "denied"

	breadcrumbs = [{'link':'/', 'text':'Hem'}]
	breadcrumbs.append({'link':'/admin/', 'text':'Admin'})
	breadcrumbs.append({'link':'/admin/reimportcsv/', 'text':'Reimport'})
	if request.method == 'POST':
		commit = 'commit' in request.form.values()
		username = request.form.get('signin[username]')
		password = request.form.get('signin[password]')
		groupid = request.form.get('groupid')
		logging.info("commit=%d, username=%s, password=%s, groupid=%s", commit, username, password, groupid)
		data = scoutnet.GetScoutnetMembersCSVData(username, password, groupid)
		result = ReimportData(data, commit)
		return render_template('table.html', items=result, rowtitle='Result', breadcrumbs=breadcrumbs)
	else:
		return render_template('updatefromscoutnetform.html', breadcrumbs=breadcrumbs)


@app.errorhandler(404)
def page_not_found(e):
	return render_template('notfound.html'), 404

@app.errorhandler(403)
def access_denied(e):
	return render_template('access.html'), 403

@app.errorhandler(500)
def serverError(e):
	logging.error("Error 500:%s", str(e))
	return render_template('error.html', error=str(e)), 500

#@app.errorhandler(Exception)
#def defaultHandler(e):
#	logging.error("Error:%s", str(e))
#	return render_template('error.html', error=str(e)), 500
