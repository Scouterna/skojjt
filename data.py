# -*- coding: utf-8 -*-
import codecs
import datetime
import logging
import re
import json

from google.appengine.api import memcache, users

from google.appengine.ext import ndb

class PropertyWriteTracker(ndb.Model):
	_dirty = False

	def __init__(self, *args, **kw):
		self._dirty = False
		super(PropertyWriteTracker, self).__init__(*args, **kw)

	def __setattr__(self, key, value):
		if key[:1] != '_': # avoid all system properties and "_dirty"
			if self.__getattribute__(key) != value:
				self._make_dirty()
		super(PropertyWriteTracker, self).__setattr__(key, value)

	def _make_dirty(self):
		self._dirty = True

	def _not_dirty(self):
		self._dirty = False


class Semester(ndb.Model):
	year = ndb.IntegerProperty(required=True)
	ht = ndb.BooleanProperty(required=True)

	@staticmethod
	def getid(year, ht):
		return str(year) + ("ht" if ht else "vt")

	@staticmethod
	def create(year, ht):
		if year < 2016:
			raise ValueError("Invalid year %d" % year)
		return Semester(id=Semester.getid(year, ht), year=year, ht=ht)
		
	@staticmethod
	def getOrCreateCurrent():
		thisdate = datetime.datetime.now()
		ht = True if thisdate.month>6 else False
		year = thisdate.year
		semester = Semester.get_by_id(Semester.getid(year, ht))
		if semester == None:
			semester = Semester.create(year, ht)
			semester.put()
		return semester

	@staticmethod
	def getOrCreateNext():
		thisdate = datetime.datetime.now()
		ht = True if thisdate.month>6 else False
		year = thisdate.year
		if ht:
			year += 1
		ht = not ht
		semester = Semester.get_by_id(Semester.getid(year, ht))
		if semester == None:
			semester = Semester.create(year, ht)
			semester.put()
		return semester

	def getname(self):
		return "%04d-%s" % (self.year, "ht" if self.ht else "vt")
		
	def getMinDateStr(self):
		if self.ht:
			return "%04d-07-01" % (self.year)
		else:
			return "%04d-01-01" % (self.year)

	def getMaxDateStr(self):
		if self.ht:
			return "%04d-12-31" % (self.year)
		else:
			return "%04d-08-30" % (self.year)

# kår
class ScoutGroup(ndb.Model):
	name = ndb.StringProperty(required=True)
	activeSemester = ndb.KeyProperty(kind=Semester, required=False) # TODO: remove
	organisationsnummer = ndb.StringProperty()
	foreningsID = ndb.StringProperty(required=False, default="")
	scoutnetID = ndb.StringProperty(required=False, default="")
	kommunID = ndb.StringProperty(default="1480")
	apikey_waitinglist = ndb.StringProperty(required=False, default="")
	apikey_all_members  = ndb.StringProperty(required=False, default="")
	bankkonto = ndb.StringProperty(required=False, default="")
	adress = ndb.StringProperty(required=False, default="")
	postadress = ndb.StringProperty(required=False, default="")
	epost = ndb.StringProperty(required=False, default="")
	telefon = ndb.StringProperty(required=False, default="")
	default_lagerplats = ndb.StringProperty(required=False, default="")
	firmatecknare = ndb.StringProperty(required=False, default="")
	firmatecknartelefon = ndb.StringProperty(required=False, default="")

	@staticmethod
	def getid(name):
		return name.lower().replace(' ', '')

	@staticmethod
	def getbyname(name):
		return ScoutGroup.get_by_id(ScoutGroup.getid(name), use_memcache=True)

	@staticmethod
	def create(name, scoutnetID):
		if len(name) < 2:
			raise ValueError("Invalid name %s" % (name))
		return ScoutGroup(id=ScoutGroup.getid(name), name=name, scoutnetID=scoutnetID)
	
	@staticmethod
	def getgroupsforuser(user):
		if user.groupaccess != None:
			return [user.groupaccess.get()]
		elif user.hasadminaccess:
			return ScoutGroup.query().fetch(100)
		else:
			return []

	def getname(self):
		return self.name

	def canAddToWaitinglist(self):
		return self.scoutnetID != None and self.scoutnetID != "" and self.apikey_waitinglist != None and self.apikey_waitinglist != ""

# avdelning
class Troop(ndb.Model):
	name = ndb.StringProperty()
	scoutgroup = ndb.KeyProperty(kind=ScoutGroup)
	defaultstarttime = ndb.StringProperty(default="18:30")
	defaultduration = ndb.IntegerProperty(default=90)
	rapportID = ndb.IntegerProperty()
	scoutnetID = ndb.IntegerProperty(required=False, default=0)
	semester_key = ndb.KeyProperty(kind=Semester)

	@staticmethod
	def getid(troop_id, scoutgroup_key, semester_key):
		semester = semester_key.get()
		return str(troop_id) + '/' + str(scoutgroup_key.id()) + '/' + semester.getname()

	@staticmethod
	def create(name, troop_id, scoutgroup_key, semester_key):
		return Troop(id=Troop.getid(troop_id, scoutgroup_key, semester_key), name=name, scoutgroup=scoutgroup_key, semester_key=semester_key)
		
	@staticmethod
	def getTroopsForUser(sgroup_key, user):
		return Troop.query(Troop.scoutgroup==sgroup_key, user.activeSemester==Troop.semester_key).fetch()

	def getname(self):
		return self.name
		
	def delete(self):
		for tp in TroopPerson.getTroopPersonsForTroop(self.key):
			tp.delete()
		for meeting in Meeting.gettroopmeetings(self.key):
			meeting.delete()
		self.key.delete()


class Person(PropertyWriteTracker):
	firstname = ndb.StringProperty(required=True)
	lastname = ndb.StringProperty(required=True)
	birthdate = ndb.DateProperty(required=True) # could be a computed property from personnr
	personnr = ndb.StringProperty()
	troop = ndb.KeyProperty(kind=Troop) # assigned default troop in scoutnet, can be member of multiple troops
	patrool = ndb.StringProperty()
	scoutgroup = ndb.KeyProperty(kind=ScoutGroup)
	notInScoutnet = ndb.BooleanProperty()
	removed = ndb.BooleanProperty()
	email = ndb.StringProperty()
	phone = ndb.StringProperty()
	mobile = ndb.StringProperty()
	alt_email = ndb.StringProperty()
	mum_name = ndb.StringProperty()
	mum_email = ndb.StringProperty()
	mum_mobile = ndb.StringProperty()
	dad_name = ndb.StringProperty()
	dad_email = ndb.StringProperty()
	dad_mobile = ndb.StringProperty()
	street = ndb.StringProperty()
	zip_code = ndb.StringProperty()
	zip_name = ndb.StringProperty()
	troop_roles = ndb.StringProperty(repeated=True)
	group_roles = ndb.StringProperty(repeated=True)
	member_years = ndb.IntegerProperty(repeated=True) # a list of years this person have been imported, used for membership reporting

	@staticmethod
	def create(id, firstname, lastname, personnr):
		person = Person(id=id,
			firstname=firstname,
			lastname=lastname)
		person.setpersonnr(personnr)
		return person

	@staticmethod
	def createlocal(firstname, lastname, personnr, mobile, phone, email):
		person = Person(
			id=personnr.replace('-', ''), # using personnr as id for local persons
			firstname=firstname,
			lastname=lastname,
			mobile=mobile,
			phone=phone,
			email=email,
			notInScoutnet=True)
		person.setpersonnr(personnr)
		return person

	@staticmethod
	def persnumbertodate(pnr):
		return datetime.datetime.strptime(pnr[:8], "%Y%m%d").date()

	@staticmethod
	def getIsFemale(personnummer):
		return False if int(personnummer[-2])&1 == 1 else True
	
	def isFemale(self):
		return Person.getIsFemale(self.personnr)
		
	def setpersonnr(self, pnr):
		self.personnr = pnr.replace('-', '')
		self.birthdate = Person.persnumbertodate(pnr)

	def getpersonnr(self):
		return self.personnr.replace('-', '')

	def getbirthdatestring(self):
		return self.birthdate.strftime("%Y-%m-%d")
	def getpersnumberstr(self):
		return self.birthdate.strftime("%Y%m%d0000")

	def getname(self):
		return self.firstname + " " + self.lastname

	def getnameWithStatus(self):
		if self.removed == True:
			return self.firstname + " " + self.lastname + ' (B)'
		return self.firstname + " " + self.lastname

	def getyearsoldthisyear(self, year):
		return year - self.birthdate.year
	
	def isLeader(self):
		if self.troop_roles != None:
			if any(u'ledare' in role for role in self.troop_roles):
				return True
		thisdate = datetime.datetime.now()
		return self.getyearsoldthisyear(thisdate.year) >= 18

	def isBoardMember(self):
		return self.group_roles != None and len(self.group_roles) > 0
		
	def getpatrol(self):
		return self.patrool # TODO: fix spelling error

	def setpatrol(self, patrolname):
		self.patrool = patrolname # TODO: fix spelling error

	def getMemberYearsString(self):
		return ','.join(str(y) for y in self.member_years)

	def getPostadress(self):
		if self.zip_code is None or self.zip_name is None:
			return ''
		return self.zip_code + ' ' + self.zip_name


class Meeting(ndb.Model):
	datetime = ndb.DateTimeProperty(auto_now_add=True, required=True)
	name = ndb.StringProperty(required=True)
	troop = ndb.KeyProperty(kind=Troop, required=True)
	duration = ndb.IntegerProperty(default=90, required=True) #minutes
	semester = ndb.KeyProperty(kind=Semester, required=False) # TODO: remove
	attendingPersons = ndb.KeyProperty(kind=Person, repeated=True) # list of attending persons' keys
	ishike = ndb.BooleanProperty(required=False)

	@staticmethod
	def __getMemcacheKeyString(troop_key):
		return 'tms:' + str(troop_key)

	@staticmethod
	def getId(meetingDatetime, troop_key):
		return meetingDatetime.strftime("%Y%m%d%H%M")+str(troop_key.id())
		
	@staticmethod
	def getOrCreate(troop_key, name, datetime, duration, ishike):
		m = Meeting.get_by_id(Meeting.getId(datetime, troop_key), use_memcache=True)
		if m != None:
			if m.name != name or m.duration != duration or m.ishike != ishike:
				m.name = name
				m.duration = duration
				m.ishike = ishike
				m.put()
		else:
			m = Meeting(id=Meeting.getId(datetime, troop_key),
				datetime=datetime,
				name=name,
				troop=troop_key,
				duration=duration,
				ishike=ishike
				)
		troopmeeting_keys = memcache.get(Meeting.__getMemcacheKeyString(troop_key))
		if troopmeeting_keys is not None and m.key not in troopmeeting_keys:
			troopmeeting_keys.append(m.key)
			memcache.replace(Meeting.__getMemcacheKeyString(troop_key), troopmeeting_keys)
		return m

	@staticmethod
	def gettroopmeetings(troop_key):
		troopmeetings = []
		troopmeeting_keys = memcache.get(Meeting.__getMemcacheKeyString(troop_key))
		if troopmeeting_keys is None:
			troopmeeting_keys = Meeting.query(Meeting.troop==troop_key).fetch(keys_only=True)
			memcache.add(Meeting.__getMemcacheKeyString(troop_key), troopmeeting_keys)
		for tm_key in troopmeeting_keys:
			m = tm_key.get()
			if m != None:
				troopmeetings.append(m)
		troopmeetings.sort(key=lambda x:x.datetime, reverse=True)
		return troopmeetings

	def delete(self):
		self.key.delete()
		troopmeeting_keys = memcache.get(Meeting.__getMemcacheKeyString(self.troop))
		if troopmeeting_keys is not None:
			troopmeeting_keys.remove(self.key)
			memcache.replace(Meeting.__getMemcacheKeyString(self.troop), troopmeeting_keys)

	def commit(self):
		self.put()

	def getdate(self):
		return self.datetime.strftime("%Y-%m-%d")
	def gettime(self):
		return self.datetime.strftime("%H:%M")
	def getname(self):
		return self.name
	def getendtime(self):
		maxEndTime = self.datetime.replace(hour=23,minute=59,second=59)
		endtime = self.datetime + datetime.timedelta(minutes=self.duration)
		if endtime > maxEndTime:
			endtime = maxEndTime # limit to the current day (to keep Stop time after Start time)
		return endtime.strftime('%H:%M')
	def getishike(self):
		result = self.ishike
		return result


class TroopPerson(ndb.Model):
	troop = ndb.KeyProperty(kind=Troop, required=True)
	person = ndb.KeyProperty(kind=Person, required=True)
	leader = ndb.BooleanProperty(default=False)
	sortname = ndb.ComputedProperty(lambda self: self.getname())

	@staticmethod
	def getid(troop_key, person_key):
		return str(troop_key.id())+str(person_key.id())

	@staticmethod
	def __getMemcacheKeyString(troop_key):
		return 'tps:' + str(troop_key)

	def delete(self):
		self.key.delete()
		troopperson_keys = memcache.get(TroopPerson.__getMemcacheKeyString(self.troop))
		if troopperson_keys is not None:
			troopperson_keys.remove(self.key)
			memcache.replace(TroopPerson.__getMemcacheKeyString(self.troop), troopperson_keys)

	@staticmethod
	def create(troop_key, person_key, isLeader):
		tp = TroopPerson(id=TroopPerson.getid(troop_key, person_key),
			troop=troop_key,
			person=person_key,
			leader=isLeader)
		troopperson_keys = memcache.get(TroopPerson.__getMemcacheKeyString(troop_key))
		if troopperson_keys is not None and tp.key not in troopperson_keys:
			troopperson_keys.append(tp.key)
			memcache.replace(TroopPerson.__getMemcacheKeyString(troop_key), troopperson_keys)
		return tp

	def put(self):
		super(TroopPerson, self).put()

	@staticmethod
	def getTroopPersonsForTroop(troop_key):
		trooppersons = []
		troopperson_keys = memcache.get(TroopPerson.__getMemcacheKeyString(troop_key))
		if troopperson_keys is None:
			troopperson_keys = TroopPerson.query(TroopPerson.troop==troop_key).fetch(keys_only=True)
			memcache.add(TroopPerson.__getMemcacheKeyString(troop_key), troopperson_keys)
		for tp_key in troopperson_keys:
			tp = tp_key.get()
			if tp != None:
				trooppersons.append(tp)
		trooppersons.sort(key=lambda x: (-x.leader, x.sortname))
		return trooppersons

	def commit(self):
		self.put()

	def getname(self):
		person = self.person.get()
		if person is None:
			return "(None)"
		return person.getname()

	def gettroopname(self):
		return self.troop.get().getname()

	def getFullTroopname(self):
		troop = self.troop.get()
		semester = troop.semester_key.get()
		return self.troop.get().getname() + ' - ' + semester.getname()

class UserPrefs(ndb.Model):
	userid = ndb.StringProperty(required=True)
	hasaccess = ndb.BooleanProperty(required=True)
	canimport = ndb.BooleanProperty(required=False)
	hasadminaccess = ndb.BooleanProperty(default=False, required=True)
	name = ndb.StringProperty(required=True)
	activeSemester = ndb.KeyProperty(kind=Semester)
	groupaccess = ndb.KeyProperty(kind=ScoutGroup, required=False, default=None)
	groupadmin = ndb.BooleanProperty(required=False, default=False)
	email = ndb.StringProperty(required=False)

	def hasAccess(self):
		return self.hasaccess

	def isAdmin(self):
		return self.hasaccess and self.hasadminaccess

	def canImport(self):
		return self.isAdmin() or self.canimport == True

	def isGroupAdmin(self):
		return self.hasadminaccess or (self.hasaccess and self.groupadmin and self.groupaccess != None)

	def getname(self):
		return self.name

	def getemail(self):
		if self.email != None and len(self.email) != 0:
			return self.email
		if '@' in self.name:
			return self.name
		return self.name + '@gmail.com'

	@staticmethod
	def current():
		cu = users.get_current_user()
		return UserPrefs.getorcreate(cu)

	def attemptAutoGroupAccess(self):
		if self.groupaccess is None:
			persons = Person.query(self.email == Person.email).fetch()
			if persons is not None and len(persons) > 0:
				person = persons[0]
				if person.isLeader():
					self.groupaccess = person.scoutgroup
					self.hasaccess = True
					self.put()
					logging.info("Auto groupaccess for %s: %s %s", self.email, person.firstname, person.lastname)

	def updateMemcache(self):
		if not memcache.add(self.userid, self):
			memcache.replace(self.userid, self)

	def put(self):
		super(UserPrefs, self).put()
		self.updateMemcache()

	@staticmethod
	def getorcreate(user):
		userprefs = memcache.get(user.user_id())
		if userprefs is not None:
			return userprefs
		else:
			userprefs = UserPrefs.get_by_id(user.user_id()) # new records have user_id as id
			if userprefs != None:
				userprefs.updateMemcache()
				return userprefs
			usersresult = UserPrefs.query(UserPrefs.userid == user.user_id()).fetch() # Fetching old records from userid
			if len(usersresult) == 0:
				userprefs = UserPrefs.create(user, users.is_current_user_admin(), users.is_current_user_admin())
				userprefs.put()
			else:
				olduser = usersresult[0]
				# old record, update to a new with user_id as id and email
				if olduser != None:
					userprefs = UserPrefs.create(user, olduser.hasAccess(), olduser.isAdmin())
					userprefs.activeSemester = olduser.activeSemester
					userprefs.groupaccess = olduser.groupaccess
					userprefs.groupadmin = olduser.groupadmin
					userprefs.put()
					olduser.key.delete()
			userprefs.updateMemcache()
			return userprefs

	@staticmethod
	def create(user, access=False, hasadminaccess=False):
		return UserPrefs(id=user.user_id(), userid=user.user_id(), name=user.nickname(), email=user.email(), hasaccess=access, hasadminaccess=hasadminaccess, activeSemester=Semester.getOrCreateCurrent().key)


class TaskProgress(ndb.Model):
	created = ndb.DateTimeProperty(auto_now_add=True, required=True)
	completed = ndb.DateTimeProperty()
	name = ndb.StringProperty(required=True)
	return_url = ndb.StringProperty(required=True)
	messages = ndb.StringProperty(repeated=True)
	failed = ndb.BooleanProperty(default=False)
	lastPut = None

	def append(self, message):
		self.messages.append(message)
		self._putIfNeeded()

	def info(self, message):
		self.messages.append(message)
		self._putIfNeeded()

	def warning(self, message):
		self.messages.append('Warning:' + message)
		self._putIfNeeded()

	def error(self, message):
		self.messages.append('Error:' + message)
		self.failed = True
		self._putIfNeeded()

	def done(self):
		self.completed = datetime.datetime.now()
		self.put()

	def isRunning(self):
		return self.completed is None

	def put(self):
		super(TaskProgress, self).put()
		self.lastPut = datetime.datetime.now()

	def _putIfNeeded(self):
		if self.lastPut is None or (datetime.datetime.now() - self.lastPut).total_seconds > 5:
			self.put()

	@staticmethod
	def cleanup():
		cutoffdate = datetime.datetime.now() - datetime.timedelta(days=30)
		keys = TaskProgress.query(TaskProgress.created < cutoffdate).fetch(keys_only=True)
		ndb.delete_multi(keys)

	def toJson(self):
		s = '{"datetime": "' + self.created.strftime("%Y%m%d%H%M")+ '",' + \
			'"name": "' + self.name + '",' + \
			'"return_url": "' + self.return_url + '",' + \
			'"messages": ' + json.dumps(self.messages) + ',' + \
			'"failed": ' + json.dumps(self.failed) + ',' + \
			'"running": ' + json.dumps(self.isRunning()) + '}'
		return s
