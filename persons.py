# -*- coding: utf-8 -*-
import scoutnet
from dataimport import UserPrefs, ndb, Person, logging, TroopPerson, ScoutGroup

from flask import Blueprint, render_template, abort, redirect, request

persons = Blueprint('persons_page', __name__, template_folder='templates')

@persons.route('/')
@persons.route('/<sgroup_url>')
@persons.route('/<sgroup_url>/')
@persons.route('/<sgroup_url>/<person_url>')
@persons.route('/<sgroup_url>/<person_url>/')
@persons.route('/<sgroup_url>/<person_url>/<action>')
def show(sgroup_url=None, person_url=None, action=None):
	user = UserPrefs.current()
	if not user.hasAccess():
		return "denied", 403

	breadcrumbs = [{'link':'/', 'text':'Hem'}]
	
	section_title = u'Personer'
	breadcrumbs.append({'link':'/persons', 'text':section_title})
	baselink='/persons/'

	scoutgroup = None
	if sgroup_url!=None:
		sgroup_key = ndb.Key(urlsafe=sgroup_url)
		scoutgroup = sgroup_key.get()
		baselink+=sgroup_url+"/"
		breadcrumbs.append({'link':baselink, 'text':scoutgroup.getname()})

	person = None
	if person_url!=None:
		person_key = ndb.Key(urlsafe=person_url)
		person = person_key.get()
		baselink+=person_url+"/"
		section_title = person.getname()
		breadcrumbs.append({'link':baselink, 'text':section_title})
	
	if action != None:
		if action == "deleteperson" or action == "addbackperson":
			person.removed = action == "deleteperson"
			person.put() # we only mark the person as removed
			if person.removed:
				tps = TroopPerson.query(TroopPerson.person == person.key).fetch()
				for tp in tps:
					tp.delete()
			return redirect(breadcrumbs[-1]['link'])
		elif action == "removefromtroop" or action == "setasleader" or action == "removeasleader":
			troop_key = ndb.Key(urlsafe=request.args["troop"])
			tps = TroopPerson.query(TroopPerson.person == person.key, TroopPerson.troop == troop_key).fetch(1)
			if len(tps) == 1:
				tp = tps[0]
				if action == "removefromtroop":
					tp.delete()
				else:
					tp.leader = (action == "setasleader")
					tp.put()
		elif action == "addtowaitinglist":
			scoutgroup = person.scoutgroup.get()
			troop = None
			tps = TroopPerson.query(TroopPerson.person == person.key).fetch(1)
			if len(tps) == 1:
				troop = tps[0].troop.get()
			scoutgroup = person.scoutgroup.get()
			if scoutgroup.canAddToWaitinglist():
				try:
					if scoutnet.AddPersonToWaitinglist(
							scoutgroup,
							person.firstname,
							person.lastname,
							person.personnr,
							person.email,
							person.street,
							person.zip_code,
							person.zip_name,
							person.phone,
							person.mobile,
							troop,
							"",
							"",
							"",
							"",
							"",
							"",
							"",
							""
					):
						person.notInScoutnet = False
						person.put()
				except scoutnet.ScoutnetException as e:
					return render_template('error.html', error=str(e))
		else:
			logging.error('unknown action=' + action)
			abort(404)
			return ""
		
	# render main pages
	if scoutgroup==None:
		return render_template('index.html', 
			heading=section_title, 
			baselink=baselink,
			items=ScoutGroup.getgroupsforuser(user),
			breadcrumbs=breadcrumbs,
			username=user.getname())
	elif person==None:
		section_title = 'Personer'
		return render_template('persons.html',
			heading=section_title,
			baselink=baselink,
			persons=Person.query(Person.scoutgroup == sgroup_key).order(Person.firstname, Person.lastname).fetch(), # TODO: memcache
			breadcrumbs=breadcrumbs,
			username=user.getname())
	else:
		return render_template('person.html',
			heading=section_title,
			baselink='/persons/' + scoutgroup.key.urlsafe() + '/',
			trooppersons=TroopPerson.query(TroopPerson.person == person.key).fetch(), # TODO: memcache
			ep=person,
			scoutgroup=scoutgroup,
			breadcrumbs=breadcrumbs)
