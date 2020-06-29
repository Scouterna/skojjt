from api.Config import ConfigResource
from api.DbTest import DbTest
from api.jwt.VerifyToken import VerifyToken
from api.KarImport import KarImport
from flask import redirect
from init import api, app

# Guest access paths
api.add_resource(ConfigResource, '/api/config')
api.add_resource(DbTest, '/api/dbtest')
api.add_resource(VerifyToken, '/api/jwt/verify_token')

# User access paths

# Admin access paths
api.add_resource(KarImport, '/api/import', '/api/import/<string:import_id>')


# if we are not logged in, we make a fake saml-session, that end at /saml, so accept and ignore it, and return to /
@app.route('/saml', methods=['GET', 'POST'])
def saml_redirect():
    return redirect('/')
