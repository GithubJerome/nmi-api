# pylint: disable=too-many-function-args
"""UserByIDs"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class UserByIDs(Common):
    """Class for UserByIDs"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UserByIDs class"""
        self.postgresql_query = PostgreSQL()
        super(UserByIDs, self).__init__()

    def user_by_ids(self):
        """
        This API is for Getting All User
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
          - name: selected_ids
            in: query
            description: Selected IDs
            required: false
            type: string
        responses:
          500:
            description: Error
          200:
            description: User
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        selected_ids = request.args.get('selected_ids')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        datas = self.get_all_users(selected_ids)
        datas['status'] = 'ok'

        return self.return_data(datas, userid)

    def get_all_users(self, selected_ids):
        """Return All Users"""
        
        rows = []

        if selected_ids:
            selected = ','.join("'{0}'".format(selected) for selected in selected_ids.split(","))

            sql_str = "SELECT id, first_name, last_name, middle_name FROM account WHERE"
            sql_str += " id IN ({0})".format(selected)
            sql_str += " ORDER BY created_on DESC"

            rows = self.postgres.query_fetch_all(sql_str)

        data = {}
        data['rows'] = rows

        return data
