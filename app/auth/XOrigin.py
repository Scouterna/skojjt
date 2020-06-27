import os

import jwt
from flask import Response, request
from flask_restful import Resource, unpack
from werkzeug.exceptions import HTTPException
from werkzeug.wrappers import Response as ResponseBase
from init import api


class XOrigin(Resource):
    def error(self, msg, status=500, data=None):
        response = api.make_response({
            "user": False,
            "admin": False,
            "data": data,
            "error": msg
        }, status)
        return self.add_cors_headers(response)

    def exception(self, exception):
        try:
            raise exception
        except jwt.ExpiredSignatureError:
            return self.error("Token Expired", 498)
        except HTTPException as e:
            return self.error(str(type(e)) + " -> " + str(e), e.code)
        except Exception as e:
            return self.error(str(type(e)) + " -> " + str(e), 403)

    def add_cors_headers(self, response):
        # Already added?
        if 'Access-Control-Allow-Origin' in response.headers:
            return response

        # Origin header?
        if 'origin' in request.headers:
            response.headers['Access-Control-Allow-Origin'] = request.headers['origin']
        else:
            response.headers['Access-Control-Allow-Origin'] = 'https://' + os.getenv('HOST_NAME')

        return response

    def options(self):
        response = Response()
        if hasattr(self, 'post'):
            response.headers['Access-Control-Allow-Methods'] = 'GET, HEAD, POST, OPTIONS'
        else:
            response.headers['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
        return response

    def dispatch_request(self, *args, **kwargs):
        try:
            response = super().dispatch_request(*args, **kwargs)
        except Exception as e:
            return self.exception(e)

        if isinstance(response, ResponseBase):
            return self.add_cors_headers(response)

        data, code, headers = unpack(response)
        return self.add_cors_headers(api.make_response(data, code, headers=headers))
