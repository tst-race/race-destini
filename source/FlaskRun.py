import argparse

class FlaskRun (object):

    def __init__ (self):
        super ().__init__ ()
        self._parser = argparse.ArgumentParser ()
        self._parser.add_argument ("-d", "--debug",
                                   action = "store_true", dest = "debug",
                                   help = argparse.SUPPRESS)
        self._args   = None

    def _flask_app_args (self, _dict, app):
        args = app.config['args']
        _dict['debug'] = args.debug
        
        return _dict

    def get_args (self):
        if not self._args:
            self._args = self._parser.parse_args ()
        return self._args

    def run (self, app):
        if not hasattr (app, 'config'):
            print ("defining app.config")
            app.config = {}

        app.config['args'] = self.get_args ()

        #print (self.get_args ())

        if hasattr (app, 'run'):
            print ("app.run ()")
            app.run (**self._flask_app_args ({}, app))
