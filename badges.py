# -*- coding: utf-8 -*-
"""Märkesdefinitioner inkl delmoment med kort och lång beskrivning."""

import urllib
import logging
import datetime
from operator import attrgetter
from collections import namedtuple
from flask import Blueprint, make_response, redirect, render_template, request


from google.appengine.ext import ndb # pylint: disable=import-error

import htmlform
from data import Meeting, Person, ScoutGroup, Semester, Troop, TroopPerson, UserPrefs
from dakdata import DakData, Deltagare, Sammankomst
from start import semester_sort
from data_badge import Badge, BadgePart


Krav = namedtuple("Krav", "index short long")

badges = Blueprint('badges_page', __name__, template_folder='templates')  # pylint : disable=invalid-name

@badges.route('/')
@badges.route('/<sgroup_url>')
@badges.route('/<sgroup_url>/')
@badges.route('/<sgroup_url>/<badge_url>', methods=['POST', 'GET'])
@badges.route('/<sgroup_url>/<badge_url>/', methods=['POST', 'GET'])
@badges.route('/<sgroup_url>/<badge_url>/<action>', methods=['POST', 'GET'])
def show(sgroup_url=None, badge_url=None, action=None):
    logging.info("badges.py: sgroup_url=%s, badge_url=%s, action=%s", sgroup_url, badge_url, action)
    user = UserPrefs.current()
    if not user.hasAccess():
        return "denied badges", 403

    breadcrumbs = [{'link': '/', 'text': 'Hem'}]
    section_title = u'Märken'
    breadcrumbs.append({'link': '/badges', 'text': section_title})
    baselink = '/badges/'

    scoutgroup = None
    if sgroup_url is not None:
        sgroup_key = ndb.Key(urlsafe=sgroup_url)
        scoutgroup = sgroup_key.get()
        baselink += sgroup_url + "/"
        breadcrumbs.append({'link': baselink, 'text': scoutgroup.getname()})

    if scoutgroup is None:
        return render_template(
            'index.html',
            heading=section_title,
            baselink=baselink,
            items=ScoutGroup.getgroupsforuser(user),
            breadcrumbs=breadcrumbs,
            username=user.getname())

    if badge_url == "newbadge":
        logging.info("METHOD %s" % request.method)
        if request.method == "POST":
            logging.info("SAVE BADGE")
            name = request.form['name']
            part_strs = request.form['parts'].split("::")
            # TODO. Check possible utf-8/unicode problem here
            parts = [p.split("|") for p in part_strs]
            logging.info("name: %s, parts: %s", name, parts)
            logging.info("raw_partsinfo %s", request.form['parts'])
            badge = Badge.create(name, sgroup_key, parts)
        elif request.method == "GET":
            section_title = "Nytt märke"
            baselink += "newbadge" + "/"
            breadcrumbs.append({'link': baselink, 'text': section_title})
            badge_parts = [
                {'part_id': 1, 'short_desc': "Utrustning", "long_desc": "Kontrollera att behövlig utrustning finns ombord"},
                {'part_id': 2, 'short_desc': 'sjökort', 'long_desc': 'Visa grundläggande kunskap om sjökort alternativt har tagit förarbevis'}
            ]

            return render_template('badge.html',
                                   heading=section_title,
                                   baselink=baselink,
                                   breadcrumbs=breadcrumbs,
                                   badge_parts=badge_parts,
                                   scoutgroup=scoutgroup)
        else:
            badge_url = None  # Reset for now. TODO. Improve

    badge = None
    if badge_url is not None and badge_url != "newbadge":
        baselink += badge_url + "/"
        badge_key = ndb.Key(urlsafe=badge_url)
        badge = badge_key.get()
        section_title = badge.getname()
        breadcrumbs.append({'link': baselink, 'text': badge.getname()})

    logging.info("In BADGES")
    logging.info("ScoutGroup=%s, Badge=%s", scoutgroup, badge)

    # render list of badges
    if badge is None:
        if not user.hasGroupKeyAccess(sgroup_key):
            return "denied", 403
        section_title = 'Märken för kår'
        badges = Badge.get_badges(sgroup_key)
        logging.info("Length of badges is %d", len(badges))

        return render_template('badgelist.html',
                            heading=section_title,
                            baselink=baselink,
                            badges=badges,
                            breadcrumbs=breadcrumbs)
