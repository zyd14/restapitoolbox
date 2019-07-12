class InvalidRequestStructureError(Exception):

    def __init__(self, error_msg:str, errors:dict=None):
        super().__init__(error_msg)
        self.request_parsing_errors = errors