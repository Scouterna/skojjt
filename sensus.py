# -*- coding: utf-8 -*-
import datetime


class Deltagare:
    id = ""
    Foernamn = ""
    Efternamn = ""
    Personnummer = ""
    Ledare = False
    Epost = ""
    MobilNr = ""
    Attending = True

    def __init__(self, id, Foernamn, Efternamn, Personnummer, ledare, epost="", mobilNr="", attending=True):
        self.id = id
        self.Foernamn = Foernamn
        self.Efternamn = Efternamn
        self.Personnummer = Personnummer
        self.Ledare = ledare
        self.Epost = epost
        self.MobilNr = mobilNr
        self.Attending = attending

    def getAttendingMark(self):
        return "1" if self.Attending else ""

    def getname(self):
        return self.Foernamn + ' ' + self.Efternamn


class Sammankomst:
    kod = ""
    datum = None
    duration = 90
    deltagare = []
    ledare = []

    def getAllPersons(self):
        return self.ledare + self.deltagare

    def isPersonAttending(self, person):
        for p in self.getAllPersons():
            if p.Personnummer == person.Personnummer:
                return p.Attending
        return False

    def __init__(self, kod, datum, duration, Aktivitet):
        self.kod = kod
        self.datum = datum
        self.duration = duration
        self.Aktivitet = Aktivitet
        self.deltagare = []
        self.ledare = []

    def GetDateString(self, format='%Y-%m-%d'):
        return self.datum.strftime(format)

    def GetStartTimeString(self, format='%H:%M:%S'):
        return self.datum.strftime(format)

    def GetStopTimeString(self, format='%H:%M:%S'):
        maxEndTime = self.datum.replace(hour=23,minute=59,second=59)
        endtime = self.datum + datetime.timedelta(minutes=self.duration)
        if endtime > maxEndTime:
            endtime = maxEndTime # limit to the current day (to keep Stop time after Start time)
        return endtime.strftime(format)


class SensusLista:
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

    def getAllPersons(self):
        return self.ledare + self.deltagare

    def getAttendantsCountsPerMeeting(self):
        attendantsCounts = []
        for m in self.Sammankomster:
            personCount = 0
            for d in m.getAllPersons():
                if d.Attending:
                    personCount += 1
            attendantsCounts.append(personCount)
        return attendantsCounts

    def getAttendantsHoursPerMeeting(self):
        attendantsHours = []
        for m in self.Sammankomster:
            attendantsHours.append(m.duration/45)
        return attendantsHours


class SensusData:
    kommunID = ""
    foreningsID = ""
    foereningsNamn=u""
    organisationsnummer=""
    verksamhetsAar = ""
    listor = []

    def __init__(self):
        self.listor = []
