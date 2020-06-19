from flask_restful import Resource

class DbTest(Resource):
    def get(self):
        # TODO: connect to database
        return {'ok': 'false'}
