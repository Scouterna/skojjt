from data import UserPrefs
from flask import request
from functools import wraps
import google.auth.transport.requests
import google.oauth2.id_token
import requests_toolbelt.adapters.appengine

# Use the App Engine Requests adapter. This makes sure that Requests uses
# URLFetch.
requests_toolbelt.adapters.appengine.monkeypatch()
HTTP_REQUEST = google.auth.transport.requests.Request()


# decorators for access
def hasAccess(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        id_token = request.headers['Authorization'].split(' ').pop()
        claims = google.oauth2.id_token.verify_firebase_token(
            id_token, HTTP_REQUEST, audience=os.environ.get('GOOGLE_CLOUD_PROJECT'))
        if not claims:
            return 'Unauthorized', 401

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

