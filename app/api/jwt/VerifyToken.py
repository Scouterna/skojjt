from flask import request
from flask_restful import Resource
import jwt

from auth.Auth import Auth


class VerifyToken(Resource):
    @staticmethod
    def error(msg, data=None):
        return {
                   "user": False,
                   "admin": False,
                   "data": data,
                   "error": msg
               }

    # fetch("/api/jwt/verify_token", {headers: {Authorization: 'Bearer ' + localStorage.getItem('ScoutID-JWT-Token')}})
    def get(self):
        if "Authorization" not in request.headers:
            return self.error("Authorization header is missing"), 403

        auth_header = request.headers["Authorization"]

        if auth_header[0:7] != "Bearer ":
            return self.error("Authorization header is not Bearer type"), 403

        try:
            auth = Auth(auth_header[7:])
        except jwt.ExpiredSignatureError:
            return self.error("Token Expired"), 498
        except jwt.DecodeError as e:
            return self.error("Failed to decode JWT, " + str(e)), 403
        except jwt.InvalidTokenError as e:
            return self.error("Invalid JWT-token, " + str(e)), 403
        except Exception as e:
            return self.error("Failed to decode JWT, unknown Exception: " + str(type(e)) + " -> " + str(e)), 403

        admin = "roles" in auth.payload and "organisation:692:scoutid_admin" in auth.payload["roles"]

        return {
                   "user": auth.user_id,
                   "admin": admin,
                   "data": auth.payload,
               }
