# -*- coding: utf-8 -*-
from data import *
from dataimport import *
import datetime
import urllib
import json
import scoutnet
import htmlform
from dakdata import *
from google.appengine.api import users
from google.appengine.api import app_identity
from google.appengine.api import mail
import random

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
	breadcrumbs = [{'link':'/', 'text':'Hem'}]
	user=UserPrefs.current()
	starturl = '/start/'
	personsurl = '/persons/'
	if user.groupaccess != None:
		starturl += user.groupaccess.urlsafe() + '/'
		personsurl += user.groupaccess.urlsafe() + '/'
	return render_template('start.html',
						   heading='Hem',
						   items=[],
						   breadcrumbs=breadcrumbs,
						   user=UserPrefs.current(),
						   starturl=starturl,
						   personsurl=personsurl
						   )

@app.route('/start')
@app.route('/start/')
@app.route('/start/<sgroup_url>')
@app.route('/start/<sgroup_url>/')
@app.route('/start/<sgroup_url>/<troop_url>', methods = ['POST', 'GET'])
@app.route('/start/<sgroup_url>/<troop_url>/', methods = ['POST', 'GET'])
@app.route('/start/<sgroup_url>/<troop_url>/<key_url>', methods = ['POST', 'GET'])
@app.route('/start/<sgroup_url>/<troop_url>/<key_url>/', methods = ['POST', 'GET'])
def start(sgroup_url=None, troop_url=None, key_url=None):
	user = UserPrefs.current()
	if not user.hasAccess():
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
		
	if key_url == "settings":
		section_title = u'Inställningar'
		baselink += "settings/"
		breadcrumbs.append({'link':baselink, 'text':section_title})
		if request.method == "POST":
			troop.defaultstarttime = request.form['defaultstarttime'] 
			troop.rapportID = int(request.form['rapportID'])
			troop.put()
			
		form = htmlform.HtmlForm('troopsettings')
		form.AddField('defaultstarttime', troop.defaultstarttime, 'Avdelningens vanliga starttid')
		form.AddField('rapportID', troop.rapportID, 'Unik rapport ID för kommunens närvarorapport', 'number')
		return render_template('form.html',
			heading=section_title,
			baselink=baselink,
			form=str(form),
			breadcrumbs=breadcrumbs)
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
			pnr = request.form['personnummer'].replace('-','')
			person = Person.createlocal(
				request.form['firstname'], 
				request.form['lastname'], 
				pnr, 
				Person.getIsFemale(pnr),
				request.form['mobile'],
				request.form['phone'],
				request.form['email'])
			person.street = request.form["street"]
			person.zip_code = request.form["zip_code"]
			person.zip_name = request.form["zip_name"]
			person.scoutgroup = sgroup_key
			logging.info("created local person %s", person.getname())
			person.put()
			troopperson = TroopPerson.create(troop_key, person.key, False)
			troopperson.commit()
			if scoutgroup.scoutnetID != None and scoutgroup.apikey_waitinglist != None:
				scoutnet.AddPersonToWaitinglist(scoutgroup, person.firstname, person.lastname, person.personnr, person.email, request.form['street'], request.form['zip_code'], request.form['zip_name'], person.mobile, person.phone)
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
			logging.info("adding person=%s to troop=%d", person.getname(), troop.getname())
			troopperson = TroopPerson.create(troop_key, person_key, False)
			troopperson.commit()
			return redirect(breadcrumbs[-1]['link'])
		elif action == "newsemester":
			if scoutgroup == None:
				raise ValueError('Missing scoutgroup')
			semester = Semester.getOrCreateCurrent()
			scoutgroup.activeSemester = semester.key
			scoutgroup.put()
			logging.info("Set new semester: %s", semester.getname())
			#ForceSemesterForAll(semester)
			return semester.getname()
		else:
			logging.error('unknown action=' + action)
			abort(404)
			return ""
		
	if request.method == "POST" and len(request.form) > 0:
		action=request.form["action"]
		if action == "saveattendance":
			if troop == None or scoutgroup == None or key_url == None:
				raise ValueError('Missing troop or group')

			meeting = ndb.Key(urlsafe=key_url).get()
			meeting.attendingPersons[:] = [] # clear the list
			for person_url in request.form["persons"].split(","):
				#logging.debug("person_url=%s", person_url)
				if len(person_url) > 0:
					person_key = ndb.Key(urlsafe=person_url)
					meeting.attendingPersons.append(person_key)
			meeting.put()
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
			meeting.delete()
			return redirect(breadcrumbs[-1]['link'])
		else:
			logging.error('unknown action=' + action)
			abort(404)
			return ""

	# render main pages
	if scoutgroup == None:
		return render_template('index.html', 
			heading=section_title, 
			baselink=baselink,
			addlink=True,
			items=ScoutGroup.getgroupsforuser(user),
			breadcrumbs=breadcrumbs)
	elif troop==None:
		section_title = 'Avdelningar'
		return render_template('troops.html',
			heading=section_title,
			baselink=baselink,
			scoutgroupinfolink='/scoutgroupinfo/' + sgroup_url + '/',
			user=user,
			troops=Troop.query(Troop.scoutgroup==sgroup_key).fetch(100), # TODO: memcache
			breadcrumbs=breadcrumbs)
	elif key_url!=None and key_url!="dak":
		meeting = ndb.Key(urlsafe=key_url).get()
		section_title = meeting.getname()
		baselink += key_url + "/"
		breadcrumbs.append({'link':baselink, 'text':section_title})

		return render_template('meeting.html',
			heading=section_title,
			baselink=baselink,
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
		trooppersons = TroopPerson.getTroopPersonsForTroop(troop_key)
		meetings = Meeting.gettroopmeetings(troop_key, scoutgroup.activeSemester)
		
		attendances = [] # [meeting][person]
		persons = []
		personsDict = {}
		for troopperson in trooppersons:
			personKey = troopperson.person
			person = troopperson.person.get()
			persons.append(person)
			personsDict[personKey] = person
		
		semester = scoutgroup.activeSemester.get()
		year = semester.getyear()
		for meeting in meetings:
			maleAttendenceCount = 0
			femaleAttendenceCount = 0
			maleLeadersAttendenceCount = 0
			femaleLeadersAttendenceCount = 0
			meetingattendance = []
			for troopperson in trooppersons:
				isAttending = troopperson.person in meeting.attendingPersons
				meetingattendance.append(isAttending)
				if isAttending:
					person = personsDict[troopperson.person]
					age = person.getyearsoldthisyear(year)
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
			totalAttendence = maleAttendenceCount+femaleAttendenceCount
			# max 40 people
			if totalAttendence > 40:
				surplusPeople = totalAttendence-40
				removedMen = min(maleAttendenceCount, surplusPeople)
				maleAttendenceCount -= removedMen
				surplusPeople -= removedMen
				femaleAttendenceCount -= surplusPeople

			maxLeaders = 1 if totalAttendence <= 10 else 2
			totalLeaders = femaleLeadersAttendenceCount+maleLeadersAttendenceCount
			if totalAttendence < 3:
				tooSmallGroupMeetingCount += 1
			else:
				if totalLeaders == 0:
					noLeaderMeetingCount += 1
				else:
					meetingCount += 1
					sumFemaleAttendenceCount += femaleAttendenceCount
					sumMaleAttendenceCount += maleAttendenceCount
					if totalLeaders > maxLeaders:
						if maleLeadersAttendenceCount > maxLeaders and femaleLeadersAttendenceCount == 0:
							maleLeadersAttendenceCount = maxLeaders
						elif maleLeadersAttendenceCount == 0 and femaleLeadersAttendenceCount > maxLeaders:
							femaleLeadersAttendenceCount = maxLeaders
						else:
							femaleLeadersAttendenceCount = maxLeaders / 2
							maxLeaders -= femaleLeadersAttendenceCount
							maleLeadersAttendenceCount = maxLeaders
						
					sumFemaleLeadersAttendenceCount += femaleLeadersAttendenceCount
					sumMaleLeadersAttendenceCount += maleLeadersAttendenceCount

		if key_url == "dak":
			dak = DakData()
			dak.foereningsNamn = scoutgroup.getname()
			dak.foreningsID = scoutgroup.foreningsID
			dak.organisationsnummer = scoutgroup.organisationsnummer
			dak.kommunID = scoutgroup.kommunID
			dak.kort.NamnPaaKort = troop.getname()
			# hack generate an "unique" id, if there is none
			if troop.rapportID == None or troop.rapportID == 0:
				troop.rapportID = random.randint(100, 1000000)
				troop.put()

			dak.kort.NaervarokortNummer = str(troop.rapportID)
			
			for tp in trooppersons:
				p = personsDict[tp.person]
				if tp.leader:
					dak.kort.ledare.append(Deltagare(str(p.key.id()), p.firstname, p.lastname, p.getpersonnr(), True, p.email, p.mobile))
				else:
					dak.kort.deltagare.append(Deltagare(str(p.key.id()), p.firstname, p.lastname, p.getpersonnr(), False))
				
			for m in meetings:
				sammankomst = Sammankomst(str(m.key.id()[:50]), m.datetime, m.duration, m.getname())
				for tp in trooppersons:
					isAttending = tp.person in m.attendingPersons
					if isAttending:
						p = personsDict[tp.person]
						if tp.leader:
							sammankomst.ledare.append(Deltagare(str(p.key.id()), p.firstname, p.lastname, p.getpersonnr(), True, p.email, p.mobile))
						else:
							sammankomst.deltagare.append(Deltagare(str(p.key.id()), p.firstname, p.lastname, p.getpersonnr(), False))
				
				dak.kort.Sammankomster.append(sammankomst)
			
			result = render_template('dak.xml', dak=dak)
			response = make_response(result)
			response.headers['Content-Type'] = 'application/xml'
			response.headers['Content-Disposition'] = 'attachment; filename=' + dak.kort.NamnPaaKort + '-' + semester.getname() + '.xml'
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
				persons=persons,
				trooppersons=trooppersons,
				meetings=meetings,
				attendances=attendances,
				breadcrumbs=breadcrumbs,
				allowance=allowance,
				defaultstarttime=troop.defaultstarttime)

@app.route('/persons')
@app.route('/persons/')
@app.route('/persons/<sgroup_url>')
@app.route('/persons/<sgroup_url>/')
@app.route('/persons/<sgroup_url>/<person_url>')
@app.route('/persons/<sgroup_url>/<person_url>/')
@app.route('/persons/<sgroup_url>/<person_url>/<action>')
def persons(sgroup_url=None, person_url=None, action=None):
	user = UserPrefs.current()
	if not user.hasAccess():
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
				tps = TroopPerson.query(TroopPerson.person == person.key).fetch()
				for tp in tps:
					tp.delete()
			return redirect(breadcrumbs[-1]['link'])
		if action == "removefromtroop" or action == "setasleader" or action == "removeasleader":
			troop_key = ndb.Key(urlsafe=request.args["troop"])
			tps = TroopPerson.query(TroopPerson.person == person.key, TroopPerson.troop == troop_key).fetch(1)
			if len(tps) == 1:
				tp = tps[0]
				if action == "removefromtroop":
					tp.delete()
				else:
					tp.leader = (action == "setasleader")
					tp.put()
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
			items=ScoutGroup.getgroupsforuser(user),
			breadcrumbs=breadcrumbs,
			username=user.getname())
	elif person==None:
		section_title = 'Personer'
		return render_template('index.html',
			heading=section_title,
			baselink=baselink,
			addlink=True,
			items=Person.query(Person.scoutgroup == sgroup_key).order(Person.firstname, Person.lastname).fetch(), # TODO: memcache
			breadcrumbs=breadcrumbs,
			username=user.getname())
	else:
		return render_template('person.html',
			heading=section_title,
			baselink='/persons/' + scoutgroup.key.urlsafe() + '/',
			addlink=True,
			trooppersons=TroopPerson.query(TroopPerson.person == person.key).fetch(), # TODO: memcache
			ep=person,
			#attendances=Attendance.query(Attendance.person==person.key).fetch(), # todo: filter by semester
			breadcrumbs=breadcrumbs,
			username=user.getname())
	
@app.route('/scoutgroupinfo/<sgroup_url>')
@app.route('/scoutgroupinfo/<sgroup_url>/', methods = ['POST', 'GET'])
def scoutgroupinfo(sgroup_url):
	user = UserPrefs.current()
	if not user.canImport():
		return "denied", 403
	breadcrumbs = [{'link':'/', 'text':'Hem'}]
	baselink = "/scoutgroupinfo/"
	section_title = "Kårinformation"
	scoutgroup = None
	if sgroup_url!=None:
		sgroup_key = ndb.Key(urlsafe=sgroup_url)
		scoutgroup = sgroup_key.get()
		baselink += sgroup_url+"/"
		breadcrumbs.append({'link':baselink, 'text':scoutgroup.getname()})
	if request.method == "POST":
		logging.info("POST, %s" % str(request.form))
		scoutgroup.organisationsnummer = request.form['organisationsnummer'].strip()
		scoutgroup.foreningsID = request.form['foreningsID'].strip()
		scoutgroup.scoutnetID = request.form['scoutnetID'].strip()
		scoutgroup.kommunID = request.form['kommunID'].strip()
		scoutgroup.apikey_waitinglist = request.form['apikey_waitinglist'].strip()
		scoutgroup.apikey_all_members = request.form['apikey_all_members'].strip()
		scoutgroup.put()
		logging.info("Done, redirect to: %s", breadcrumbs[-1]['link'])
		if "import" in request.form:
			result = RunScoutnetImport(scoutgroup.scoutnetID, scoutgroup.apikey_all_members, user)
			return render_template('table.html', items=result, rowtitle='Result', breadcrumbs=breadcrumbs)
		else:
			return redirect(breadcrumbs[-1]['link'])
	else:
		return render_template('scoutgroupinfo.html',
			heading=section_title,
			baselink=baselink,
			scoutgroup=scoutgroup,
			breadcrumbs=breadcrumbs)

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

@app.route('/import')
@app.route('/import/', methods = ['POST', 'GET'])
def import_():
	user = UserPrefs.current()
	if not user.canImport():
		abort(403)
		return "denied"

	breadcrumbs = [{'link':'/', 'text':'Hem'},
				   {'link':'/import', 'text':'Import'}]

	if request.method != 'POST':
		return render_template('updatefromscoutnetform.html', heading="Import", breadcrumbs=breadcrumbs, username=user.getname())

	commit = 'commit' in request.form.values()
	api_key = request.form.get('apikey').strip()
	groupid = request.form.get('groupid').strip()
	result = RunScoutnetImport(groupid, api_key, user, commit)
	return render_template('table.html', items=result, rowtitle='Result', breadcrumbs=breadcrumbs)


@app.route('/admin')
@app.route('/admin/')
def admin():
	user = UserPrefs.current()
	if not user.isAdmin():
		abort(403)
		return "denied"

	breadcrumbs = [{'link':'/', 'text':'Hem'},
				   {'link':'/admin', 'text':'Admin'}]
	return render_template('admin.html', heading="Admin", breadcrumbs=breadcrumbs, username=user.getname())

@app.route('/admin/access/')
@app.route('/admin/access/<userprefs_url>')
@app.route('/admin/access/<userprefs_url>/', methods = ['POST', 'GET'])
def adminaccess(userprefs_url=None):
	user = UserPrefs.current()
	if not user.isAdmin():
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
		return render_template('userlist.html',
			heading=section_title,
			baselink=baselink,
			addlink=True,
			users=UserPrefs().query().fetch(),
			breadcrumbs=breadcrumbs)
	else:
		userprefs = ndb.Key(urlsafe=userprefs_url).get()
		if request.method == 'POST':
			#logging.info('request.form=%s', str(request.form))
			userprefs.hasaccess = request.form.get('hasAccess') == 'on'
			userprefs.hasadminaccess = request.form.get('hasAdminAccess') == 'on'
			userprefs.groupadmin = request.form.get('groupadmin') == 'on'
			userprefs.canimport = request.form.get('canImport') == 'on'
			sgroup_key = None
			if len(request.form.get('groupaccess')) != 0:
				sgroup_key = ndb.Key(urlsafe=request.form.get('groupaccess'))
			userprefs.groupaccess = sgroup_key
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
				breadcrumbs=breadcrumbs,
				scoutgroups=ScoutGroup.query().fetch(300))
	
	abort(404)

@app.route('/admin/deleteall/')
def dodelete():
	user = UserPrefs.current()
	if not user.isAdmin():
		abort(403)
		return "denied"

	# DeleteAllData()
	return redirect('/admin')

	
@app.route('/admin/settroopsemester/')
def settroopsemester():
	user = UserPrefs.current()
	if not user.isAdmin():
		abort(403)
		return "denied"

	dosettroopsemester()
	return redirect('/admin')
	
@app.route('/admin/fixsgroupids/')
def fixsgroupids():
	user = UserPrefs.current()
	if not user.isAdmin():
		abort(403)
		return "denied"

	dofixsgroupids()
	return redirect('/admin')
	

@app.route('/admin/updateschemas')
def doupdateschemas():
	user = UserPrefs.current()
	if not user.isAdmin():
		abort(403)
		return "denied"

	UpdateSchemas()
	return redirect('/admin')

@app.route('/admin/backup')
@app.route('/admin/backup/')
def dobackup():
	user = UserPrefs.current()
	if not user.isAdmin():
		abort(403)
		return "denied"

	response = make_response(GetBackupXML())
	response.headers['Content-Type'] = 'application/xml'
	thisdate = datetime.datetime.now()
	response.headers['Content-Disposition'] = 'attachment; filename=skojjt-backup-' + str(thisdate.isoformat()) + '.xml'
	return response
	
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
