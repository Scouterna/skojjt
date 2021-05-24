# -*- coding: utf-8 -*-
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import ndb
import datetime
import logging


class PropertyWriteTracker(ndb.Model):
    _dirty = False

    def __init__(self, *args, **kw):
        self._dirty = False
        super(PropertyWriteTracker, self).__init__(*args, **kw)

    def __setattr__(self, key, value):
        if key[:1] != '_': # avoid all system properties and "_dirty"
            if self.__getattribute__(key) != value:
                self._make_dirty()
        super(PropertyWriteTracker, self).__setattr__(key, value)

    def _make_dirty(self):
        self._dirty = True

    def _not_dirty(self):
        self._dirty = False


class Semester(ndb.Model):
    year = ndb.IntegerProperty(required=True)
    ht = ndb.BooleanProperty(required=True)

    @staticmethod
    def getid(year, ht):
        return str(year) + ("ht" if ht else "vt")

    @staticmethod
    def create(year, ht):
        if year < 2016:
            raise ValueError("Invalid year %d" % year)
        return Semester(id=Semester.getid(year, ht), year=year, ht=ht)

    @staticmethod
    def getbyId(id_string):
        return Semester.get_by_id(id_string.replace('-',''), use_memcache=True)

    @staticmethod
    def getOrCreateCurrent():
        thisdate = datetime.datetime.now()
        ht = True if thisdate.month>6 else False
        year = thisdate.year
        semester = Semester.get_by_id(Semester.getid(year, ht), use_memcache=True)
        if semester == None:
            semester = Semester.create(year, ht)
            semester.put()
        return semester

    @staticmethod
    def getAllSemestersSorted(ascending=False):
        semesters=[]
        semesters.extend(Semester.query().order(-Semester.year, -Semester.ht).fetch())
        if len(semesters) == 0:
            semesters = [Semester.getOrCreateCurrent()]
        if ascending:
            semesters.reverse()
        return semesters

    def getname(self):
        return "%04d-%s" % (self.year, "ht" if self.ht else "vt")

    def getMinDateStr(self):
        if self.ht:
            return "%04d-07-01" % (self.year)
        else:
            return "%04d-01-01" % (self.year)

    def getMaxDateStr(self):
        if self.ht:
            return "%04d-12-31" % (self.year)
        else:
            return "%04d-06-30" % (self.year)

# kår
class ScoutGroup(ndb.Model):
    name = ndb.StringProperty(required=True)
    activeSemester = ndb.KeyProperty(kind=Semester, required=False) # TODO: remove
    organisationsnummer = ndb.StringProperty()
    foreningsID = ndb.StringProperty(required=False, default="")
    scoutnetID = ndb.StringProperty(required=False, default="")
    kommunID = ndb.StringProperty(default="1480")
    apikey_waitinglist = ndb.StringProperty(required=False, default="")
    apikey_all_members = ndb.StringProperty(required=False, default="")
    bankkonto = ndb.StringProperty(required=False, default="")
    adress = ndb.StringProperty(required=False, default="")
    postadress = ndb.StringProperty(required=False, default="")
    epost = ndb.StringProperty(required=False, default="")
    telefon = ndb.StringProperty(required=False, default="")
    default_lagerplats = ndb.StringProperty(required=False, default="")
    firmatecknare = ndb.StringProperty(required=False, default="")
    firmatecknartelefon = ndb.StringProperty(required=False, default="")
    firmatecknaremail = ndb.StringProperty(required=False, default="")
    attendance_min_year = ndb.IntegerProperty(required=False, default=10)
    attendance_incl_hike = ndb.BooleanProperty(required=False, default=True)

    @staticmethod
    def getid(name):
        return name.lower().replace(' ', '')

    @staticmethod
    def getbyname(name):
        return ScoutGroup.get_by_id(ScoutGroup.getid(name), use_memcache=True)

    @staticmethod
    def create(name, scoutnetID):
        if len(name) < 2:
            raise ValueError("Invalid name %s" % (name))
        return ScoutGroup(id=ScoutGroup.getid(name), name=name, scoutnetID=scoutnetID)

    @staticmethod
    def getgroupsforuser(user):
        if user.hasadminaccess:
            return ScoutGroup.query().fetch(100)
        # TODO Multi-group access
        if user.groupaccess is not None:
            return [user.groupaccess.get()]
        return []

    def getname(self):
        return self.name

    def canAddToWaitinglist(self):
        return self.scoutnetID != None and self.scoutnetID != "" and self.apikey_waitinglist != None and self.apikey_waitinglist != ""

# avdelning
class Troop(ndb.Model):
    name = ndb.StringProperty()
    scoutgroup = ndb.KeyProperty(kind=ScoutGroup)
    defaultstarttime = ndb.StringProperty(default="18:30")
    defaultduration = ndb.IntegerProperty(default=90)
    rapportID = ndb.IntegerProperty()
    scoutnetID = ndb.IntegerProperty(required=False, default=0)
    semester_key = ndb.KeyProperty(kind=Semester)

    @staticmethod
    def getid(troop_id, scoutgroup_key, semester_key):
        semester = semester_key.get()
        return str(troop_id) + '/' + str(scoutgroup_key.id()) + '/' + semester.getname()

    @staticmethod
    def create(name, troop_id, scoutgroup_key, semester_key):
        return Troop(id=Troop.getid(troop_id, scoutgroup_key, semester_key), name=name, scoutgroup=scoutgroup_key, semester_key=semester_key)

    @staticmethod
    def getTroopsForUser(sgroup_key, user):
        return Troop.query(Troop.scoutgroup==sgroup_key, user.activeSemester==Troop.semester_key).fetch()

    def getname(self):
        return self.name

    def delete(self):
        for tp in TroopPerson.getTroopPersonsForTroop(self.key):
            tp.delete()
        for meeting in Meeting.gettroopmeetings(self.key):
            meeting.delete()
        self.key.delete()


class PendingPersonKeyChange(PropertyWriteTracker):
    pass # forward declaration see below


class Person(PropertyWriteTracker):
    firstname = ndb.StringProperty(required=True)
    lastname = ndb.StringProperty(required=True)
    birthdate = ndb.DateProperty(required=True) # could be a computed property from personnr
    personnr = ndb.StringProperty()
    member_no = ndb.IntegerProperty()
    patrool = ndb.StringProperty()
    scoutgroup = ndb.KeyProperty(kind=ScoutGroup)
    notInScoutnet = ndb.BooleanProperty()
    removed = ndb.BooleanProperty()
    email = ndb.StringProperty()
    phone = ndb.StringProperty()
    mobile = ndb.StringProperty()
    alt_email = ndb.StringProperty()
    mum_name = ndb.StringProperty()
    mum_email = ndb.StringProperty()
    mum_mobile = ndb.StringProperty()
    dad_name = ndb.StringProperty()
    dad_email = ndb.StringProperty()
    dad_mobile = ndb.StringProperty()
    street = ndb.StringProperty()
    zip_code = ndb.StringProperty()
    zip_name = ndb.StringProperty()
    troop_roles = ndb.StringProperty(repeated=True)
    group_roles = ndb.StringProperty(repeated=True)
    member_years = ndb.IntegerProperty(repeated=True) # a list of years this person have been imported, used for membership reporting
    version = ndb.IntegerProperty() # data version, to keep track of updates

    @staticmethod
    def create(member_no, firstname, lastname, personnr):
        person = Person(id=member_no,
            member_no=member_no,
            firstname=firstname,
            lastname=lastname)
        person.setpersonnr(personnr)
        return person

    @staticmethod
    def persnumbertodate(pnr):
        return datetime.datetime.strptime(pnr[:8], "%Y%m%d").date()

    @staticmethod
    def getIsFemale(personnummer):
        return False if int(personnummer[-2])&1 == 1 else True

    @staticmethod
    def getByMemberNo(member_no):
        return Person.get_by_id(member_no, use_memcache=True)

    #deprecated 
    @staticmethod
    def getByPersonNr(personnr):
        return Person.get_by_id(personnr, use_memcache=True)

    def getMemberNo(self):
        return self.key.id()

    """
    # updateKey
    # If the person is not using member_no as id
    # create a new person with member_no as id
    # copy all fields to the new person
    # update all TroopPerson's person
    # update all Meeting's attending persons
    # create update record, old_id -> new_id
    # do after calls to this method:
    #   remove the old persons
    #   commit changes
    #   clear memcache
    #
    # returns: newPerson, pendingKeyChange (to be committed)
    """
    def updateKey(self): 
        if self.member_no is not None and self.key.id() != self.member_no:
            newPerson = Person.create(self.member_no, self.firstname, self.lastname, self.personnr)
            newPerson.patrool = self.patrool
            newPerson.scoutgroup = self.scoutgroup
            newPerson.notInScoutnet = self.notInScoutnet
            newPerson.removed = self.removed
            newPerson.email = self.email
            newPerson.phone = self.phone
            newPerson.mobile = self.mobile
            newPerson.alt_email = self.alt_email
            newPerson.mum_name = self.mum_name
            newPerson.mum_email = self.mum_email
            newPerson.mum_mobile = self.mum_mobile
            newPerson.dad_name = self.dad_name
            newPerson.dad_email = self.dad_email
            newPerson.dad_mobile = self.dad_mobile
            newPerson.street = self.street
            newPerson.zip_code = self.zip_code
            newPerson.zip_name = self.zip_name
            newPerson.troop_roles = self.troop_roles
            newPerson.group_roles = self.group_roles
            newPerson.member_years = self.member_years
            # set a version number to allow us to work incrementally, the records with version 1 will not be checked again
            self.version = 1 # this means that we have processed this record (it still has the wrong id, but will be deleted)
            newPerson.version = 2
            pendingKeyChange = PendingPersonKeyChange.create_or_update(self.key, newPerson.key)
            return (newPerson, pendingKeyChange)
        else:
            return (None, None)


    def isFemale(self):
        return Person.getIsFemale(self.personnr)

    def setpersonnr(self, pnr):
        self.personnr = pnr.replace('-', '')
        self.birthdate = Person.persnumbertodate(pnr)

    def getpersonnr(self):
        return self.personnr.replace('-', '')

    def getbirthdatestring(self):
        return self.birthdate.strftime("%Y-%m-%d")
    def getpersnumberstr(self):
        return self.birthdate.strftime("%Y%m%d0000")

    def getname(self):
        return self.firstname + " " + self.lastname

    def getnameWithStatus(self):
        if self.removed == True:
            return self.firstname + " " + self.lastname + ' (B)'
        return self.firstname + " " + self.lastname

    def getyearsoldthisyear(self, year):
        return year - self.birthdate.year

    def isLeader(self):
        if self.troop_roles != None:
            if any(u'ledare' in role for role in self.troop_roles):
                return True
        thisdate = datetime.datetime.now()
        return self.getyearsoldthisyear(thisdate.year) >= 18

    def isBoardMember(self):
        if self.group_roles != None:
            for role in self.group_roles:
                if role in [u'k\xe5rstyrelseledamot', u'k\xe5rkass\xf6r', u'k\xe5rordf\xf6rande', u'vice k\xe5rordf\xf6rande', u'k\xe5rsekreterare']:
                    return True
        return False

    def getpatrol(self):
        return self.patrool # TODO: fix spelling error

    def getReportID(self):
        """Returns a person ID that can be used in reports.
        It will prefer the scoutnet id if imported, else the old key id.
        Eventually all persons will have scoutnet id set."""
        return str(self.member_no) if self.member_no is not None else str(self.key.id())

    def getmembernumber(self):
        return self.member_no

    def setpatrol(self, patrolname):
        self.patrool = patrolname # TODO: fix spelling error

    def getMemberYearsString(self):
        return ','.join(str(y) for y in self.member_years)

    def getPostadress(self):
        if self.zip_code is None or self.zip_name is None:
            return ''
        return self.zip_code + ' ' + self.zip_name


# used for key person key update
class PendingPersonKeyChange(PropertyWriteTracker):
    old_key = ndb.KeyProperty(kind=Person)
    new_key = ndb.KeyProperty(kind=Person)

    @staticmethod
    def create_or_update(old_key, new_key):
        person_id = old_key.id()
        ppkc = PendingPersonKeyChange.get_by_id(person_id, use_memcache=True)
        if ppkc is not None:
            ppkc.old_key = old_key
            ppkc.new_key = new_key
        else:
            ppkc = PendingPersonKeyChange(id=person_id, old_key=old_key, new_key=new_key)
            ppkc._dirty = True
        return ppkc


class Meeting(ndb.Model):
    datetime = ndb.DateTimeProperty(auto_now_add=True, required=True)
    name = ndb.StringProperty(required=True)
    troop = ndb.KeyProperty(kind=Troop, required=True)
    duration = ndb.IntegerProperty(default=90, required=True) #minutes
    semester = ndb.KeyProperty(kind=Semester, required=False) # TODO: remove
    attendingPersons = ndb.KeyProperty(kind=Person, repeated=True) # list of attending persons' keys
    ishike = ndb.BooleanProperty(required=False, default=False)

    @staticmethod
    def __getMemcacheKeyString(troop_key):
        return 'tms:' + str(troop_key)

    @staticmethod
    def getId(meetingDatetime, troop_key):
        return meetingDatetime.strftime("%Y%m%d%H%M")+str(troop_key.id())

    @staticmethod
    def getOrCreate(troop_key, name, datetime, duration, ishike):
        m = Meeting.get_by_id(Meeting.getId(datetime, troop_key), use_memcache=True)
        if m != None:
            if m.name != name or m.duration != duration or m.ishike != ishike:
                m.name = name
                m.duration = duration
                m.ishike = ishike
                m.put()
        else:
            m = Meeting(id=Meeting.getId(datetime, troop_key),
                datetime=datetime,
                name=name,
                troop=troop_key,
                duration=duration,
                ishike=ishike
                )
        troopmeeting_keys = memcache.get(Meeting.__getMemcacheKeyString(troop_key))
        if troopmeeting_keys is not None and m.key not in troopmeeting_keys:
            troopmeeting_keys.append(m.key)
            memcache.replace(Meeting.__getMemcacheKeyString(troop_key), troopmeeting_keys)
        return m

    @staticmethod
    def gettroopmeetings(troop_key):
        troopmeetings = []
        troopmeeting_keys = memcache.get(Meeting.__getMemcacheKeyString(troop_key))
        if troopmeeting_keys is None:
            troopmeeting_keys = Meeting.query(Meeting.troop==troop_key).fetch(keys_only=True)
            memcache.add(Meeting.__getMemcacheKeyString(troop_key), troopmeeting_keys)
        for tm_key in troopmeeting_keys:
            m = tm_key.get()
            if m != None:
                troopmeetings.append(m)
        troopmeetings.sort(key=lambda x:x.datetime, reverse=True)
        return troopmeetings

    def delete(self):
        self.key.delete()
        troopmeeting_keys = memcache.get(Meeting.__getMemcacheKeyString(self.troop))
        if troopmeeting_keys is not None:
            troopmeeting_keys.remove(self.key)
            memcache.replace(Meeting.__getMemcacheKeyString(self.troop), troopmeeting_keys)

    def getdate(self):
        return self.datetime.strftime("%Y-%m-%d")
    def gettime(self):
        return self.datetime.strftime("%H:%M")
    def getname(self):
        return self.name
    def getendtime(self):
        maxEndTime = self.datetime.replace(hour=23,minute=59,second=59)
        endtime = self.datetime + datetime.timedelta(minutes=self.duration)
        if endtime > maxEndTime:
            endtime = maxEndTime # limit to the current day (to keep Stop time after Start time)
        return endtime.strftime('%H:%M')
    def getishike(self):
        return self.ishike
    
    def uppdateOldPersonKeys(self, oldToNewDict):
        was_updated = False
        for i in range(0, len(self.attendingPersons)):
            if self.attendingPersons[i] in oldToNewDict:
                self.attendingPersons[i] = oldToNewDict[self.attendingPersons[i]]
                was_updated = True

        return was_updated


class TroopPerson(ndb.Model):
    troop = ndb.KeyProperty(kind=Troop, required=True)
    person = ndb.KeyProperty(kind=Person, required=True)
    leader = ndb.BooleanProperty(default=False)
    sortname = ndb.ComputedProperty(lambda self: self.getname())

    @staticmethod
    def create_or_update(troop_key, person_key, isLeader):
        tps = TroopPerson.query(TroopPerson.troop==troop_key, TroopPerson.person==person_key).fetch(1)
        if len(tps) == 0:
            tp = TroopPerson(
                troop=troop_key,
                person=person_key,
                leader=isLeader)
        else:
            tp = tps[0]
            tp.leader=isLeader

        return tp

    def delete(self):
        self.key.delete()

    def put(self):
        super(TroopPerson, self).put()

    @staticmethod
    def getTroopPersonsForTroop(troop_key):
        return TroopPerson.query(TroopPerson.troop==troop_key).order(-TroopPerson.leader, TroopPerson.sortname).fetch()

    def getname(self):
        person = self.person.get()
        if person is None:
            return "(None)"
        return person.getname()

    def gettroopname(self):
        return self.troop.get().getname()

    def getFullTroopname(self):
        troop = self.troop.get()
        semester = troop.semester_key.get()
        return self.troop.get().getname() + ' - ' + semester.getname()


class UserPrefs(ndb.Model):
    userid = ndb.StringProperty(required=True)
    hasaccess = ndb.BooleanProperty(required=True)
    canimport = ndb.BooleanProperty(required=False)
    hasadminaccess = ndb.BooleanProperty(default=False, required=True)
    name = ndb.StringProperty(required=True)
    activeSemester = ndb.KeyProperty(kind=Semester)
    groupaccess = ndb.KeyProperty(kind=ScoutGroup, required=False, default=None)
    groupadmin = ndb.BooleanProperty(required=False, default=False)
    email = ndb.StringProperty(required=False)

    def hasAccess(self):
        return self.hasaccess

    def hasGroupAccess(self, group):
        """
        :type group: ScoutGroup
        :rtype bool
        """
        return self.hasGroupKeyAccess(group.key())

    def hasGroupKeyAccess(self, group_key):
        """
        :param group_key: key for ScoutGroup
        :type group_key: google.appengine.ext.ndb.Key
        :rtype bool
        """
        if not self.hasaccess:
            return False
        if self.hasadminaccess:
            return True
        if self.groupaccess is not None and self.groupaccess == group_key:
            return True
        # TODO Multi-group access
        return False

    def hasPersonAccess(self, person):
        """
        :type person: Person
        :rtype bool
        """
        if person is None or person.scoutgroup is None:
            return False
        return self.hasGroupKeyAccess(person.scoutgroup)

    def isAdmin(self):
        return self.hasaccess and self.hasadminaccess

    def canImport(self):
        return self.isAdmin() or self.canimport == True

    def isGroupAdmin(self):
        return self.hasadminaccess or (self.hasaccess and self.groupadmin and self.groupaccess != None)

    def getname(self):
        return self.name

    def getemail(self):
        if self.email != None and len(self.email) != 0:
            return self.email
        if '@' in self.name:
            return self.name
        return self.name + '@gmail.com'

    @staticmethod
    def current():
        cu = users.get_current_user()
        return UserPrefs.getorcreate(cu)

    def attemptAutoGroupAccess(self):
        if self.groupaccess is None:
            persons = Person.query(self.email == Person.email).fetch()
            if persons is not None and len(persons) > 0:
                person = persons[0]
                if person.isLeader():
                    self.groupaccess = person.scoutgroup
                    self.hasaccess = True
                    self.put()
                    logging.info("Auto groupaccess for %s: %s %s", self.email, person.firstname, person.lastname)

    def updateMemcache(self):
        if not memcache.add(self.userid, self):
            memcache.replace(self.userid, self)

    def put(self):
        super(UserPrefs, self).put()
        self.updateMemcache()

    @staticmethod
    def getorcreate(user):
        userprefs = memcache.get(user.user_id())
        if userprefs is not None:
            return userprefs
        else:
            userprefs = UserPrefs.get_by_id(user.user_id()) # new records have user_id as id
            if userprefs != None:
                userprefs.updateMemcache()
                return userprefs
            usersresult = UserPrefs.query(UserPrefs.userid == user.user_id()).fetch() # Fetching old records from userid
            if len(usersresult) == 0:
                userprefs = UserPrefs.create(user, users.is_current_user_admin(), users.is_current_user_admin())
                userprefs.put()
            else:
                olduser = usersresult[0]
                # old record, update to a new with user_id as id and email
                if olduser != None:
                    userprefs = UserPrefs.create(user, olduser.hasAccess(), olduser.isAdmin())
                    userprefs.activeSemester = olduser.activeSemester
                    userprefs.groupaccess = olduser.groupaccess
                    userprefs.groupadmin = olduser.groupadmin
                    userprefs.put()
                    olduser.key.delete()
            userprefs.updateMemcache()
            return userprefs

    @staticmethod
    def create(user, access=False, hasadminaccess=False):
        return UserPrefs(id=user.user_id(), userid=user.user_id(), name=user.nickname(), email=user.email(), hasaccess=access, hasadminaccess=hasadminaccess, activeSemester=Semester.getOrCreateCurrent().key)

