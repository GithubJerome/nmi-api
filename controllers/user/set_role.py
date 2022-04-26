"""Set Role"""
import time
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class SetRole(Common):
    """Class for SetRole"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for SetRole class"""

        self.postgres = PostgreSQL()
        super(SetRole, self).__init__()

    def set_role(self):
        """
        This API is for Updating User Role
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
            description: Updating User Role
            required: true
            schema:
              id: Updating User Role
              properties:
                role_name:
                    type: string
        responses:
          500:
            description: Error
          200:
            description: Updating User Role
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

        user_info = {}
        user_info['account_id'] = userid
        user_info['remote_addr'] = request.remote_addr
        user_info['platform'] = request.user_agent.platform
        user_info['browser'] = request.user_agent.browser
        user_info['version'] = request.user_agent.version
        user_info['language'] = request.user_agent.language
        user_info['string'] = request.user_agent.string

        if not self.update_users(query_json, user_info):

            data["alert"] = "Please check your query!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        data['message'] = "User Role successfully updated!"
        data['status'] = "ok"
        return self.return_data(data, userid)

    def update_users(self, query_json, user_info):
        """Update Users"""

        # UPDATE
        # INIT CONDITION
        conditions = []

        conditions.append({
            "col": "account_id",
            "con": "=",
            "val": user_info['account_id']
            })

        conditions.append({
            "col": "remote_addr",
            "con": "=",
            "val": user_info['remote_addr']
            })

        conditions.append({
            "col": "platform",
            "con": "=",
            "val": user_info['platform']
            })

        conditions.append({
            "col": "browser",
            "con": "=",
            "val": user_info['browser']
            })

        conditions.append({
            "col": "version",
            "con": "=",
            "val": user_info['version']
            })

        sql_str = "SELECT role_id FROM role WHERE"
        sql_str += " role_name='{0}'".format(query_json['role_name'])
        acc_role = self.postgres.query_fetch_one(sql_str)
        role_id = acc_role['role_id']

        data = {}
        data['role_id'] = role_id
        data['update_on'] = time.time()

        # UPDATE ROLE
        if self.postgres.update('account_token', data, conditions):

            # RETURN
            return 1

        # RETURN
        return 0
