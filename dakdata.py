# -*- coding: utf-8 -*-
import datetime

# http://www.sverigesforeningssystem.se/dak-formatet/vad-ar-dak/

class Deltagare:
	def __init__(self, id, Foernamn, Efternamn, Personnummer, ledare, epost="", mobilNr="", postnummer=""):
		self.id = id
		self.Foernamn = Foernamn
		self.Efternamn = Efternamn
		self.Personnummer = Personnummer
		self.Ledare = ledare
		self.Epost = epost
		self.MobilNr = mobilNr
		self.Postnummer = postnummer

	def IsFemale(self):
		return False if int(self.Personnummer[-2])&1 == 1 else True

	def AgeThisSemester(self, semester):
		return int(self.Personnummer[0:4]) - semester.year

	def __eq__(self, other):
		return self.Personnummer == other.Personnummer

	def __hash__(self):
		return hash(self.Personnummer)

class Sammankomst:
	kod = ""
	datum = None
	duration = 90
	Aktivitet = "Moete" # OBS en av: Traening, Match, Moete, Oevrigt
	deltagare = []
	ledare = []
	
	def __init__(self, kod, datum, duration, Aktivitet):
		self.kod = kod
		self.datum = datum
		self.duration = duration
		self.Aktivitet = Aktivitet
		self.deltagare = []
		self.ledare = []

	def GetDateString(self, formatString='%Y-%m-%d'):
		return self.datum.strftime(formatString)
	
	def GetStartTimeString(self, formatString='%H:%M:%S'):
		return self.datum.strftime(formatString)
	
	def GetStopTimeString(self, formatString='%H:%M:%S'):
		maxEndTime = self.datum.replace(hour=23,minute=59,second=59)
		endtime = self.datum + datetime.timedelta(minutes=self.duration)
		if endtime > maxEndTime:
			endtime = maxEndTime # limit to the current day (to keep Stop time after Start time)
		return endtime.strftime(formatString)
	
	def GetAllPersons(self):
		return self.ledare + self.deltagare

	def IsPersonAttending(self, person):
		for p in self.GetAllPersons():
			if p.Personnummer == person.Personnummer:
				return p.Attending
		return False

class Narvarokort:
	NaervarokortNummer=""
	Sammankomster = []
	Aktivitet="Moete"
	Lokal="Scouthuset"
	NamnPaaKort=""
	deltagare = []
	ledare = []

	def __init__(self):
		self.deltagare = []
		self.ledare = []
		self.Sammankomster = []
	
class DakData:
	kommunID = ""
	foreningsID = ""
	foereningsNamn=u""
	organisationsnummer=""
	kort = None
	
	def __init__(self):
		self.kort = Narvarokort()
	