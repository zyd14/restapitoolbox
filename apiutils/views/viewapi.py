"""

Project: ApiToolbox

File Name: viewapi

Author: Zachary Romer, zach@scharp.org

Creation Date: 8/12/19

Version: 1.0

Purpose:

Special Notes:

"""

import json
import logging
from flask import request, make_response
from flask_restful import Resource, ResponseBase

from apiutils import api_utils
from apiutils.dbconnect import BaseDBConnect
from apiutils.views.viewpresenter import ViewPresenter, UnexepctedQueryArgs

ENDPOINT_CONFIG = json.load('config.json')


class BaseViewApi(Resource):
    """ Provides base functionality for performing queries on database views. The main responsibilities of this class are
        to pass request information to AbstractDB view, handling exceptions, and creates responses depending on the results
        of AbstractDBViewer.view_db().  Defers query logic to AbstractDBViewer, which maps an endpoint to a specific view function, and parses url-passed parameters to enable filtering on queries.
        This class can be used directly to provide a Flask API Resource, but can also be subclassed if custom behavior
        is necessary.  Unhandled exceptions are raised to api_utils.fail_gracefully(), which logs the exception and returns
        a 500 response to the requester with the exception message.

        Attributes:
              logger - logging.Logger instance to log information / errors to console, files, and / or CloudWatch.
    """

    logger = logging.getLogger('BaseViewApi')

    @api_utils.fail_gracefully
    def get(self):
        """ Return view information to requester, filterable by user-provided URL query string arguments.

            For example, a request to /files/view?user_name=Ted would return all files which were recorded as uploaded
            by user 'Ted'.

            Returns:
                Flask HTTP Response
        """

        try:
            matching_args, request_view = self.get_view_config('apiutils/config.json')
            pg_connection_data = api_utils.parse_authorization_details(request.authorization)
            connection = BaseDBConnect(**pg_connection_data)
            view_data = ViewPresenter.view_contents(connection, matching_args, request_view, request.args)
        except Exception as exc:
            return self.handle_view_exceptions(exc)

        return self.create_response(code=200, message='Success', body=view_data)

    @api_utils.fail_gracefully
    def patch(self):
        return make_response(json.dumps({"message": "PATCH requests have not been implemented at this endpoint"}), 400)

    @api_utils.fail_gracefully
    def post(self):
        return make_response(json.dumps({"message": "POST requests have not been implemented at this endpoint"}), 400)

    @classmethod
    @api_utils.fail_gracefully
    def create_response(cls, code=200, message='Success', body=None) -> ResponseBase:
        """ Defers response creation to api_utils method, but allows for subclasses to override with custom behavior
            if required.
        """
        if body is None:
            body = {}

        return api_utils.create_response(code=code, message=message, body=body)

    @classmethod
    @api_utils.fail_gracefully
    def handle_view_exceptions(cls, exc: BaseException):
        """ Handles various errors and exceptional states and attempts to present informative responses to
            the user about them.
        """
        if isinstance(exc, UnexepctedQueryArgs):
            return cls.create_response(code=400, message=exc.error_msg, body={})
        else:
            return cls.create_response(code=500, message=str(exc.args), body={})

    @classmethod
    def get_view_config(cls, config_path: str=''):
        if not config_path:
            config_path = 'apiutils/config.json'

        with open(config_path, 'r') as config:
            return json.load(config)
