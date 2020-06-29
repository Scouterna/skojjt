from os import getenv
from pymongo import MongoClient


def dbConnect():
    authed_uri = getenv('MONGO_URI') % (getenv('MONGO_USER'), getenv('MONGO_PASSWORD'))
    client = MongoClient(authed_uri)
    return client[getenv('MONGO_DATABASE')]
