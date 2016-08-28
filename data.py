# -*- coding: utf-8 -*-
import re
import codecs
import datetime


from google.appengine.ext import ndb

class Semester(ndb.Model):
	year = ndb.IntegerProperty(required=True)
	ht = ndb.BooleanProperty(required=True)

	@staticmethod
	def getid(year, ht):
		return str(year)+str(ht)
	
	@staticmethod
	def create(year, ht):
		if year < 2016:
			raise ValueError("Invalid year %d" % year)
		return Semester(id=Semester.getid(year, ht), year=year, ht=ht)
		
	def getyear(self):
		return self.year

	def getname(self):
		return "%04d-%s" % (self.getyear(), "ht" if self.ht else "vt")

known_nicknames = ['jacob.thoren', 'kattis@famgreen.se', 'magan174', 'dedden1', 'sephyra', 'kerstin.nyborg', 'madad273', 'znark86', 'Rossniklasson', 'thyrabratthammar', 'katper0730', 'erland.green']

class UserPrefs(ndb.Model):
	userid = ndb.StringProperty(required=True)
	hasaccess = ndb.BooleanProperty(required=True)
	hasadminaccess = ndb.BooleanProperty(default=False, required=True)
	name = ndb.StringProperty(required=True)
	activeSemester = ndb.KeyProperty(kind=Semester)
	
	def getname(self):
		return self.name
	
	@staticmethod
	def create(user, access=False):
		return UserPrefs(userid = user.user_id(), name=user.nickname(), hasaccess=access)
		
	@staticmethod
	def checkandcreate(user, admin=False):
		users = UserPrefs.query(UserPrefs.userid==user.user_id()).fetch()
		if len(users) == 0:
			user = UserPrefs.create(user, user.nickname() in known_nicknames)
			user.put()
		else:
			user = users[0]
		return user.hasaccess if not admin else user.hasadminaccess

class ScoutGroup(ndb.Model):
	name = ndb.StringProperty(required=True)
	activeSemester = ndb.KeyProperty(kind=Semester)
	
	@staticmethod
	def getid(name):
		return name.lower().replace(' ', '')
		
	@staticmethod
	def create(name):
		if len(name) < 2:
			raise ValueError("Invalid name %s" % name)
		return ScoutGroup(id = ScoutGroup.getid(name), name=name)
		
	def getname(self):
		return self.name

class Troop(ndb.Model):
	name = ndb.StringProperty()
	scoutgroup = ndb.KeyProperty(kind=ScoutGroup)

	@staticmethod
	def getid(name, scoutgroup_key):
		return name.lower().replace(' ', '')+scoutgroup_key.id()
		
	@staticmethod
	def create(name, scoutgroup_key):
		return Troop(id=Troop.getid(name, scoutgroup_key), name=name, scoutgroup=scoutgroup_key)

	def getname(self):
		return self.name
	
class Person(ndb.Model):
	firstname = ndb.StringProperty(required=True)
	lastname = ndb.StringProperty(required=True)
	birthdate = ndb.DateProperty(required=True)
	female = ndb.BooleanProperty(required=True)
	troop = ndb.KeyProperty(kind=Troop) # assigned default troop in scoutnet, can be member of multiple troops 
	patrool = ndb.StringProperty()
	scoutgroup = ndb.KeyProperty(kind=ScoutGroup)
	notInScoutnet = ndb.BooleanProperty()
	removed = ndb.BooleanProperty()

	@staticmethod
	def create(id, firstname, lastname, birthdatestr, female):
		return Person(id=id,
			firstname=firstname,
			lastname=lastname,
			birthdate=Person.persnumbertodatetime(birthdatestr),
			female=female)

	@staticmethod
	def createlocal(firstname, lastname, birthdatestr, female):
		return Person(
			firstname=firstname,
			lastname=lastname,
			birthdate=Person.persnumbertodatetime(birthdatestr),
			female=female,
			notInScoutnet=True)
	
	@staticmethod
	def persnumbertodatetime(pnr):
		return datetime.datetime.strptime(pnr[:8], "%Y%m%d")
		
	def getbirthdatestring(self):
		return self.birthdate.strftime("%Y-%m-%d")
	def getpersnumberstr(self):
		return self.birthdate.strftime("%Y%m%d0000")

	def getname(self):
		pattern = re.compile("\( -")
		fn = self.firstname #pattern.split(self.firstname)[0][:10]
		ln = pattern.split(self.lastname)[0][:10]
		return fn + " " + ln
	
	def getyearsold(self):
		thisdate = datetime.datetime.now().date()
		delta = thisdate - self.birthdate
		return delta.days / 365

	
class Meeting(ndb.Model):
	datetime = ndb.DateTimeProperty(auto_now_add=True, required=True)
	name = ndb.StringProperty(required=True)
	troop = ndb.KeyProperty(kind=Troop, required=True)
	duration = ndb.IntegerProperty(default=90, required=True) #minutes
	semester = ndb.KeyProperty(kind=Semester, required=True)

	@staticmethod
	def overlapsanother(meeting):
		return False
		# todo:
		# Meeting(Meeting.datetime == meeting.datetime)
	
	@staticmethod
	def create(troop_key, name, datetime, duration, semester_key):
		return Meeting(id=datetime.strftime("%Y%m%d%H%M")+str(troop_key.id())+str(semester_key.id()),
			datetime=datetime,
			name=name,
			troop=troop_key,
			duration=duration,
			semester=semester_key
			)

	@staticmethod
	def gettroopmeetings(troop_key):
		return Meeting.query(Meeting.troop==troop_key).order(-Meeting.datetime)

	def commit(self):
		self.put()

	def getdate(self):
		return self.datetime.strftime("%Y-%m-%d")
	def gettime(self):
		return self.datetime.strftime("%H:%M")
	def getname(self):
		return self.name
	
class TroopPerson(ndb.Model):
	troop = ndb.KeyProperty(kind=Troop, required=True)
	person = ndb.KeyProperty(kind=Person, required=True)
	leader = ndb.BooleanProperty(default=False)
	sortname = ndb.ComputedProperty(lambda self: self.person.get().getname().lower())

	@staticmethod
	def getid(troop_key, person_key):
		return str(troop_key.id())+str(person_key.id())
	@staticmethod
	def create(troop_key, person_key, isLeader):
		return TroopPerson(id=TroopPerson.getid(troop_key, person_key),
			troop=troop_key,
			person=person_key,
			leader=isLeader)

	def commit(self):
		self.put()
		
	def getname(self):
		return self.person.get().getname()

	def gettroopname(self):
		return self.troop.get().getname()
		
class Attendance(ndb.Model):
	person = ndb.KeyProperty(kind=Person)
	meeting = ndb.KeyProperty(kind=Meeting)

	@staticmethod
	def getid(person_key, meeting_key):
		return str(person_key.id())+str(meeting_key.id())

	@staticmethod
	def create(person_key, meeting_key):
		return Attendance(id=Attendance.getid(person_key, meeting_key),
			person=person_key,
			meeting=meeting_key
			)
