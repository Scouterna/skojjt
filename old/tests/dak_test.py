# -*- coding: utf-8 -*-
"""
Tests of DAK handling.
"""
import sys
import shutil
import time
import platform
import os
import json
import unittest
import datetime

# Disable all import warnings since the imports are pretty hacky
#pylint: disable=import-error,wrong-import-order,wrong-import-position
sys.path.append('../lib') # add lib to path for unit-testing
sys.path.append('..') # add parent to path for unit-testing
sys.path.append('./lib') # add lib to path for unit-testing
sys.path.append('.') # add current dir to path for unit-testing
import xmlschema
import jsonpickle
from openpyxl import load_workbook
from flask import Flask, render_template
from jsonreport import JsonReport
from dakdata import DakData, Deltagare, Sammankomst
if platform.system() == 'Windows':
    # Add app engine paths on windows.
    sys.path.append("C:/Program Files (x86)/Google/google_appengine")
    sys.path.append("C:/Program Files (x86)/Google/google_appengine/lib")
    sys.path.append("c:/Program Files (x86)/Google/google_appengine/google/appengine/api")
    sys.path.append("c:/Program Files (x86)/Google/google_appengine/google/appengine")
elif platform.system() == 'Darwin':  # i.e. MacOS
    BASE = "/usr/local/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/"
    sys.path.append(BASE + "platform/google_appengine/lib/fancy_urllib")
    sys.path.append(BASE + "platform/google_appengine/lib")
    sys.path.append(BASE + "platform/google_appengine/api")
    sys.path.append(BASE + "platform/google_appengine")
    sys.path.append(BASE + "lib/third_party")

from google.appengine.ext import ndb
from google.appengine.ext import testbed
from excelreport import ExcelReport
from data import Semester


class XmlValidator():
    "XML validation"
    def __init__(self, xsdPath):
        self.xmlschema = xmlschema.XMLSchema(xsdPath)

    def validate(self, xml):
        "Run the validator"
        self.xmlschema.validate(xml)

def create_dak_data():
    "Creates test DAK data"
    dak = DakData()
    dak.foerenings_namn = u"Test Scoutkår"
    dak.forenings_id = "1111"
    dak.organisationsnummer = "556677-8899"
    dak.kommun_id = "0"
    dak.kort.namn_paa_kort = "Testavdelning"
    dak.kort.naervarokort_nummer = "1"
    dak.kort.aktivitet = u'Moete'
    #
    dak.kort.ledare.append(Deltagare("1234", "Adam", "Adamsson", u"198501011234", True, "adam@test.com", "12345678", u"Göteborg"))
    dak.kort.deltagare.append(Deltagare("1235", "Bertil", "Bertilsson", u"200501011234", False, "bertil@test.com", "12345678", u"Göteborg"))
    dak.kort.deltagare.append(Deltagare("1236", "Ada", "Adasson", u"200601011244", False, "ada@test.com", "12345679", u"Göteborg"))
    dak.kort.deltagare.append(Deltagare("1237", "Ceda", "Cedasson", u"200701011244", False, "ada@test.com", "12345679", u"Göteborg"))

    sammankomst1 = Sammankomst(u"123", datetime.datetime(2019, 1, 1, 18, 30), 90, u"Möte")
    sammankomst1.ledare.append(dak.kort.ledare[0])
    sammankomst1.deltagare.append(dak.kort.deltagare[0])
    sammankomst1.deltagare.append(dak.kort.deltagare[1])
    sammankomst1.deltagare.append(dak.kort.deltagare[2])
    dak.kort.sammankomster.append(sammankomst1)

    sammankomst2 = Sammankomst(u"123", datetime.datetime(2019, 1, 7, 18, 30), 90, u"Möte")
    sammankomst2.ledare.append(dak.kort.ledare[0])
    sammankomst2.deltagare.append(dak.kort.deltagare[0])
    sammankomst2.deltagare.append(dak.kort.deltagare[1])
    sammankomst2.deltagare.append(dak.kort.deltagare[2])
    dak.kort.sammankomster.append(sammankomst2)

    sammankomst3 = Sammankomst(u"123", datetime.datetime(2019, 1, 14, 18, 30), 90, u"Möte")
    sammankomst3.ledare.append(dak.kort.ledare[0])
    sammankomst3.deltagare.append(dak.kort.deltagare[0])
    sammankomst3.deltagare.append(dak.kort.deltagare[2])
    dak.kort.sammankomster.append(sammankomst3)

    return dak

def create_flask_app(cfg=None):
    "Creates small app for the unit test"
    template_path = os.path.join(os.path.dirname(__file__), '..', 'templates')
    app = Flask(cfg, template_folder=template_path)
    # app.config['DEBUG'] = True
    # app.config['SERVER_NAME'] = 'localhost'
    return app


class TestJsonReport(unittest.TestCase):
    "DAK handling tests"

    outputDir = 'derived'
    expectedDir = 'expected'

    @classmethod
    def setUpClass(cls):
        output_dir_full = os.path.join(os.path.dirname(__file__), cls.outputDir)
        if not os.path.exists(output_dir_full):
            os.makedirs(output_dir_full)
            time.sleep(0.05)

    @classmethod
    def tearDownClass(cls):
        output_dir_full = os.path.join(os.path.dirname(__file__), cls.outputDir)
        os.rmdir(output_dir_full)

    def save_and_check(self, generated_data, expected_file, generated_file, check_xsd=False, force=False):
        "Save the data and read it back and check with expected file"
        expected_path = os.path.join(os.path.dirname(__file__), TestJsonReport.expectedDir, expected_file)
        generated_path = os.path.join(os.path.dirname(__file__), TestJsonReport.outputDir, generated_file)

        with open(generated_path, "wb") as filep:
            filep.write(generated_data)

        if check_xsd:
            self.validate.validate(generated_path)

        if force:
            shutil.copyfile(generated_path, expected_path)

        with open(expected_path, "rb") as filep:
            expected_text = filep.read()

        with open(generated_path, "rb") as filep:
            generated_text = filep.read()

        self.assertEqual(expected_text, generated_text)

        os.remove(generated_path)

    def setUp(self):
        # Google app engine testbed setup.
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        # Clear ndb's in-context cache between tests.
        # This prevents data from leaking between tests.
        # Alternatively, you could disable caching by
        # using ndb.get_context().set_cache_policy(False)
        ndb.get_context().clear_cache()

        # Flask app test setup.
        xsd_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'importSchema.xsd')
        self.validate = XmlValidator(xsd_path)
        self.dak = create_dak_data()
        self.app = create_flask_app('mytest')
        # self.app_context = self.app.app_context()
        # self.app_context.push()
        self.client = self.app.test_client()

        @self.app.route("/")
        def hello(): # pylint: disable=unused-variable
            return render_template('dak.xml', dak=self.dak)

    def tearDown(self):
        self.testbed.deactivate()

    def test_dak_json_export(self):
        "Test json report of DAK data"
        semester = Semester.create(2019, False) # 2019, vt
        jsonpickle.set_encoder_options('json', indent=4)
        jsonreport = JsonReport(self.dak, semester)
        stream = jsonreport.get_json(unpicklable=False, warn=True)
        data = json.loads(stream)

        self.assertEqual(data[u'foerenings_namn'], u"Test Scoutkår")
        self.assertEqual(data[u'forenings_id'], u"1111")
        self.assertEqual(data[u'kort'][u'namn_paa_kort'], "Testavdelning")
        self.assertEqual(data[u'kort'][u'sammankomster'][0]['deltagare'][0]['uid'], "1235")
        self.assertEqual(data[u'kort'][u'sammankomster'][0]['deltagare'][1]['uid'], "1236")
        self.assertEqual(data[u'kort'][u'sammankomster'][0]['ledare'][0]['uid'], "1234")
        self.assertEqual(data[u'kort'][u'naervarokort_nummer'], "1")
        self.save_and_check(stream, 'dak_json_export.json', 'dak_json_export.json')

        stream = jsonreport.get_report_string()
        data = jsonpickle.decode(stream)

        self.assertEqual(data.foerenings_namn, u"Test Scoutkår")
        self.assertEqual(data.forenings_id, u"1111")
        self.assertEqual(data.kort.namn_paa_kort, "Testavdelning")
        self.assertEqual(data.kort.sammankomster[0].deltagare[0].uid, "1235")
        self.assertEqual(data.kort.sammankomster[0].deltagare[1].uid, "1236")
        self.assertEqual(data.kort.sammankomster[0].ledare[0].uid, "1234")
        self.assertEqual(data.kort.naervarokort_nummer, "1")
        self.save_and_check(stream, 'dak_json_pickable_export.json', 'dak_json_pickable_export.json', force=True)

    def test_dak_xml_export(self):
        "Test XML report of DAK data"
        response = self.client.get('/')
        self.save_and_check(response.data, 'dak_xml_export.xml', 'dak_xml_export.xml', check_xsd=True)

    def test_dak_excel_export(self):
        "Test excel report of DAK data"
        current_semester = Semester.create(2019, False) # 2019, vt
        excel_report = ExcelReport(self.dak, current_semester)
        result_bytes = excel_report.getFilledInExcelSpreadsheet()

        generated_path = os.path.join(os.path.dirname(__file__), TestJsonReport.outputDir, 'dak_excel_export.xlsx')

        with open(generated_path, "wb") as filep:
            filep.write(result_bytes)

        workbook = load_workbook(generated_path)
        worksheets = workbook.worksheets[0]
        self.assertEqual(self.dak.kort.naervarokort_nummer, worksheets['E1'].value)
        self.assertEqual(current_semester.year, worksheets['I1'].value)
        self.assertEqual(self.dak.kort.namn_paa_kort, worksheets['D2'].value)
        self.assertEqual("Scouting", worksheets['D3'].value)
        self.assertEqual(self.dak.kort.lokal, worksheets['D4'].value)
        if current_semester.ht:
            self.assertEqual(worksheets['C6'].value, None)
            self.assertEqual(worksheets['C7'].value, 'X')
        else:
            self.assertEqual(worksheets['C6'].value, 'X')
            self.assertEqual(worksheets['C7'].value, None)

        row = 13
        for deltagaren in self.dak.kort.deltagare:
            self.assertEqual(deltagaren.foernamn + " " + deltagaren.efternamn, worksheets['B' + str(row)].value)
            self.assertEqual('K' if deltagaren.is_female() else 'M', worksheets['H' + str(row)].value)
            self.assertEqual(deltagaren.personnummer[0:8], worksheets['J' + str(row)].value)
            self.assertEqual(1, worksheets['K' + str(row)].value)
            self.assertEqual(1, worksheets['L' + str(row)].value)
            row += 1
        self.assertEqual(1, worksheets['M13'].value)
        self.assertEqual(None, worksheets['M14'].value)
        self.assertEqual(1, worksheets['M15'].value)

        os.remove(generated_path)


if __name__ == '__main__':
    unittest.main()
