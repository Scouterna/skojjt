from flask_restful import Resource
from db import db, db_error


class DbTest(Resource):
    def get(self):
        if db is None:
            return {"ok": False, "error": str(db_error)}
        try:
            testdb = db["test"]
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
