# -*- coding: utf-8 -*-
import os
from urlparse import urlparse

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils

from flask import Blueprint, redirect, request, session

scoutid = Blueprint('scoutid', __name__)


def scoutid_init_saml_auth(req):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saml')
    auth = OneLogin_Saml2_Auth(req, custom_base_path=path)
    return auth


def scoutid_prepare_flask_request(request):
    # If server is behind proxys or balancers use the HTTP_X_FORWARDED fields
    url_data = urlparse(request.url)
    return {
        'https': 'on' if request.scheme == 'https' else 'off',
        'http_host': request.host,
        'server_port': url_data.port,
        'script_name': request.path,
        'get_data': request.args.copy(),
        'post_data': request.form.copy()
    }


@scoutid.route('/')
def scoutid():
    req = scoutid_prepare_flask_request(request)
    auth = scoutid_init_saml_auth(req)
    return redirect(auth.login())


@scoutid.route('/acs')
@scoutid.route('/acs/')
def scoutid_asc():
    req = scoutid_prepare_flask_request(request)
    auth = scoutid_init_saml_auth(req)
    auth.process_response()
    errors = auth.get_errors()
    if len(errors) > 0:
        return redirect('/')
    session['samlUserdata'] = auth.get_attributes()
    session['samlNameId'] = auth.get_nameid()
    session['samlNameIdFormat'] = auth.get_nameid_format()
    session['samlNameIdNameQualifier'] = auth.get_nameid_nq()
    session['samlNameIdSPNameQualifier'] = auth.get_nameid_spnq()
    session['samlSessionIndex'] = auth.get_session_index()
    self_url = OneLogin_Saml2_Utils.get_self_url(req)
    if 'RelayState' in request.form and self_url != request.form['RelayState']:
        return redirect(auth.redirect_to(request.form['RelayState']))
    return redirect('/')


@scoutid.route('/sls')
@scoutid.route('/sls/')
def scoutid_sls():
    req = scoutid_prepare_flask_request(request)
    auth = scoutid_init_saml_auth(req)
    url = auth.process_slo(delete_session_cb=lambda: session.clear())
    return redirect(url)
