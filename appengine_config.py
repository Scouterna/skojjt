"""
`appengine_config.py` is automatically loaded when Google App Engine
starts a new instance of your application. This runs before any
WSGI applications specified in app.yaml are loaded.
"""
from google.appengine.ext import vendor
from google.appengine.datastore.entity_pb import Reference # to be able to use the data from retail version (urlsafe refs)
import logging
import os

# Set path to your libraries folder.
path = 'lib'
# Add libraries installed in the path folder.
vendor.add(path)
# Add libraries to pkg_resources working set to find the distribution.
import pkg_resources
pkg_resources.working_set.add_entry(path)

import six; reload(six)

def myApp(*args): 
    return os.environ['APPLICATION_ID'].replace("dev~", "s~")

if os.environ.get('SERVER_SOFTWARE','').startswith('Development'):
    logging.info("*** Dev mode ***")
    remoteapi_CUSTOM_ENVIRONMENT_AUTHENTICATION = ('REMOTE_ADDR', ['127.0.0.1'])
    Reference.app = myApp

