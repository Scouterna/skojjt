from typing import Dict, Literal, TypedDict


class ScoutnetStringValue(TypedDict):
    value: str


class ScoutnetDictValue(TypedDict):
    value: dict


class ScoutnetKeyValue(TypedDict):
    raw_value: str
    value: str


class MemberListJsonMemberRequired(TypedDict):
    address_1: ScoutnetStringValue
    confirmed_at: ScoutnetStringValue
    country: ScoutnetStringValue
    created_at: ScoutnetStringValue
    current_term: ScoutnetKeyValue
    current_term_due_date: ScoutnetStringValue
    date_of_birth: ScoutnetStringValue
    first_name: ScoutnetStringValue
    group: ScoutnetKeyValue
    last_name: ScoutnetStringValue
    member_no: ScoutnetStringValue
    postcode: ScoutnetStringValue
    prev_term: ScoutnetKeyValue
    roles: ScoutnetDictValue
    sex: ScoutnetKeyValue
    ssno: ScoutnetStringValue
    status: ScoutnetKeyValue
    town: ScoutnetStringValue
    unit: ScoutnetKeyValue


MemberListJsonMemberHyphenedAttributes = TypedDict('MemberListJsonMemberHyphenedAttributes', {'contact_maalsmans_e-post': ScoutnetStringValue}, total=False)


class MemberListJsonMember(MemberListJsonMemberRequired, MemberListJsonMemberHyphenedAttributes):
    address_2: ScoutnetStringValue
    contact_alt_email: ScoutnetStringValue
    contact_email: ScoutnetStringValue
    contact_email_dad: ScoutnetStringValue
    contact_email_mum: ScoutnetStringValue
    contact_fathers_name: ScoutnetStringValue
    contact_guardian_email: ScoutnetStringValue
    contact_guardian_phone_no: ScoutnetStringValue
    contact_home_phone: ScoutnetStringValue
    contact_leader_interest: ScoutnetStringValue
    contact_maalsmans_mobil: ScoutnetStringValue
    contact_maalsmans_telefon: ScoutnetStringValue
    contact_mobile_dad: ScoutnetStringValue
    contact_mobile_me: ScoutnetStringValue
    contact_mobile_mum: ScoutnetStringValue
    contact_mobile_phone: ScoutnetStringValue
    contact_mothers_name: ScoutnetStringValue
    contact_telephone_dad: ScoutnetStringValue
    contact_telephone_home: ScoutnetStringValue
    contact_telephone_mum: ScoutnetStringValue
    contact_work_phone: ScoutnetStringValue
    email: ScoutnetStringValue
    group_role: ScoutnetKeyValue
    note: ScoutnetStringValue
    patrol: ScoutnetKeyValue
    prev_term_due_date: ScoutnetStringValue
    unit_role: ScoutnetKeyValue


class MemberListJson(TypedDict):
    data: Dict[int, MemberListJsonMember]
    labels: Dict[str, str]


# MemberListJsonMemberKeys = Literal[MemberListJsonMember.keys()]
MemberListJsonMemberKeys = Literal[
    'address_1',
    'address_2',
    'confirmed_at',
    'contact_alt_email',
    'contact_email',
    'contact_email_dad',
    'contact_email_mum',
    'contact_fathers_name',
    'contact_guardian_email',
    'contact_guardian_phone_no',
    'contact_home_phone',
    'contact_leader_interest',
    # 'contact_maalsmans_e-post',
    'contact_maalsmans_mobil',
    'contact_maalsmans_telefon',
    'contact_mobile_dad',
    'contact_mobile_me',
    'contact_mobile_mum',
    'contact_mobile_phone',
    'contact_mothers_name',
    'contact_telephone_dad',
    'contact_telephone_home',
    'contact_telephone_mum',
    'contact_work_phone',
    'country',
    'created_at',
    'current_term',
    'current_term_due_date',
    'date_of_birth',
    'email',
    'first_name',
    'group',
    'group_role',
    'last_name',
    'member_no',
    'note',
    'patrol',
    'postcode',
    'prev_term',
    'prev_term_due_date',
    'roles',
    'sex',
    'ssno',
    'status',
    'town',
    'unit',
    'unit_role',
]
