# -*- coding: utf-8 -*-
# [WIP]
from data import Meeting, Person, ScoutGroup, Semester, Troop, TroopPerson, UserPrefs
from flask import Blueprint, render_template, request, make_response, redirect
from google.appengine.ext import deferred
from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext.ndb import metadata
from datetime import datetime
import bisect
import htmlform
import logging
import scoutnet
import time
import traceback
import json

stats = Blueprint('stats', __name__, template_folder='templates')


@stats.route('/')
def stats_():
    user = UserPrefs.current()
    if not user.isAdmin():
        return "denied", 403

    breadcrumbs = [{'link':'/', 'text':'Hem'},
                   {'link':'/admin', 'text':'Stats'}]
    return render_template('stats.html', heading="Stats", breadcrumbs=breadcrumbs, username=user.getname())


# return all persons per scoutgroup, let the client combine the numbers or filter out.
# male/female, leaders

# -"-
# and all antendee counts (per day?)

@stats.route('/meetings/')
def meetings():
    s = json.dumps({'2016-ht': {"m":100, "f":100}, '2017-vt': {"m":110, "f":120}, '2017-ht': {"m":120, "f":125}, '2018-vt': {"m":125, "f":135}})
    response = make_response(s)
    response.headers['Content-Type'] = 'application/json'
    return response


@stats.route('/meeting_date_count/')
def meeting_date_count():
    meeting_date_counter = memcache.get("meeting_date_count")
    if meeting_date_counter == None:
        return update_meeting_date_count()

    s = json.dumps(meeting_date_counter)
    response = make_response(s)
    response.headers['Content-Type'] = 'application/json'
    return response


@stats.route('/update_meeting_date_count/')
def update_meeting_date_count():
    update_meeting_date_count_is_running = memcache.get("update_meeting_date_count_is_running")
    if update_meeting_date_count_is_running:
        return "Already started update, in progress"

    memcache.add("update_meeting_date_count_is_running", True)
    memcache.delete("meeting_date_counter_dict")
    memcache.add("meeting_date_counter_dict", {})
    deferred.defer(meeting_date_count_deferred, None)
    return "Running update"


max_time_seconds = 7*60
def meeting_date_count_deferred(start_cursor):
    start_time = time.time()
    # collect meetings per scoutgroup and day, count number of trooppersons and meeting attendees 
    meeting_date_counter_dict = memcache.get("meeting_date_counter_dict") # dict: datetime => number of attendee that day
    # {"Scoutgroup X": {meetings:[{"date": 2020-01-01, pers:"23"}, {"date": 2020-01-02, pers:"33"}]}, "Scoutgroup Y": {meetings:[{"date": 2020-01-01, pers:"23"}, {"date": 2020-01-02, pers:"33"}]}}
    there_is_more = true
    while there_is_more:
        sgs, start_cursor, there_is_more = ScoutGroup.query().fetch_page(page_size=1, start_cursor=start_cursor):
        for sg in sgs:
            logging.info("Updating:%s" % (semester.getname()))
            for semester in Semester.query().fetch():
                for troop_key in Troop.query(Troop.scoutgroup==sg.key, Troop.semester_key==semester.key).fetch(keys_only=True):
                    #troopPersonKeys = TroopPerson.query(TroopPerson.troop == troop.key).fetch(keys_only=True)
                    #numTroopPersons = len(TroopPerson)
                    for meeting in Meeting.query(Meeting.troop == troop_key).fetch():
                        attending_count = len(meeting.attendingPersons)
                        meeting_day = meeting.datetime.strftime('%Y-%m-%d')

                        if meeting_date_counter_dict.has_key(meeting_day):
                            attending_count += meeting_date_counter_dict[meeting_day]
                        
                        meeting_date_counter_dict[meeting_day] = attending_count
            
            if there_is_more:
                memcache.delete("meeting_date_counter_dict")
                memcache.add("meeting_date_counter_dict", meeting_date_counter_dict)
                deferred.defer(meeting_date_count_deferred, start_cursor)


    meeting_date_counter = [{"date" : day_key, "delt": meeting_date_counter_dict[day_key]} for day_key in sorted(meeting_date_counter_dict)]
    
    logging.info("meeting_date_count update done")
    memcache.delete("meeting_date_count")
    memcache.add("meeting_date_count", meeting_date_counter)
    memcache.delete("update_meeting_date_count_is_running")

