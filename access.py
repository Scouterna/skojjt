import logging
from data import UserPrefs
from flask import request, render_template, redirect
from functools import wraps
import google.auth.transport.requests
import google.oauth2.id_token
import requests_toolbelt.adapters.appengine
import os
from firebase_admin import auth

# Use the App Engine Requests adapter. This makes sure that Requests uses
# URLFetch.
requests_toolbelt.adapters.appengine.monkeypatch()
HTTP_REQUEST = google.auth.transport.requests.Request()


# decorators for access
def hasAccess(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(str(request.headers))
        session_cookie = request.cookies.get('session')
        if not session_cookie:
            return redirect('/login/')
        else:
            logging.info("*** session_cookie=" + session_cookie)
            decoded_claims = auth.verify_session_cookie(session_cookie, check_revoked=True)
            # claims = google.oauth2.id_token.verify_firebase_token(id_token, HTTP_REQUEST, audience=os.environ.get('GOOGLE_CLOUD_PROJECT'))
            if decoded_claims:
                return func(*args, **kwargs)

        return redirect('/login/')

    return wrapper


"""
def hasAccess(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = UserPrefs.current()
        if not user.hasAccess():
            return "denied", 403
        return func(*args, **kwargs)
    return wrapper
"""

def canImport(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = UserPrefs.current()
        if not user.canImport():
            return "denied", 403
        return func(*args, **kwargs)
    return wrapper


def isAdmin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = UserPrefs.current()
        if not user.isAdmin():
            return "denied", 403
        return func(*args, **kwargs)
    return wrapper

