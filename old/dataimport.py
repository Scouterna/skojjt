# -*- coding: utf-8 -*-
from data import Meeting, Person, ScoutGroup, Semester, TaskProgress, Troop, TroopPerson, UserPrefs
from datetime import datetime
from google.appengine.ext import ndb
from google.appengine.ext.ndb import metadata
import logging
import scoutnet
import urllib2

def RunScoutnetImport(groupid, api_key, user, semester, result):
    """
    :type groupid: str
    :type api_key: str
    :type user: data.UserPrefs
    :type semester: data.Semester
    :type result: data.TaskProgress
    :rtype: bool
    """
    result.info('Importerar för termin %s' % semester.getname())
    if groupid is None or groupid == "" or api_key is None or api_key == "":
        result.error(u"Du måste ange både kårid och api nyckel")
        return False

    try:
        data = scoutnet.GetScoutnetMembersAPIJsonData(groupid, api_key)
    except urllib2.HTTPError as e:
        logging.error('Scoutnet http error=%s' % str(e))
        result.error(u"Kunde inte läsa medlemmar från scoutnet, fel:%s" % (str(e)))
        if e.code == 401:
            result.error(u"Kontrollera: api nyckel och kårid. Se till att du har rollen 'Medlemsregistrerare', och möjligen 'Webbansvarig' i scoutnet")
        return False

    importer = ScoutnetImporter(result)
    success = importer.DoImport(data, semester)
    if not success:
        return False

    if user.activeSemester != semester.key:
        user.activeSemester = semester.key
        result.append('Sätter %s till vald termin.' % semester.getname())
        user.put()

    # Don't Connect the group if the user is an admin
    if user.hasadminaccess:
        return True

    # Don't Connect the group if the user already has an connection
    if user.groupaccess is not None:
        return True

    user.groupaccess = importer.importedScoutGroup_key
    user.hasaccess = True
    user.put()
    if user.groupadmin:
        result.append(u"Du är kåradmin och kan dela ut tillgång till din kår för andra användare")
    return True


def GetBackupXML():
    thisdate = datetime.now()
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


class ScoutnetImporter:
    commit = True
    rapportID = 1
    importedScoutGroup_key = None
    result = None

    def __init__(self, result):
        """
        :type result: data.TaskProgress
        """
        self.result = result
        self.commit = True
        self.rapportID = 1

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
            self.result.append("Ny avdelning %s, ID=%s" % (name, troop_id))
            troop = Troop.create(name, troop_id, group_key, semester_key)
            troop.rapportID = self.rapportID # TODO: should check the highest number in the sgroup, will work for full imports
            troop.scoutnetID = int(troop_id)
            self.rapportID += 1
            if self.commit:
                troop.put()

        if troop.scoutnetID != int(troop_id):
            troop.scoutnetID = int(troop_id)
            self.result.append("Nytt ID=%d för avdelning %s" % (troop.scoutnetID, name))
            troop.put()

        return troop

    def GetOrCreateGroup(self, name, scoutnetID):
        if len(name) == 0:
            return None
        group = ScoutGroup.get_by_id(ScoutGroup.getid(name), use_memcache=True)
        if group == None:
            self.result.append(u"Ny kår %s, id=%s" % (name, str(scoutnetID)))
            group = ScoutGroup.create(name, scoutnetID)
            group.scoutnetID = scoutnetID
            if self.commit:
                group.put()

        if group.scoutnetID != scoutnetID:
            group.scoutnetID = scoutnetID
            if self.commit:
                group.put()

        self.importedScoutGroup_key = group.key
        return group

    def DoImport(self, data, semester):
        """
        :param data: from scoutnet
        :type data: str
        :type semester: data.Semester
        :rtype bool
        """
        if not self.commit:
            self.result.append("*** sparar inte, test mode ***")

        if data == None or len(data) < 80:
            self.result.error(u"ingen data från scoutnet")
            return False

        list = scoutnet.GetScoutnetDataListJson(data)
        self.result.append("antal personer=%d" % len(list))
        if len(list) < 1:
            self.result.error(u"för få rader: %d st" % len(list))
            return False

        personsToSave = []
        troopPersonsToSave = []
        activePersons = set() # person.ids that was seen in this import

        for p in list:
            id = int(p["id"])
            person = Person.get_by_id(id, use_memcache=True) # need to be an integer due to backwards compatibility with imported data
            personnr = p["personnr"].replace('-', '')
            if len(personnr) < 12:
                self.result.warning(u"%s %s har inte korrekt personnummer: '%s', hoppar över personen" % (p["firstname"], p["lastname"], personnr))
                continue
            if person == None:
                id = personnr
                person = Person.get_by_id(id, use_memcache=True) # attempt to find using personnr, created as a local person

            if person != None:
                person.firstname = p["firstname"]
                person.lastname = p["lastname"]
                person.setpersonnr(personnr)
                if person.notInScoutnet != None:
                    person.notInScoutnet = False
            else:
                person = Person.create(
                    id,
                    p["firstname"],
                    p["lastname"],
                    p["personnr"])
                self.result.append("Ny person:%s %s %s" % (id, p["firstname"], p["lastname"]))

            activePersons.add(id)

            person.removed = False
            person.patrool = p["patrool"]
            person.email = p["email"]
            person.member_no = p["member_no"]
            person.phone = p["phone"]
            person.mobile = p["mobile"]
            person.alt_email = p["contact_alt_email"]
            person.mum_name = p["mum_name"]
            person.mum_email = p["mum_email"]
            person.mum_mobile = p["mum_mobile"]
            person.dad_name = p["dad_name"]
            person.dad_email = p["dad_email"]
            person.dad_mobile = p["dad_mobile"]
            person.street = p["street"]
            person.zip_code = p["zip_code"]
            person.zip_name = p["zip_name"]
            person.troop_roles = p["troop_roles"]
            person.group_roles = p["group_roles"]
            if semester.year not in person.member_years:
                person.member_years.append(semester.year)
                person._dirty = True

            scoutgroup = self.GetOrCreateGroup(p["group"], p["group_id"])
            person.scoutgroup = scoutgroup.key
            if len(p["troop"]) == 0:
                self.result.warning(u"Ingen avdelning vald för %s %s %s" % (id, p["firstname"], p["lastname"]))

            troop = self.GetOrCreateTroop(p["troop"], p["troop_id"], scoutgroup.key, semester.key)
            troop_key = troop.key if troop != None else None
            person.troop = troop_key

            if person._dirty:
                self.result.append(u"Sparar ändringar:%s %s %s" % (id, p["firstname"], p["lastname"]))
                if self.commit:
                    personsToSave.append(person)

            if troop_key != None:
                if self.commit:
                    tp = TroopPerson.get_by_id(TroopPerson.getid(person.troop, person.key), use_memcache=True)
                    if tp == None:
                        tp = TroopPerson.create(troop_key, person.key, False)
                        troopPersonsToSave.append(tp)
                        self.result.append(u"Ny avdelning '%s' för:%s %s" % (p["troop"], p["firstname"], p["lastname"]))

        # check if old persons are still members, mark persons not imported in the pass as removed
        if len(personsToSave) > 0: # protect agains a failed import, with no persons maring everyone as removed
            previousPersons = Person.query(Person.scoutgroup == scoutgroup.key, Person.removed != True)
            for previousPersonKey in previousPersons.iter(keys_only=True):
                if previousPersonKey.id() not in activePersons:
                    personToMarkAsRemoved = previousPersonKey.get()
                    personToMarkAsRemoved.removed = True
                    self.result.append(u"%s finns inte i scoutnet, markeras som borttagen" % (personToMarkAsRemoved.getname()))
                    if personToMarkAsRemoved in personsToSave:
                        raise Exception('A removed person cannot be in that list')
                    personsToSave.append(personToMarkAsRemoved)

        if self.commit:
            ndb.put_multi(personsToSave)
            ndb.put_multi(troopPersonsToSave)

        return True


def DeleteAllData():
    entries = []
    entries.extend(Person.query().fetch(keys_only=True))
    entries.extend(Troop.query().fetch(keys_only=True))
    entries.extend(ScoutGroup.query().fetch(keys_only=True))
    entries.extend(Meeting.query().fetch(keys_only=True))
    entries.extend(TroopPerson.query().fetch(keys_only=True))
    entries.extend(Semester.query().fetch(keys_only=True))
    entries.extend(TaskProgress.query().fetch(keys_only=True))
    entries.extend(UserPrefs.query().fetch(keys_only=True))
    ndb.delete_multi(entries)
    ndb.get_context().clear_cache() # clear memcache


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
