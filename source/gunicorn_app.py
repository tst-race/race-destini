#!/usr/bin/env python3

# https://stackoverflow.com/questions/12269537/is-the-server-bundled-with-flask-safe-to-use-in-production
#
# Flask's bundled server is Werkzeug's development server.
# - It only handles one request at a time by default.
# - If you leave debug mode on and an error pops up, it opens up a
#   shell that allows for arbitrary code to be executed on your
#   server (think "os.system('rm -rf /')").
# - It doesn't scale.
#
# - https://gunicorn.org/
#   - https://stackoverflow.com/questions/8495367/using-additional-command-line-arguments-with-gunicorn


# Gunicorn entry point generator
def appgen (*args, **kwargs):
    # Gunicorn CLI args are useless.
    # https://stackoverflow.com/questions/8495367/
    #
    # Start the application in modified environment.
    # https://stackoverflow.com/questions/18668947/
    #
    import sys

    sys.argv = ['--gunicorn']

    for k in kwargs:
        dash_delim = '--' if len (k) > 1 else '-'
        sys.argv.append (dash_delim + k)
        sys.argv.append (kwargs[k])

    for v in args:
        sys.argv.append (v)

    from FlaskRACECOMMS import app

    return app
