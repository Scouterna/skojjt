# -*- coding: utf-8 -*-
import logging
from flask import Flask, make_response, redirect, render_template, request, jsonify

app = Flask(__name__)
app.debug = True


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/1/whoami')
def whoami():
    return jsonify(ok=False, error="Not Implemented"), 200;


@app.errorhandler(404)
def page_not_found(e):
    return jsonify(ok=False, error=str(e)), 404;


@app.errorhandler(403)
def access_denied(e):
    return jsonify(ok=False, error=str(e)), 403;


@app.errorhandler(500)
def serverError(e):
    logging.error("Error 500:%s", str(e))
    return jsonify(ok=False, error=str(e)), 500;
