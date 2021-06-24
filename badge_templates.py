# -*- coding: utf-8 -*-
"""Badge definitions including parts with short and long descriptions."""

import logging
from collections import namedtuple
from flask import Blueprint, render_template, request


from google.appengine.ext import ndb  # pylint: disable=import-error

from data import ScoutGroup, TroopPerson, UserPrefs
from data_badge import Badge, BadgePartDone, TroopBadge, BadgeCompleted, ADMIN_OFFSET

badge_templates = Blueprint('badgetemplates_page', __name__, template_folder='templates')  # pylint : disable=invalid-name

@badges.route('/')
@badges.route('/<badge_url>/)
def show(badge_url=None):
    logging.info("badgetemplates: badge_url=%s", badge_url)
    user = UserPrefs.current()
    if not user.hasAccess():
        return "denied badges", 403

    breadcrumbs = [{'link': '/', 'text': 'Hem'}]
    section_title = u'Märkesmallar'
    breadcrumbs.append({'link': '/badgetemplates', 'text': section_title})
    baselink = '/badgetemplates/'

    if badge_url is None:
        # logging.info("Render list of all badges for scout_group")
        section_title = 'Märken för kår'
        badges = Badge.get_badges('general')

        return render_template('badgelist.html',
                                heading=section_title,
                                baselink=baselink,
                                badges=badges,
                                breadcrumbs=breadcrumbs)