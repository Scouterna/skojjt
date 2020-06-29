from auth.RequireAdmin import RequireAdmin
from bson.objectid import ObjectId
from db import dbConnect
from flask import request
from time import time


class KarImport(RequireAdmin):
    def post(self):
        db = dbConnect()
        result = db['pending_import'].insert_one({
            'kar_id': request.json['karId'],
            'api_key': request.json['apiKey'],
            'added_at': time(),
            'started_at': 0,
            'done_at': 0,
            'error_at': 0,
            'rows_total': 0,
            'rows_done': 0,
            'report': '',
        })

        import_id = str(result.inserted_id)
        kar_name_row = db['kar_names'].find_one({'_id': request.json['karId']})
        if kar_name_row is None:
            kar_name = 'Kår ' + str(request.json['karId'])
        else:
            kar_name = kar_name_row['name'] + ' (' + str(request.json['karId']) + ')'

        html = f"""
        <h3>Importerar {kar_name}</h3>
        <p>Import id: {import_id}</p>
        """

        return {'ok': True, 'refrechUrl': '/api/import/' + import_id, 'html': html}

    def get(self, import_id):
        query = {'_id': ObjectId(import_id)}
        db = dbConnect()
        row = db['pending_import'].find_one(query)
        if row is None:
            return {'ok': False, 'error': 'Import not found'}, 404

        if row['done_at'] > 0:
            append = "<pre>" + row['report'] + "</pre>";
            return {'ok': True, 'append': append}

        if row['error_at'] > 0:
            append = "<pre>" + row['report'] + "</pre>";
            return {'ok': False, 'append': append}

        if row['rows_total'] > 0:
            append = str(100 * row['rows_done'] / row['rows_total']) + '% done'
            return {'ok': True, 'refrechUrl': '/api/import/' + import_id, 'delay': 2, 'append': append}

        return {'ok': True, 'refrechUrl': '/api/import/' + import_id, 'delay': 5, 'append': 'waiting...'}
