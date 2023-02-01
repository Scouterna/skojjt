# -*- coding: utf-8 -*-
"""
Module for exporting data according to DAC format.

http://www.sverigesforeningssystem.se/dak-formatet/vad-ar-dak/
"""
import datetime

class Deltagare(object):
    def __init__(self, uid, foernamn, efternamn, personnummer, ledare, epost="", mobil_nr="", postnummer=""):
        self.uid = uid
        self.foernamn = foernamn
        self.efternamn = efternamn
        self.personnummer = personnummer
        self.ledare = ledare
        self.epost = epost
        self.mobil_nr = mobil_nr
        self.postnummer = postnummer

    def is_female(self):
        "Return True if the person is female"
        return False if int(self.personnummer[-2])&1 == 1 else True

    def age_this_semester(self, semester):
        "Is the person aget this semester"
        return int(self.personnummer[0:4]) - semester.year

    def __eq__(self, other):
        return self.personnummer == other.personnummer

    def __hash__(self):
        return hash(self.personnummer)


class Sammankomst(object):

    def __init__(self, kod, datum, duration, aktivitet):
        self.kod = kod
        self.datum = datum
        self.duration = duration
        self.aktivitet = aktivitet
        self.typ = "Moete" # OBS en av: Traening, Match, Moete, Oevrigt
        self.deltagare = []
        self.ledare = []

    def get_date_string(self, format_string='%Y-%m-%d'):
        return self.datum.strftime(format_string)

    def get_start_time_string(self, format_string='%H:%M:%S'):
        return self.datum.strftime(format_string)

    def get_stop_time_string(self, format_string='%H:%M:%S'):
        max_end_time = self.datum.replace(hour=23, minute=59, second=59)
        endtime = self.datum + datetime.timedelta(minutes=self.duration)
        if endtime > max_end_time:
            endtime = max_end_time # limit to the current day (to keep Stop time after Start time)
        return endtime.strftime(format_string)

    def get_all_persons(self):
        return self.ledare + self.deltagare

    def is_person_attending(self, person):
        for person in self.get_all_persons():
            if person.Personnummer == person.Personnummer:
                return person.Attending
        return False


class Narvarokort(object):
    def __init__(self):
        self.deltagare = []
        self.ledare = []
        self.sammankomster = []
        self.naervarokort_nummer = ""
        self.lokal = "Scouthuset"
        self.namn_paa_kort = ""
        self.aktivitet = "Scouting" # Huvudsaklig aktivitet för närvarokortet. 


class DakData(object):
    "Main container for DAK data"
    def __init__(self):
        self.kort = Narvarokort()
        self.kommun_id = ""
        self.forenings_id = ""
        self.foerenings_namn = ""
        self.organisationsnummer = ""
