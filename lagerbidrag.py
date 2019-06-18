
import datetime
import math
from dataimport import ndb, Meeting

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
    def __init__(self, kar):
        self.kar = kar
        self.under26 = 0
        self.over26 = 0

def createLagerbidrag(scoutgroup, trooppersons, troopkey_key, contactperson, site, fromDate, toDate):
    container = LagerBidragContainer()

    from_date_time = datetime.datetime.strptime(fromDate + " 00:00", "%Y-%m-%d %H:%M")
    to_date_time = datetime.datetime.strptime(toDate + " 23:59", "%Y-%m-%d %H:%M")
    year = to_date_time.year

    bidrag=LagerBidrag(scoutgroup.getname())
    bidrag.email = scoutgroup.epost
    bidrag.phone = scoutgroup.telefon
    bidrag.address = scoutgroup.adress
    bidrag.zipCode = scoutgroup.postadress
    bidrag.account = scoutgroup.bankkonto
    bidrag.contact = contactperson
    bidrag.site = site
    bidrag.dateFrom=from_date_time.strftime("%Y-%m-%d")
    bidrag.dateTo=to_date_time.strftime("%Y-%m-%d")

    # Collect number of persons
    for troopperson in trooppersons:
        container.persons.append(LagerPerson(troopperson.person, troopperson.getname(), troopperson.person.get().birthdate.year, troopperson.person.get().getyearsoldthisyear(year)))

    # Count number of days participating
    for meeting in Meeting.query(Meeting.datetime >= from_date_time, Meeting.datetime <= to_date_time, Meeting.troop == troopkey_key).fetch():
        for person in container.persons:
            isAttending = person.person in meeting.attendingPersons
            if isAttending:
                person.days += 1


    # Filter out persons participation at least 3 days
    container.persons = [p for p in container.persons if p.days >= 3]

    # sum number of persons and days for person under 26
    for person in container.persons:
        if person.age > 25:
            bidrag.over26 = bidrag.over26 + 1
        elif person.age > 6:
            bidrag.under26 = bidrag.under26 + 1
            bidrag.nights += person.days

    # Count number of days for person 26 or older
    allowed_26_and_older = math.floor(bidrag.under26 / 3)
    count_26_and_older = 0
    for person in container.persons:
        if count_26_and_older == allowed_26_and_older:
            break
        if person.age > 25:
            count_26_and_older += 1
            bidrag.nights += person.days

    # Add empty persons
    container.persons.extend([LagerPerson() for i in range(0, 50 - len(container.persons))])

    container.bidrag = bidrag
    container.numbers = range(0, 25)

    return container

