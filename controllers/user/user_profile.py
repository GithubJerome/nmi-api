"""User Profile"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class UserProfile(Common):
    """Class for """

    # INITIALIZE
    def __init__(self):
        """The Constructor for UserProfile class"""
        self.postgres = PostgreSQL()

        super(UserProfile, self).__init__()

    # LOGIN FUNCTION
    def user_profile(self):
        """
        This API is for Getting User Information
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
            description: User Information
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

        # OPEN CONNECTION
        self.postgres.connection()

        if not self.check_account(userid):
            data["alert"] = "Account does not exist"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        datas = self.get_users(userid)

        # CLOSE CONNECTION
        self.postgres.close_connection()

        datas['status'] = 'ok'

        return self.return_data(datas)

    def get_users(self, userid):
        """Return Users"""

        # DATA
        sql_str = "SELECT * FROM account_master WHERE id='{0}'".format(userid)

        res = self.postgres.query_fetch_one(sql_str)
        data = {}

        if res:
            if "no_username" in res['username']:
                res['username'] = ""

        # REMOVE PASSWORD
        del res['password']

        data['data'] = res

        return data

    def check_account(self, account_id):
        """ Return if account does not exist """

        sql_str = "SELECT * FROM account WHERE id='{0}'".format(account_id)
        result = self.postgres.query_fetch_one(sql_str)

        if result:
            return 1

        return 0
