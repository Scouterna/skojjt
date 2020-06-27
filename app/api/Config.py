import os
from auth.XOrigin import XOrigin
from db import db
from datetime import datetime


class ConfigResource(XOrigin):
    def get(self):
        karer = {}
        for kar in db['kar_names'].find():
            karer[kar['_id']] = kar['name']
        semesters = {}
        time = datetime.now()
        for year in range(2018, time.year):
            year_str = str(year)
            semesters[year_str + '01'] = 'VT-' + year_str
            semesters[year_str + '07'] = 'HT-' + year_str
        year_str = str(time.year)
        semesters[year_str + '01'] = 'VT-' + year_str
        if time.month > 6:
            semesters[year_str + '07'] = 'HT-' + year_str
        return {'ok': True, 'jwturl': os.getenv('JWT_URL'), 'karer': karer, 'semesters': semesters}
