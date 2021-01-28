# -*- coding: utf-8 -*-
"""Badge definitions including parts with short and long descriptions."""

import logging
from collections import namedtuple
from flask import Blueprint, render_template, request


from google.appengine.ext import ndb  # pylint: disable=import-error

from data import ScoutGroup, TroopPerson, UserPrefs
from data_badge import Badge, BadgePartDone, TroopBadge, ADMIN_OFFSET

badges = Blueprint('badges_page', __name__, template_folder='templates')  # pylint : disable=invalid-name


@badges.route('/')
@badges.route('/<sgroup_url>/')
@badges.route('/<sgroup_url>/badge/<badge_url>/', methods=['POST', 'GET'])  # A specific badge, post with newbadge
@badges.route('/<sgroup_url>/badge/<badge_url>/<action>/', methods=['POST', 'GET'])  # Actions: show, change
@badges.route('/<sgroup_url>/troop/<troop_url>/', methods=['POST', 'GET'])
@badges.route('/<sgroup_url>/troop/<troop_url>/<badge_url>/', methods=['POST', 'GET'])
@badges.route('/<sgroup_url>/troop/<troop_url>/<badge_url>/<person_url>/', methods=['POST', 'GET'])
@badges.route('/<sgroup_url>/person/<person_url>/')  # List of badges for a person
@badges.route('/<sgroup_url>/person/<person_url>/<badge_url>/', methods=['POST', 'GET'])
@badges.route('/<sgroup_url>/person/<person_url>/<badge_url>/<action>/', methods=['POST', 'GET'])  # Actions:show/change
def show(sgroup_url=None, badge_url=None, troop_url=None, person_url=None, action=None):
    logging.info("badges.py: sgroup_url=%s, badge_url=%s, troop_url=%s, person_url=%s, action=%s",
                 sgroup_url, badge_url, troop_url, person_url, action)
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

    if troop_url is None and person_url is None:  # scoutgroup level
        if badge_url is None:
            logging.info("Render list of all badges for scout_group")
            section_title = 'Märken för kår'
            badges = Badge.get_badges(sgroup_key)

            return render_template('badgelist.html',
                                   heading=section_title,
                                   baselink=baselink,
                                   badges=badges,
                                   breadcrumbs=breadcrumbs)
        # Specfic badge or new badge
        if request.method == "GET":
            if badge_url == "newbadge":  # Get form for or create new
                section_title = "Nytt märke"
                name = "Nytt"
                badge_parts_nonadmin = []
                badge_parts_admin = []
            else:
                section_title = "Märke"
                badge_key = ndb.Key(urlsafe=badge_url)
                badge = badge_key.get()
                name = badge.name
                badge_parts = badge.get_parts()
                badge_parts_nonadmin = [bp for bp in badge_parts if bp.idx < ADMIN_OFFSET]
                badge_parts_admin = [bp for bp in badge_parts if bp.idx >= ADMIN_OFFSET]

            baselink += 'badge/' + badge_url + "/"
            if action is not None:
                baselink += action + '/'
            breadcrumbs.append({'link': baselink, 'text': name})

            return render_template('badge.html',
                                   name=name,
                                   heading=section_title,
                                   baselink=baselink,
                                   breadcrumbs=breadcrumbs,
                                   badge_parts_nonadmin=badge_parts_nonadmin,
                                   badge_parts_admin=badge_parts_admin,
                                   action=action,
                                   scoutgroup=scoutgroup)
        if request.method == "POST":
            name = request.form['name']
            part_strs = request.form['parts'].split("::")
            parts = [p.split("|") for p in part_strs]
            # logging.info("name: %s, parts: %s", name, parts)
            if badge_url == "newbadge":
                badge = Badge.create(name, sgroup_key, parts)
                return "ok"
            else:  # Update an existing badge
                badge_key = ndb.Key(urlsafe=badge_url)
                badge = badge_key.get()
                badge.update(name, parts)
                return "ok"
        else:
            return "Unsupported method %s" % request.method, 500

    if troop_url is not None and badge_url is None:
        logging.info("TROOP_URL without BADGE_URL")
        troop_key = ndb.Key(urlsafe=troop_url)
        troop = troop_key.get()
        if request.method == "GET":
            # Since we come from /start/... instead of /badges/... replace part links
            for bc in breadcrumbs:
                bc['link'] = bc['link'].replace('badges', 'start')
                bc['text'] = bc['text'].replace('Märken', 'Kårer')
            baselink += "troop/" + troop_url + "/"
            badges = Badge.get_badges(sgroup_key)
            semester_key = troop.semester_key
            semester = semester_key.get()
            semester_name = semester.getname()
            section_title = "Märken för %s %s" % (troop.name, semester_name)
            breadcrumbs.append({'link': baselink, 'text': "Märken %s" % troop.name})
            troop_badges = TroopBadge.get_badges_for_troop(troop)
            # logging.info("Nr troop_badges is %d" % len(troop_badges))
            troop_badge_names = [tb.name for tb in troop_badges]
            return render_template('badges_for_troop.html',
                                   name=troop.name,
                                   heading=section_title,
                                   baselink=baselink,
                                   breadcrumbs=breadcrumbs,
                                   badges=badges,
                                   troop_badge_names=troop_badge_names,
                                   scoutgroup=scoutgroup)
        # POST
        new_badge_names = request.form['badges'].split("|")
        logging.info(new_badge_names)
        TroopBadge.update_for_troop(troop, new_badge_names)
        return "ok"

    if troop_url is not None and badge_url is not None:
        troop_key = ndb.Key(urlsafe=troop_url)
        troop = troop_key.get()
        badge_key = ndb.Key(urlsafe=badge_url)
        badge = badge_key.get()
        if request.method == "POST":
            if person_url is not None:
                return render_badge_for_user(request, person_url, badge_url, baselink, breadcrumbs, True)
            logging.info("POST %s %s" % (troop.name, badge.name))
            update = request.form['update']
            if update == "":
                return "ok"  # Return ok to Ajax call
            new_progress = update.split(",")
            examiner_name = UserPrefs.current().name
            logging.info("new_progress %s" % new_progress)
            for prog in new_progress:
                scout_url, idx = prog.split(":")
                badge_part_idx = int(idx)
                scout_key = ndb.Key(urlsafe=scout_url)
                logging.info("Update: %s %s %d %s", scout_key, badge_key, badge_part_idx, examiner_name)
                BadgePartDone.create(scout_key, badge_key, badge_part_idx, examiner_name)
            return "ok"  # Return ok to Ajax call
        if request.method == "GET":
            logging.info("GET %s %s" % (troop.name, badge.name))
            # Since we come from /start/... instead of /badges/... replace part links
            for bc in breadcrumbs:
                bc['link'] = bc['link'].replace('badges', 'start')
                bc['text'] = bc['text'].replace('Märken', 'Kårer')
            baselink += "troop/" + troop_url + "/" + badge_url + "/"
            breadcrumbs.append({'link': baselink, 'text': "%s %s" % (troop.name, badge.name)})
            if person_url is not None:
                baselink += person_url + '/'
                person_key = ndb.Key(urlsafe=person_url)
                person = person_key.get()
                breadcrumbs.append({'link': baselink, 'text': person.getname()})
                return render_badge_for_user(request, person_url, badge_url, baselink, breadcrumbs, True)
            return render_badge_for_troop(sgroup_url, badge_key, badge, troop_key, troop, baselink, breadcrumbs)

    if person_url is not None:
        person_key = ndb.Key(urlsafe=person_url)
        person = person_key.get()
        baselink = "/badges/" + sgroup_url + '/person/' + person_url + '/'
        breadcrumbs.append({'link': baselink, 'text': "%s" % person.getname()})
        if badge_url is None:
            logging.info("Badges for %s" % person.getname())
            badge_parts_done = BadgePartDone.query(BadgePartDone.person_key == person_key).fetch()
            badge_keys = set()
            for part in badge_parts_done:
                badge_keys.add(part.badge_key)
            badges = []
            for badge_key in badge_keys:
                badges.append(badge_key.get())
            badges.sort(key=lambda x: x.name)

            return render_template('badgelist_person.html',
                                   heading="Märken för %s" % person.getname(),
                                   baselink=baselink,
                                   breadcrumbs=breadcrumbs,
                                   badges=badges,
                                   badge_parts_done=badge_parts_done)
        # badge_url is not none

    if person_url is not None and badge_url is not None:
        canedit = action == 'change'
        baselink += badge_url + "/"
        badge_key = ndb.Key(urlsafe=badge_url)
        badge = badge_key.get()
        breadcrumbs.append({'link': baselink, 'text': "%s" % badge.name})
        return render_badge_for_user(request, person_url, badge_url, baselink, breadcrumbs, canedit)

    # note that we set the 404 status explicitly
    return "Page not found", 404


def render_badge_for_user(request, person_url, badge_url, baselink, breadcrumbs, canedit):
    person_key = ndb.Key(urlsafe=person_url)
    person = person_key.get()
    badge_key = ndb.Key(urlsafe=badge_url)
    badge = badge_key.get()
    if request.method == "POST":
        update = request.form['update']
        logging.info("update: %s" % update)
        indices = [int(idx) for idx in update.split(",")]
        examiner_name = UserPrefs.current().name
        for idx in indices:
            logging.info("Setting badge %s idx %s for %s" % (badge.name, idx, person.getname()))
            BadgePartDone.create(person_key, badge_key, idx, examiner_name)
        return "ok"

    logging.info("Badge %s for %s" % (badge.name, person.getname()))
    badge_parts = badge.get_parts()
    parts_done = BadgePartDone.parts_done(person_key, badge_key)
    d_pos = 0
    done = []
    Done = namedtuple('Done', 'idx date examiner done')
    for bp in badge_parts:
        if d_pos >= len(parts_done):
            done.append(Done(bp.idx, "- - -", "- - -", False))
            continue
        pd = parts_done[d_pos]
        if pd.idx == bp.idx:
            done.append(Done(pd.idx, pd.date.strftime("%Y-%m-%d"), pd.examiner_name, True))
            d_pos += 1
        else:
            done.append(Done(bp.idx, "- - -", "- - -", False))

    logging.info("DONE: %s" % done)

    return render_template('badgeparts_person.html',
                           person=person,
                           baselink=baselink,
                           breadcrumbs=breadcrumbs,
                           badge=badge,
                           badge_parts=badge_parts,
                           done=done,
                           change=canedit)


def render_badge_for_troop(sgroup_url, badge_key, badge, troop_key, troop, baselink, breadcrumbs):
    # section_title = "%s för %s" % (badge.name, troop.name)  # TODO. Check if needed
    troop_persons = TroopPerson.getTroopPersonsForTroop(troop_key)
    # Remove leaders since they are not candidates for badges
    troop_persons = [tp for tp in troop_persons if not tp.leader]
    persons = []
    persons_dict = {}
    persons_progess = []
    for troop_person in troop_persons:
        person_key = troop_person.person
        person = troop_person.person.get()
        if person.removed:
            continue  # Skip people removed from scoutnet
        persons.append(person)
        persons_progess.append(BadgePartDone.parts_done(person_key, badge_key))
        persons_dict[person_key] = person
    badge_parts = badge.get_parts()
    parts_progress = []  # [part][person] boolean matrix
    for part in badge_parts:
        person_done = []
        for progress in persons_progess:
            for part_done in progress:
                if part_done.idx == part.idx:
                    person_done.append(True)
                    break
            else:  # No break
                person_done.append(False)
        parts_progress.append(person_done)
    return render_template('badge_troop.html',
                           heading=badge.name,
                           baselink=baselink,
                           breadcrumbs=breadcrumbs,
                           troop=troop,
                           badge=badge,
                           badge_parts=badge_parts,
                           persons=persons,
                           parts_progress=parts_progress)