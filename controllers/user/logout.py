# pylint: disable=too-many-function-args
"""Logout"""
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity

class Logout(Common):
    """Class for Logout"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Logout class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(Logout, self).__init__()

    def logout(self):
        """
        This API is for Logout
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
        responses:
          500:
            description: Error
          200:
            description: Create Course
        """
        data = {}

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

        self.logout_user(userid, request)

        data['message'] = "Successfully Logout!"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def logout_user(self, account_id, request_info):
        """ LOG OUT USER """

        data = {}
        data['update_on'] = time.time()
        data['status'] = False

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

        sql_str = "UPDATE account_logs SET"
        sql_str += " logout={0},".format(time.time())
        sql_str += " update_on={0} WHERE".format(time.time())
        sql_str += " account_id='{0}' AND logout IS NULL".format(account_id)

        self.postgres.connection()
        self.postgres.exec_query(sql_str, False)
        self.postgres.conn.commit()
        self.postgres.close_connection()

        return 1
