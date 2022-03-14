# -*- coding: utf-8 -*-
from data import Meeting, Person, Semester, UserPrefs, ScoutGroup, dbcontext
from flask import Blueprint, render_template
import datetime

groupsummary = Blueprint('groupsummary_page', __name__, template_folder='templates')

@groupsummary.route('/<sgroup_url>')
@groupsummary.route('/<sgroup_url>/')
@dbcontext
def scoutgroupsummary(sgroup_url):
    user = UserPrefs.current()
    if not user.canImport():
        return "denied", 403
    if sgroup_url is None:
        return "missing group", 404

    if user.activeSemester is None:
        semester = Semester.getOrCreateCurrent()
    else:
        semester = user.activeSemester.get()

    scoutgroup = ScoutGroup.getFromUrlSafe(sgroup_url)
    breadcrumbs = [{'link':'/', 'text':'Hem'}]
    baselink = "/groupsummary/" + sgroup_url
    section_title = "Föreningsredovisning - " + scoutgroup.getname()
    breadcrumbs.append({'link':baselink, 'text':section_title})
    class Item():
        age = 0
        women = 0
        womenMeetings = 0
        men = 0
        menMeetings = 0
        def __init__(self, age, women=0, womenMeetings=0, men=0, menMeetings=0):
            self.age = age
            self.women = women
            self.womenMeetings = womenMeetings
            self.men = men
            self.menMeetings = menMeetings

    year = semester.year
    women = 0
    womenMeetings = 0
    men = 0
    menMeetings = 0
    startage = 7
    endage = 25
    ages = [Item('0 - 6')]
    ages.extend([Item(i) for i in range(startage, endage+1)])
    ages.append(Item('26 - 64'))
    ages.append(Item('65 -'))
    leaders = [Item(u't.o.m. 25 år'), Item(u'över 25 år')]
    boardmebers = [Item('')]

    from_date_time = datetime.datetime.strptime(str(semester.year) + "-01-01 00:00", "%Y-%m-%d %H:%M")
    to_date_time = datetime.datetime.strptime(str(semester.year) + "-12-31 00:00", "%Y-%m-%d %H:%M")

    emails = []
    for person in Person.query(Person.scoutgroup==scoutgroup.key).fetch():
        if person.member_years is None or semester.year not in person.member_years:
            continue
        if person.email is not None and len(person.email) != 0 and person.email not in emails:
            emails.append(person.email)

        age = person.getyearsoldthisyear(year)

        if scoutgroup.attendance_incl_hike:
            number_of_meetings = Meeting.query(Meeting.attendingPersons==person.key,
                                              Meeting.datetime >= from_date_time,
                                              Meeting.datetime <= to_date_time).count()
        else:
           meetings = Meeting.query(Meeting.attendingPersons==person.key,
                                    Meeting.datetime >= from_date_time,
                                    Meeting.datetime <= to_date_time)
           nr_all = meetings.count()
           nr_hike_meetings = meetings.filter(Meeting.ishike == True).count()
           number_of_meetings = nr_all - nr_hike_meetings

        index = 0
        if 7 <= age <= 25:
            index = age-startage + 1
        elif age < 7:
            index = 0
        elif 26 <= age <= 64:
            index = endage - startage + 2
        else:
            index = endage - startage + 3

        if person.isFemale():
            women += 1
            ages[index].women += 1
        else:
            men += 1
            ages[index].men += 1

        if number_of_meetings >= scoutgroup.attendance_min_year:
            if person.isFemale():
                womenMeetings += 1
                ages[index].womenMeetings += 1
            else:
                menMeetings += 1
                ages[index].menMeetings += 1

        if person.isBoardMember():
            if person.isFemale():
                boardmebers[0].women += 1
            else:
                boardmebers[0].men += 1
        if person.isLeader():
            index = 0 if age <= 25 else 1
            if person.isFemale():
                leaders[index].women += 1
            else:
                leaders[index].men += 1

    ages.append(Item("Totalt", women, womenMeetings, men, menMeetings))
    return render_template('groupsummary.html', ages=ages, boardmebers=boardmebers, leaders=leaders,
                           breadcrumbs=breadcrumbs, emails=emails, year=semester.year,
                           min_nr_meetings=str(scoutgroup.attendance_min_year),
                           incl_hikes=scoutgroup.attendance_incl_hike)
