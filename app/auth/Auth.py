import jwt
import os
from urllib.parse import urlparse
from jwt import InvalidTokenError


class Auth:
    token = ''
    payload = None
    user_id = None

    @staticmethod
    def read_token(token):
        return Auth(token)

    def __init__(self, token):
        self.token = token
        self.parse_token()

    def parse_token(self):
        try:
            public_key = open(os.getenv('JWT_PUBLIC_KEY_FILE')).read()
        except Exception:
            raise EnvironmentError('Public key for JWT is missing on server')

        issuer = urlparse(os.getenv('JWT_URL')).hostname
        audience = os.getenv('HOST_NAME')

        self.payload = jwt.decode(self.token, public_key, algorithms=['RS256'], issuer=issuer, audience=audience)

        if 'aud' not in self.payload:
            raise InvalidTokenError('Payload have no aud-field')

        if 'sub' not in self.payload:
            raise InvalidTokenError('Payload have no sub-field')

        if self.payload['aud'] != os.getenv('HOST_NAME'):
            raise InvalidTokenError('Payload have bad aud-field')

        try:
            user_id_string, user_source = self.payload['sub'].split('@', 1)
            self.user_id = int(user_id_string)
        except ValueError:
            raise InvalidTokenError('Payload have bad sub-field')

        if user_source != os.getenv('JWT_SOURCE_HOST'):
            raise InvalidTokenError('Payload have bad sub-field')
