# -*- coding: utf-8 -*-
from data import Person, ScoutGroup, TroopPerson, UserPrefs, Semester
from flask import abort, Blueprint, redirect, render_template, request, make_response
from google.appengine.ext import ndb
import logging
import scoutnet
import urllib

persons = Blueprint('persons_page', __name__, template_folder='templates')


@persons.route('/')
@persons.route('/<sgroup_url>')
@persons.route('/<sgroup_url>/')
@persons.route('/<sgroup_url>/<person_url>')
@persons.route('/<sgroup_url>/<person_url>/')
@persons.route('/<sgroup_url>/<person_url>/<action>')
def show(sgroup_url=None, person_url=None, action=None):
    # logging.info("persons.py: sgroup_url=%s, person_url=%s, action=%s", sgroup_url, person_url, action)
    user = UserPrefs.current()
    if not user.hasAccess():
        return "denied", 403

    breadcrumbs = [{'link':'/', 'text':'Hem'}]

    section_title = u'Personer'
    breadcrumbs.append({'link': '/persons', 'text': section_title})
    baselink = '/persons/'

    sgroup_key = None  # type: ndb.Key
    scoutgroup = None  # type: ScoutGroup
    if sgroup_url is not None:
        sgroup_key = ndb.Key(urlsafe=sgroup_url)
        if not user.hasGroupKeyAccess(sgroup_key):
            return "denied", 403

        scoutgroup = sgroup_key.get()
        baselink += sgroup_url+"/"
        breadcrumbs.append({'link': baselink, 'text': scoutgroup.getname()})

    if "gbg_csv" in request.args:
        return get_gbg_csv(sgroup_url)

    if scoutgroup is None:
        return render_template(
            'index.html',
            heading=section_title,
            baselink=baselink,
            items=ScoutGroup.getgroupsforuser(user),
            breadcrumbs=breadcrumbs,
            username=user.getname())

    person_key = None  # type: ndb.Key
    person = None  # type: Person
    if person_url is not None:
        person_key = ndb.Key(urlsafe=person_url)
        person = person_key.get()
        baselink += person_url+"/"
        section_title = person.getname()
        breadcrumbs.append({'link': baselink, 'text': section_title})

    if person is None:
        section_title = 'Personer'
        return render_template(
            'persons.html',
            heading=section_title,
            baselink=baselink,
            persons=Person.query(Person.scoutgroup == sgroup_key).order(Person.firstname, Person.lastname).fetch(),
            breadcrumbs=breadcrumbs,
            username=user.getname())

    if person.scoutgroup != sgroup_key:
        return "denied", 403

    if not user.hasPersonAccess(person):
        return "denied", 403

    if action is not None:
        if action == "deleteperson" or action == "addbackperson":
            person.removed = action == "deleteperson"
            person.put() # we only mark the person as removed
            if person.removed:
                tps = TroopPerson.query(TroopPerson.person == person.key).fetch()
                for tp in tps:
                    tp.key.delete()
            return redirect(breadcrumbs[-1]['link'])
        elif action == "removefromtroop" or action == "setasleader" or action == "removeasleader":
            troop_key = ndb.Key(urlsafe=request.args["troop"])
            tps = TroopPerson.query(TroopPerson.person == person.key, TroopPerson.troop == troop_key).fetch(1)
            if len(tps) == 1:
                tp = tps[0]
                if action == "removefromtroop":
                    tp.key.delete()
                else:
                    tp.leader = (action == "setasleader")
                    tp.put()
        elif action == "addtowaitinglist":
            scoutgroup = person.scoutgroup.get()
            troop = None
            tps = TroopPerson.query(TroopPerson.person == person.key).fetch(1)
            if len(tps) == 1:
                troop = tps[0].troop.get()
            scoutgroup = person.scoutgroup.get()
            if scoutgroup.canAddToWaitinglist():
                try:
                    member_no = scoutnet.AddPersonToWaitinglist(
                            scoutgroup,
                            person.firstname,
                            person.lastname,
                            person.personnr,
                            person.email,
                            person.street,
                            person.zip_code,
                            person.zip_name,
                            person.phone,
                            person.mobile,
                            troop,
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "")
                    person.notInScoutnet = False
                    person.put()
                except scoutnet.ScoutnetException as e:
                    return render_template('error.html', error=str(e))
        else:
            logging.error('unknown action=' + action)
            abort(404)
            return ""

    # render main pages
    scoutgroup_url = scoutgroup.key.urlsafe()
    person_url = person.key.urlsafe()
    return render_template(
        'person.html',
        heading=section_title,
        baselink='/persons/' + scoutgroup_url + '/',
        # TODO: memcache
        trooppersons=TroopPerson.query(TroopPerson.person == person.key).fetch(),
        ep=person,
        scoutgroup=scoutgroup,
        breadcrumbs=breadcrumbs,
        badge_url='/badges/' + scoutgroup_url + '/person/' + person_url + '/')


def get_gbg_csv(sgroup_url=None):
    user = UserPrefs.current()
    if not user.hasAccess():
        return "denied", 403

    sgroup_key = None  # type: ndb.Key
    scoutgroup = None  # type: ScoutGroup
    if sgroup_url is not None:
        sgroup_key = ndb.Key(urlsafe=sgroup_url)
        scoutgroup = sgroup_key.get()

    if user.activeSemester is None:
        semester = Semester.getOrCreateCurrent()
    else:
        semester = user.activeSemester.get()
    
    gothenburg_zip_prefixes = [400, 401, 402, 403, 404, 405, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 430, 436, 442, 475]
    persons=Person.query(Person.scoutgroup == sgroup_key).order(Person.firstname, Person.lastname).fetch()
    rows = u''
    rows += u"Förnamn;Efternamn;Personnummer;Postnummer;Är bosatt i Göteborgs Stad (Ja/Nej);Har funktionsnedsättning (Ja/Nej)\n"
    for person in persons:
        if semester.year not in person.member_years:
            continue
        is_living_in_gothenburg = "Nej"
        zip_prefix = int(person.zip_code[:3])
        if zip_prefix in gothenburg_zip_prefixes:
            is_living_in_gothenburg = "Ja"

        rows += person.firstname + u';' + person.lastname + u';' + person.personnr + u';' + person.zip_code + u';' + is_living_in_gothenburg + u';' + 'Nej' + '\n'

    response = make_response(rows)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = ('attachment; filename=' + urllib.parse.quote(str(scoutgroup.name), safe='') +
                                                           '-' + str(semester.year) + '.csv;')
    return response

