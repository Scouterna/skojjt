from db import db_connect
from flask_restful import Resource
from logging import exception as logging_exception
from models.apiReponses import DbTestResponse


class DbTest(Resource):
    def get(self) -> DbTestResponse:
        try:
            db = db_connect()
            testdb = db["test"]
            query = {"_id": "test"}
            row = testdb.find_one(query)
            if row is None:
                testdb.insert({"_id": "test", "count": 1})
            else:
                testdb.update_one(query, {"$inc": {"count": 1}})
            row = testdb.find_one(query)
            if row is None:
                return {"ok": False, "error": "empty database"}
            return {"ok": True, "count": row["count"]}
        except Exception as e:
            logging_exception('error in db-test')
            return {"ok": False, "error": str(e)}
