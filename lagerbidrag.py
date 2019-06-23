# -*- coding: utf-8 -*-
from datetime import datetime, date
import math
from dataimport import ndb, Meeting

def person_sort(a, b):

    if a.year == b.year:
        if a.name > b.name:
            return 1
        else:
            return -1
    elif a.year > b.year:
        return 1
    else:
        return -1

class LagerBidragContainer:
    bidrag = ""
    persons = []
    numbers = []

    def __init__(self):
        self.persons = []
        self.numbers = []


class LagerPerson():
    name = ""
    year = ""
    person = ""
    days = 0
    age = 0
    def __init__(self, person="", name="", year="", age=0):
        self.person = person
        self.name = name
        self.age = age
        self.year = year
        self.days = 0

class LagerBidrag():
    contact = ""
    kar = ""
    account = ""
    dateFrom = ""
    dateTo = ""
    site = ""
    address = ""
    zipCode = ""
    phone = ""
    email = ""
    under26 = 0
    over26 = 0
    nights = 0
    nights = 0
    divider = 25
    def __init__(self, kar):
        self.kar = kar
        self.under26 = 0
        self.over26 = 0

def createLagerbidragGroup(scoutgroup, troops, contactperson, site, from_date, to_date):

    from_date_time = datetime.strptime(from_date + " 00:00", "%Y-%m-%d %H:%M")
    to_date_time = datetime.strptime(to_date + " 23:59", "%Y-%m-%d %H:%M")
    year = to_date_time.year
    persons = []
    person_ids = {}

    validateLagetbidragInput(from_date_time, to_date_time)

    for troop in troops:
        # Count number of days participating
        for meeting in Meeting.query(Meeting.datetime >= from_date_time, Meeting.datetime <= to_date_time, Meeting.troop == troop.key).fetch():
            for person in meeting.attendingPersons:
                if not person in person_ids:
                    person_ids[person] = 1
                else:
                    person_ids[person] += 1

    # Collect number of persons
    for person_key, days in person_ids.iteritems():
        person = person_key.get()
        lager_person = LagerPerson(person_key, person.getname(), person.birthdate.year, person.getyearsoldthisyear(year))
        lager_person.days = days
        persons.append(lager_person)

    return createLagerbidragReport(scoutgroup, persons, contactperson, site, from_date, to_date)

def createLagerbidrag(scoutgroup, trooppersons, troopkey_key, contactperson, site, from_date, to_date):

    from_date_time = datetime.strptime(from_date + " 00:00", "%Y-%m-%d %H:%M")
    to_date_time = datetime.strptime(to_date + " 23:59", "%Y-%m-%d %H:%M")
    year = to_date_time.year
    persons = []

    validateLagetbidragInput(from_date_time, to_date_time)

    # Collect number of persons
    for troopperson in trooppersons:
        person_ob = troopperson.person.get()
        persons.append(LagerPerson(troopperson.person, troopperson.getname(), person_ob.birthdate.year, person_ob.getyearsoldthisyear(year)))

    # Count number of days participating
    for meeting in Meeting.query(Meeting.datetime >= from_date_time, Meeting.datetime <= to_date_time, Meeting.troop == troopkey_key).fetch():
        for person in persons:
            is_attending = person.person in meeting.attendingPersons
            if is_attending:
                person.days += 1

    return createLagerbidragReport(scoutgroup, persons, contactperson, site, from_date, to_date)

def validateLagetbidragInput(from_date_time, to_date_time):

    delta = to_date_time.date() - from_date_time.date()
    if delta.days > 14:
        raise ValueError('Lägret får max vara 14 nätter')
    if delta.days < 2:
        raise ValueError('Lägret måsta vara minst 2 nätter')


def createLagerbidragReport(scoutgroup, persons, contactperson, site, from_date, to_date):
    container = LagerBidragContainer()

    bidrag=LagerBidrag(scoutgroup.getname())
    bidrag.email = scoutgroup.epost
    bidrag.phone = scoutgroup.telefon
    bidrag.address = scoutgroup.adress
    bidrag.zipCode = scoutgroup.postadress
    bidrag.account = scoutgroup.bankkonto
    bidrag.contact = contactperson
    bidrag.site = site
    bidrag.dateFrom=from_date
    bidrag.dateTo=to_date

    container.persons = persons

    # Filter out persons participation at least 3 days
    container.persons = [p for p in container.persons if p.days >= 3]

    # Sort by number of days to get the persons over 26 with most days first
    container.persons.sort(key=lambda x: x.days, reverse=True)

    # sum number of persons and days for person under 26
    for person in container.persons:
        if person.age > 25:
            bidrag.over26 = bidrag.over26 + 1
        elif person.age > 6:
            bidrag.under26 = bidrag.under26 + 1
            bidrag.nights += person.days - 1

    # Count number of days for person 26 or older
    allowed_26_and_older = math.floor(bidrag.under26 / 3)
    count_26_and_older = 0
    for person in container.persons:
        if count_26_and_older == allowed_26_and_older:
            break
        if person.age > 25:
            count_26_and_older += 1
            bidrag.nights += person.days - 1

    container.persons.sort(person_sort)

    number_of_persons = len(container.persons)
    tmp_divider = int(math.ceil(number_of_persons / 2.0))

    bidrag.divider = 25 if tmp_divider < 25 else tmp_divider

    # Add empty persons
    container.persons.extend([LagerPerson() for i in range(0, bidrag.divider * 2 - len(container.persons))])

    container.bidrag = bidrag
    container.numbers = range(0, container.bidrag.divider)

    return container

