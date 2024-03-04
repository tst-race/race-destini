from FlaskRun import FlaskRun

class FlaskHostPort (FlaskRun):

    def __init__ (self,
                  default_host = "127.0.0.1",
                  default_port = "5000",
                  *args,
                  **kwargs):
        super ().__init__ (*args, **kwargs)
        self._parser.add_argument ("-H", "--host",
                                   help = "hostname of the Flask app (default: %(default)s)",
                                   default = default_host)
        self._parser.add_argument ("-P", "--port",
                                   help = "port for the Flask app (default: %(default)s)",
                                   default = default_port)

    def _flask_app_args (self, _dict, app):
        _dict = super (__class__, self)._flask_app_args (_dict, app)
        args  = app.config['args']
        _dict['host'] = args.host
        _dict['port'] = int (args.port)
        
        return _dict
        
