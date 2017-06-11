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
import urllib2

def RunScoutnetImport(groupid, api_key, user, semester):
	commit = True
	data = None
	result = []
	logging.info('Importing semester=%s', semester.getname())
	if groupid == None or groupid == "" or api_key == None or api_key == "":
		result.append(u"Du måste ange både kårid och api nyckel")
		return result

	try:
		data = scoutnet.GetScoutnetMembersAPIJsonData(groupid, api_key)
	except urllib2.HTTPError as e:
		logging.error('Scoutnet http error=%s', str(e))
		result.append(u"Kunde inte läsa medlämmar från scoutnet, fel=%s" % (str(e)))
		if e.code == 401:
			result.append(u"Kontrollera: api nyckel och kårid.")
			result.append(u"Se till att du har rollen 'Medlemsregistrerare', och möjligen 'Webbansvarig' i scoutnet")
		
	if data != None:
		importer = ScoutnetImporter()
		result = importer.DoImport(data, semester)
		if user.groupaccess != importer.importedScoutGroup_key or user.hasaccess != True:
			user.groupaccess = importer.importedScoutGroup_key
			user.hasaccess = True
			user.put()
	return result
	

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
	commit = True
	rapportID = 1
	importedScoutGroup_key = None
	
	def __init__(self):
		self.report = []
		commit = True
		rapportID = 1
	
	def GetOrCreateTroop(self, name, troop_id, group_key, semester_key):
		if len(name) == 0:
			return None
		troop = Troop.get_by_id(Troop.getid(troop_id, group_key, semester_key), use_memcache=True)
		if troop != None:
			if troop.name != name:
				troop.name = name
				if self.commit:
					troop.put()
		else:
			self.report.append("Ny avdelning %s, ID=%s" % (name, troop_id))
			troop = Troop.create(name, troop_id, group_key, semester_key)
			troop.rapportID = self.rapportID # TODO: should check the highest number in the sgroup, will work for full imports
			troop.scoutnetID = int(troop_id)
			self.rapportID += 1
			if self.commit:
				troop.put()

		if troop.scoutnetID != int(troop_id):
			troop.scoutnetID = int(troop_id)
			self.report.append("Nytt ID=%d för avdelning %s" % (troop.scoutnetID, name))
			troop.put()

		return troop

	def GetOrCreateGroup(self, name, scoutnetID):
		if len(name) == 0:
			return None
		group = ScoutGroup.get_by_id(ScoutGroup.getid(name), use_memcache=True)
		if group == None:
			self.report.append(u"Ny kår %s, id=%s" % (name, str(scoutnetID)))
			group = ScoutGroup.create(name, scoutnetID)
			group.scoutnetID = scoutnetID
			group.foreningsID, group.organisationsnummer = GetOrgnrAndKommunIDForGroup(name)
			if self.commit:
				group.put()
			
		if group.scoutnetID != scoutnetID:
			group.scoutnetID = scoutnetID
			if self.commit:
				group.put()

		self.importedScoutGroup_key = group.key
		return group

	def DoImport(self, data, semester):
		if not self.commit:
			self.report.append("*** sparar inte, test mode ***")

		if data == None or len(data) < 80:
			self.report.append(u"Fel: ingen data från scoutnet")
			return self.report

		list = scoutnet.GetScoutnetDataListJson(data)
		self.report.append("antal personer=%d" % (len(list)-1))
		if len(list) < 1:
			self.report.append("Error, too few rows=%d" % len(list))
			return self.report
		
		personsToSave = []
		troopPersonsToSave = []

		for p in list:
			id = int(p["id"])
			person = Person.get_by_id(id, use_memcache=True) # need to be an integer due to backwards compatibility with imported data
			if person == None:
				id = p["personnr"].replace('-', '')
				person = Person.get_by_id(id, use_memcache=True) # attempt to find using personnr, created as a local person

			if person != None:
				person.firstname = p["firstname"]
				person.lastname = p["lastname"]
				person.female = p["female"]
				person.setpersonnr(p["personnr"])
				if person.notInScoutnet != None:
					person.notInScoutnet = False
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
			person.street = p["street"]
			person.zip_code = p["zip_code"]
			person.zip_name = p["zip_name"]
			person.troop_roles = p["troop_roles"]
			person.group_roles = p["group_roles"]
			if semester.year not in person.member_years:
				person.member_years.append(semester.year)
				person._dirty = True;
				
			scoutgroup = self.GetOrCreateGroup(p["group"], p["group_id"])
			person.scoutgroup = scoutgroup.key
			if len(p["troop"]) == 0:
				self.report.append("Ingen avdelning vald för %s %s %s" % (id, p["firstname"], p["lastname"]))
				
			troop = self.GetOrCreateTroop(p["troop"], p["troop_id"], scoutgroup.key, semester.key)
			troop_key = troop.key if troop != None else None
			person.troop = troop_key

			if person._dirty:
				self.report.append(u"Sparar ändringar:%s %s %s" % (id, p["firstname"], p["lastname"]))
				if self.commit:
					personsToSave.append(person)

			if troop_key != None:
				if self.commit:
					tp = TroopPerson.get_by_id(TroopPerson.getid(person.troop, person.key), use_memcache=True)
					if tp == None:
						tp = TroopPerson.create(troop_key, person.key, False)
						troopPersonsToSave.append(tp)
						self.report.append(u"Ny avdelning '%s' för:%s %s" % (p["troop"], p["firstname"], p["lastname"]))

			if person.removed:
				self.report.append(u"%s borttagen, tar bort från avdelningar" % (person.getname()))
				if self.commit:
					tps = TroopPerson.query(TroopPerson.person==person.key).fetch()
					if self.commit:
						for tp in tps:
							tp.delete()
						person.key.delete()
			
		if self.commit:
			ndb.put_multi(personsToSave)
			ndb.put_multi(troopPersonsToSave)

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
	#entries = UserPrefs.query().fetch(1000, keys_only=True)
	#ndb.delete_multi(entries)
	ndb.get_context().clear_cache() # clear memcache

def dofixsgroupids():
	sgroups = ScoutGroup.query().fetch(1000)
	for group in sgroups:
		fid, orgnr = GetOrgnrAndKommunIDForGroup(group.getname())
		if fid != "" and orgnr != "":
			group.foreningsID = fid
			group.organisationsnummer = orgnr
			group.put()

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
