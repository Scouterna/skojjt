from bson import ObjectId
from typing import List, Literal, Optional, TypedDict

timestamp = int


class KarName(TypedDict):
    _id: str
    name: str


class UserName(TypedDict):
    _id: str
    name: str
    roles: List[str]


class PendingImport(TypedDict):
    _id: ObjectId
    added_at: timestamp
    api_key: str
    done_at: timestamp
    kar_id: int
    report: str
    rows_done: int
    rows_totla: int
    started_at: timestamp


class SemesterTroop(TypedDict):
    _id: ObjectId
    kar_id: int
    name: str
    semester: int
    troop_id: int


class SemesterTroopMember(TypedDict):
    _id: ObjectId
    troop: ObjectId
    member: ObjectId
    member_no: int
    troop_id: int
    leader: bool


class SemesterKarMember(TypedDict):
    _id: ObjectId
    member: ObjectId
    member_no: int
    kar_id: int
    semester: int


class NewMember(TypedDict):
    alt_email: str
    dad_email: str
    dad_mobile: str
    dad_name: str
    email: str
    firstname: str
    lastname: str
    member_no: int
    mobile: str
    mum_email: str
    mum_mobile: str
    mum_name: str
    phone: str
    pnr_sex: int
    street: str
    sex: int
    zip_code: str
    zip_name: str


class Member(NewMember):
    _id: Optional[ObjectId]


MemberKeys = Literal[
    '_id',
    'alt_email',
    'dad_email',
    'dad_mobile',
    'dad_name',
    'email',
    'firstname',
    'lastname',
    'member_no',
    'mobile',
    'mum_email',
    'mum_mobile',
    'mum_name',
    'phone',
    'pnr_sex',
    'street',
    'sex',
    'zip_code',
    'zip_name',
]

class MemberStatus(TypedDict):
    is_member: bool
    member: Member
    updated: bool
    was_member: bool
