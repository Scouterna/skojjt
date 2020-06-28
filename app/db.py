import pymongo
import os


def dbConnect():
    authed_uri = os.getenv('MONGO_URI') % (os.getenv('MONGO_USER'), os.getenv('MONGO_PASSWORD'))
    client = pymongo.MongoClient(authed_uri)
    return client[os.getenv('MONGO_DATABASE')]
