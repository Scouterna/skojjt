import os
import pymongo
from flask_restful import Resource


class DbTest(Resource):
    def get(self):
        try:
            authed_uri = os.getenv("MONGO_URI") % (os.getenv("MONGO_USER"), os.getenv("MONGO_PASSWORD"))
            client = pymongo.MongoClient(authed_uri)
            testdb = client["test"]["test"]
            query = {"id": "test"}
            row = testdb.find_one(query)
            if row is None:
                testdb.insert({"id": "test", "count": 1})
            else:
                testdb.update_one(query, {"$inc": {"count": 1}})
            row = testdb.find_one(query)
            if row is None:
                return {"ok": False, "error": "empty database"}
            return {"ok": True, "count": row["count"]}
        except Exception as e:
            return {"ok": False, "error": str(e)}
