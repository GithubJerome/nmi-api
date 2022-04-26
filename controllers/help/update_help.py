# pylint: disable=too-many-function-args
"""Update Hep"""
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity

class UpdateHep(Common):
    """Class for UpdateHep"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateHep class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(UpdateHep, self).__init__()

    def update_help(self):
        """
        This API is for Updating Help
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
            description: Update Help
            required: true
            schema:
              id: Update Help
              properties:
                help_id:
                    type: string
                url:
                    type: string
                skill:
                    type: string

        responses:
          500:
            description: Error
          200:
            description: Update Help
        """
        data = {}

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

        # GET HEADER
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        if not self.edit_help(query_json):

            data["alert"] = "Please check your query!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        data['message'] = "Help successfully updated!"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def edit_help(self, query_json):
        """Update Help"""

        query_json['update_on'] = time.time()

        conditions = []

        conditions.append({
            "col": "help_id",
            "con": "=",
            "val": query_json['help_id']
            })

        data = self.remove_key(query_json, "help_id")

        if self.postgres.update('help', data, conditions):
            return 1

        return 0
