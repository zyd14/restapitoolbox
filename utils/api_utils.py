from functools import wraps
import logging
from logging import Logger
from marshmallow import Schema
from typing import Union, Tuple

from flask import make_response, jsonify, Response
from werkzeug.local import LocalProxy

from utils.apiexceptions import InvalidRequestStructureError

DEFAULT_LOGGER = logging.getLogger('api_logger')

def fail_gracefully(func):
    """ Wrapper method to put a try/except block around the function passed by user which returns an HTTP 500 Internal Server Error
        response to the client when unhandled exceptions occur.  Should only be used in cases where a Response object is
        desired to be returned when an unhandled exception occurs.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Response:
        if 'logger' not in kwargs:
            logger = DEFAULT_LOGGER
        else:
            logger = kwargs['logger']
        try:
            return func(*args, **kwargs)
        except BaseException as exc:
            logger.exception(exc)
            return make_response(jsonify(message='Internal server error due to unhandled exception', error=str(exc), code=500,
                                  status='failure'), 500)
    return wrapper

def parse_request(schema_type:type(Schema), request:Union[LocalProxy, dict]) -> Tuple[dict, dict]:
    """ Use a marshmallow schema to parse JSON from a request or dict.  Will raise a InvalidRequestStructureError if any
        errors occur during parsing (such as missing or unexpected fields, wrong types).
    """
    schema = schema_type()

    if isinstance(request, LocalProxy):
        # Request originated externally.
        request_data = request.get_json(force=True)
        parsed_request = schema.load(request_data)
    else:
        # Request originated locally, probably from a test.
        parsed_request = schema.load(request)

    if parsed_request.errors:
        error_msg = 'Request is missing required keys or contains invalid value types.'
        raise InvalidRequestStructureError(error_msg, errors=parsed_request.errors)

    return parsed_request.data

def log_request(logger:Logger, raw_request:LocalProxy):
    logger.info(f'Received request {raw_request}')
    logger.info(f'Request data: {raw_request.get_json(force=True)}')

def create_response(code: int, message: str, body: dict) -> Response:
    response_dict = {'code': code,
                     'message': message,
                     'body': body
                     }

    response = make_response(jsonify(**response_dict), code)
    response.headers['Content-Type'] = 'application/json'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response