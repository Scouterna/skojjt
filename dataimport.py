# -*- coding: utf-8 -*-
import logging
import codecs
import ucsv as ucsv
from datetime import *
from data import *
import scoutnet
from google.appengine.ext import ndb
from google.appengine.ext.ndb import metadata
import StringIO

def GetBackupXML():
	thisdate = datetime.datetime.now()
	xml = '<?xml version="1.0" encoding="utf-8"?>\r\n<data date="' + thisdate.isoformat() + '">\r\n'
	kinds = metadata.get_kinds()
	for kind in kinds:
		if kind.startswith('_'):
			pass  # Ignore kinds that begin with _, they are internal to GAE
		else:
			q = ndb.Query(kind=kind)
			all = q.fetch()
			for e in all:
				xml += '<' + kind + '>\r\n'
				for n, v in e._properties.items():
					xml += '  <' + n + '>'
					xml += str(getattr(e, n))
					xml += '</' + n + '>\r\n'
				xml += '</' + kind + '>\r\n'

	xml += '</data>'
	return xml
	
def GetOrgnrAndKommunIDForGroup(groupname):
	groupname = groupname.lower()
	with open('data/kommunid.csv', 'rb') as f:
		reader = ucsv.DictReader(f, delimiter=',', quoting=ucsv.QUOTE_NONE, fieldnames=['namn', 'id', 'orgnr'])
		for row in reader:
			name = row['namn'].lower().strip("\"")
			if name == groupname:
				return str(row['id']), str(row['orgnr'])
	return "", ""

class ScoutnetImporter:
	report = []
	commit = False
	rapportID = 1
	
	def GetOrCreateCurrentSemester(self):
		thisdate = datetime.datetime.now()
		ht = False if thisdate.month>6 else True
		semester = Semester.get_by_id(Semester.getid(thisdate.year + 1, ht))
		if semester == None:
			semester = Semester.create(thisdate.year + 1, ht)
			if self.commit:
				semester.put()
		return semester
		
	def GetOrCreateTroop(self, name, group_key):
		if len(name) == 0:
			return None
		troop = Troop.get_by_id(Troop.getid(name, group_key))
		if troop == None:
			self.report.append("Ny avdelning %s" % (name))
			troop = Troop.create(name, group_key)
			troop.rapportID = self.rapportID # TODO: should check the highest number in the sgroup, will work for full imports
			self.rapportID += 1
			if self.commit:
				troop.put()
		return troop
		
	def GetOrCreateGroup(self, name):
		if len(name) == 0:
			return None
		group = ScoutGroup.get_by_id(ScoutGroup.getid(name))
		if group == None:
			self.report.append(u"Ny kår %s" % (name))
			group = ScoutGroup.create(name)
			group.activeSemester = self.GetOrCreateCurrentSemester().key
			fid, orgnr = GetOrgnrAndKommunIDForGroup(name)
			group.foreningsID, group.organisationsnummer = GetOrgnrAndKommunIDForGroup(name)
			if self.commit:
				group.put()
		return group

	def DoImport(self, data):
		if not self.commit:
			self.report.append("*** sparar inte, test mode ***")

		if len(data) < 80:
			self.report.append("Error, too little data length=%d" % len(data))
			return report
			
		list = scoutnet.GetScoutnetDataList(StringIO.StringIO(data))
		self.report.append("antal personer=%d" % (len(list)-1))
		if len(list) < 1:
			self.report.append("Error, too few rows=%d" % len(list))
			return self.report
			
		for p in list:
			id = int(p["id"])
			p2 = Person.get_by_id(p["id"])
			duplicate = False
			person = Person.get_by_id(id) # need to be an integer due to backwards compatibility with imported data
			if p2 != None and person != None and p2.key.id() != person.key.id() and p2.firstname == person.firstname and p2.lastname == person.lastname:
				self.report.append("removing id=%s, keeping=%s" % (str(p2.key.id()), str(person.key.id())))
				if p2.troop != None:
					tp = TroopPerson.get_by_id(TroopPerson.getid(p2.troop, p2.key))
					if tp != None:
						self.report.append("removing id=%s from troop" % (str(p2.key.id())))
						if self.commit:
							tp.key.delete()
				if self.commit:
					p2.key.delete()
					
			if person != None:
				person.firstname = p["firstname"]
				person.lastname = p["lastname"]
				person.female = p["female"]
				person.birthdate = Person.persnumbertodatetime(p["personnr"])
			else:
				person = Person.create(
					id,
					p["firstname"],
					p["lastname"],
					p["personnr"],
					p["female"])
				self.report.append("Ny person:%s %s %s" % (id, p["firstname"], p["lastname"]))

			person.removed = not p["active"]
			person.patrool = p["patrool"]
			person.email = p["email"]
			person.phone = p["phone"]
			person.mobile = p["mobile"]

			person.scoutgroup = self.GetOrCreateGroup(p["group"]).key
			troop = self.GetOrCreateTroop(p["troop"], person.scoutgroup)
			troop_key = troop.key if troop != None else None
			new_troop = person.troop != troop_key
			person.troop = troop_key
			tp = TroopPerson.get_by_id(TroopPerson.getid(person.troop, person.key))
			if tp == None:
				new_troop = True
			if self.commit:
				person.put()
			if new_troop:
				if person.troop:
					tp = TroopPerson.get_by_id(TroopPerson.getid(person.troop, person.key))
					if tp and self.commit:
						tp.key.delete()

				if troop_key != None:
					if self.commit:
						TroopPerson.create(troop_key, person.key, False).put()
					self.report.append(u"Ny avdelning '%s' för:%s %s" % (p["troop"], p["firstname"], p["lastname"]))

			if person.removed:
				self.report.append("%s marked as removed, removing from troops" % (person.getname()))
				if self.commit:
					tpkeys = TroopPerson.query(TroopPerson.person==person.key).fetch(keys_only=True)
					ndb.delete_multi(tpkeys)
					if self.commit:
						person.key.delete()

		return self.report
				
def DeleteAllData():
	entries = Person.query().fetch(1000, keys_only=True)
	ndb.delete_multi(entries)
	entries = Troop.query().fetch(1000, keys_only=True)
	ndb.delete_multi(entries)
	entries = ScoutGroup.query().fetch(1000, keys_only=True)
	ndb.delete_multi(entries)
	entries = Meeting.query().fetch(10000, keys_only=True)
	ndb.delete_multi(entries)
	entries = TroopPerson.query().fetch(1000, keys_only=True)
	ndb.delete_multi(entries)
	entries = Semester.query().fetch(1000, keys_only=True)
	ndb.delete_multi(entries)
	ndb.get_context().clear_cache() # clear memcache

def ForceSemesterForAll(activeSemester):
	for u in UserPrefs.query().fetch(1000):
		u.activeSemester = activeSemester.key
		u.put()
	for m in Meeting.query().fetch(1000):
		m.semester = activeSemester.key
		m.put()

def UpdateSchemaTroopPerson():
	entries = TroopPerson().query().fetch()
	for e in entries:
		e.put()
		
def UpdateSchemas():
	UpdateSchemaTroopPerson()
