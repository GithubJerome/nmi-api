"""Tutor"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class Tutors(Common):
    """Class for Tutor"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Tutor class"""
        self.postgres = PostgreSQL()
        super(Tutors, self).__init__()

    # LOGIN FUNCTION
    def tutors(self):
        """
        This API is for Getting All Tutor
        ---
        tags:
          - Tutor
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
          - name: limit
            in: query
            description: Limit
            required: true
            type: integer
          - name: page
            in: query
            description: Page
            required: true
            type: integer
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
        page = int(request.args.get('page'))
        limit = int(request.args.get('limit'))

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # CHECK ACCESS RIGHTS
        if not self.can_access_tutorenv(userid):
            data['alert'] = "Sorry, you have no rights to access this!"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        datas = self.get_users(page, limit)

        datas['status'] = 'ok'

        return self.return_data(datas)

    def get_users(self, page, limit):
        """Return Users"""

        offset = int((page - 1) * limit)

        sql_str = "SELECT * FROM account_master WHERE id IN ("
        sql_str += " SELECT account_id FROM account_role WHERE"
        sql_str += " role_id IN (SELECT role_id FROM role WHERE role_name ='tutor'))"

        # COUNT
        count_str = "SELECT COUNT(*) FROM ({0}) as accounts".format(sql_str)
        count = self.postgres.query_fetch_one(count_str)

        #LIMIT
        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)

        accounts = self.postgres.query_fetch_all(sql_str)

        # CHECK USERNAME
        if accounts:

            for account in accounts:
                if "no_username" in account['username']:
                    account['username'] = ""

                # REMOVE PASSWORD
                self.remove_key(account, "password")

        total_rows = count['count']
        total_page = int((total_rows + limit - 1) / limit)
        data = {}
        data['rows'] = accounts
        data['total_rows'] = total_rows
        data['total_page'] = total_page
        data['limit'] = limit
        data['page'] = page

        return data
