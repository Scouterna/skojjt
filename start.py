# -*- coding: utf-8 -*-
import random
import urllib
import logging
import datetime
from operator import attrgetter
from flask import Blueprint, make_response, redirect, render_template, request

from google.appengine.ext import ndb # pylint: disable=import-error

import htmlform
import lagerbidrag
import scoutnet
import sensus
from excelreport import ExcelReport
from excelreport_sthlm import ExcelReportSthlm
from jsonreport import JsonReport
from data import Meeting, Person, ScoutGroup, Semester, Troop, TroopPerson, UserPrefs
from dakdata import DakData, Deltagare, Sammankomst


def semester_sort(sem_a, sem_b):
    "Return 1 if sem_a later than sem_b, -1 otherwise."
    a_name = sem_a.getname()
    b_name = sem_b.getname()

    a_year = a_name[:4]
    b_year = b_name[:4]

    if a_year == b_year:
        result = 1 if a_name[-2:] == "ht" else -1
    else:
        result = 1 if  a_year > b_year else -1
    return result


start = Blueprint('start_page', __name__, template_folder='templates') # pylint : disable=invalid-name


@start.route('/')
@start.route('/<sgroup_url>', methods=['POST', 'GET'])
@start.route('/<sgroup_url>/', methods=['POST', 'GET'])
@start.route('/<sgroup_url>/<troop_url>', methods=['POST', 'GET'])
@start.route('/<sgroup_url>/<troop_url>/', methods=['POST', 'GET'])
@start.route('/<sgroup_url>/<troop_url>/<key_url>', methods=['POST', 'GET'])
@start.route('/<sgroup_url>/<troop_url>/<key_url>/', methods=['POST', 'GET'])
def show(sgroup_url=None, troop_url=None, key_url=None):
    user = UserPrefs.current()
    if not user.hasAccess():
        return "denied", 403

    breadcrumbs = [{'link':'/', 'text':'Hem'}]
    section_title = u'Kårer'
    breadcrumbs.append({'link':'/start', 'text':section_title})
    baselink = '/start/'

    scoutgroup = None
    if sgroup_url is not None:
        sgroup_key = ndb.Key(urlsafe=sgroup_url)
        scoutgroup = sgroup_key.get()
        baselink += sgroup_url+"/"
        breadcrumbs.append({'link':baselink, 'text':scoutgroup.getname()})

    troop = None
    semester = user.activeSemester.get()
    if troop_url is not None and troop_url != 'lagerbidrag':
        baselink += troop_url + "/"
        troop_key = ndb.Key(urlsafe=troop_url)
        troop = troop_key.get()
        breadcrumbs.append({'link':baselink, 'text':troop.getname()})
        semester = troop.semester_key.get()

    if key_url == "settings":
        section_title = u'Inställningar'
        baselink += "settings/"
        breadcrumbs.append({'link':baselink, 'text':section_title})
        if request.method == "POST":
            troop.defaultstarttime = request.form['defaultstarttime']
            troop.defaultduration = int(request.form['defaultduration'])
            troop.rapportID = int(request.form['rapportID'])
            troop.put()

        form = htmlform.HtmlForm('troopsettings')
        form.AddField('defaultstarttime', troop.defaultstarttime, 'Avdelningens vanliga starttid')
        form.AddField('defaultduration', troop.defaultduration, u'Avdelningens vanliga mötestid i minuter', 'number')
        form.AddField('rapportID', troop.rapportID, u'Unik rapport ID för kommunens närvarorapport', 'number')
        return render_template('form.html',
                               heading=section_title,
                               baselink=baselink,
                               form=str(form),
                               breadcrumbs=breadcrumbs)
    if key_url == "delete":
        if troop is None:
            return "", 404
        if request.form and "confirm" in request.form:
            if not user.isGroupAdmin():
                return "", 403
            troop.delete()
            troop = None
            del breadcrumbs[-1]
            baselink = breadcrumbs[-1]["link"]
        else:
            form = htmlform.HtmlForm('deletetroop', submittext="Radera", buttonType="btn-danger",
                                     descriptionText=u"Vill du verkligen radera avdelningen och all registrerad närvaro?\n"
                                                     u"Det går här inte att ångra.")
            form.AddField('confirm', '', '', 'hidden')
            return render_template('form.html',
                                   heading=section_title,
                                   baselink=baselink,
                                   form=str(form),
                                   breadcrumbs=breadcrumbs)

    if key_url == "newperson":
        section_title = "Ny person"
        baselink += key_url + "/"
        breadcrumbs.append({'link':baselink, 'text':section_title})
        if request.method == "GET":
            return render_template('person.html',
                                   heading=section_title,
                                   baselink=baselink,
                                   breadcrumbs=breadcrumbs,
                                   troop_persons=[],
                                   scoutgroup=scoutgroup)
        elif request.method == "POST":
            pnr = request.form['personnummer'].replace('-', '')
            person = Person.createlocal(
                request.form['firstname'],
                request.form['lastname'],
                pnr,
                request.form['mobile'],
                request.form['phone'],
                request.form['email'])
            person.street = request.form["street"]
            person.zip_code = request.form["zip_code"]
            person.zip_name = request.form["zip_name"]
            if "patrol" in request.form:
                person.setpatrol(request.form["patrol"])
            person.scoutgroup = sgroup_key
            logging.info("created local person %s", person.getname())
            person.put()
            troop_person = TroopPerson.create(troop_key, person.key, False)
            troop_person.commit()
            if scoutgroup.canAddToWaitinglist():
                try:
                    if scoutnet.AddPersonToWaitinglist(scoutgroup,
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
                                                       request.form['anhorig1_name'],
                                                       request.form['anhorig1_email'],
                                                       request.form['anhorig1_mobile'],
                                                       request.form['anhorig1_phone'],
                                                       request.form['anhorig2_name'],
                                                       request.form['anhorig2_email'],
                                                       request.form['anhorig2_mobile'],
                                                       request.form['anhorig2_phone']):
                        person.notInScoutnet = False
                        person.put()
                except scoutnet.ScoutnetException as exp:
                    return render_template('error.html', error=str(exp))
            return redirect(breadcrumbs[-2]['link'])

    if request.method == "GET" and request.args and "action" in request.args:
        action = request.args["action"]
        logging.debug("action %s", action)
        if action == "lookupperson":
            if scoutgroup is None:
                raise ValueError('Missing group')
            name = request.args['name'].lower()
            if len(name) < 2:
                return "[]"
            logging.debug("name=%s", name)
            json_str = '['
            person_counter = 0
            for person in Person().query(Person.scoutgroup == sgroup_key).order(Person.removed, Person.firstname, Person.lastname):
                if person.getname().lower().find(name) != -1:
                    if person_counter != 0:
                        json_str += ', '
                    json_str += '{"name": "'+person.getnameWithStatus()+'", "url": "' + person.key.urlsafe() + '"}'
                    person_counter += 1
                    if person_counter == 8:
                        break
            json_str += ']'
            return json_str
        elif action == "addperson":
            if troop is None or key_url is None:
                raise ValueError('Missing troop or person')
            person_key = ndb.Key(urlsafe=key_url)
            person = person_key.get()
            logging.info("adding person=%s to troop=%d", person.getname(), troop.getname())
            troop_person = TroopPerson.create(troop_key, person_key, person.isLeader())
            troop_person.commit()
            return redirect(breadcrumbs[-1]['link'])
        elif action == "setsemester":
            if user is None or "semester" not in request.args:
                raise ValueError('Missing user or semester arg')
            semester_url = request.args["semester"]
            user.activeSemester = ndb.Key(urlsafe=semester_url)
            user.put()
        elif action == "removefromtroop" or action == "setasleader" or action == "removeasleader":
            if troop is None or key_url is None:
                raise ValueError('Missing troop or person')
            person_key = ndb.Key(urlsafe=key_url)
            tps = TroopPerson.query(TroopPerson.person == person_key, TroopPerson.troop == troop_key).fetch(1)
            if len(tps) == 1:
                troop_person = tps[0]
                if action == "removefromtroop":
                    troop_person.delete()
                else:
                    troop_person.leader = (action == "setasleader")
                    troop_person.put()
            return "ok"
        else:
            logging.error('unknown action=%s', action)
            return "", 404

    if request.method == "POST" and request.form and "action" in request.form:
        action = request.form["action"]
        if action == "saveattendance":
            if troop is None or scoutgroup is None or key_url is None:
                raise ValueError('Missing troop or group')

            meeting = ndb.Key(urlsafe=key_url).get()
            meeting.attendingPersons[:] = [] # clear the list
            for person_url in request.form["persons"].split(","):
                #logging.debug("person_url=%s", person_url)
                if len(person_url) > 0:
                    person_key = ndb.Key(urlsafe=person_url)
                    meeting.attendingPersons.append(person_key)
            meeting.put()
            return "ok"
        elif action == "addmeeting" or action == "updatemeeting":
            mname = request.form['name']
            mdate = request.form['date']
            mishike = bool(request.form.get('ishike'))
            mtime = request.form['starttime'].replace('.', ':')
            dtstring = mdate + "T" + mtime
            mduration = request.form['duration']
            date_str = datetime.datetime.strptime(dtstring, "%Y-%m-%dT%H:%M")
            if action == "addmeeting":
                meeting = Meeting.getOrCreate(troop_key,
                                              mname,
                                              date_str,
                                              int(mduration),
                                              mishike)
            else:
                meeting = ndb.Key(urlsafe=key_url).get()

            meeting.name = mname
            meeting.datetime = date_str
            meeting.duration = int(mduration)
            meeting.ishike = mishike
            meeting.commit()
            return redirect(breadcrumbs[-1]['link'])
        elif action == "deletemeeting":
            meeting = ndb.Key(urlsafe=key_url).get()
            logging.debug("deleting meeting=%s", meeting.getname())
            meeting.delete()
            return redirect(breadcrumbs[-1]['link'])
        elif action == "addhike":
            mname = request.form['name']
            mdate = request.form['date']
            mdays = int(request.form['days'])
            date_str = datetime.datetime.strptime(mdate, "%Y-%m-%d")
            for i in range(mdays):
                day_time = date_str + datetime.timedelta(days=i)
                meeting = Meeting.getOrCreate(troop_key,
                                              mname,
                                              day_time,
                                              duration=1440,  # 24h (needs some value)
                                              ishike=True)
                meeting.commit()
            return redirect(breadcrumbs[-1]['link'])

        elif action == "savepatrol":
            patrolperson = ndb.Key(urlsafe=request.form['person']).get()
            patrolperson.setpatrol(request.form['patrolName'])
            patrolperson.put()
            return "ok"
        elif action == "newtroop":
            troopname = request.form['troopname']
            troop_id = hash(troopname)
            conflict = Troop.get_by_id(Troop.getid(troop_id, scoutgroup.key, user.activeSemester), use_memcache=True)
            if conflict is not None:
                return "Avdelningen finns redan", 404
            troop = Troop.create(troopname, troop_id, scoutgroup.key, user.activeSemester)
            troop.put()
            troop_key = troop.key
            logging.info("created local troop %s", troopname)
            action = ""
            return redirect(breadcrumbs[-1]['link'])
        else:
            logging.error('unknown action=%s', action)
            return "", 404

    # render main pages
    if scoutgroup is None:
        return render_template('index.html',
                               heading=section_title,
                               baselink=baselink,
                               items=ScoutGroup.getgroupsforuser(user),
                               breadcrumbs=breadcrumbs)
    elif troop_url == "lagerbidrag":
        return lagerbidrag.render_lagerbidrag(request, scoutgroup, "group", user=user, sgroup_key=sgroup_key)
    elif troop is None:
        section_title = 'Avdelningar'
        return render_template('troops.html',
                               heading=section_title,
                               baselink=baselink,
                               scoutgroupbadgeslink='/scoutgroupbadges/' + sgroup_url + '/',
                               scoutgroupinfolink='/scoutgroupinfo/' + sgroup_url + '/',
                               groupsummarylink='/groupsummary/' + sgroup_url + '/',
                               user=user,
                               semester=semester,
                               semesters=sorted(Semester.query(), semester_sort),
                               troops=sorted(Troop.getTroopsForUser(sgroup_key, user), key=attrgetter('name')),
                               lagerplats=scoutgroup.default_lagerplats,
                               breadcrumbs=breadcrumbs)
    elif key_url is not None and key_url not in ("dak", "sensus", "lagerbidrag", "excel", "excel_sthlm", "json"):
        meeting = ndb.Key(urlsafe=key_url).get()
        section_title = meeting.getname()
        baselink += key_url + "/"
        breadcrumbs.append({'link':baselink, 'text':section_title})

        return render_template('meeting.html',
                               heading=section_title,
                               baselink=baselink,
                               existingmeeting=meeting,
                               breadcrumbs=breadcrumbs,
                               semester=troop.semester_key.get(),
                               troop=troop)
    else:
        meeting_count = 0
        sum_male_attendance_count = 0
        sum_female_attendance_count = 0
        sum_male_leader_attendance_count = 0
        sum_female_leader_attendance_count = 0
        no_leader_meeting_count = 0
        too_small_group_meeting_count = 0
        age_problem_count = 0
        age_problem_desc = []

        section_title = troop.getname()
        troop_persons = TroopPerson.getTroopPersonsForTroop(troop_key)
        meetings = Meeting.gettroopmeetings(troop_key)

        attendances = [] # [meeting][person]
        persons = []
        persons_dict = {}
        for troop_person in troop_persons:
            person_key = troop_person.person
            person = troop_person.person.get()
            persons.append(person)
            persons_dict[person_key] = person

        year = semester.year
        for meeting in meetings:
            male_attendance_count = 0
            female_attendence_count = 0
            male_leader_attendance_count = 0
            female_leader_attendence_count = 0
            meeting_attendance = []
            for troop_person in troop_persons:
                is_attending = troop_person.person in meeting.attendingPersons
                meeting_attendance.append(is_attending)
                if is_attending:
                    person = persons_dict[troop_person.person]
                    age = person.getyearsoldthisyear(year)
                    if troop_person.leader:
                        if 13 <= age <= 100:
                            if female_leader_attendence_count + male_leader_attendance_count < 2:
                                if person.isFemale():
                                    female_leader_attendence_count += 1
                                else:
                                    male_leader_attendance_count += 1
                        else:
                            age_problem_count += 1
                            age_problem_desc.append(person.getname() + ": " + str(age))
                    else:
                        if 7 <= age <= 25:
                            if person.isFemale():
                                female_attendence_count += 1
                            else:
                                male_attendance_count += 1
                        else:
                            age_problem_count += 1
                            age_problem_desc.append(person.getname() + ": " + str(age))

            attendances.append(meeting_attendance)
            total_attendance = male_attendance_count+female_attendence_count
            # max 40 people
            if total_attendance > 40:
                surplus_people = total_attendance - 40
                removed_men = min(male_attendance_count, surplus_people)
                male_attendance_count -= removed_men
                surplus_people -= removed_men
                female_attendence_count -= surplus_people

            max_leaders = 1 if total_attendance <= 10 else 2
            total_leaders = female_leader_attendence_count + male_leader_attendance_count
            if total_attendance < 3:
                too_small_group_meeting_count += 1
            else:
                if total_leaders == 0:
                    no_leader_meeting_count += 1
                else:
                    meeting_count += 1
                    sum_female_attendance_count += female_attendence_count
                    sum_male_attendance_count += male_attendance_count
                    if total_leaders > max_leaders:
                        if male_leader_attendance_count > max_leaders and female_leader_attendence_count == 0:
                            male_leader_attendance_count = max_leaders
                        elif male_leader_attendance_count == 0 and female_leader_attendence_count > max_leaders:
                            female_leader_attendence_count = max_leaders
                        else:
                            female_leader_attendence_count = max_leaders / 2
                            max_leaders -= female_leader_attendence_count
                            male_leader_attendance_count = max_leaders

                    sum_female_leader_attendance_count += female_leader_attendence_count
                    sum_male_leader_attendance_count += male_leader_attendance_count

        if key_url in ("dak", "excel", "excel_sthlm", "json"):
            dak = DakData()
            dak.foerenings_namn = scoutgroup.getname()
            dak.forenings_id = scoutgroup.foreningsID
            dak.organisationsnummer = scoutgroup.organisationsnummer
            dak.kommun_id = scoutgroup.kommunID
            dak.kort.namn_paa_kort = troop.getname()
            # hack generate an "unique" id, if there is none
            if troop.rapportID is None or troop.rapportID == 0:
                troop.rapportID = random.randint(1000, 1000000)
                troop.put()

            dak.kort.naervarokort_nummer = str(troop.rapportID)

            for troop_person in troop_persons:
                p = persons_dict[troop_person.person]
                if troop_person.leader:
                    dak.kort.ledare.append(Deltagare(p.getReportID(), p.firstname, p.lastname, p.getpersonnr(),
                                                     True, p.email, p.mobile, p.zip_code))
                else:
                    dak.kort.deltagare.append(Deltagare(p.getReportID(), p.firstname, p.lastname, p.getpersonnr(),
                                                        False, p.email, p.mobile, p.zip_code))

            for m in meetings:
                if (not scoutgroup.attendance_incl_hike) and m.ishike:
                    continue
                sammankomst = Sammankomst(str(m.key.id()[:50]), m.datetime, m.duration, m.getname())
                for troop_person in troop_persons:
                    is_attending = troop_person.person in m.attendingPersons
                    if is_attending:
                        p = persons_dict[troop_person.person]
                        if troop_person.leader:
                            sammankomst.ledare.append(Deltagare(p.getReportID(), p.firstname, p.lastname, p.getpersonnr(),
                                                                True, p.email, p.mobile, p.zip_code))
                        else:
                            sammankomst.deltagare.append(Deltagare(p.getReportID(), p.firstname, p.lastname, p.getpersonnr(),
                                                                   False, p.email, p.mobile, p.zip_code))

                dak.kort.sammankomster.append(sammankomst)
            if key_url in ("excel", "excel_sthlm"):
                if key_url == "excel":
                    excel_report = ExcelReport(dak, semester)
                else:
                    dak.kort.lokal = scoutgroup.default_lagerplats
                    excel_report = ExcelReportSthlm(dak, semester)
                resultbytes = excel_report.getFilledInExcelSpreadsheet()
                response = make_response(resultbytes)
                response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                response.headers['Content-Disposition'] = ('attachment; filename=' + urllib.quote(str(dak.kort.namn_paa_kort), safe='') +
                                                           '-' + semester.getname() + '.xlsx;')
                return response
            elif key_url == "json":
                json_report = JsonReport(dak, semester)
                resultbytes = json_report.get_report_string()
                response = make_response(resultbytes)
                response.headers['Content-Type'] = json_report.get_mime_type()
                response.headers['Content-Disposition'] = 'attachment; filename=' + urllib.quote(json_report.get_filename(), safe='') + ';'
                return response
            else:
                result = render_template('dak.xml', dak=dak)
                response = make_response(result)
                response.headers['Content-Type'] = 'application/xml'
                response.headers['Content-Disposition'] = ('attachment; filename=' + urllib.quote(str(dak.kort.namn_paa_kort), safe='') +
                                                           '-' + semester.getname() + '.xml;')
                return response
        elif key_url == "sensus":
            leaders = []
            for troop_person in troop_persons:
                if troop_person.leader:
                    leaders.append(troop_person.getname())

            patrols = []
            for p in persons:
                if p.getpatrol() not in patrols:
                    patrols.append(p.getpatrol())

            sensusdata = sensus.SensusData()
            sensusdata.foereningsNamn = scoutgroup.getname()
            sensusdata.foreningsID = scoutgroup.foreningsID
            sensusdata.organisationsnummer = scoutgroup.organisationsnummer
            sensusdata.kommunID = scoutgroup.kommunID
            sensusdata.verksamhetsAar = semester.getname()

            for patrol in patrols:
                sensuslista = sensus.SensusLista()
                sensuslista.NamnPaaKort = troop.getname() + "/" + patrol

                for troop_person in troop_persons:
                    p = persons_dict[troop_person.person]
                    if p.getpatrol() != patrol:
                        continue
                    if troop_person.leader:
                        sensuslista.ledare.append(sensus.Deltagare(p.getReportID(), p.firstname, p.lastname, p.getpersonnr(),
                                                                   True, p.email, p.mobile))
                    else:
                        sensuslista.deltagare.append(sensus.Deltagare(p.getReportID(), p.firstname, p.lastname, p.getpersonnr(), False))

                for m in meetings:
                    sammankomst = sensus.Sammankomst(str(m.key.id()[:50]), m.datetime, m.duration, m.getname())
                    for troop_person in troop_persons:
                        p = persons_dict[troop_person.person]
                        if p.getpatrol() != patrol:
                            continue
                        is_attending = troop_person.person in m.attendingPersons

                        if troop_person.leader:
                            sammankomst.ledare.append(sensus.Deltagare(p.getReportID(), p.firstname, p.lastname, p.getpersonnr(),
                                                                       True, p.email, p.mobile, is_attending))
                        else:
                            sammankomst.deltagare.append(sensus.Deltagare(p.getReportID(), p.firstname, p.lastname, p.getpersonnr(),
                                                                          False, p.email, p.mobile, is_attending))

                    sensuslista.Sammankomster.append(sammankomst)

                sensusdata.listor.append(sensuslista)

            result = render_template('sensusnarvaro.html', sensusdata=sensusdata)
            response = make_response(result)
            return response
        elif key_url == "lagerbidrag":
            return lagerbidrag.render_lagerbidrag(request, scoutgroup, "troop", trooppersons=troop_persons, troop_key=troop_key)
        else:
            allowance = []
            allowance.append({'name':'Antal möten:', 'value':meeting_count})
            allowance.append({'name':'Deltagartillfällen', 'value':''})
            allowance.append({'name':'Kvinnor:', 'value':sum_female_attendance_count})
            allowance.append({'name':'Män:', 'value':sum_male_attendance_count})
            allowance.append({'name':'Ledare Kvinnor:', 'value':sum_female_leader_attendance_count})
            allowance.append({'name':'Ledare Män:', 'value':sum_male_leader_attendance_count})
            if no_leader_meeting_count > 0:
                allowance.append({'name':'Antal möten utan ledare', 'value':no_leader_meeting_count})
            if too_small_group_meeting_count > 0:
                allowance.append({'name':'Antal möten med för få deltagare', 'value':too_small_group_meeting_count})
            if age_problem_count > 0:
                allowance.append({'name':'Ålder utanför intervall:', 'value':age_problem_count})
            if age_problem_desc != "":
                age_problem_desc_str = ','.join(age_problem_desc[:3])
                if len(age_problem_desc) > 3:
                    age_problem_desc_str += "..."
                allowance.append({'name':'', 'value':age_problem_desc_str})

            return render_template('troop.html',
                                   heading=section_title,
                                   semestername=semester.getname(),
                                   baselink='/persons/' + scoutgroup.key.urlsafe() + '/',
                                   persons=persons,
                                   trooppersons=troop_persons,
                                   meetings=meetings,
                                   attendances=attendances,
                                   breadcrumbs=breadcrumbs,
                                   allowance=allowance,
                                   troop=troop,
                                   user=user,
                                   semester=semester,
                                   lagerplats=scoutgroup.default_lagerplats
                                  )
