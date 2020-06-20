from flask import Flask
from flask_restful import Resource, Api

from api.DbTest import DbTest
from api.jwt.VerifyToken import VerifyToken

app = Flask(__name__)
api = Api(app)

api.add_resource(DbTest, '/api/dbtest')
api.add_resource(VerifyToken, '/api/jwt/verify_token')


class Ping(Resource):
    def get(self):
        return {'ping': 'pong'}


api.add_resource(Ping, '/ping')
