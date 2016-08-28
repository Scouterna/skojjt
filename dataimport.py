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


def GetOrCreateCurrentSemester():
	thisdate = datetime.datetime.now()
	ht = False if thisdate.month>6 else True
	semester = Semester.get_by_id(Semester.getid(thisdate.year + 1, ht))
	if semester == None:
		semester = Semester.create(thisdate.year + 1, ht)
		semester.put()
	return semester
	
def GetOrCreateTroop(name, group_key):
	if len(name) == 0:
		return None
	troop = Troop.get_by_id(Troop.getid(name, group_key))
	if troop == None:
		logging.info("Creating troop %s", name)
		troop = Troop.create(name, group_key)
		troop.put()
	return troop
	
def GetOrCreateGroup(name):
	if len(name) == 0:
		return None
	group = ScoutGroup.get_by_id(ScoutGroup.getid(name))
	if group == None:
		logging.info("Creating group %s", name)
		group = ScoutGroup.create(name)
		group.activeSemester = GetOrCreateCurrentSemester().key
		group.put()
	return group

def ReimportData(data, commit=False):
	report = []
	if not commit:
		report.append("*** sparar inte, test mode ***")

	if len(data) < 80:
		report.append("Error, too little data length=%d" % len(data))
		return report
		
	list = scoutnet.GetScoutnetDataList(StringIO.StringIO(data))
	report.append("antal personer=%d" % (len(list)-1))
	if len(list) < 1:
		report.append("Error, too few rows=%d" % len(list))
		return report
		
	for p in list:
		person = Person.get_by_id(p["id"])
		if person != None:
			person.firstname = p["firstname"]
			person.lastname = p["lastname"]
			person.female = p["female"]
			person.birthdate = Person.persnumbertodatetime(p["personnr"])
		else:
			person = Person.create(
				p["id"],
				p["firstname"],
				p["lastname"],
				p["personnr"],
				p["female"])
			report.append("Ny person:%s %s %s" % (p["id"], p["firstname"], p["lastname"]))

		person.removed = not p["active"]
		person.patrool = p["patrool"]
		person.scoutgroup = GetOrCreateGroup(p["group"]).key
		troop = GetOrCreateTroop(p["troop"], person.scoutgroup)
		troop_key = troop.key if troop != None else None
		new_troop = person.troop != troop_key
		person.troop = troop_key
		if commit:
			person.put()
		if new_troop:
			if person.troop:
				tp = TroopPerson.get_by_id(TroopPerson.getid(person.troop, person.key))
				if tp and commit:
					tp.key.delete()

			if troop_key != None:
				if commit:
					TroopPerson.create(troop_key, person.key, False).put()
				report.append(u"Ny avdelning '%s' för:%s %s" % (p["troop"], p["firstname"], p["lastname"]))

		if person.removed:
			report.append("%s marked as removed, removing from troops" % (person.getname()))
			if commit:
				tpkeys = TroopPerson.query(TroopPerson.person==person.key).fetch(keys_only=True)
				ndb.delete_multi(tpkeys)
			if len(Attendance.query(Attendance.person==person.key).fetch(1, keys_only=True)) == 0:
				report.append("%s has no attendance, deleting" % (person.getname()))
				if commit:
					person.key.delete()

	return report
				
			
def unicode_csv_reader(utf8_data):
	csv_reader = ucsv.reader(utf8_data, delimiter=',', quoting=ucsv.QUOTE_ALL)
	for row in csv_reader:
		yield [cell for cell in row]

def ImportData():
	thisdate = datetime.datetime.now()
	ht = False if thisdate.month>6 else True
	activeSemester = Semester.create(thisdate.year + 1, ht)
	
	filename = 'members.csv'
	reader = unicode_csv_reader(open(filename))
	first = True
	inr = -1
	ifname = 0
	ilname = 0
	ipnummer = 0
	isgroup = 0
	itroop = 0
	ipatrool = 0
	isex = 0
	scoutgroupname = ""
	troopname = ""
	scoutgroup_key = 0
	troop_key = 0
	for row in reader:
		if first:
			first = False
			for index, col in enumerate(row):
				if col == "Medlemsnr.":
					inr = index
				elif col == u"Förnamn":
					ifname = index
				elif col == "Efternamn":
					ilname = index
				elif col == u"Personnummer":
					ipnummer = index
				elif col == u"Kår":
					isgroup = index
				elif col == "Avdelning":
					itroop = index
				elif col == "Patrull":
					ipatrool = index
				elif col == u"Kön":
					isex = index
			
			#logging.info("fields %d, %d, %d, %d, %d, %d, %d, %d", inr,ifname,ilname,ipnummer,isgroup,itroop,ipatrool,isex)
			if (inr+1) * ifname * ilname * ipnummer * isgroup * itroop * ipatrool * isex == 0:
				logging.error("missing some field %d, %d, %d, %d, %d, %d, %d, %d", inr,ifname,ilname,ipnummer,isgroup,itroop,ipatrool,isex)
				raise ValueError('Missing some field')
		else:
			logging.info(row[isgroup])
			if row[isgroup] != scoutgroupname:
				scoutgroupname = row[isgroup]
				scoutgroup = ScoutGroup.create(scoutgroupname)
				scoutgroup.activeSemester = activeSemester.key
				scoutgroup.put()
			if row[itroop] != troopname and len(row[itroop])>0:
				troopname = row[itroop]
				troop = Troop.create(troopname, scoutgroup.key)
				troop.put()
			
			logging.info("%s %s %s %s %s", row[inr], row[ifname], row[ilname], row[ipnummer], row[isex])
			person = Person.create(
				row[inr],
				row[ifname],
				row[ilname],
				row[ipnummer],
				row[isex]!='Man')
			person.troop=troop.key
			person.patrool=row[ipatrool]
			person.scoutgroup = scoutgroup.key
			person.put()
			
			TroopPerson.create(troop.key, person.key, False).put()

			
def DeleteAllData():
#	entries = Person.query().fetch(1000, keys_only=True)
#	ndb.delete_multi(entries)
#	entries = Troop.query().fetch(1000, keys_only=True)
#	ndb.delete_multi(entries)
#	entries = ScoutGroup.query().fetch(1000, keys_only=True)
#	ndb.delete_multi(entries)
#	entries = Meeting.query().fetch(10000, keys_only=True)
#	ndb.delete_multi(entries)
#	entries = Attendance.query().fetch(10000, keys_only=True)
#	ndb.delete_multi(entries)
#	entries = TroopPerson.query().fetch(1000, keys_only=True)
#	ndb.delete_multi(entries)
#	entries = Semester.query().fetch(1000, keys_only=True)
#	ndb.delete_multi(entries)

	ndb.get_context().clear_cache() # clear memcache


def UpdateSchemaTroopPerson():
	entries = TroopPerson().query().fetch()
	for e in entries:
		e.put()
		
def UpdateSchemas():
	UpdateSchemaTroopPerson()

	
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
