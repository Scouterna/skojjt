from __future__ import annotations
from typing import Dict, Optional, Union

# Real external imports
from bson import ObjectId
from datetime import datetime
from os import getenv
from requests import get as get_url
from time import time

# Typeings
from models.scoutnetTypes import MemberListJson, MemberListJsonMember, MemberListJsonMemberKeys
from models.types import Member, MemberKeys, MemberStatus, NewMember, PendingImport, \
    SemesterKarMember, SemesterTroop, SemesterTroopMember
from pymongo.collection import Collection
from pymongo.database import Database

# Internal imports
from db import db_connect


class KarImportJob:
    db: Database = None
    import_id: str = None
    query: dict = None
    row: PendingImport = None
    semester: int = None
    report: str = None
    table: Collection = None
    troops: Dict[int, SemesterTroop] = None

    @staticmethod
    def find() -> Optional[KarImportJob]:
        query = {'started_at': 0}
        db = db_connect()
        table = db['pending_import']
        row: Optional[PendingImport] = table.find_one(query)
        if row is None:
            return None

        job = KarImportJob()
        job.import_id = str(row['_id'])
        job.query = {'_id': ObjectId(job.import_id)}
        job.db = db
        job.table = table
        job.row = row
        job.report = row['report']
        return job

    def update(self, set_data) -> None:
        self.table.update_one(self.query, {'$set': set_data})

    def append_report(self, row: str) -> None:
        # self.update({'report': {'$concat': ['$report', "\n", row]}})
        self.report += "\n" + row
        self.update({'report': self.report})

    def error(self, error) -> None:
        # self.update({'error_at': time(), 'report': {'$concat': ['$report', "\n", "Error: ", error]}})
        self.report += "\n" + "Error: " + str(error)
        self.update({'error_at': time(), 'report': self.report})

    def run(self) -> None:
        started_at = time()
        self.update({'started_at': started_at})
        date = datetime.now()
        date_str = str(date)[:19]
        if date.month > 6:
            self.semester = date.year * 100 + 7
            semester_name = 'HT-' + str(date.year)
        else:
            self.semester = date.year * 100 + 1
            semester_name = 'VT-' + str(date.year)
        pass
        kar_id = self.row['kar_id']
        api_key = self.row['api_key']
        self.append_report(f'Startar import för terminen {semester_name} @ {date_str}')

        scoutnet_hostname = getenv('SCOUTNET_IMPORT_HOST')
        url = f'https://{kar_id}:{api_key}@{scoutnet_hostname}/api/group/memberlist'
        try:
            memberlist: MemberListJson = get_url(url).json()
        except Exception as e:
            self.error(e)
            raise e

        members = len(memberlist['data'])
        if members < 3:
            e = Exception(f'Scoutnet memberlist have no/few members: {members}')
            self.error(e)
            raise e
        self.update({'rows_total': members})

        skojjt_members: Dict[int, MemberStatus] = {}
        for row in self.db['members'].find({'kar_id': kar_id}):  # type: Member
            skojjt_members[int(row['member_no'])] = {
                'is_member': False,
                'member': row,
                'updated': False,
                'was_member': len(row['member_no']) > 0,
            }

        counter = 0
        for member_no_str, member in memberlist['data'].items():  # type: str, MemberListJsonMember
            member_no = int(member_no_str)

            if member_no in skojjt_members:
                skojjt_members[member_no]['is_member'] = True
                if self.update_member(skojjt_members[member_no]['member'], member):
                    skojjt_members[member_no]['updated'] = True
                    self.append_report(f"Uppdaterade {member['first_name']} {member['last_name']} ({member_no})")
            else:
                new_member = self.add_member(member)
                skojjt_members[member_no] = {
                    'is_member': True,
                    'member': new_member,
                    'updated': True,
                    'was_member': False,
                }
                self.append_report(f"La till {member['first_name']} {member['last_name']} ({member_no})")

            self.add_kar_member(skojjt_members[member_no]['member'])

            if member['unit'] is not None:
                unit_id = int(member['unit']['raw_value'])
                if unit_id > 0:
                    troop = self.get_troop(unit_id, member['unit']['value'])
                    self.add_troop_member(troop, skojjt_members[member_no]['member'])

            counter += 1
            self.update({'rows_done': counter})
        done_at = time()
        self.update({'done_at': done_at})
        total_time = done_at - started_at;
        self.append_report(f"Importerat {counter} medelammar, vilket tog {total_time} sekunder.")

    def add_kar_member(self, member: Member) -> SemesterKarMember:
        table = self.db['kar_members']
        kar_id = self.row['kar_id']
        query = {'kar_id': kar_id, 'semester': self.semester, 'member': member['_id']}
        result = table.find_one(query)
        if result is not None:
            return result
        table.insert({
            'kar_id': kar_id,
            'member': member['_id'],
            'member_no': member['member_no'],
            'semester': self.semester
        })
        return table.find_one(query)

    def get_troop(self, troop_id, name) -> Optional[SemesterTroop]:
        troop_table = self.db['troops']
        if len(name) == 0:
            return None

        if self.troops is None:
            query = {'kar_id': self.row['kar_id'], 'semester': self.semester}
            self.troops = {}
            for troop in troop_table.find(query):
                self.troops[troop['troop_id']] = troop

        if troop_id in self.troops:
            troop = self.troops[troop_id]
            if troop['name'] == name:
                return troop

            troop_table.update({'_id': troop['_id']}, {'$set': {'name': name}})
            troop['name'] = name
            return troop

        new_troop = {'kar_id': self.row['kar_id'], 'semester': self.semester, 'troop_id': troop_id, 'name': name}
        result = troop_table.insert_one(new_troop)
        troop: SemesterTroop = troop_table.find_one({'_id': result.inserted_id})
        self.troops[troop_id] = troop
        self.append_report(f"Ny avdelning {name}, ID={troop_id}, semester={self.semester}")
        return troop

    def add_troop_member(self, troop: SemesterTroop, member: Member, leader=False) -> SemesterTroopMember:
        table = self.db['troop_members']
        query = {'troop': troop['_id'], 'member': member['_id']}
        result = table.find_one(query)
        if result is not None:
            return result
        table.insert({
            'troop': troop['_id'],
            'member': member['_id'],
            'member_no': member['member_no'],
            'troop_id': troop['troop_id'],
            'leader': leader
        })
        return table.find_one(query)

    def generate_member(self, scoutnet_member: MemberListJsonMember) -> NewMember:
        def member_value(key: MemberListJsonMemberKeys, key2: str = 'value'):
            if key not in scoutnet_member:
                return ''
            if key2 not in scoutnet_member[key]:
                return ''
            return scoutnet_member[key][key2]

        pnr_sex = 0
        if len(member_value('ssno')) == 13:
            pnr_sex = 2 - (int(member_value('ssno')[12:13]) % 2)
        phone1 = member_value('contact_home_phone')
        phone2 = member_value('contact_telephone_home')
        phone = ''
        if 'contact_home_phone' in scoutnet_member and len(phone1) > 3:
            phone = phone1
        if 'contact_home_phone' in scoutnet_member and len(phone2) > 3:
            phone = phone2
        street = (member_value('address_1') + "\n" + member_value('address_2')).strip()
        member: NewMember = {
            'alt_email': member_value('contact_alt_email'),
            'dad_email': member_value('contact_email_dad'),
            'dad_mobile': member_value('contact_mobile_dad'),
            'dad_name': member_value('contact_fathers_name'),
            'email': member_value('email'),
            'firstname': member_value('first_name'),
            'lastname': member_value('last_name'),
            'member_no': int(member_value('member_no')),
            'mobile': member_value('contact_mobile_phone'),
            'mum_email': member_value('contact_email_mum'),
            'mum_mobile': member_value('contact_mobile_mum'),
            'mum_name': member_value('contact_mothers_name'),
            'phone': phone,
            'pnr_sex': pnr_sex,  # 1: Man, 2: Kvinna, 0: fullständigt personnummer saknas
            'sex': int(member_value('sex', 'raw_value')),  # 1: Man, 2: Kvinna, 0: Annat
            'street': street,
            'zip_code': member_value('postcode'),
            'zip_name': member_value('town'),
        }
        return member

    def add_member(self, scoutnet_member: MemberListJsonMember) -> Member:
        table = self.db['members']
        new_member = self.generate_member(scoutnet_member)
        result = table.insert_one(new_member)
        return table.find_one({'_id': result.inserted_id})

    def update_member(self, skojjt_member: Member, scoutnet_member: MemberListJsonMember) -> bool:
        table = self.db['members']
        new_member = self.generate_member(scoutnet_member)
        diff = {}
        diff_count = 0
        for key, value in new_member:  # type: MemberKeys, Union[str, int, ObjectId]
            if skojjt_member[key] != value:
                diff[key] = value
                diff_count += 1
        if diff_count < 1:
            return False
        table.update_one({'_id': skojjt_member['_id']}, {'$set': diff})
        return True
