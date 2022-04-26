"""User Group"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class TutorGroupTable(Common):
    """Class for UserGroup"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UserGroup class"""
        self.postgres = PostgreSQL()
        super(TutorGroupTable, self).__init__()

    # LOGIN FUNCTION
    def tutor_group_table(self):
        """
        This API is for Getting all Tutor group
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
        # sort_type = request.args.get('sort_type')
        # sort_column = request.args.get('sort_column')
        # filter_column = request.args.get('filter_column')
        # filter_value = request.args.get('filter_value')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # VALIDATE USER
        if not self.validate_user(userid, 'tutor'):
            data["alert"] = "Invalid User"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)


        # # COUNT
        # count_str = "SELECT COUNT(*) FROM user_group_master"
        # count = self.postgres.query_fetch_one(count_str)

        # COUNT
        sql_str = "SELECT COUNT(user_group_id) FROM user_group WHERE"
        sql_str += " user_group_id IN (SELECT user_group_id FROM"
        sql_str += " user_group_tutors WHERE"
        sql_str += " tutor_id='{0}')".format(userid)

        count = self.postgres.query_fetch_one(sql_str)

        total_rows = count['count']
        total_page = int((total_rows + limit - 1) / limit)
        data = {}
        data['status'] = 'ok'
        data['page'] = page
        data['limit'] = limit
        data['rows'] = self.get_user_group(userid, page, limit)
        data['total_rows'] = total_rows
        data['total_page'] = total_page

        return self.return_data(data, userid)

    def get_user_group(self, userid, page, limit):
        """ RETURN USER GROUP """
        offset = int((page - 1) * limit)

        sql_str = "SELECT ugm.user_group_id as key, * FROM user_group_master ugm"
        sql_str += " LEFT JOIN user_group ug ON ugm.user_group_id = ug.user_group_id"
        sql_str += " WHERE ug.user_group_id IN"
        sql_str += " (SELECT user_group_id FROM"
        sql_str += " user_group_tutors WHERE"
        sql_str += " tutor_id='{0}')".format(userid)
        sql_str += " ORDER BY ug.user_group_name DESC"
        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)

        return self.postgres.query_fetch_all(sql_str)
