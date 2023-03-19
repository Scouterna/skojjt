# -*- coding: utf-8 -*-
import datetime
from google.appengine.api import memcache
from flask import Blueprint, render_template, request, make_response
import urllib.parse
import json
import logging
import pickle
import base64



progress = Blueprint('progress_page', __name__, template_folder='templates')


class TaskProgress():
    pass

class TaskProgressKey():
    def __init__(self, taskProgress):
        self.taskProgress = taskProgress

    def urlsafe(self):
        return self.taskProgress.urlsafe()

class TaskProgress():
    def __init__(self, name, return_url):
        self.created = datetime.datetime.now()
        self.name = name
        self.return_url = return_url
        self.messages = []
        self.key = self
        self.failed = False
        self.completed = None
        logging.info(f"adding new taskProgress={self.urlsafe()} to memcache")
        memcache.add(self.urlsafe(), base64.b64encode(pickle.dumps(self)))
        logging.info(f"added new taskProgress={self.urlsafe()} to memcache")


    def urlsafe(self):
        return urllib.parse.quote(self.name + self.created.strftime("_%Y%m%d%H%M%S%f"))

    @staticmethod
    def getTaskProgress(url_safe):
        if isinstance(url_safe, TaskProgressKey):
            return url_safe.taskProgress
        if isinstance(url_safe, TaskProgress):
            return url_safe
        logging.info(f"getting url_safe={url_safe} from memcache")
        encodedTaskProgress = memcache.get(url_safe)
        if encodedTaskProgress:
            return pickle.loads(base64.b64decode(encodedTaskProgress))
        logging.warning(f"not found url_safe={url_safe} in memcache")
        return None

    def append(self, message):
        self.messages.append(message)
        logging.info(f"appending={self.urlsafe()} to memcache")
        memcache.replace(self.urlsafe(), base64.b64encode(pickle.dumps(self)))
        logging.info(f"append={self.urlsafe()} to memcache")


    def info(self, message):
        self.append(message)

    def warning(self, message):
        self.append('Warning:' + message)

    def error(self, message):
        self.failed = True
        self.append('Error:' + message)
        logging.error(message)

    def done(self):
        self.completed = datetime.datetime.now()
        memcache.replace(self.urlsafe(), base64.b64encode(pickle.dumps(self)))

    def isRunning(self):
        return self.completed is None

    def put(self):
        pass

    @staticmethod
    def cleanup():
        pass

    def toJson(self, cursor=None):
        BATCH_SIZE = 20
        more = True
        start_index = 0
        if cursor is not None:
            start_index = int(cursor)
        
        messages = self.messages[start_index:]
        cursor = len(self.messages)

        return '{"datetime": "' + self.created.strftime("%Y%m%d%H%M")+ '",' + \
            '"name": "' + self.name + '",' + \
            '"return_url":"' + self.return_url + '",' + \
            '"messages":' + json.dumps(messages) + ',' + \
            '"failed":' + json.dumps(self.failed) + ',' + \
            '"running":' + json.dumps(self.isRunning()) + ',' + \
            '"cursor":"' + str(cursor) + '"}'



@progress.route('/<progress_url>')
@progress.route('/<progress_url>/')
@progress.route('/<progress_url>/<update>')
@progress.route('/<progress_url>/<update>/')
def getProgress(progress_url, update=None):
    logging.info(f"getProgress: progress_url={progress_url}, update={update}")
    taskProgress = TaskProgress.getTaskProgress(progress_url)
    logging.info(f"getProgress: taskProgress={taskProgress.urlsafe()}")

    if update is not None:
        if taskProgress is not None:
            urlsafeCursor = request.args["cursor"] if "cursor" in request.args else ''
            cursor = urlsafeCursor if urlsafeCursor else None # note: empty strings are "Falsy"
            s = taskProgress.toJson(cursor)
        else:
            s = '{"messages": ["Error: Hittar inte uppgiften"], "failed": "true", "running": "false"}'

        response = make_response(s)
        response.headers['Content-Type'] = 'application/json'
        return response

    if taskProgress is not None:
        breadcrumbs = [{'link':'/', 'text':'Hem'}, {'link':taskProgress.return_url, 'text':'Tillbaka'}]
        return render_template('progressreport.html', tabletitle=taskProgress.name, rowtitle='Result', breadcrumbs=breadcrumbs, return_url=taskProgress.return_url)
    else:
        breadcrumbs = [{'link':'/', 'text':'Hem'}, {'link':'', 'text':'Tillbaka'}]
        return render_template('progressreport.html', tabletitle='<raderad>', rowtitle='Result', breadcrumbs=breadcrumbs, return_url='')

