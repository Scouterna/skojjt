from os import getenv
from pymongo import MongoClient
from pymongo.database import Database


def db_connect() -> Database:
    authed_uri = getenv('MONGO_URI') % (getenv('MONGO_USER'), getenv('MONGO_PASSWORD'))
    client = MongoClient(authed_uri)
    return client[getenv('MONGO_DATABASE')]
