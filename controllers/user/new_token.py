# pylint: disable=too-many-function-args
"""New Token"""
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity

class NewToken(Common, ShaSecurity):
    """Class for NewToken"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for NewToken class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(NewToken, self).__init__()

    def new_token(self):
        """
        This API is for New Token
        ---
        tags:
          - User
        produces:
          - application/json
        parameters:
          - name: refreshtoken
            in: header
            description: Refresh Token
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
            description: Create Course
        """
        data = {}

        # GET HEADER
        refreshtoken = request.headers.get('refreshtoken')
        userid = request.headers.get('userid')

        # CHECK TOKEN
        token_validation = self.validate_refresh_token(refreshtoken, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Refresh Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        new_token = self.get_new_token(userid, request)

        data['message'] = "New Token generated!"
        data['token'] = new_token
        data['status'] = "ok"

        return self.return_data(data, userid)

    def validate_refresh_token(self, token, account_id, request_info):
        """ VALIDATE REFRESH TOKEN """

        sql_str = "SELECT * FROM account_token WHERE"
        sql_str += " account_id='{0}'".format(account_id)
        sql_str += " AND refresh_token='{0}'".format(token)
        sql_str += " AND remote_addr='{0}'".format(request_info.remote_addr)
        sql_str += " AND platform='{0}'".format(request_info.platform)
        sql_str += " AND browser='{0}'".format(request_info.browser)
        sql_str += " AND version='{0}'".format(request_info.version)

        if not self.postgres.query_fetch_one(sql_str):

            return 0

        return 1

    def get_new_token(self, account_id, request_info):
        """ LOG OUT USER """

        token_expire_date = int(time.time()) + 3600 # ADD 1 HOUR IN CURRENT TIME
        new_token = self.generate_token(False)
        data = {}
        data['update_on'] = time.time()
        data['token'] = new_token
        data['token_expire_date'] = token_expire_date

        conditions = []

        conditions.append({
            "col": "account_id",
            "con": "=",
            "val": account_id
            })

        conditions.append({
            "col": "remote_addr",
            "con": "=",
            "val": request_info.remote_addr
            })

        conditions.append({
            "col": "platform",
            "con": "=",
            "val": request_info.user_agent.platform
            })

        conditions.append({
            "col": "browser",
            "con": "=",
            "val": request_info.user_agent.browser
            })

        conditions.append({
            "col": "version",
            "con": "=",
            "val": request_info.user_agent.version
            })

        self.postgres.update('account_token', data, conditions)

        return new_token
