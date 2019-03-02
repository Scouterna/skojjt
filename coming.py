# -*- coding: utf-8 -*-
from data import *
from flask import Flask, Blueprint, render_template, abort, redirect, url_for, request, make_response
import sys

coming_blueprint = Blueprint('coming', __name__, template_folder='templates')

@coming_blueprint.route('/<meeting_url>/<person_url>', methods = ['POST', 'GET'])
@coming_blueprint.route('/<meeting_url>/<person_url>/', methods = ['POST', 'GET'])
def coming(meeting_url, person_url):
	comment = ""
	yes = False
	no = False
	if request.method == "POST":
		yes = request.form.get("coming") == "yes"
		no = request.form.get("coming") == "no"
		comment = request.form.get("comment")

	return render_template("coming.html", 
		meeting_title=r"Mötes titel", 
		meeting_date="2018-11-13 18:30-20:00",
		meeting_information=r"Vi ses utanför huset, tag med regnkläder och en varm tröja.",
		yes=yes, no=no, comment=comment)
