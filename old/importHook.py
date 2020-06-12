""" pylint init-hook script. Used to create a multiline init-hook"""

import sys
import platform
sys.path.append("lib")

if platform.system() == 'Windows':
    # Add app engine paths on windows.
    sys.path.append("C:/Program Files (x86)/Google/google_appengine")
    sys.path.append("C:/Program Files (x86)/Google/google_appengine/lib")
    sys.path.append("c:/Program Files (x86)/Google/google_appengine/google/appengine/api")
    sys.path.append("c:/Program Files (x86)/Google/google_appengine/google/appengine")
