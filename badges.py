# -*- coding: utf-8 -*-
"""Badge definitions including parts with short and long descriptions."""

import logging
from collections import namedtuple
from flask import Blueprint, render_template, request


from google.appengine.ext import ndb  # pylint: disable=import-error

from data import ScoutGroup, TroopPerson, UserPrefs
from data_badge import Badge, BadgePartDone, TroopBadge, BadgeCompleted, ADMIN_OFFSET

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
@badges.route('/<sgroup_url>/person/<person_url>/<badge_url>/', methods=['POST', 'GET'])
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
            # logging.info("Render list of all badges for scout_group")
            section_title = 'Märken för kår'
            badges = Badge.get_badges(sgroup_key)
            counts = []
            for badge in badges:
                counts.append(BadgeCompleted.query(BadgeCompleted.badge_key == badge.key).count())

            return render_template('badgelist.html',
                                   heading=section_title,
                                   baselink=baselink,
                                   badges=badges,
                                   counts=counts,
                                   breadcrumbs=breadcrumbs)
        # Specific badge or new badge
        if request.method == "GET":
            if badge_url == "newbadge":  # Get form for or create new
                section_title = "Nytt märke"
                badge = None
                name = "Nytt"
                description = ""
            else:
                section_title = "Märke"
                badge_key = ndb.Key(urlsafe=badge_url)
                badge = badge_key.get()
                name = badge.name
                description = badge.description

            baselink += 'badge/' + badge_url + "/"
            if action is not None:
                baselink += action + '/'
            breadcrumbs.append({'link': baselink, 'text': name})

            if action == "showcompleted":
                badgeCompleted = BadgeCompleted.query(BadgeCompleted.badge_key == badge_key).fetch()
                Compl = namedtuple("Compl", "name date examiner")
                completed = [Compl(bc.person_key.get().getname(),
                                   bc.date.strftime("%Y-%m-%d"),
                                   bc.examiner) for bc in badgeCompleted]
                # logging.info("Completed: %s" % completed)
                return render_template('badge_completed_list.html',
                                       breadcrumbs=breadcrumbs,
                                       badge=badge,
                                       badge_completed=completed)
            if badge is not None:
                parts_scout = zip(badge.parts_scout_short, badge.parts_scout_long)
                parts_admin = zip(badge.parts_admin_short, badge.parts_admin_long)
            else:
                parts_scout = []
                parts_admin = []
            thumbnail = badge.thumbnail
            return render_template('badge.html',
                                   name=name,
                                   heading=section_title,
                                   baselink=baselink,
                                   breadcrumbs=breadcrumbs,
                                   description=description,
                                   parts_scout=parts_scout,
                                   parts_admin=parts_admin,
                                   action=action,
                                   thumbnail=thumbnail,
                                   scoutgroup=scoutgroup)
        if request.method == "POST":
            name = request.form['name']
            description = request.form['description']
            parts_scout = request.form['parts_scout'].split("::")
            parts_scout = [p.split("|") for p in parts_scout]
            parts_admin = request.form['parts_admin'].split("::")
            parts_admin = [p.split("|") for p in parts_admin]
            thumbnail = request.form['thumbnail']
            logging.info('description=%s' % description)
            # logging.info("name: %s, parts: %s", name, parts)
            if badge_url == "newbadge":
                badge = Badge.create(name, sgroup_key, description, parts_scout, parts_admin, thumbnail)
                return "ok"
            else:  # Update an existing badge
                badge_key = ndb.Key(urlsafe=badge_url)
                badge = badge_key.get()
                badge.update(name, description, parts_scout, parts_admin, thumbnail)
                return "ok"
        else:
            return "Unsupported method %s" % request.method, 500

    if troop_url is not None and badge_url is None:
        # logging.info("TROOP_URL without BADGE_URL")
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
        # logging.info(new_badge_names)
        TroopBadge.update_for_troop(troop, new_badge_names)
        return "ok"

    if troop_url is not None and badge_url is not None:
        troop_key = ndb.Key(urlsafe=troop_url)
        troop = troop_key.get()
        badge_key = ndb.Key(urlsafe=badge_url)
        badge = badge_key.get()
        if request.method == "POST":
            if person_url is not None:
                return render_badge_for_user(request, person_url, badge_url, baselink, breadcrumbs)
            # logging.info("POST %s %s" % (troop.name, badge.name))
            update = request.form['update']
            if update == "":
                return "ok"  # Return ok to Ajax call
            new_progress = update.split(",")
            examiner_name = UserPrefs.current().name
            # logging.info("new_progress %s" % new_progress)
            prev_scout_url = None
            idx_list = []
            for prog in new_progress:
                scout_url, idx_str = prog.split(":")
                idx = int(idx_str)
                if prev_scout_url is None:
                    prev_scout_url = scout_url
                elif scout_url != prev_scout_url:
                    if len(idx_list) > 0:
                        scout_key = ndb.Key(urlsafe=prev_scout_url)
                        badge.update_for_person(scout_key, idx_list, examiner_name)
                        idx_list = []
                        prev_scout_url = scout_url
                idx_list.append(idx)
            if len(idx_list) > 0:
                scout_key = ndb.Key(urlsafe=prev_scout_url)
                badge.update_for_person(scout_key, idx_list, examiner_name)
            return "ok"  # Return ok to Ajax call
        if request.method == "GET":
            # logging.info("GET %s %s" % (troop.name, badge.name))
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
                return render_badge_for_user(request, person_url, badge_url, baselink, breadcrumbs)
            return render_badge_for_troop(sgroup_url, badge_key, badge, troop_key, troop, baselink, breadcrumbs)

    if person_url is not None:
        person_key = ndb.Key(urlsafe=person_url)
        person = person_key.get()
        baselink = "/badges/" + sgroup_url + '/person/' + person_url + '/'
        breadcrumbs.append({'link': baselink, 'text': "%s" % person.getname()})
        if badge_url is None:
            # logging.info("Badges for %s" % person.getname())
            badge_parts_done = BadgePartDone.query(BadgePartDone.person_key == person_key).fetch()
            badge_keys = {part.badge_key for part in badge_parts_done}
            badges = [badge_key.get() for badge_key in badge_keys]
            badges.sort(key=lambda x: x.name)
            badges_completed = BadgeCompleted.query(BadgeCompleted.person_key == person_key).fetch()
            logging.info(badges_completed)
            completed_keys = {bc.badge_key for bc in badges_completed}
            completed = [b.key in completed_keys for b in badges]
            logging.info("badges %s completed %s" % ([b.name for b in badges], completed))

            return render_template('badgelist_person.html',
                                   heading="Märken för %s" % person.getname(),
                                   baselink=baselink,
                                   breadcrumbs=breadcrumbs,
                                   badges=badges,
                                   completed=completed,
                                   badge_parts_done=badge_parts_done)
        # badge_url is not none

    if person_url is not None and badge_url is not None:
        baselink += badge_url + "/"
        badge_key = ndb.Key(urlsafe=badge_url)
        badge = badge_key.get()
        breadcrumbs.append({'link': baselink, 'text': "%s" % badge.name})
        return render_badge_for_user(request, person_url, badge_url, baselink, breadcrumbs)

    # note that we set the 404 status explicitly
    return "Page not found", 404


def render_badge_for_user(request, person_url, badge_url, baselink, breadcrumbs):
    person_key = ndb.Key(urlsafe=person_url)
    person = person_key.get()
    badge_key = ndb.Key(urlsafe=badge_url)
    badge = badge_key.get()
    parts_done = BadgePartDone.parts_done(person_key, badge_key)
    parts_done_map = {pd.idx: pd for pd in parts_done}
    if request.method == "POST":
        update = request.form['update']
        #logging.info("update: %s" % update)
        if update == "":
            return "ok"
        indices = [int(idx) for idx in update.split(",")]
        examiner_name = UserPrefs.current().name
        badge.update_for_person(person_key, indices, examiner_name)
        return "ok"

    # logging.info("Badge %s for %s" % (badge.name, person.getname()))
    BadgePart = namedtuple('BadgePart', 'idx short_desc long_desc')
    badge_parts = []
    for i in range(len(badge.parts_scout_short)):
        badge_parts.append(BadgePart(i, badge.parts_scout_short[i], badge.parts_scout_long[i]))
    for i in range(len(badge.parts_admin_short)):
        badge_parts.append(BadgePart(i+ADMIN_OFFSET, badge.parts_admin_short[i], badge.parts_admin_long[i]))
    done = []
    Done = namedtuple('Done', 'idx approved done')
    for bp in badge_parts:
        if bp.idx in parts_done_map:
            pd = parts_done_map[bp.idx]
            done.append(Done(bp.idx, pd.date.strftime("%Y-%m-%d") + " " + pd.examiner_name, True))
        else:
            done.append(Done(bp.idx, "- - -", False))

    # logging.info("DONE: %s" % done)

    return render_template('badgeparts_person.html',
                           person=person,
                           baselink=baselink,
                           breadcrumbs=breadcrumbs,
                           badge=badge,
                           badge_parts=badge_parts,
                           done=done,
                           ADMIN_OFFSET=ADMIN_OFFSET)


def render_badge_for_troop(sgroup_url, badge_key, badge, troop_key, troop, baselink, breadcrumbs):
    # section_title = "%s för %s" % (badge.name, troop.name)  # TODO. Check if needed
    troop_persons = TroopPerson.getTroopPersonsForTroop(troop_key)
    # Remove leaders since they are not candidates for badges
    troop_persons = [tp for tp in troop_persons if not tp.leader]
    badge_parts_scout = zip(badge.parts_scout_short, badge.parts_scout_long)
    badge_parts_admin = zip(badge.parts_admin_short, badge.parts_admin_long)
    nr_scout_parts = len(badge_parts_scout)
    nr_parts = nr_scout_parts + len(badge_parts_admin)
    persons = []
    persons_progress = []
    # Categorize person into scout_part, admin_part, or done depending on
    # how far they have got
    persons_scout_part = []
    persons_admin_part = []
    persons_done = []
    persons_scout_progress = []
    persons_admin_progress = []

    for troop_person in troop_persons:
        person_key = troop_person.person
        person = troop_person.person.get()
        if person.removed:
            continue  # Skip people removed from scoutnet
        parts_done = BadgePartDone.parts_done(person_key, badge_key)
        if len(parts_done) < nr_scout_parts:
            persons_scout_part.append(person)
            persons_scout_progress.append(parts_done)
        elif len(parts_done) < nr_parts:
            persons_admin_part.append(person)
            persons_admin_progress.append([pd for pd in parts_done if pd.idx >= ADMIN_OFFSET])
        else:
            persons_done.append(person)
        persons.append(person)
        persons_progress.append(parts_done)

    # logging.info("Persons: %d %d %d %d" % (len(persons), len(persons_scout_part), len(persons_admin_part), len(persons_done)))

    progress_scout_parts = compile_progress(persons_scout_part, persons_scout_progress, badge_parts_scout, 0)
    progress_admin_parts = compile_progress(persons_admin_part, persons_admin_progress, badge_parts_admin, ADMIN_OFFSET)

    return render_template('badge_troop.html',
                           heading=badge.name,
                           baselink=baselink,
                           breadcrumbs=breadcrumbs,
                           troop=troop,
                           badge=badge,
                           persons=persons,
                           parts_progress=[],
                           badge_parts_scout=badge_parts_scout,
                           persons_scout_part=persons_scout_part,
                           progress_scout_parts=progress_scout_parts,
                           badge_parts_admin=badge_parts_admin,
                           persons_admin_part=persons_admin_part,
                           progress_admin_parts=progress_admin_parts,
                           persons_done=persons_done,
                           ADMIN_OFFSET=ADMIN_OFFSET,
                           )


def compile_progress(persons, persons_progress, badge_parts, offset):
    "Return [part][person] boolean matrix."
    parts_progress = []  # [part][person] boolean matrix
    for idx, part in enumerate(badge_parts):
        person_done = []
        for progress in persons_progress:
            for part_done in progress:
                if part_done.idx == idx + offset:
                    person_done.append(True)
                    break
            else:  # No break
                person_done.append(False)
        parts_progress.append(person_done)
    return parts_progress