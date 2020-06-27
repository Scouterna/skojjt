from auth.RequireUser import RequireUser


class VerifyToken(RequireUser):
    # fetch("/api/jwt/verify_token", {headers: {Authorization: 'Bearer ' + localStorage.getItem('ScoutID-JWT-Token')}})
    def get(self):
        return {
            "user": self.auth.user_id,
            "admin": self.auth.is_admin(),
            "data": self.auth.payload,
        }
