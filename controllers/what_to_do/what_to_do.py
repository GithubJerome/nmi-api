# pylint: disable=too-few-public-methods
"""What To Do"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class WhatToDo(Common):
    """Class for WhatToDo"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for WhatToDo class"""
        self.postgresql_query = PostgreSQL()
        super(WhatToDo, self).__init__()

    def what_to_do(self):
        """
        This API is for Getting All What To Do
        ---
        tags:
          - WhatToDo
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
          - name: page
            in: query
            description: Page
            required: true
            type: string
        responses:
          500:
            description: Error
          200:
            description: What to do
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        page = request.args.get('page')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        sql_str = "SELECT description FROM what_to_do WHERE"
        sql_str += " page='{0}'".format(page)
        response = self.postgres.query_fetch_one(sql_str)

        sql_str = "SELECT language FROM account WHERE"
        sql_str += " id='{0}'".format(userid)
        language = self.postgres.query_fetch_one(sql_str)

        description = self.translate_key(language, response['description'])

        data['data'] = description
        data['status'] = 'ok'

        return self.return_data(data)
