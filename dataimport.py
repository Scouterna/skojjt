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
		reader = ucsv.DictReader(f, delimiter=',', quoting=ucsv.QUOTE_ALL, fieldnames=['namn', 'id', 'orgnr'])
		for row in reader:
			name = row['namn'].lower().strip("\"")
			if name == groupname:
				return str(row['id']), str(row['orgnr'])
	return "", ""

class ScoutnetImporter:
	report = []
	commit = False
	rapportID = 1
	
	def __init__(self):
		self.report = []
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

		list = scoutnet.GetScoutnetDataListJson(data)
		self.report.append("antal personer=%d" % (len(list)-1))
		if len(list) < 1:
			self.report.append("Error, too few rows=%d" % len(list))
			return self.report

		for p in list:
			id = int(p["id"])
			person = Person.get_by_id(id) # need to be an integer due to backwards compatility with imported data

			if person != None:
				person.firstname = p["firstname"]
				person.lastname = p["lastname"]
				person.female = p["female"]
				person.setpersonnr(p["personnr"])
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
			if len(p["troop"]) == 0:
				self.report.append("Ingen avdelning vald för %s %s %s" % (id, p["firstname"], p["lastname"]))

			troop = self.GetOrCreateTroop(p["troop"], person.scoutgroup)
			troop_key = troop.key if troop != None else None
			new_troop = person.troop != troop_key
			person.troop = troop_key
			#if person.troop != None:
			#	tp = TroopPerson.get_by_id(TroopPerson.getid(person.troop, person.key)) # check if troop person doesn't exist
			#	if tp == None:
			#		new_troop = True
			if person._dirty:
				self.report.append(u"Sparar ändringar:%s %s %s" % (id, p["firstname"], p["lastname"]))
				if self.commit:
					person.put()

			if new_troop:
				if person.troop:
					tp = TroopPerson.get_by_id(TroopPerson.getid(person.troop, person.key))
					if tp != None and self.commit:
						tp.delete()

				if troop_key != None:
					if self.commit:
						TroopPerson.create(troop_key, person.key, False).put()
					self.report.append(u"Ny avdelning '%s' för:%s %s" % (p["troop"], p["firstname"], p["lastname"]))

			if person.removed:
				self.report.append(u"%s borttagen, tar bort från avdelningar" % (person.getname()))
				if self.commit:
					tps = TroopPerson.query(TroopPerson.person==person.key).fetch()
					if self.commit:
						for tp in tps:
							tp.delete()
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

def dofixsgroupids():
	sgroups = ScoutGroup.query().fetch(1000)
	for group in sgroups:
		fid, orgnr = GetOrgnrAndKommunIDForGroup(group.getname())
		if fid != "" and orgnr != "":
			group.foreningsID = fid
			group.organisationsnummer = orgnr
			group.put()

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
