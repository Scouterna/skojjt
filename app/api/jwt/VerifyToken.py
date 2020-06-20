import os
from flask import request
from flask_restful import Resource
from urllib.parse import urlparse
import jwt


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
            public_key = open(os.getenv("JWT_PUBLIC_KEY_FILE")).read()
        except Exception:
            return self.error("Public key for JWT is missing on server"), 500

        issuer = urlparse(os.getenv("JWT_URL")).hostname
        audience = os.getenv("HOST_NAME")

        try:
            payload = jwt.decode(auth_header[7:], public_key, algorithms=["RS256"], issuer=issuer, audience=audience)
        except jwt.ExpiredSignatureError:
            return self.error("Token Expired"), 498
        except jwt.DecodeError as e:
            return self.error("Failed to decode JWT, " + str(e)), 403
        except jwt.InvalidTokenError as e:
            return self.error("Invalid JWT-token, " + str(e)), 403
        except Exception as e:
            return self.error("Failed to decode JWT, unknown Exception: " + type(e) + " -> " + str(e)), 403

        if "aud" not in payload:
            return self.error("Payload have no aud-field", payload), 403

        if "sub" not in payload:
            return self.error("Payload have no sub-field", payload), 403

        if payload["aud"] != os.getenv("HOST_NAME"):
            return self.error("Payload have bad aud-field", payload), 403

        try:
            user_id_string, user_source = payload["sub"].split("@", 1)
            user_id = int(user_id_string)
        except ValueError:
            return self.error("Payload have bad sub-field", payload), 403

        if user_source != os.getenv("JWT_SOURCE_HOST"):
            return self.error("Payload have bad sub-field", payload), 403

        admin = "roles" in payload and "organisation:692:scoutid_admin" in payload["roles"]

        return {
                   "user": user_id,
                   "admin": admin,
                   "data": payload,
               }
