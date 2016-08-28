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

def unicode_csv_reader(utf8_data):
	csv_reader = ucsv.reader(utf8_data, delimiter=',', quoting=ucsv.QUOTE_ALL)
	for row in csv_reader:
		yield [cell for cell in row]

def GetScoutnetMembersCSVData(username, password, groupid='1137'):
	payload = {'signin[username]': username, 'signin[password]': password}

	cj = cookielib.CookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
	urllib2.install_opener(opener)

	data = urllib.urlencode(payload)
	header = {"User-Agent", "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36"}
	req = urllib2.Request('https://www.scoutnet.se/login')
	req.add_data(data)
	print("Login request")
	response = urllib2.urlopen(req)
	print("after urlopen, response=%s", response)
	req2 = urllib2.Request('https://www.scoutnet.se/reports/groups/members/group_id/' + groupid + '/download/true/format/csv')
	response = urllib2.urlopen(req2)
	return response.read()
	
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

			#logging.info("fields %d, %d, %d, %d, %d, %d, %d, %d", inr,ifname,ilname,ipnummer,isgroup,itroop,ipatrool,isex)
			if (inr+1) * ifname * ilname * ipnummer * isgroup * itroop * ipatrool * isex * iaktiv == 0:
				logging.error("missing some field %d, %d, %d, %d, %d, %d, %d, %d, %d", inr,ifname,ilname,ipnummer,isgroup,itroop,ipatrool,isex,iaktiv)
				raise ValueError('Missing some field')
		else:
			m = {}
			m["group"] = row[isgroup]
			m["troop"] = row[itroop]
			m["id"] = row[inr]
			m["firstname"] = row[ifname]
			m["lastname"] = row[ilname]
			m["personnr"] = row[ipnummer]
			m["female"] = row[isex]!='Man'
			m["patrool"] = row[ipatrool]
			m["active"] = row[iaktiv] == "Aktiv"
			result.append(m)

	return result

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
