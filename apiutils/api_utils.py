from functools import wraps
import logging
from marshmallow import Schema
import os
from typing import Union, Tuple

from flask import make_response, jsonify, Response
from werkzeug.local import LocalProxy

from apiutils.apiexceptions import InvalidRequestStructureError

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
        except Exception as exc:
            logger.exception(exc)
            return make_response(jsonify(message='Internal server error due to unhandled exception',
                                         error=str(exc),
                                         code=500,
                                         status='failure'),
                                         500)
    return wrapper


def parse_authorization_details(auth_header_data):
    pg_host = os.getenv('PG_HOST', '127.0.0.1')
    pg_database = os.getenv('PG_DATABASE', 'test_database')

    return {'user_role': auth_header_data.username, 'password': auth_header_data.password,
            'host': pg_host, 'database': pg_database}


def parse_post_data(schema_type:type(Schema), request:Union[LocalProxy, dict]) -> Tuple[dict, dict]:
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


def create_response(code: int, message: str, body: dict) -> Response:
    """ Create a basic HTTP response with 'Content-Type:application/json' and 'Access-Control-Allow-Origin:*' headers."""
    response_dict = {'code': code,
                     'message': message,
                     'body': body
                     }

    response = make_response(jsonify(**response_dict), code)
    response.headers['Content-Type'] = 'application/json'
    return response
