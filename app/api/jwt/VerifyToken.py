import jwt
from flask import request
from auth.Auth import Auth
from auth.RequireUser import RequireUser


class VerifyToken(RequireUser):
    # fetch("/api/jwt/verify_token", {headers: {Authorization: 'Bearer ' + localStorage.getItem('ScoutID-JWT-Token')}})
    def get(self):
        admin = "roles" in self.auth.payload and "organisation:692:scoutid_admin" in self.auth.payload["roles"]

        return {
            "user": self.auth.user_id,
            "admin": admin,
            "data": self.auth.payload,
        }
