# pylint: disable=too-few-public-methods
""" Sidebar """
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class Sidebar(Common):
    """Class for Sidebar"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Sidebar class"""
        self.postgresql_query = PostgreSQL()
        super(Sidebar, self).__init__()

    def sidebar(self):
        """
        This API is for Getting Sidebar status
        ---
        tags:
          - Sidebar
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
        responses:
          500:
            description: Error
          200:
            description: Sidebar
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:

            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        response = self.get_sidebar_status(userid)

        data['data'] = response
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def get_sidebar_status(self, userid):
        """ Return Side bar status """

        sql_str = "SELECT sidebar FROM account WHERE"
        sql_str += " id='{0}'".format(userid)
        account = self.postgres.query_fetch_one(sql_str)

        response = {}
        response['sidebar'] = True

        if account:

            response['sidebar'] = account['sidebar']

        else:

            # UPDATE
            # INIT CONDITION
            conditions = []

            # CONDITION FOR QUERY
            conditions.append({
                "col": "id",
                "con": "=",
                "val": userid
                })

            self.postgres.update('account', response, conditions)

        return response
