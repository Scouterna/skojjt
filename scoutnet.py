# -*- coding: utf-8 -*-
# cannot use requests library, doesn't work in gae!
#import requests
import urllib
import urllib2
import cookielib
import codecs
import logging
import sys
import json
from flask import render_template
from google.appengine.api import mail
from google.appengine.runtime import apiproxy_errors
from google.appengine.ext.webapp.mail_handlers import BounceNotificationHandler
from data import *


def GetScoutnetMembersAPIJsonData(groupid, api_key):
	request = urllib2.Request('https://www.scoutnet.se/api/group/memberlist?id=' + groupid + '&key=' + api_key)
	response = urllib2.urlopen(request, timeout=25) # "let it throw, let it throw, let it throw..."
	return response.read()
	
def GetValueFromJsonObject(p, key, value_name='value'):
	if key in p:
		return p[key][value_name]
	return ''
	
def GetScoutnetDataListJson(json_data):
	j = json.loads(json_data)
	result = []
	for pid in j['data']:
		p = j['data'][pid]
		m = {}
		m["group"] = GetValueFromJsonObject(p, 'group')
		m["group_id"] = GetValueFromJsonObject(p, 'group', 'raw_value')
		m["troop"] = GetValueFromJsonObject(p, 'unit')
		m["troop_id"] = GetValueFromJsonObject(p, 'unit', 'raw_value')
		m["id"] = int(pid) # must be int
		m["firstname"] = GetValueFromJsonObject(p, 'first_name')
		m["lastname"] = GetValueFromJsonObject(p, 'last_name')
		m["personnr"] = GetValueFromJsonObject(p, 'ssno')
		sex = GetValueFromJsonObject(p, 'sex')
		if sex == "Annat":
			continue # ignore non-persons
		m["female"] = sex != 'Man'
		m["patrool"] = GetValueFromJsonObject(p, 'patrol')
		m["active"] = GetValueFromJsonObject(p, 'status') == 'Aktiv'
		m["email"] = GetValueFromJsonObject(p, 'email')
		phone = FixCountryPrefix(GetValueFromJsonObject(p, 'contact_home_phone'))
		if phone == "":
			phone = FixCountryPrefix(GetValueFromJsonObject(p, 'contact_telephone_home')) # scoutnet has both "Telefon hem" and "Hemtelefon" pick one!
		m["phone"] = phone
		m["mobile"] = FixCountryPrefix(GetValueFromJsonObject(p, 'contact_mobile_phone'))
		m["street"] = GetValueFromJsonObject(p, 'address_1')
		m["zip_code"] = GetValueFromJsonObject(p, 'postcode')
		m["zip_name"] = GetValueFromJsonObject(p, 'town')
		m["troop_roles"] = filter(None, GetValueFromJsonObject(p, 'unit_role').lower().split(','))
		m["group_roles"] = filter(None, GetValueFromJsonObject(p, 'group_role').lower().split(','))
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

def AddPersonToWaitinglist(scoutgroup, firstname, lastname, personnummer, emailaddress, address_line1, zip_code, zip_name, phone, mobile, troop,
						   anhorig1_name, anhorig1_email, anhorig1_mobile, anhorig1_telefon, anhorig2_name, anhorig2_email, anhorig2_mobile, anhorig2_telefon):
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
	form['profile[product_subscription_8]'] = 1 # Medlemstidningen
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
	
	url = 'https://www.scoutnet.se/api/organisation/register/member?id=' + scoutgroup.scoutnetID + '&key=' + scoutgroup.apikey_waitinglist + '&' + urllib.urlencode(form)
	logging.info(url)
	request = urllib2.Request(url)
	try:
		response = urllib2.urlopen(request)
	except urllib2.HTTPError as e:
		result_json = e.read()
		logging.error("Failed to add person, code=%d, msg=%s", e.code, result_json)
		# Typical responses:
		"""{"profile":[{"key":"ssno","value":null,"msg":"Personnumret \u00e4r redan registrerat p\u00e5 medlem '######'. Kontakta Scouternas kansli p\u00e5 scoutnet@scouterna.se f\u00f6r att f\u00e5 hj\u00e4lp."}]}"""
		"""{"contact_list":[{"key":"contact_17","value":"karin.modig-pallin@vgregion.se","subkey":"contact_type_id","msg":"Invalid. Please choose contact type"}]}"""
		#j = json.loads(result_json)
		raise ScoutnetException(result_json.decode('unicode_escape')) # display the raw json message
		return False
	   
	if 200 <= response.getcode() <= 201:
		result_json = response.read()
		logging.info("Added person: " + result_json)
		sendRegistrationQueueInformationEmail(scoutgroup)
		return True


def sendRegistrationQueueInformationEmail(scoutgroup):
	try:
		message = mail.EmailMessage(
			sender="noreply@skojjt.appspotmail.com",
			subject=u"Ny person i scoutnets kölista",
			body=render_template("email_queueinfo.txt",	scoutgroup=scoutgroup)
			)
		user=UserPrefs.current()
		message.to=user.getemail()
		message.send()

	except apiproxy_errors.OverQuotaError as message:
		# Log the error.
		logging.error(message)
	
