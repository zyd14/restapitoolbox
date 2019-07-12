import logging


from flask_restful import Resource, request
from flask import Response

from utils.api_utils import fail_gracefully, parse_request, log_request, create_response

class BaseApi(Resource):

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

    def perform_get_request(self, raw_request: type(request)):
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




