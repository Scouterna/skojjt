from __future__ import annotations
from jwt import decode as jwt_decode, InvalidTokenError
from os import getenv
from urllib.parse import urlparse


class Auth:
    token: str = None
    payload: dict = None  # Todo: define Payload type
    user_id: int = None

    @staticmethod
    def read_token(token: str) -> Auth:
        return Auth(token)

    def __init__(self, token: str) -> None:
        self.token = token
        self.parse_token()

    def parse_token(self) -> None:
        try:
            public_key = open(getenv('JWT_PUBLIC_KEY_FILE')).read()
        except Exception:
            raise EnvironmentError('Public key for JWT is missing on server')

        issuer = urlparse(getenv('JWT_URL')).hostname
        audience = getenv('HOST_NAME')

        self.payload = jwt_decode(self.token, public_key, algorithms=['RS256'], issuer=issuer, audience=audience)

        if 'aud' not in self.payload:
            raise InvalidTokenError('Payload have no aud-field')

        if 'sub' not in self.payload:
            raise InvalidTokenError('Payload have no sub-field')

        if self.payload['aud'] != getenv('HOST_NAME'):
            raise InvalidTokenError('Payload have bad aud-field')

        try:
            user_id_string, user_source = self.payload['sub'].split('@', 1)
            self.user_id = int(user_id_string)
        except ValueError:
            raise InvalidTokenError('Payload have bad sub-field')

        if user_source != getenv('JWT_SOURCE_HOST'):
            raise InvalidTokenError('Payload have bad sub-field')

    def is_admin(self) -> bool:
        return 'roles' in self.payload and 'organisation:692:scoutid_admin' in self.payload['roles']

    def has_kar_admin_access(self, kar_id: int) -> bool:
        if self.is_admin():
            return True

        if kar_id not in self.payload['karer']:
            return False

        # group-leader = Kårordförande
        admin_roller = ['member_registrar', 'it_manager', 'leader', 'treasurer']

        for roll in admin_roller:
            if 'group:' + str(kar_id) + ':' + roll in self.payload['roles']:
                return True

        return False

    def has_kar_access(self, kar_id: int) -> bool:
        if self.is_admin():
            return True

        kar_id_str = str(kar_id)

        # todo is keys in karer str or int?
        if kar_id not in self.payload['karer'] and kar_id_str not in self.payload['karer']:
            return False

        # TODO load kår config, support different auth models
        if 'group:' + kar_id_str + ':*' in self.payload['roles']:
            return True

        if 'troop:*:leader' not in self.payload['roles']:
            return False

        # TODO get troups by kar
        troops = []

        for troop in troops:
            if 'troop:' + troop + ':leader' in self.payload['roles']:
                return True

        return False
