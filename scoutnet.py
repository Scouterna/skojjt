# -*- coding: utf-8 -*-
# cannot use requests library, doesn't work in gae!
#import requests
import urllib
import urllib2
import cookielib
import codecs
import ucsv
import logging
import sys
import json


def unicode_csv_reader(utf8_data):
	csv_reader = ucsv.reader(utf8_data, delimiter=',', quoting=ucsv.QUOTE_NONE) # QUOTE_NONE to avoid evaluating strings as numbers
	for row in csv_reader:
		yield [cell.strip("\"") for cell in row] # QUOTE_NONE will keep quotes

def GetScoutnetMembersCSVData(username, password, groupid):
	payload = {'signin[username]': username, 'signin[password]': password}

	cj = cookielib.CookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	urllib2.install_opener(opener)
	data = urllib.urlencode(payload)
	header = {"User-Agent", "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36"}
	req = urllib2.Request('https://www.scoutnet.se/login')
	req.add_data(data)
	response = urllib2.urlopen(req)
	req2 = urllib2.Request('https://www.scoutnet.se/reports/groups/members/group_id/' + groupid + '/download/true/format/csv')
	response = urllib2.urlopen(req2)
	return response.read()

def GetScoutnetMembersAPIJsonData(groupid, api_key):
	request = urllib2.Request('https://www.scoutnet.se/api/group/memberlist?id=' + groupid + '&key=' + api_key)
	response = urllib2.urlopen(request) # "let it throw, let it throw, let it throw..."
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
	
def GetScoutnetDataList(data):
	result = []
	reader = unicode_csv_reader(data)
	first = True
	inr = -1
	ifname = 0
	ilname = 0
	ipnummer = 0
	isgroup = 0
	itroop = 0
	ipatrool = 0
	isex = 0
	iaktiv = 0
	iepost = 0
	ihemtel = 0
	itelhem = 0
	imobil = 0
	
	for row in reader:
		if first:
			first = False
			for index, col in enumerate(row):
				if col == "Medlemsnr.":
					inr = index
				elif col == u"Förnamn":
					ifname = index
				elif col == "Efternamn":
					ilname = index
				elif col == u"Personnummer":
					ipnummer = index
				elif col == u"Kår":
					isgroup = index
				elif col == "Avdelning":
					itroop = index
				elif col == "Patrull":
					ipatrool = index
				elif col == u"Kön":
					isex = index
				elif col == "Status":
					iaktiv = index
				elif col == "E-post":
					iepost = index
				elif col == "Telefon hem":
					itelhem = index
				elif col == "Hemtelefon":
					ihemtel = index
				elif col == "Mobiltelefon":
					imobil = index

			#logging.info("fields %d, %d, %d, %d, %d, %d, %d, %d", inr,ifname,ilname,ipnummer,isgroup,itroop,ipatrool,isex)
			if (inr+1) * ifname * ilname * ipnummer * isgroup * itroop * ipatrool * isex * iaktiv == 0:
				logging.error("missing some field %d, %d, %d, %d, %d, %d, %d, %d, %d", inr,ifname,ilname,ipnummer,isgroup,itroop,ipatrool,isex,iaktiv)
				raise ValueError('Missing some field')
		else:
			m = {}
			m["group"] = row[isgroup]
			m["troop"] = row[itroop]
			m["id"] = str(row[inr])
			m["firstname"] = row[ifname]
			m["lastname"] = row[ilname]
			m["personnr"] = str(row[ipnummer])
			m["female"] = row[isex]!='Man'
			m["patrool"] = row[ipatrool]
			m["active"] = row[iaktiv] == "Aktiv"
			m["email"] = row[iepost] if iepost != 0 else ""
			phone = FixCountryPrefix(str(row[ihemtel]) if ihemtel != 0 else "")
			if phone == "":
				phone = FixCountryPrefix(str(row[itelhem]) if itelhem != 0 else "") # scoutnet has both "Telefon hem" and "Hemtelefon" pick one!
			m["phone"] = phone
			m["mobile"] = FixCountryPrefix(str(row[imobil]) if imobil != 0 else "")
			result.append(m)

	return result

def FixCountryPrefix(phone):
	if len(phone) > 8 and phone[0] != '0': # "46 31 123456"
		return '+' + phone
	return phone
	
def ImportScoutnetAsCSV(filename='members.csv'):
	data = GetScoutnetMembersCSVData()
	if data:
		f = codecs.open(filename, 'w', 'utf-8')
		f.write(GetScoutnetMembersCSVData())
	else:
		print("Failed")
		
def AddPersonToWaitinglist(scoutgroup, firstname, lastname, personnummer, emailaddress, address_line1, zip_code, zip_name, mobile, phone):
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
	form['profile[product_subscription_8]'] = 1 # Medlemstidningen
	
	form['contact_list[contacts][contact_1][details]']=mobile
	form['contact_list[contacts][contact_1][contact_type_id]']=1 # mobiltelefon

	form['contact_list[contacts][contact_2][details]']=phone
	form['contact_list[contacts][contact_2][contact_type_id]']=2 # hemtelefon

	form['contact_list[contacts][contact_17][details]']=emailaddress
	form['contact_list[contacts][contact_17][contact_type_id]']=17 # epost
	
	#form['contact_list[contacts][contact_14][details]']=mamma
	#form['contact_list[contacts][contact_14][contact_type_id]']=14 # Mammas namn
	#form['contact_list[contacts][contact_33][details]']=mammaepost
	#form['contact_list[contacts][contact_33][contact_type_id]']=33  # Mamma E-post
	#form['contact_list[contacts][contact_38][details]']=mammamobil
	#form['contact_list[contacts][contact_38][contact_type_id]']=38 # Mamma mobil
	#form['contact_list[contacts][contact_43][details]']=mammatelefon
	#form['contact_list[contacts][contact_43][contact_type_id]']=43 # Mamma telefon
	#form['contact_list[contacts][contact_16][details]']=pappa
	#form['contact_list[contacts][contact_16][contact_type_id]']=16 # Pappas namn
	#form['contact_list[contacts][contact_34][details]']=pappaepost
	#form['contact_list[contacts][contact_34][contact_type_id]']=34 # Pappa E-post 
	#form['contact_list[contacts][contact_39][details]']=pappamobil
	#form['contact_list[contacts][contact_39][contact_type_id]']=39 # Pappa mobil
	#form['contact_list[contacts][contact_44][details]']=pappatelefon
	#form['contact_list[contacts][contact_44][contact_type_id]']=44 # Pappa telefon

	form['membership[status]']=1

	url = 'https://www.scoutnet.se/api/organisation/register/member?id=' + scoutgroup.scoutnetID + '&key=' + scoutgroup.apikey_waitinglist + '&' + urllib.urlencode(form)
	logging.info(url)
	request = urllib2.Request(url)
	try:
		response = urllib2.urlopen(request)
	except urllib2.HTTPError as e:
		logging.error("Failed to add person, code=%d", e.code)
		return False
	   
	if 200 <= response.getcode() <= 201:
		result_json = response.read()
		logging.info("Added person: " + result_json)
		return True


if __name__ == "__main__":
	reload(sys)  
	sys.setdefaultencoding('utf8')
	ImportScoutnetAsCSV()
