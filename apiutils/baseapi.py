import logging


from flask_restful import Resource, request
from flask import Response

from apiutils.api_utils import fail_gracefully, parse_request, log_request, create_response


class BaseApi(Resource):

    """ Provides some base functionality for GET and POST requests to a particular endpoint.

        The parse_requece, log_request, and create_response methods are pulled from api_utils.py
        but are assigned as class attributes so that they can be overridden by subclasses requiring
        custom behavior for those functions.

        At a minimum the perform_get_request method must be overridden with some sort of handling of a request which returns
        a dictionary with the following keys:
            code - <int> HTTP status code of response
            message - <str> Description of result
            body - <dict> JSON-serializable dictionary containing any results which need to be returned to the requester
    """

    __logger_name__ = 'api_logger'

    logger = logging.getLogger('api_logger')

    # Assign default functions from api_utils
    # All these can be overridden when BaseApi is subclassed to provide custom functionality
    parse_request = parse_request
    log_request = log_request
    create_response = create_response

    @fail_gracefully
    def get(self):

        self.log_request(self.logger, request)

        try:
            results = self.perform_get_request(request)
        except Exception as exc:
            return self.handle_get_exceptions(exc)

        return create_response(code=200, message='Success', body=results)

    def perform_get_request(self, raw_request: type(request), *args, **kwargs) -> dict:
        # Add logic for handling get request here
        raise NotImplementedError

    def handle_get_exceptions(self, exc: BaseException):
        # Add logic for creating custom responses for specific exceptions raised during processing here
        raise exc

    @fail_gracefully
    def post(self):
        self.log_request(self.logger, request)

        try:
            results = self.perform_post_request(request)
        except Exception as exc:
            return self.handle_post_exceptions(exc)

        return create_response(code=200, message='Success', body=results)

    def perform_post_request(self, raw_request: type(request)):
        # Add logic for handling post request here
        raise NotImplementedError

    def handle_post_exceptions(self, exc: BaseException) -> Response:
        # Add logic for creating custom responses for specific exceptions raised during processing here
        raise exc




