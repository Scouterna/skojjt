import os
from flask_restful import Resource


class ConfigResource(Resource):
    def get(self):
        return {"ok": True, "jwturl": os.getenv("JWT_URL")}
