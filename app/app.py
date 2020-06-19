from flask import Flask
from flask_restful import Resource, Api

from api.DbTest import DbTest

app = Flask(__name__)
api = Api(app)

api.add_resource(DbTest, '/api/dbtest')


class Ping(Resource):
    def get(self):
        return {'ping': 'pong'}


api.add_resource(Ping, '/ping')
