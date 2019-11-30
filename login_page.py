from flask import Blueprint, render_template, request, make_response, redirect
from google.appengine.api import users

login_page = Blueprint('login_page', __name__, template_folder='templates')


def login():
    google_url = users.CreateLoginURL('/')
    scoutid_url = '/scoutid/'
    return render_template(
        'login.html',
        title='Skojjt - Login',
        google_url=google_url,
        scoutid_url=scoutid_url
    );
