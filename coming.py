# -*- coding: utf-8 -*-
from data import *
from flask import Flask, Blueprint, render_template, abort, redirect, url_for, request, make_response
import sys

coming_blueprint = Blueprint('coming', __name__, template_folder='templates')

@coming_blueprint.route('/<meeting_url>/<person_url>', methods = ['POST', 'GET'])
@coming_blueprint.route('/<meeting_url>/<person_url>/', methods = ['POST', 'GET'])
def coming(meeting_url, person_url):
	comment = request.form.get("comment")
	if request.method == "POST":
		comment = request.form.get('coming')

	return render_template("coming.html", yes=True, no=False, comment=comment)
