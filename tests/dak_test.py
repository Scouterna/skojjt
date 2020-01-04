# -*- coding: utf-8 -*-
"""
Tests of DAK handling.
"""
import sys
import shutil
import time
import os
import json
import unittest
import datetime
import xmlschema
from flask import Flask, render_template
sys.path.append('../lib') # add lib to path for unit-testing
sys.path.append('..') # add lib to path for unit-testing
from jsonreport import JsonReport # pylint: disable=wrong-import-position
from dakdata import DakData, Deltagare, Sammankomst # pylint: disable=wrong-import-position

class XmlValidator(object):
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
    dak.kort.ledare.append(Deltagare("1234", "Adam", "Adamsson", u"200501011234", True, "adam@test.com", "12345678", u"Göteborg"))
    dak.kort.deltagare.append(Deltagare("1235", "Bertil", "Bertilsson", u"198501011234", False, "bertil@test.com", "12345678", u"Göteborg"))
    dak.kort.deltagare.append(Deltagare("1236", "Ada", "Adasson", u"198601011234", False, "ada@test.com", "12345679", u"Göteborg"))
    dak.kort.deltagare.append(Deltagare("1237", "Ceda", "Cedasson", u"198701011234", False, "ada@test.com", "12345679", u"Göteborg"))

    sammankomst1 = Sammankomst(u"123", datetime.datetime(2019, 1, 1, 18, 30), 90, u"Möte")
    sammankomst1.ledare.append(dak.kort.ledare[0])
    sammankomst1.deltagare.append(dak.kort.deltagare[0])
    sammankomst1.deltagare.append(dak.kort.deltagare[1])
    sammankomst1.deltagare.append(dak.kort.deltagare[2])
    dak.kort.Sammankomster.append(sammankomst1)

    sammankomst2 = Sammankomst(u"123", datetime.datetime(2019, 1, 7, 18, 30), 90, u"Möte")
    sammankomst2.ledare.append(dak.kort.ledare[0])
    sammankomst2.deltagare.append(dak.kort.deltagare[0])
    sammankomst2.deltagare.append(dak.kort.deltagare[1])
    sammankomst2.deltagare.append(dak.kort.deltagare[2])
    dak.kort.Sammankomster.append(sammankomst2)
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

    def save_and_check(self, generated_data, expected_file, generated_file, force=False):
        "Save the data and read it back and check with expected file"
        expected_path = os.path.join(os.path.dirname(__file__), TestJsonReport.expectedDir, expected_file)
        generated_path = os.path.join(os.path.dirname(__file__), TestJsonReport.outputDir, generated_file)

        with open(generated_path, "w") as filep:
            filep.write(generated_data)

        self.validate.validate(generated_path)

        if force:
            shutil.copyfile(generated_path, expected_path)

        with open(expected_path, "r") as filep:
            expected_text = filep.read()

        with open(generated_path, "r") as filep:
            generated_text = filep.read()

        self.assertEqual(expected_text, generated_text)

        os.remove(generated_path)

    def setUp(self):
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

    def test_dak_json_export(self):
        "Test json report of DAK data"
        dak = create_dak_data()
        #semester = Semester(2019, false) # 2019, vt
        semester = None
        jsonreport = JsonReport(dak, semester)
        stream = jsonreport.get_report_string()
        data = json.loads(stream)

        self.assertEqual(data[u'foerenings_namn'], u"Test Scoutkår")
        self.assertEqual(data[u'forenings_id'], u"1111")
        self.assertEqual(data[u'kort'][u'namn_paa_kort'], "Testavdelning")
        self.assertEqual(data[u'kort'][u'Sammankomster'][0]['deltagare'][0]['uid'], "1235")
        self.assertEqual(data[u'kort'][u'Sammankomster'][0]['deltagare'][1]['uid'], "1236")
        self.assertEqual(data[u'kort'][u'Sammankomster'][0]['ledare'][0]['uid'], "1234")
        self.assertEqual(data[u'kort'][u'naervarokort_nummer'], "1")

    def test_dak_xml_export(self):
        "Test XML report of DAK data"
        response = self.client.get('/')
        self.save_and_check(response.data, 'dak_export.xml', 'dak_export.xml', force=True)

if __name__ == '__main__':
    unittest.main()
