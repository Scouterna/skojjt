# -*- coding: utf-8 -*-
import json
import unittest
from dakdata import DakData, Deltagare, Sammankomst
from ireport import IReport


class JsonReport(IReport):
    def __init__(self, dak, semester):
        self.dak = dak
        self.semester = semester

    def GetUrlName(self):
        return "json"

    def GetMimeType(self):
        return "text/json"

    def GetBinaryStream(self):
        return self.getJson()

    def GetFilename(self):
        return str(self.dak.kort.NamnPaaKort) + '-' + self.semester.getname() + '.json'

    def getJson(self):
        return json.dumps(self.dak.__dict__)


class TestJsonReport(unittest.TestCase):
    def createDakData(self):
        dak = DakData()
        dak.foereningsNamn = u"Test Scoutkår"
        dak.foreningsID = "1111"
        dak.organisationsnummer = "556677-8899"
        dak.kommunID = "0"
        dak.kort.NamnPaaKort = "Testavdelning"
        dak.kort.NaervarokortNummer = "1"
        
        dak.kort.ledare.append(Deltagare("1", "Adam", "Adamsson", "200501011234", True, "adam@test.com", "12345678", u"Göteborg"))
        dak.kort.deltagare.append(Deltagare("2", "Bertil", "Bertilsson", "198501011234", False, "bertil@test.com", "12345678", u"Göteborg"))
        sammankomst = Sammankomst(u"123", datetime.date(2019, 1, 1), 180, u"Möte")
        sammankomst.ledare.append(dak.kort.ledare[0])
        sammankomst.deltagare.append(dak.kort.deltagare[0])   
        dak.kort.Sammankomster.append(sammankomst)
        return dak

    def test(self):
        dak = self.createDakData()
        semester = Semester(2019, false) # 2019, vt
        jsonReport = JsonReport(dak, semester)
        data = json.loads(jsonReport)
        
        self.assertEqual(data.dak.foereningsNamn, u"Test Scoutkår")

if __name__ == '__main__':
    unittest.main()