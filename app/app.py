from flask import redirect
from init import app, api
from api.Config import ConfigResource
from api.DbTest import DbTest
from api.jwt.VerifyToken import VerifyToken

api.add_resource(ConfigResource, '/api/config')
api.add_resource(DbTest, '/api/dbtest')
api.add_resource(VerifyToken, '/api/jwt/verify_token')

# if we are not logged in, we make a fake saml-session, that end at /saml, so accept and ignore it, and return to /
@app.route('/saml')
def samlRedirect():
    return redirect('/');
