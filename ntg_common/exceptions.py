class EditException (Exception):
    """ See: http://flask.pocoo.org/docs/0.12/patterns/apierrors/ """

    default_status_code = 400

    def __init__ (self, message, status_code=None, payload=None):
        Exception.__init__ (self)
        self.message     = 'Error: ' + message
        self.status_code = status_code or self.default_status_code
        self.payload     = payload

    def to_dict (self):
        rv = dict ()
        rv['status']  = self.status_code
        rv['message'] = self.message
        if self.payload:
            rv['payload'] = self.payload
        return rv


class EditError (EditException):
    pass


class PrivilegeError (EditException):
    pass
