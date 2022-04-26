"""Set Language"""
import time
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class SetLanguage(Common):
    """Class for SetLanguage"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for SetLanguage class"""

        self.postgres = PostgreSQL()
        super(SetLanguage, self).__init__()

    def set_language(self):
        """
        This API is for Updating User Language
        ---
        tags:
          - User
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
            description: Updating User Language
            required: true
            schema:
              id: Updating User Language
              properties:
                language:
                    type: string
        responses:
          500:
            description: Error
          200:
            description: Updating User Language
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

        if not self.update_users(query_json, userid):

            data["alert"] = "Please check your query!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        data['message'] = "User Language successfully updated!"
        data['status'] = "ok"
        return self.return_data(data, userid)

    def update_users(self, query_json, account_id):
        """Update Users"""

        # UPDATE
        # INIT CONDITION
        conditions = []

        # CONDITION FOR QUERY
        conditions.append({
            "col": "id",
            "con": "=",
            "val": account_id
            })

        # REMOVE KEYS
        data = {}
        data['language'] = query_json['language']
        data['update_on'] = time.time()

        # UPDATE ROLE
        if self.postgres.update('account', data, conditions):

            # RETURN
            return 1

        # RETURN
        return 0
