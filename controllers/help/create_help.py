"""Create Help"""
import string
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.emailer import Email
from templates.invitation import Invitation

class CreateHelp(Common, ShaSecurity):
    """Class for CreateHelp"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CreateHelp class"""

        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(CreateHelp, self).__init__()

    def create_help(self):
        """
        This API is for Creating Help
        ---
        tags:
          - Help
        produces:
          - application/json
        parameters:
          - name: token
            in: header
            description: Token
            required: true
            type: string
          - name: userid
            in: header
            description: User ID
            required: true
            type: string
          - name: query
            in: body
            description: Add Help
            required: true
            schema:
              id: Add Help
              properties:
                skill:
                    type: string
                url:
                    type: string
        responses:
          500:
            description: Error
          200:
            description: Create Help
        """

        # INIT DATA
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # CREATE HELP
        if not self.run(query_json):
            data["alert"] = "Help already exist!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)


        data = {}
        data['message'] = "Help successfully created"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def run(self, query_json):
        """ CREATE HELP """

        # VALIDATE HELP
        if not self.validate_help(query_json):

            # CREATE HELP
            helper = {}
            helper['help_id'] = self.sha_security.generate_token(False)
            helper['skill'] = query_json['skill']
            helper['url'] = query_json['url']
            helper['status'] = True
            helper['created_on'] = time.time()

            self.postgres.insert('help', helper, 'help_id')

            return 1

        return 0

    def validate_help(self, query):
        """ VALIDATE HELP """

        sql_str = "SELECT skill FROM help WHERE"
        sql_str += " skill='{0}' AND status=True".format(query['skill'])

        hlp = self.postgres.query_fetch_one(sql_str)

        if hlp:

            return 1

        return 0
