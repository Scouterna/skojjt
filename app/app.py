from flask import Flask, redirect
from flask_restful import Resource, Api

from api.Config import ConfigResource
from api.DbTest import DbTest
from api.jwt.VerifyToken import VerifyToken

app = Flask(__name__)
api = Api(app)

api.add_resource(ConfigResource, '/api/config')
api.add_resource(DbTest, '/api/dbtest')
api.add_resource(VerifyToken, '/api/jwt/verify_token')

# if we are not logged in, we make a fake saml-session, that end at /saml, so accept and ignore it, and return to /
@app.route('/saml')
def samlRedirect():
    return redirect('/');
