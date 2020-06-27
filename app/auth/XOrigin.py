import os
from flask import Response, request
from flask_restful import Resource, unpack
from werkzeug.wrappers import Response as ResponseBase
from init import api


class XOrigin(Resource):
    def add_cors_headers(self, response):
        if 'origin' in request.headers:
            response.headers['Access-Control-Allow-Origin'] = request.headers['origin']
        else:
            response.headers['Access-Control-Allow-Origin'] = 'https://' + os.getenv('HOST_NAME')

        if hasattr(self, 'post'):
            response.headers['Access-Control-Allow-Methods'] = 'GET, HEAD, POST, OPTIONS'
        else:
            response.headers['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
        return response

    def options(self):
        Response()

    def dispatch_request(self, *args, **kwargs):
        response = super().dispatch_request(*args, **kwargs)

        if isinstance(response, ResponseBase):
            return self.add_cors_headers(response)

        data, code, headers = unpack(response)
        return self.add_cors_headers(api.make_response(data, code, headers=headers))
