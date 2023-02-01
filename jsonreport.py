# -*- coding: utf-8 -*-
import jsonpickle
from ireport import IReport

class JsonReport(IReport):
    def __init__(self, dak, semester):
        super(JsonReport, self).__init__(dak, semester)
        self.dak = dak
        self.semester = semester

    def get_url_name(self):
        return "json"

    def get_mime_type(self):
        return "text/json"

    def get_report_string(self):
        return self.get_json()

    def get_filename(self):
        return str(self.dak.kort.namn_paa_kort) + '-' + self.semester.getname() + '.json'

    def get_json(self, unpicklable=True, warn=False):
        return jsonpickle.encode(self.dak, unpicklable=unpicklable, warn=warn)
