from data import Meeting, ScoutGroup, Semester, Troop
from flask import Blueprint, render_template, make_response
from google.appengine.api import memcache
from google.appengine.ext import ndb
import urllib.parse

terminsprogram = Blueprint('terminsprogram', __name__, template_folder='templates')

@terminsprogram.route('/<troop_url>.<filetype>', methods=['GET'])
def show(troop_url, filetype):
    troop = None
    semester = None
    scoutgroup = None
    if troop_url is not None:
        troop_key = ndb.Key(urlsafe=troop_url)
        troop = troop_key.get()
        semester = troop.semester_key.get()
        scoutgroup = troop.scoutgroup.get()

    meetings = Meeting.query(Meeting.troop==troop.key).fetch()

    title = "Terminsprogram - " + semester.getname() + " - " + troop.getname() + " - " + scoutgroup.getname()
    filename = title + "." + filetype
    if filetype=="html":
        return render_template('terminsprogram.html', heading=title, title=title, meetings=meetings)
    elif filetype=="xml":
        xml =  '<?xml version="1.0" encoding="utf-8"?>\r\n'
        xml += '<terminsprogram semester="' + semester.getname() + '" troop="' + troop.getname() + '" scoutgroup="' + scoutgroup.getname() + '">\r\n'
        xml += '<meetings>\r\n'
        for meeting in meetings:
            xml += '<meeting name="' + meeting.getname() + '" date="' + meeting.getdate() + '" time="' + meeting.gettime() + '" endtime="' + meeting.getendtime() + '"/>\r\n'
        xml += '</meetings>\r\n'
        xml += '</terminsprogram>\r\n'
        response = make_response(xml)
        response.headers['Content-Type'] = 'application/xml'
        response.headers['Content-Disposition'] = 'attachment; filename=' + urllib.parse.quote(str(filename), safe='')
        return response
    elif filetype=="json":
        json = "{"
        json += '"semester":"' + semester.getname() + '", "troop":"' + troop.getname() + '", "scoutgroup=":"' + scoutgroup.getname() + '",\r\n'
        json += '"meetings":[\r\n'
        first = True
        for meeting in meetings:
            if not first: json += ",\r\n"
            json += '{"name":"' + meeting.getname() + '", "date":"' + meeting.getdate() + '", "time":"' + meeting.gettime() + '", "endtime":"' + meeting.getendtime() + '"}'
            first = False
        json += ']\r\n'
        json += "}"
        response = make_response(json)
        response.headers['Content-Type'] = 'text/json'
        response.headers['Content-Disposition'] = 'attachment; filename=' + urllib.parse.quote(str(filename), safe='')
        return response
    else:
        return "Unknown file format, html, xml or json is supported"

