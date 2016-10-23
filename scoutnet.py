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
	req2 = urllib2.Request('https://www.scoutnet.se/api/group/memberlist?id=' + groupid + '&key=' + api_key)
	response = urllib2.urlopen(req2)
	return response.read()
	
def GetValueFromJsonObject(p, key):
	if key in p:
		return p[key]['value']
	return ''
	
def GetScoutnetDataListJson(json_data):
	j = json.loads(json_data)
	result = []
	for pid in j['data']:
		p = j['data'][pid]
		m = {}
		m["group"] = GetValueFromJsonObject(p, 'group')
		m["troop"] = GetValueFromJsonObject(p, 'unit')
		m["id"] = int(pid) # must be int
		m["firstname"] = GetValueFromJsonObject(p, 'first_name')
		m["lastname"] = GetValueFromJsonObject(p, 'last_name')
		m["personnr"] = GetValueFromJsonObject(p, 'ssno')
		m["female"] = GetValueFromJsonObject(p, 'sex') != 'Man'
		m["patrool"] = GetValueFromJsonObject(p, 'patrol')
		m["active"] = GetValueFromJsonObject(p, 'status') == 'Aktiv'
		m["email"] = GetValueFromJsonObject(p, 'email')
		phone = FixCountryPrefix(GetValueFromJsonObject(p, 'contact_home_phone'))
		if phone == "":
			phone = FixCountryPrefix(GetValueFromJsonObject(p, 'contact_telephone_home')) # scoutnet has both "Telefon hem" and "Hemtelefon" pick one!
		m["phone"] = phone
		m["mobile"] = FixCountryPrefix(GetValueFromJsonObject(p, 'contact_mobile_phone'))
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

if __name__ == "__main__":
	reload(sys)  
	sys.setdefaultencoding('utf8')
	ImportScoutnetAsCSV()
