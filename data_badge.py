# -*- coding: utf-8 -*-
"""Badge class används för märken och cerifikat och deras olika delar."""
import logging
from collections import namedtuple

from google.appengine.api import memcache, users
from google.appengine.ext import ndb


from data import ScoutGroup, Troop, Person, PropertyWriteTracker

ADMIN_OFFSET = 100  # Offset for administrative badge parts


class Badge(ndb.Model):
    "Badge definition for a scout group (scoutkår). The required parts are separate as BadgePart."
    name = ndb.StringProperty(required=True)
    scoutgroup = ndb.KeyProperty(kind=ScoutGroup, required=True)
    description = ndb.StringProperty(required=True)
    # Short and long descriptions of scout parts (idx = 0, 1, 2, ...99)
    parts_scout_short = ndb.StringProperty(repeated=True)
    parts_scout_long = ndb.StringProperty(repeated=True)
    # Short and long descriptions of admin parts (idx=100, 101, 101, ...)
    parts_admin_short = ndb.StringProperty(repeated=True)
    parts_admin_long = ndb.StringProperty(repeated=True)
    thumbnail = ndb.TextProperty()  # Quadratic png image of size 128x128 pixels or similar

    @staticmethod
    def create(name, scoutgroup_key, description, parts_scout, parts_admin, thumbnail):
        if name == "" or name is None:
            logging.error("No name set for new badge")
            return
        parts_scout_short = [p[0] for p in parts_scout]
        parts_scout_long = [p[1] for p in parts_scout]
        parts_admin_short = [p[0] for p in parts_admin]
        parts_admin_long = [p[1] for p in parts_admin]
        badge = Badge(name=name,
                      scoutgroup=scoutgroup_key,
                      description=description,
                      parts_scout_short=parts_scout_short,
                      parts_scout_long=parts_scout_long,
                      parts_admin_short=parts_admin_short,
                      parts_admin_long=parts_admin_long)
        if thumbnail:
            badge.thumbnail = thumbnail
        badge.put()

    def update(self, name, description, parts_scout, parts_admin, thumbnail):
        """Update badge parts for badge. Separate scout series from admin."""
        changed = False
        if name == "" or name is None:
            logging.info("No name set for badge update")
            return
        if name != self.name:
            self.name = name
            changed = True

        if description != self.description:
            self.description = description
            changed = True

        if len(parts_scout) < len(self.parts_scout_short):
            # Remove parts not supported yet. Should also remove BadgePartDone
            logging.error("Removing scout parts in update, not yet supported")
            return

        if len(parts_admin) < len(self.parts_admin_short):
            # Remove parts not supported yet. Should also remove BadgePartDone
            logging.error("Removing admin parts in update, not yet supported")
            return

        parts_scout_short = [p[0] for p in parts_scout]
        parts_scout_long = [p[1] for p in parts_scout]
        parts_admin_short = [p[0] for p in parts_admin]
        parts_admin_long = [p[1] for p in parts_admin]

        if parts_scout_short != self.parts_scout_short:
            self.parts_scout_short = parts_scout_short
            changed = True

        if parts_scout_long != self.parts_scout_long:
            self.parts_scout_long = parts_scout_long
            changed = True

        if parts_admin_short != self.parts_admin_short:
            self.parts_admin_short = parts_admin_short
            changed = True

        if parts_admin_long != self.parts_admin_long:
            self.parts_admin_long = parts_admin_long
            changed = True

        if thumbnail:
            self.thumbnail = thumbnail
            changed = True

        if changed:
            logging.info("Badge %s updated" % self.name)
            self.put()

    @staticmethod
    def get_badges(scoutgroup_key):
        badges = []
        if scoutgroup_key is not None:
            badges = Badge.query(Badge.scoutgroup == scoutgroup_key).order(Badge.name).fetch()
        return badges

    def update_for_person(self, person_key, idx_list, examiner_name):
        "Add new idx and create BadgeCompleted when all parts done."
        person = person_key.get()
        logging.info("Badge %s parts %s for %s" % (self.name, idx_list, person.getname()))
        badge_key = self.key
        parts_done = BadgePartDone.parts_done(person_key, badge_key)
        prev_idx = [pd.idx for pd in parts_done]
        nr_idx_added = 0
        all_idx = range(len(self.parts_scout_short))
        for idx in range(ADMIN_OFFSET, ADMIN_OFFSET+len(self.parts_admin_short)):
            all_idx.append(idx)
        for idx in idx_list:
            if idx in prev_idx:
                logging.warn("Trying to set idx %d again", idx)
            if idx not in all_idx:
                logging.warn("Trying to set bad idx %d" % idx)
            BadgePartDone.create(person_key, badge_key, idx, examiner_name)
            nr_idx_added += 1
        if nr_idx_added > 0 and nr_idx_added + len(prev_idx) == len(all_idx):
            bc = BadgeCompleted(badge_key=badge_key, person_key=person_key, examiner=examiner_name)
            bc.put()
            logging.info("Badge %s completed by %s" % (self.name, examiner_name))


class BadgePartDone(ndb.Model):
    "Part that has been done including date and who registered in Skojjt."
    badge_key = ndb.KeyProperty(kind=Badge, required=True)
    person_key = ndb.KeyProperty(kind=Person, required=True)
    idx = ndb.IntegerProperty(required=True)  # idx for BadgePart
    date = ndb.DateTimeProperty(auto_now_add=True)
    examiner_name = ndb.StringProperty(required=True)

    @staticmethod
    def create(person_key, badge_key, badge_part_idx, examiner_name):
        bpd = BadgePartDone(person_key=person_key, badge_key=badge_key,
                            idx=badge_part_idx, examiner_name=examiner_name)
        bpd.put()

    @staticmethod
    def parts_done(person_key, badge_key):
        "What parts a specific person has done."
        bpd = BadgePartDone.query(ndb.AND(BadgePartDone.person_key == person_key,
                                          BadgePartDone.badge_key == badge_key)).order(BadgePartDone.idx).fetch()
        return bpd


class BadgeCompleted(ndb.Model):
    "BadgeCompleted should be created as all requirements are set for a scout and badge."
    badge_key = ndb.KeyProperty(kind=Badge, required=True)
    person_key = ndb.KeyProperty(kind=Person, required=True)
    date = ndb.DateTimeProperty(auto_now_add=True)
    examiner = ndb.StringProperty()


class TroopBadge(ndb.Model):
    "Badge for troop (avdelning + termin)"
    troop_key = ndb.KeyProperty(kind=Troop)
    badge_key = ndb.KeyProperty(kind=Badge)

    @staticmethod
    def get_badges_for_troop(troop):
        tps = TroopBadge.query(TroopBadge.troop_key == troop.key).fetch()
        badges = [Badge.get_by_id(tp.badge_key.id()) for tp in tps]
        return sorted(badges, lambda x: x.name)

    @staticmethod
    def update_for_troop(troop, name_list):
        old_troop_badge_ids = TroopBadge.query(TroopBadge.troop_key == troop.key).fetch()
        old_troop_badges = [Badge.get_by_id(tp.badge_key.id()) for tp in old_troop_badge_ids]
        old_troop_badges = sorted(old_troop_badges, lambda x: x.name)
        nr_old_troop_badges = len(old_troop_badges)
        logging.info("New are %d, old were %d" % (len(name_list), nr_old_troop_badges))
        # First find keys to remove
        to_remove = []
        for old in old_troop_badges:
            if old.name not in name_list:
                to_remove.append(old.key)
        # Next remove them from the troop badges
        for old_key in to_remove:
            for otb in old_troop_badges:
                if otb.badge_key == old_key:
                    otb.key.delete()
        # Now find really new names
        really_new = []
        for name in name_list:
            for old in old_troop_badges:
                if old.name == name:
                    break
            else:
                really_new.append(name)
        if len(really_new) == 0:
            return
        logging.info("Really new are %d" % len(really_new))
        allbadges = Badge.get_badges(troop.scoutgroup)
        idx = nr_old_troop_badges
        for badge in allbadges:
            if badge.name in really_new:
                tb = TroopBadge(troop_key=troop.key, badge_key=badge.key)
                tb.put()
                idx += 1
