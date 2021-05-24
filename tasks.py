# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, make_response, redirect
from progress import TaskProgress


tasks = Blueprint('tasks', __name__, template_folder='templates')


# cron job:
@tasks.route('/cleanup')
@tasks.route('/cleanup/')
def tasksCleanup():
    TaskProgress.cleanup()
    return "", 200
