from auth.Auth import Auth
from auth.XOrigin import XOrigin
from flask import request
from werkzeug.exceptions import Forbidden as ForbiddenException
from werkzeug.wrappers import Response as ResponseBase


class RequireUser(XOrigin):
    auth: Auth = None

    def require_user(self) -> None:
        if "Authorization" not in request.headers:
            raise ForbiddenException("Authorization header is missing")

        auth_header = request.headers["Authorization"]

        if auth_header[0:7] != "Bearer ":
            raise ForbiddenException("Authorization header is not Bearer type")

        self.auth = Auth(auth_header[7:])

    def dispatch_request(self, *args, **kwargs) -> ResponseBase:
        try:
            self.require_user()
        except Exception as e:
            return self.exception(e)

        return super().dispatch_request(*args, **kwargs)

    def require_kar_admin(self, kar_id: int) -> None:
        if not self.auth.has_kar_admin_access(kar_id):
            raise ForbiddenException("You are not admin for this group(kår)")

    def require_kar_access(self, kar_id: int) -> None:
        if not self.auth.has_kar_access(kar_id):
            raise ForbiddenException("You don't have access for this group(kår)")
