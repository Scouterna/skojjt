from auth.RequireUser import RequireUser
from db import db_connect
from logging import exception as logging_exception
from models.apiReponses import VerifyTokenResponse


class VerifyToken(RequireUser):
    # fetch("/api/jwt/verify_token", {headers: {Authorization: 'Bearer ' + localStorage.getItem('ScoutID-JWT-Token')}})
    def get(self) -> VerifyTokenResponse:
        try:
            db = db_connect()
        except Exception as e:
            logging_exception('db error in VerifyToken')
            return {
                "user": self.auth.user_id,
                "admin": self.auth.is_admin(),
                "data": self.auth.payload,
                "error": str(e),
            }

        if self.auth.user_id:
            query = {'_id': self.auth.user_id}
            new_row = {
                '_id': self.auth.user_id,
                'name': self.auth.payload['name'],
                'roles': self.auth.payload['roles']
            }
            old_row = db['user_names'].find_one(query)
            if old_row is None:
                db['user_names'].insert(new_row)
            else:
                db['user_names'].update_one(query, {'$set': new_row})

        if self.auth.payload['karer']:
            for kar_id, kar_name in self.auth.payload['karer'].items():
                query = {'_id': kar_id}
                new_row = {'_id': kar_id, 'name': kar_name}
                same_row = db['kar_names'].find_one(new_row)
                if same_row is None:
                    old_row = db['kar_names'].find_one(query)
                    if old_row is None:
                        db['kar_names'].insert(new_row)
                    else:
                        db['kar_names'].update_one(query, {'$set': new_row})

        return {
            "user": self.auth.user_id,
            "admin": self.auth.is_admin(),
            "data": self.auth.payload,
        }
