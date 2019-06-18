# -*- coding: utf-8 -*-
from dataimport import UserPrefs, ndb, logging, Semester
from imports import startAsyncImport

from flask import Blueprint, render_template, redirect, request

scoutgroupinfo = Blueprint('scoutgroupinfo_page', __name__, template_folder='templates')

@scoutgroupinfo.route('/<sgroup_url>')
@scoutgroupinfo.route('/<sgroup_url>/', methods = ['POST', 'GET'])
def show(sgroup_url):
	user = UserPrefs.current()
	if not user.canImport():
		return "denied", 403
	breadcrumbs = [{'link':'/', 'text':'Hem'}]
	baselink = "/scoutgroupinfo/"
	section_title = "Kårinformation"
	scoutgroup = None
	if sgroup_url!=None:
		sgroup_key = ndb.Key(urlsafe=sgroup_url)
		scoutgroup = sgroup_key.get()
		baselink += sgroup_url+"/"
		breadcrumbs.append({'link':baselink, 'text':scoutgroup.getname()})
	if request.method == "POST":
		logging.info("POST, %s" % str(request.form))
		scoutgroup.organisationsnummer = request.form['organisationsnummer'].strip()
		scoutgroup.foreningsID = request.form['foreningsID'].strip()
		scoutgroup.scoutnetID = request.form['scoutnetID'].strip()
		scoutgroup.kommunID = request.form['kommunID'].strip()
		scoutgroup.apikey_waitinglist = request.form['apikey_waitinglist'].strip()
		scoutgroup.apikey_all_members = request.form['apikey_all_members'].strip()
		scoutgroup.bankkonto = request.form['bankkonto'].strip()
		scoutgroup.epost = request.form['epost'].strip()
		scoutgroup.telefon = request.form['telefon'].strip()
		scoutgroup.adress = request.form['adress'].strip()
		scoutgroup.postadress = request.form['postadress'].strip()
		scoutgroup.default_lagerplats = request.form['lagerplats'].strip()
		scoutgroup.put()
		if "import" in request.form:
			return startAsyncImport(scoutgroup.apikey_all_members, scoutgroup.scoutnetID, Semester.getOrCreateCurrent().key, user, request)
		else:
			return redirect(breadcrumbs[-1]['link'])
	else:
		return render_template('scoutgroupinfo.html',
			heading=section_title,
			baselink=baselink,
			scoutgroup=scoutgroup,
			breadcrumbs=breadcrumbs)
