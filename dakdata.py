# -*- coding: utf-8 -*-
import datetime

# http://www.sverigesforeningssystem.se/dak-formatet/vad-ar-dak/

class Deltagare:
	id = ""
	Foernamn = ""
	Efternamn = ""
	Personnummer = ""
	Ledare = False
	Epost = ""
	MobilNr = ""

	def __init__(self, id, Foernamn, Efternamn, Personnummer, ledare, epost="", mobilNr=""):
		self.id = id
		self.Foernamn = Foernamn
		self.Efternamn = Efternamn
		self.Personnummer = Personnummer
		self.Ledare = ledare
		self.Epost = epost
		self.MobilNr = mobilNr

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

	def GetDateString(self):
		return self.datum.strftime('%Y-%m-%d')
	
	def GetStartTimeString(self):
		return self.datum.strftime('%H:%M:%S')
		
	def GetStopTimeString(self):
		endtime = self.datum + datetime.timedelta(minutes=self.duration)
		return endtime.strftime('%H:%M:%S')

class Narvarokort:
	NaervarokortNummer="1"
	Sammankomster = []
	Aktivitet="Moete"
	Lokal="Scouthuset"
	NamnPaaKort=""
	deltagare = []
	ledare = []
	
	
class DakData:
	kommunID = "1480"
	foreningsID = "3843"
	foereningsNamn=u""
	organisationsnummer="857203-7722"
	
	def __init__(self):
		self.kort = Narvarokort()
	