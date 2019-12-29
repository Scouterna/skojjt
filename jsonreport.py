# -*- coding: utf-8 -*-

if __name__ == '__main__':
    import sys
    sys.path.append('lib') # add lib to path for unit-testing
    import json

import jsonpickle
import unittest
import datetime
from dakdata import DakData, Deltagare, Sammankomst
from ireport import IReport


class JsonReport(IReport):
    def __init__(self, dak, semester):
        self.dak = dak
        self.semester = semester

    def getUrlName(self):
        return "json"

    def getMimeType(self):
        return "text/json"

    def getReportString(self):
        return self.getJson()

    def getFilename(self):
        return str(self.dak.kort.NamnPaaKort) + '-' + self.semester.getname() + '.json'

    def getJson(self):
        return jsonpickle.encode(self.dak)


class TestJsonReport(unittest.TestCase):
    def createDakData(self):
        dak = DakData()
        dak.foereningsNamn = u"Test Scoutkår"
        dak.foreningsID = "1111"
        dak.organisationsnummer = "556677-8899"
        dak.kommunID = "0"
        dak.kort.NamnPaaKort = "Testavdelning"
        dak.kort.NaervarokortNummer = "1"
        #
        dak.kort.ledare.append(Deltagare("1234", "Adam", "Adamsson", "200501011234", True, "adam@test.com", "12345678", u"Göteborg"))
        dak.kort.deltagare.append(Deltagare("1235", "Bertil", "Bertilsson", "198501011234", False, "bertil@test.com", "12345678", u"Göteborg"))
        sammankomst = Sammankomst(u"123", datetime.date(2019, 1, 1), 180, u"Möte")
        sammankomst.ledare.append(dak.kort.ledare[0])
        sammankomst.deltagare.append(dak.kort.deltagare[0])   
        dak.kort.Sammankomster.append(sammankomst)
        return dak

    def test_dakexport(self):
        dak = self.createDakData()
        #semester = Semester(2019, false) # 2019, vt
        semester = None
        json_report = JsonReport(dak, semester)
        stream = json_report.getReportString()
        #print(stream)
        data = json.loads(stream)

        self.assertEqual(data[u'foereningsNamn'], u"Test Scoutkår")
        self.assertEqual(data[u'foreningsID'], u"1111")
        self.assertEqual(data[u'kort'][u'NamnPaaKort'], "Testavdelning")
        self.assertEqual(data[u'kort'][u'Sammankomster'][0]['deltagare'][0]['id'], "1235")
        self.assertEqual(data[u'kort'][u'Sammankomster'][0]['ledare'][0]['id'], "1234")


if __name__ == '__main__':
    unittest.main()
