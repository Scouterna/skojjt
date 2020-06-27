import pymongo
import os


def connect():
    try:
        authed_uri = os.getenv('MONGO_URI') % (os.getenv('MONGO_USER'), os.getenv('MONGO_PASSWORD'))
        client = pymongo.MongoClient(authed_uri)
        return client[os.getenv('MONGO_DATABASE')], None
    except Exception as e:
        return None, e


db, db_error = connect()
