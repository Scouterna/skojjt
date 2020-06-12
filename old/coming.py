# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request

coming_blueprint = Blueprint('coming', __name__, template_folder='templates')

@coming_blueprint.route('/<meeting_url>/<person_url>', methods = ['POST', 'GET'])
@coming_blueprint.route('/<meeting_url>/<person_url>/', methods = ['POST', 'GET'])
def coming(meeting_url, person_url):
    comment = request.form.get("comment")
    if request.method == "POST":
        comment = request.form.get('coming')

    return render_template("coming.html", yes=True, no=False, comment=comment)
