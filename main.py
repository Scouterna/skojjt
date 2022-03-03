# -*- coding: utf-8 -*-
import requests_toolbelt.adapters.appengine
requests_toolbelt.adapters.appengine.monkeypatch()
from firebase_admin import auth
from firebase_admin import exceptions
from firebase_admin import initialize_app
import logging
import sys
from data import ScoutGroup, UserPrefs
import access
from badges import badges
from flask import Flask, redirect, render_template, request, jsonify, abort
from datetime import datetime, timedelta
from google.appengine.api import users
from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.ext import ndb

#HTTP_REQUEST = google.auth.transport.requests.Request()


app = Flask(__name__)
app.debug = True
firebase_default_app = initialize_app()

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.

reload(sys)
sys.setdefaultencoding('utf8')



# page routes:
from groupsummary import groupsummary
from persons import persons
from scoutgroupinfo import scoutgroupinfo
from start import start
from imports import import_page
from progress import progress
from admin import admin
from tasks import tasks
from terminsprogram import terminsprogram
app.register_blueprint(start, url_prefix='/start')
app.register_blueprint(persons, url_prefix='/persons')
app.register_blueprint(scoutgroupinfo, url_prefix='/scoutgroupinfo')
app.register_blueprint(groupsummary, url_prefix='/groupsummary')
app.register_blueprint(import_page, url_prefix='/import')
app.register_blueprint(progress, url_prefix='/progress')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(tasks, url_prefix='/tasks')
app.register_blueprint(badges, url_prefix='/badges')
app.register_blueprint(terminsprogram, url_prefix='/terminsprogram')

@app.route('/login')
@app.route('/login/')
def login_():
    return render_template('login.html') 

@app.route('/')
@access.hasAccess
def home_():
    breadcrumbs = [{'link':'/', 'text':'Hem'}]
    return render_template('start.html',
                           heading='Hem',
                           items=[],
                           breadcrumbs=breadcrumbs,
                           user=None,
                           starturl="starturl",
                           personsurl="personsurl",
                           badgesurl="badgesurl",
                           logouturl=users.create_logout_url('/')
                           ) 


@app.route('/sessionLogin', methods=['POST'])
def session_login():
    # Get the ID token sent by the client
    id_token = request.json['idToken']
    logging.info("id_token=" + id_token)

    # Set session expiration to 5 days.
    expires_in = timedelta(days=5)
    #try:
    # Create the session cookie. This will also verify the ID token in the process.
    # The session cookie will have the same claims as the ID token.
    session_cookie = auth.create_session_cookie(id_token, expires_in=expires_in, app=firebase_default_app)
    response = jsonify({'status': 'success'})
    # Set cookie policy for session cookie.
    expires = datetime.now() + expires_in
    response.set_cookie('session', session_cookie, expires=expires, httponly=True, secure=True)
    return response
    #except exceptions.FirebaseError as ex:
    #    return abort(401, 'Failed to create a session cookie, error=' + str(ex))


@app.route('/loggedIn')
def loggedIn():
    return "You are logged in!"


@app.route('/asdsa')
@access.hasAccess
def home():
    breadcrumbs = [{'link':'/', 'text':'Hem'}]
    user = UserPrefs.current()
    user.attemptAutoGroupAccess()
    starturl = '/start/'
    personsurl = '/persons/'
    badgesurl = '/badges/'
    if user.groupaccess != None:
        starturl += user.groupaccess.urlsafe() + '/'
        personsurl += user.groupaccess.urlsafe() + '/'
        badgesurl += user.groupaccess.urlsafe() + '/'
    return render_template('start.html',
                           heading='Hem',
                           items=[],
                           breadcrumbs=breadcrumbs,
                           user=user,
                           starturl=starturl,
                           personsurl=personsurl,
                           badgesurl=badgesurl,
                           logouturl=users.create_logout_url('/')
                           )


@app.route('/getaccess/', methods = ['POST', 'GET'])
def getaccess():
    user = UserPrefs.current()
    breadcrumbs = [{'link':'/', 'text':'Hem'}]
    baselink = "/getaccess/"
    section_title = "Access"
    breadcrumbs.append({'link':baselink, 'text':section_title})
    if request.method == "POST":

        # anti-spam protection, the user can only ask once.
        user_request_access_key = "request_access_" + user.getemail()
        if memcache.get(user_request_access_key) is not None:
            logging.warning("User is spamming req-access:" + user.getemail())
            return "denied", 403
        memcache.add(user_request_access_key, True)

        sgroup = None
        if len(request.form.get('scoutgroup')) != 0:
            sgroup = ndb.Key(urlsafe=request.form.get('scoutgroup')).get()

        if sgroup is not None:
            groupAdminEmails = UserPrefs.getAllGroupAdminEmails(sgroup.key)
            if len(groupAdminEmails) > 0:
                mail.send_mail(
                    sender="noreply@skojjt.appspotmail.com",
                    to=','.join(groupAdminEmails),
                    subject=u"""Användaren: {} vill ha access till närvaroregistrering i Skojjt
                    för scoutkåren {}""".format(user.getemail(), sgroup.getname()),
                    body=u"""Gå till {} för att lägga till {}""".format(request.host_url + "groupaccess/", user.getname()))
        return redirect('/')
    else:
        return render_template('getaccess.html',
            baselink=baselink,
            breadcrumbs=breadcrumbs,
            scoutgroups=ScoutGroup.query().fetch())



@app.route('/groupaccess')
@app.route('/groupaccess/')
@app.route('/groupaccess/<userprefs_url>')
def groupaccess(userprefs_url=None):
    user = UserPrefs.current()
    if not user.isGroupAdmin() and user.groupaccess is None:
        return "denied", 403

    section_title = u'Hem'
    baselink = '/'
    breadcrumbs = [{'link':baselink, 'text':section_title}]

    section_title = u'Kåraccess'
    baselink += 'groupaccess/'
    breadcrumbs.append({'link':baselink, 'text':section_title})

    if userprefs_url != None:
        userprefs = ndb.Key(urlsafe=userprefs_url).get()
        groupaccessurl = request.args["setgroupaccess"]
        if groupaccessurl == 'None':
            userprefs.groupaccess = None
        else:
            userprefs.groupaccess = ndb.Key(urlsafe=groupaccessurl)
            userprefs.hasaccess = True
        userprefs.put()

    users = UserPrefs().query(UserPrefs.groupaccess == None).fetch()
    users.extend(UserPrefs().query(UserPrefs.groupaccess == user.groupaccess).fetch())
    return render_template('groupaccess.html',
        heading=section_title,
        baselink=baselink,
        users=users,
        breadcrumbs=breadcrumbs,
        mygroupurl=user.groupaccess.urlsafe(),
        mygroupname=user.groupaccess.get().getname())


@app.errorhandler(404)
def page_not_found(e):
    return render_template('notfound.html'), 404

@app.errorhandler(403)
def access_denied(e):
    return render_template('403.html'), 403

@app.errorhandler(401)
def unauthorized(e):
    return render_template('401.html'), 401

@app.errorhandler(500)
def serverError(e):
    logging.error("Error 500:%s", str(e))
    return render_template('error.html', error=str(e)), 500

#@app.errorhandler(Exception)
#def defaultHandler(e):
#    logging.error("Error:%s", str(e))
#    return render_template('error.html', error=str(e)), 500
