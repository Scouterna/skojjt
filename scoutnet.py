# -*- coding: utf-8 -*-
# cannot use requests library, doesn't work in gae!
from data import UserPrefs
from flask import render_template
from google.appengine.api import mail
from google.appengine.runtime import apiproxy_errors
import json
import logging
import urllib
import urllib2

def GetScoutnetUrl():
    #scoutnet_url = 'https://demo2.custard.no/'
    scoutnet_url = 'https://www.scoutnet.se/'
    return scoutnet_url


def GetScoutnetMembersAPIJsonData(groupid, api_key):
    """
    :type groupid: str
    :type api_key: str
    :rtype: str
    """
    request = urllib2.Request(GetScoutnetUrl() + 'api/group/memberlist?id=' + groupid + '&key=' + api_key)
    response = urllib2.urlopen(request, timeout=25) # "let it throw, let it throw, let it throw..."
    return response.read()


def GetValueFromJsonObject(p, key, value_name='value'):
    if key in p:
        return p[key][value_name]
    return ''


def GetScoutnetDataListJson(json_data):
    """
    :param json_data: from scoutnet
    :type json_data: str
    """
    j = json.loads(json_data)
    result = []
    for pid in j['data']:
        p = j['data'][pid]
        m = {}
        m["member_no"] = int(GetValueFromJsonObject(p, 'member_no'))
        m["group"] = GetValueFromJsonObject(p, 'group')
        m["group_id"] = GetValueFromJsonObject(p, 'group', 'raw_value')
        m["troop"] = GetValueFromJsonObject(p, 'unit')
        m["troop_id"] = GetValueFromJsonObject(p, 'unit', 'raw_value')
        m["id"] = int(pid) # must be int
        m["firstname"] = GetValueFromJsonObject(p, 'first_name')
        m["lastname"] = GetValueFromJsonObject(p, 'last_name')
        m["personnr"] = GetValueFromJsonObject(p, 'ssno')
        m['sex'] = int(GetValueFromJsonObject(p, 'sex', 'raw_value'))
        m["patrool"] = GetValueFromJsonObject(p, 'patrol')
        m["active"] = GetValueFromJsonObject(p, 'status') == 'Aktiv'
        m["email"] = GetValueFromJsonObject(p, 'email')
        m['contact_alt_email'] = GetValueFromJsonObject(p, 'contact_alt_email')
        phone = FixCountryPrefix(GetValueFromJsonObject(p, 'contact_home_phone'))
        if phone == "":
            phone = FixCountryPrefix(GetValueFromJsonObject(p, 'contact_telephone_home')) # scoutnet has both "Telefon hem" and "Hemtelefon" pick one!
        m["phone"] = phone
        m["mobile"] = FixCountryPrefix(GetValueFromJsonObject(p, 'contact_mobile_phone'))
        m['mum_name'] = GetValueFromJsonObject(p, 'contact_mothers_name')
        m['mum_email'] = GetValueFromJsonObject(p, 'contact_email_mum')
        m['mum_mobile'] = GetValueFromJsonObject(p, 'contact_mobile_mum')
        m['dad_name'] = GetValueFromJsonObject(p, 'contact_fathers_name')
        m['dad_email'] = GetValueFromJsonObject(p, 'contact_email_dad')
        m['dad_mobile'] = GetValueFromJsonObject(p, 'contact_mobile_dad')
        m["street"] = GetValueFromJsonObject(p, 'address_1')
        m["zip_code"] = GetValueFromJsonObject(p, 'postcode')
        m["zip_name"] = GetValueFromJsonObject(p, 'town')
        m["troop_roles"] = [x.strip() for x in GetValueFromJsonObject(p, 'unit_role').lower().split(',')]
        m["group_roles"] = [x.strip() for x in GetValueFromJsonObject(p, 'group_role').lower().split(',')]
        result.append(m)
    return result


def FixCountryPrefix(phone):
    if len(phone) > 8 and phone[0] != '0': # "46 31 123456"
        return '+' + phone
    return phone


class ScoutnetException(Exception):
    pass


class ContactFields():
    Mobiltelefon=1
    Hemtelefon=2
    Alternativ_epost=9
    Anhorig_1_namn=14
    Anhorig_1_e_post=33
    Anhorig_1_mobiltelefon=38
    Anhorig_1_hemtelefon=43
    Anhorig_2_namn=16
    Anhorig_2_e_post=34
    Anhorig_2_mobiltelefon=39
    Anhorig_2_hemtelefon=44


def AddPersonToWaitinglist( scoutgroup, 
                            firstname, 
                            lastname, 
                            personnummer,
                            emailaddress, 
                            address_line1, 
                            zip_code, 
                            zip_name, 
                            phone, 
                            mobile, 
                            troop,
                            anhorig1_name = None, 
                            anhorig1_email = None, 
                            anhorig1_mobile = None, 
                            anhorig1_telefon = None, 
                            anhorig2_name = None, 
                            anhorig2_email = None, 
                            anhorig2_mobile = None, 
                            anhorig2_telefon = None):
    """
    :type scoutgroup: data.ScoutGroup
    :type firstname: str 
    :type lastname: str
    :type personnummer: str
    :type emailaddress: str
    :type address_line1: str
    :type zip_code: str
    :type zip_name: str
    :type phone: str 
    :type mobile: str 
    :type troop: str
    :type anhorig1_name: str
    :type anhorig1_email: str
    :type anhorig1_mobile: str
    :type anhorig1_telefon: str
    :type anhorig2_name: str
    :type anhorig2_email: str
    :type anhorig2_mobile: str
    :type anhorig2_telefon: str
    :rtype: str
    """
    form = {}
    form['profile[first_name]']=firstname
    form['profile[last_name]']=lastname
    form['profile[ssno]']=personnummer
    form['profile[email]']=emailaddress
    form['profile[date_of_birth]']=personnummer[0:4] + '-' + personnummer[4:6] + '-' + personnummer[6:8]
    form['profile[sex]']='1' if int(personnummer[-2])&1 == 1 else '2'
    form['address_list[addresses][address_1][address_line1]']=address_line1
    form['address_list[addresses][address_1][zip_code]']=zip_code
    form['address_list[addresses][address_1][zip_name]']=zip_name
    form['address_list[addresses][address_1][address_type]']=0 # 0=Hemadress, 1=Tillfällig adress
    form['address_list[addresses][address_1][country_code]']=752 # Sweden
    form['address_list[addresses][address_1][is_primary]']=1
    form['profile[preferred_culture]'] = 'sv' # Språk
    form['profile[newsletter]'] = 1 # Nyhetsbrev

    form['contact_list[contacts][contact_1][details]']=mobile
    form['contact_list[contacts][contact_1][contact_type_id]']=ContactFields.Mobiltelefon
    form['contact_list[contacts][contact_2][details]']=phone
    form['contact_list[contacts][contact_2][contact_type_id]']=ContactFields.Hemtelefon

    form['contact_list[contacts][contact_3][details]']=anhorig1_name
    form['contact_list[contacts][contact_3][contact_type_id]']=ContactFields.Anhorig_1_namn
    form['contact_list[contacts][contact_4][details]']=anhorig1_email
    form['contact_list[contacts][contact_4][contact_type_id]']=ContactFields.Anhorig_1_e_post
    form['contact_list[contacts][contact_5][details]']=anhorig1_mobile
    form['contact_list[contacts][contact_5][contact_type_id]']=ContactFields.Anhorig_1_mobiltelefon
    form['contact_list[contacts][contact_6][details]']=anhorig1_telefon
    form['contact_list[contacts][contact_6][contact_type_id]']=ContactFields.Anhorig_1_hemtelefon

    form['contact_list[contacts][contact_7][details]']=anhorig2_name
    form['contact_list[contacts][contact_7][contact_type_id]']=ContactFields.Anhorig_2_namn
    form['contact_list[contacts][contact_8][details]']=anhorig2_email
    form['contact_list[contacts][contact_8][contact_type_id]']=ContactFields.Anhorig_2_e_post
    form['contact_list[contacts][contact_9][details]']=anhorig2_mobile
    form['contact_list[contacts][contact_9][contact_type_id]']=ContactFields.Anhorig_2_mobiltelefon
    form['contact_list[contacts][contact_10][details]']=anhorig2_telefon
    form['contact_list[contacts][contact_10][contact_type_id]']=ContactFields.Anhorig_2_hemtelefon

    form['membership[status]']=1

    logging.info('Adding %s %s to waitinglist' % (firstname, lastname))

    url = GetScoutnetUrl() + 'api/organisation/register/member?id=' + scoutgroup.scoutnetID + '&key=' + scoutgroup.apikey_waitinglist + '&' + urllib.urlencode(form)
    logging.info(url)
    request = urllib2.Request(url)
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        result_json = e.read()
        logging.error("Failed to add person, code=%d, msg=%s", e.code, result_json)
        # Typical responses:
        """{"profile":[{"key":"ssno","value":null,"msg":"Personnumret \u00e4r redan registrerat p\u00e5 medlem '######'. Kontakta Scouternas kansli p\u00e5 scoutnet@scouterna.se f\u00f6r att f\u00e5 hj\u00e4lp."}]}"""
        """{"contact_list":[{"key":"contact_17","value":"example@mail.com","subkey":"contact_type_id","msg":"Invalid. Please choose contact type"}]}"""
        raise ScoutnetException(result_json.decode('unicode_escape')) # display the raw json message
        return 0

    if 200 <= response.getcode() <= 201:
        result_json = response.read()
        logging.info("Added person: " + result_json)
        # response = """{"ss":{"member_no":111111,"sex":"1|2","date_of_birth":"YYYY-MM-DD","first_name":"xx","last_name":"yy","email":"xx@yy.se","newsletter":"1","preferred_culture":"sv","ssno":"nnnn","nick_name":null,"note":null,"product_subscription_8":"1","id":null},"membership":{"troop_id":null,"status":2,"feegroup_id":null,"patrol_id":null},"contact_list":{"contacts":{"contact_9":{"details":"1111111","contact_type_id":"39"},"contact_1":{"contact_type_id":"1","details":"1111111"},"contact_3":{"details":"Contact Person","contact_type_id":"14"},"contact_5":{"details":"1111111","contact_type_id":"38"}}},"address_list":{"addresses":{"address_1":{"country_code":"752","zip_name":"City","address_type":"0","zip_code":"#####","is_primary":"1","address_line1":"gatan 1"}}}}"""
        # response = """{"profile":{"member_no":1234567,"sex":"1","date_of_birth":"2000-01-02","first_name":"Test","last_name":"Persson","email":"xxxxxxxxxx@gmail.com","newsletter":"1","preferred_culture":"sv","ssno":"2391","nick_name":null,"note":null,"id":null},"membership":{"status":2},"contact_list":{"contacts":{"contact_3":{"contact_type_id":"14","details":"asd"},"contact_1":{"contact_type_id":"1","details":"123"},"contact_2":{"contact_type_id":"2","details":"123"}}},"address_list":{"addresses":{"address_1":{"zip_code":"11111","zip_name":"asd","is_primary":"1","address_line1":"test","address_type":"0","country_code":"752"}}}}"""

        member_no = 0
        j = json.loads(result_json)
        for x in j.values():
            if x.has_key('member_no'):
                member_no = x['member_no']
                break

        if member_no == 0:
            logging.error('No member id found in response: "%s"' % (result_json))
        else:
            logging.info("Added person with member_no: %d" % (member_no))

        sendRegistrationQueueInformationEmail(scoutgroup)
        return member_no


def sendRegistrationQueueInformationEmail(scoutgroup):
    try:
        message = mail.EmailMessage(
            sender="noreply@skojjt.appspotmail.com",
            subject=u"Ny person i scoutnets kölista",
            body=render_template("email_queueinfo.txt",    scoutgroup=scoutgroup)
            )
        user=UserPrefs.current()
        message.to=user.getemail()
        message.send()

    except apiproxy_errors.OverQuotaError as message:
        # Log the error.
        logging.error(message)
