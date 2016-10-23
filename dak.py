# -*- coding: utf-8 -*-


class Deltagare():
	id = ""
	Foernamn = ""
	Efternamn = ""
	Personnummer = ""
	Kon = "" # Man/Kvinna
	Ledare = False

class Sammankomst():
	datum = None
	duration = 90
	kod = ""
	Aktivitet = "Scouting"
	deltagare = []
	
	def GetDateString(self):
		return self.datum.strftime('%Y-%m-%d')
	
	def GetStartTimeString(self):
		return self.datum.strftime('%H-%M')
		
	def GetStopTimeString(self):
		endtime = self.datum + datetime.timedelta(minutes=self.duration)
		return endtime.strftime('%H-%M')
	

class Narvarokort():
	NaervarokortNummer="1"
	Sammankomster = []
	Aktivitet="Scouting"
	Lokal="Scouthuset eller ute"
	NamnPaaKort=""
	deltagare = []
	
	
class DakData:
	kommunID = "1480"
	foreningsID = "3843"
	foereningsNamn="Tynnereds Scoutkår"
	organisationsnummer="857203-7722"
	
	def __init__():
		self.kort = Narvarokort()
	