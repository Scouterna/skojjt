# -*- coding: utf-8 -*-
import datetime
import urllib
import random
import htmlform


import scoutnet
from dataimport import UserPrefs, ndb, Person, logging, TroopPerson, Meeting, Troop, ScoutGroup, Semester
from dakdata import DakData, Deltagare, Sammankomst
import sensus

from google.appengine.api import users
from google.appengine.api import app_identity
from google.appengine.api import mail
from google.appengine.api import taskqueue

from flask import Blueprint, render_template, redirect, request, make_response

def semester_sort(a, b):
	a_name = a.getname()
	b_name = b.getname()

	a_year = a_name[:4]
	b_year = b_name[:4]

	if a_year == b_year:
		if a_name[-2:] == "ht":
			return 1
		else:
			return -1
	elif a_year > b_year:
		return 1
	else:
		return -1

start = Blueprint('start_page', __name__, template_folder='templates')

@start.route('/')
@start.route('/<sgroup_url>', methods = ['POST', 'GET'])
@start.route('/<sgroup_url>/', methods = ['POST', 'GET'])
@start.route('/<sgroup_url>/<troop_url>', methods = ['POST', 'GET'])
@start.route('/<sgroup_url>/<troop_url>/', methods = ['POST', 'GET'])
@start.route('/<sgroup_url>/<troop_url>/<key_url>', methods = ['POST', 'GET'])
@start.route('/<sgroup_url>/<troop_url>/<key_url>/', methods = ['POST', 'GET'])
def show(sgroup_url=None, troop_url=None, key_url=None):
	user = UserPrefs.current()
	if not user.hasAccess():
		return "denied", 403

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
			troop.defaultduration = int(request.form['defaultduration'])
			troop.rapportID = int(request.form['rapportID'])
			troop.put()
			
		form = htmlform.HtmlForm('troopsettings')
		form.AddField('defaultstarttime', troop.defaultstarttime, 'Avdelningens vanliga starttid')
		form.AddField('defaultduration', troop.defaultduration, u'Avdelningens vanliga mötestid i minuter', 'number')
		form.AddField('rapportID', troop.rapportID, 'Unik rapport ID för kommunens närvarorapport', 'number')
		return render_template('form.html',
			heading=section_title,
			baselink=baselink,
			form=str(form),
			breadcrumbs=breadcrumbs)
	if key_url == "delete":
		if troop == None:
			return "", 404
		if len(request.form) > 0 and "confirm" in request.form:
			if not user.isGroupAdmin():
				return "", 403
			troop.delete()
			troop = None	
			del breadcrumbs[-1]
			baselink=breadcrumbs[-1]["link"]
		else:
			form = htmlform.HtmlForm('deletetroop', submittext="Radera", buttonType="btn-danger", 
				descriptionText=u"Vill du verkligen radera avdelningen och all registrerad närvaro?\nDet går här inte att ångra.")
			form.AddField('confirm', '', '', 'hidden')
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
				breadcrumbs=breadcrumbs,
				trooppersons=[],
				scoutgroup=scoutgroup)
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
			if "patrol" in request.form:
				person.setpatrol(request.form["patrol"])
			person.scoutgroup = sgroup_key
			logging.info("created local person %s", person.getname())
			person.put()
			troopperson = TroopPerson.create(troop_key, person.key, False)
			troopperson.commit()
			if scoutgroup.canAddToWaitinglist():
				try:
					if scoutnet.AddPersonToWaitinglist(
							scoutgroup,
							person.firstname,
							person.lastname,
							person.personnr,
							person.email,
							person.street,
							person.zip_code,
							person.zip_name,
							person.phone,
							person.mobile,
							troop,
							request.form['anhorig1_name'],
							request.form['anhorig1_email'],
							request.form['anhorig1_mobile'],
							request.form['anhorig1_phone'],
							request.form['anhorig2_name'],
							request.form['anhorig2_email'],
							request.form['anhorig2_mobile'],
							request.form['anhorig2_phone']
					):
						person.notInScoutnet = False
						person.put()
				except scoutnet.ScoutnetException as e:
					return render_template('error.html', error=str(e))
			return redirect(breadcrumbs[-2]['link'])
	
	if request.method == "GET" and len(request.args) > 0 and "action" in request.args:
		action = request.args["action"]
		logging.debug("action %s", action)
		if action == "lookupperson":
			if scoutgroup == None:
				raise ValueError('Missing group')
			name = request.args['name'].lower()
			if len(name) < 2:
				return "[]"
			logging.debug("name=%s", name)
			jsonstr='['
			personCounter = 0
			for person in Person().query(Person.scoutgroup == sgroup_key).order(Person.removed, Person.firstname, Person.lastname):
				if person.getname().lower().find(name) != -1:
					if personCounter != 0:
						jsonstr += ', '
					jsonstr += '{"name": "'+person.getnameWithStatus()+'", "url": "' + person.key.urlsafe() + '"}'
					personCounter += 1
					if personCounter == 8:
						break
			jsonstr+=']'
			return jsonstr
		elif action == "addperson":
			if troop == None or key_url == None:
				raise ValueError('Missing troop or person')
			person_key = ndb.Key(urlsafe=key_url)
			person = person_key.get()
			logging.info("adding person=%s to troop=%d", person.getname(), troop.getname())
			troopperson = TroopPerson.create(troop_key, person_key, person.isLeader())
			troopperson.commit()
			return redirect(breadcrumbs[-1]['link'])
		elif action == "setsemester":
			if user == None or "semester" not in request.args:
				raise ValueError('Missing user or semester arg')
			semester_url = request.args["semester"]
			user.activeSemester = ndb.Key(urlsafe=semester_url)
			user.put()
		elif action == "removefromtroop" or action == "setasleader" or action == "removeasleader":
			if troop == None or key_url == None:
				raise ValueError('Missing troop or person')
			person_key = ndb.Key(urlsafe=key_url)
			tps = TroopPerson.query(TroopPerson.person == person_key, TroopPerson.troop == troop_key).fetch(1)
			if len(tps) == 1:
				tp = tps[0]
				if action == "removefromtroop":
					tp.delete()
				else:
					tp.leader = (action == "setasleader")
					tp.put()
			return "ok"
		else:
			logging.error('unknown action=' + action)
			return "", 404

	if request.method == "POST" and len(request.form) > 0 and "action" in request.form:
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
				meeting = Meeting.getOrCreate(troop_key, 
					mname,
					dt,
					int(mduration))
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
		elif action == "savepatrol":
			patrolperson = ndb.Key(urlsafe=request.form['person']).get()
			patrolperson.setpatrol(request.form['patrolName'])
			patrolperson.put()
			return "ok"
		elif action == "newtroop":
			troopname = request.form['troopname']
			troop_id = hash(troopname)
			conflict = Troop.get_by_id(Troop.getid(troop_id, scoutgroup.key, user.activeSemester), use_memcache=True)
			if conflict is not None:
				return "Avdelningen finns redan", 404
			troop = Troop.create(troopname, troop_id, scoutgroup.key, user.activeSemester)
			troop.put()
			troop_key = troop.key
			logging.info("created local troop %s", troopname)
			action = ""
			return redirect(breadcrumbs[-1]['link'])
		else:
			logging.error('unknown action=' + action)
			return "", 404

	# render main pages
	if scoutgroup == None:
		return render_template('index.html', 
			heading=section_title, 
			baselink=baselink,
			items=ScoutGroup.getgroupsforuser(user),
			breadcrumbs=breadcrumbs)
	elif troop==None:
		section_title = 'Avdelningar'
		return render_template('troops.html',
			heading=section_title,
			baselink=baselink,
			scoutgroupinfolink='/scoutgroupinfo/' + sgroup_url + '/',
			groupsummarylink='/groupsummary/' + sgroup_url + '/',
			user=user,
			semesters=sorted(Semester.query(), semester_sort),
			troops=Troop.getTroopsForUser(sgroup_key, user),
			breadcrumbs=breadcrumbs)
	elif key_url!=None and key_url!="dak" and key_url!="sensus":
		meeting = ndb.Key(urlsafe=key_url).get()
		section_title = meeting.getname()
		baselink += key_url + "/"
		breadcrumbs.append({'link':baselink, 'text':section_title})

		return render_template('meeting.html',
			heading=section_title,
			baselink=baselink,
			existingmeeting=meeting,
			breadcrumbs=breadcrumbs,
			semester=troop.semester_key.get())
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
		meetings = Meeting.gettroopmeetings(troop_key)
		
		attendances = [] # [meeting][person]
		persons = []
		personsDict = {}
		for troopperson in trooppersons:
			personKey = troopperson.person
			person = troopperson.person.get()
			persons.append(person)
			personsDict[personKey] = person
		
		semester = troop.semester_key.get()
		year = semester.year
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
				troop.rapportID = random.randint(1000, 1000000)
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
			response.headers['Content-Disposition'] = 'attachment; filename=' + urllib.quote(str(dak.kort.NamnPaaKort), safe='') + '-' + semester.getname() + '.xml;'
			return response
		elif key_url == "sensus":
			leaders = []
			for tp in trooppersons:
				if tp.leader:
					leaders.append(tp.getname())

			patrols = []
			for p in persons:
				if p.getpatrol() not in patrols:
					patrols.append(p.getpatrol())
					
			sensusdata = sensus.SensusData()
			sensusdata.foereningsNamn = scoutgroup.getname()
			sensusdata.foreningsID = scoutgroup.foreningsID
			sensusdata.organisationsnummer = scoutgroup.organisationsnummer
			sensusdata.kommunID = scoutgroup.kommunID
			sensusdata.verksamhetsAar = semester.getname()
			
			for patrol in patrols:
				sensuslista = sensus.SensusLista()
				sensuslista.NamnPaaKort = troop.getname() + "/" + patrol
				
				for tp in trooppersons:
					p = personsDict[tp.person]
					if p.getpatrol() != patrol:
						continue
					if tp.leader:
						sensuslista.ledare.append(sensus.Deltagare(str(p.key.id()), p.firstname, p.lastname, p.getpersonnr(), True, p.email, p.mobile))
					else:
						sensuslista.deltagare.append(sensus.Deltagare(str(p.key.id()), p.firstname, p.lastname, p.getpersonnr(), False))
					
				for m in meetings:
					sammankomst = sensus.Sammankomst(str(m.key.id()[:50]), m.datetime, m.duration, m.getname())
					for tp in trooppersons:
						p = personsDict[tp.person]
						if p.getpatrol() != patrol:
							continue
						isAttending = tp.person in m.attendingPersons

						if tp.leader:
							sammankomst.ledare.append(sensus.Deltagare(str(p.key.id()), p.firstname, p.lastname, p.getpersonnr(), True, p.email, p.mobile, isAttending))
						else:
							sammankomst.deltagare.append(sensus.Deltagare(str(p.key.id()), p.firstname, p.lastname, p.getpersonnr(), False, p.email, p.mobile, isAttending))

					sensuslista.Sammankomster.append(sammankomst)

				sensusdata.listor.append(sensuslista)
			
			result = render_template(
						'sensusnarvaro.html',
						sensusdata=sensusdata)
			response = make_response(result)
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
				semestername=semester.getname(),
				baselink='/persons/' + scoutgroup.key.urlsafe() + '/',
				persons=persons,
				trooppersons=trooppersons,
				meetings=meetings,
				attendances=attendances,
				breadcrumbs=breadcrumbs,
				allowance=allowance,
				troop=troop,
				user=user,
				semester=semester
				)
