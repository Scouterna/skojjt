# -*- coding: utf-8 -*-
import logging

from google.cloud import ndb

from data import ScoutGroup, Troop, Person

DEFAULT_IMG_URL = '/img/question_mark_PNG122.png'


class Badge(ndb.Model):
    """Badge definition for a scout group (scoutkår). The required parts are separate as BadgePart."""
    name = ndb.StringProperty(required=True)
    scoutgroup = ndb.KeyProperty(kind=ScoutGroup, required=True)
    description = ndb.StringProperty(required=True)
    # Short and long descriptions of scout parts (idx = 0, 1, 2, ...99)
    parts_scout_short = ndb.StringProperty(repeated=True)
    parts_scout_long = ndb.StringProperty(repeated=True)
    # Short and long descriptions of admin parts (idx=100, 101, 101, ...)
    parts_admin_short = ndb.StringProperty(repeated=True)
    parts_admin_long = ndb.StringProperty(repeated=True)
    img_url = ndb.StringProperty()

    @staticmethod
    def create(name, scoutgroup_key, description, parts_scout, parts_admin, img_url):
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
                      parts_admin_long=parts_admin_long,
                      img_url=img_url)
        badge.put()

    def update(self, name, description, parts_scout, parts_admin, img_url):
        """Update badge parts for badge. Separate scout series from admin."""
        changed = False
        if name == "" or name is None:
            logging.warning("No name set for badge update")
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

        if img_url != self.img_url:
            self.img_url = img_url
            changed = True

        if changed:
            # logging.info("Badge %s updated" % self.name)
            self.put()

    @staticmethod
    def get_badges(scoutgroup_key):
        badges = []
        if scoutgroup_key is not None:
            badges = Badge.query(Badge.scoutgroup == scoutgroup_key).order(Badge.name).fetch()
        return badges

    def update_for_person(self, person_key, scout_idx_list, admin_idx_list, examiner_name):
        "Add new idx and create BadgeCompleted when all parts done."
        # logging.info("Badge %s parts %s for %s" % (self.name, idx_list, person.getname()))
        badge_key = self.key
        parts_done = BadgePartDone.parts_done(person_key, badge_key)
        prev_scout_idx = [pd.idx for pd in parts_done if pd.is_scout_part]
        prev_admin_idx = [pd.idx for pd in parts_done if not pd.is_scout_part]
        nr_prev_parts = len(prev_scout_idx) + len(prev_admin_idx)
        nr_all_parts = len(self.parts_scout_short) + len(self.parts_admin_short)

        nr_idx_added = 0
        for idx in scout_idx_list:
            if idx in prev_scout_idx:
                logging.warn("Trying to set scout idx %d again", idx)
                continue
            if idx >= len(self.parts_scout_short):
                logging.warn("Trying to set scout idx %d beyond top", idx)
                continue
            BadgePartDone.create(person_key, badge_key, idx, True, examiner_name)
            nr_idx_added += 1
        for idx in admin_idx_list:
            if idx in prev_admin_idx:
                logging.warn("Trying to set admin idx %d again", idx)
                continue
            if idx >= len(self.parts_admin_short):
                logging.warn("Trying to set admin idx %d beyond top", idx)
                continue
            BadgePartDone.create(person_key, badge_key, idx, False, examiner_name)
            nr_idx_added += 1
        if nr_idx_added > 0 and nr_idx_added + nr_prev_parts == nr_all_parts:
            bc = BadgeCompleted(badge_key=badge_key, person_key=person_key, examiner=examiner_name)
            bc.put()
            # logging.info("Badge %s completed by %s" % (self.name, examiner_name))


class BadgePartDone(ndb.Model):
    "Part that has been done including date and who registered in Skojjt."
    badge_key = ndb.KeyProperty(kind=Badge, required=True)
    person_key = ndb.KeyProperty(kind=Person, required=True)
    idx = ndb.IntegerProperty(required=True)  # idx for BadgePart (zero-based)
    is_scout_part = ndb.BooleanProperty(required=True)
    date = ndb.DateTimeProperty(auto_now_add=True)
    examiner_name = ndb.StringProperty(required=True)

    @staticmethod
    def create(person_key, badge_key, badge_part_idx, is_scout_part, examiner_name):
        bpd = BadgePartDone(person_key=person_key, badge_key=badge_key,
                            idx=badge_part_idx, is_scout_part=is_scout_part,
                            examiner_name=examiner_name)
        bpd.put()

    @staticmethod
    def parts_done(person_key, badge_key):
        """Parts of a badge a specific person has done."""
        bpd = BadgePartDone.query(ndb.AND(BadgePartDone.person_key == person_key,
                                          BadgePartDone.badge_key == badge_key)).order(BadgePartDone.idx).fetch()
        return bpd


class BadgeCompleted(ndb.Model):
    """BadgeCompleted should be created as all requirements are set for a scout and badge."""
    badge_key = ndb.KeyProperty(kind=Badge, required=True)
    person_key = ndb.KeyProperty(kind=Person, required=True)
    date = ndb.DateTimeProperty(auto_now_add=True)
    examiner = ndb.StringProperty()


class TroopBadge(ndb.Model):
    """Badge for troop (avdelning + termin)"""
    troop_key = ndb.KeyProperty(kind=Troop)
    badge_key = ndb.KeyProperty(kind=Badge)

    @staticmethod
    def get_badges_for_troop(troop):
        tps = TroopBadge.query(TroopBadge.troop_key == troop.key).fetch()
        badges = [Badge.get_by_id(tp.badge_key.id()) for tp in tps]
        # logging.info("Badges=%s" % badges)
        return sorted(badges, key=lambda x: x.name)

    @staticmethod
    def update_for_troop(troop, name_list):
        # logging.info("update_for_troop: %s" % name_list)
        old_troop_badges = TroopBadge.query(TroopBadge.troop_key == troop.key).fetch()
        # logging.info("old_troop_badges: %s" % old_troop_badges)
        old_badges_for_troop = [Badge.get_by_id(otp.badge_key.id()) for otp in old_troop_badges]
        old_badges_for_troop = sorted(old_badges_for_troop, key=lambda x: x.name)
        nr_old_troop_badges = len(old_badges_for_troop)
        # logging.info("New are %d, old were %d" % (len(name_list), nr_old_troop_badges))
        # First find keys to remove
        to_remove = []
        for old in old_badges_for_troop:
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
            for old in old_badges_for_troop:
                if old.name == name:
                    break
            else:
                really_new.append(name)
        if len(really_new) == 0:
            return
        # logging.info("Really new are %d" % len(really_new))
        allbadges = Badge.get_badges(troop.scoutgroup)
        idx = nr_old_troop_badges
        for badge in allbadges:
            if badge.name in really_new:
                tb = TroopBadge(troop_key=troop.key, badge_key=badge.key)
                tb.put()
                idx += 1


class BadgeTemplate(ndb.Model):
    """Badge template/blue print to start make a Badge for ascout group (scoutkår)."""
    name = ndb.StringProperty(required=True)
    description = ndb.StringProperty(required=True)
    # Short and long descriptions of scout parts (idx = 0, 1, 2, ...99)
    parts_scout_short = ndb.StringProperty(repeated=True)
    parts_scout_long = ndb.StringProperty(repeated=True)
    # Short and long descriptions of admin parts (idx=100, 101, 101, ...)
    parts_admin_short = ndb.StringProperty(repeated=True)
    parts_admin_long = ndb.StringProperty(repeated=True)
    img_url = ndb.StringProperty()

    @staticmethod
    def get_templates():
        return BadgeTemplate.query().order(BadgeTemplate.name).fetch()

    @staticmethod
    def create(name, description, parts_scout, parts_admin, img_url):
        if name == "" or name is None:
            logging.error("No name set for new badge")
            return
        # logging.info(parts_admin)
        parts_scout_short = [p[0] for p in parts_scout]
        parts_scout_long = [p[1] for p in parts_scout]
        parts_admin_short = [p[0] for p in parts_admin]
        parts_admin_long = [p[1] for p in parts_admin]
        template = BadgeTemplate(name=name,
                                 description=description,
                                 parts_scout_short=parts_scout_short,
                                 parts_scout_long=parts_scout_long,
                                 parts_admin_short=parts_admin_short,
                                 parts_admin_long=parts_admin_long,
                                 img_url=img_url)
        template.put()

    def update(self, name, description, parts_scout, parts_admin, img_url):
        """Update badge parts for badge. Separate scout series from admin."""
        changed = False
        if name == "" or name is None:
            logging.warning("No name set for badge update")
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

        if img_url != self.img_url:
            self.img_url = img_url
            changed = True

        if changed:
            # logging.info("Badge %s updated" % self.name)
            self.put()
