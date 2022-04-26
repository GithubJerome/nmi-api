
"""TUTOR COURSES"""

from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class TutorCourse(Common):
    """Class for Tutor Course"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Tutor Course class"""
        self.postgres = PostgreSQL()
        super(TutorCourse, self).__init__()

    def tutor_course(self):
        """
        This API is for Getting Tutor Course
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
            description: Tutor
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

        datas = self.get_courses(userid, page, limit)

        datas['status'] = 'ok'

        return self.return_data(datas, userid)

    def get_courses(self, user_id, page, limit):
        """Return Role"""

        offset = int((page - 1) * limit)

        # COUNT
        sql_str = "SELECT COUNT(*) FROM tutor_courses WHERE"
        sql_str += " account_id='{0}'".format(user_id)

        count = self.postgres.query_fetch_one(sql_str)
        total_rows = count['count']

        # FETCH DATA
        sql_str = "SELECT c.course_id, c.course_name, c.description,"
        sql_str += " c.difficulty_level, c.status, c.course_title"
        sql_str += " FROM tutor_courses tc INNER JOIN course c"
        sql_str += " ON tc.course_id=c.course_id WHERE"
        sql_str += " tc.account_id='{0}'".format(user_id)
        sql_str += " ORDER BY c.difficulty_level"
        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)
        res = self.postgres.query_fetch_all(sql_str)

        total_page = int((total_rows + limit - 1) / limit)

        data = {}
        data['rows'] = res
        data['total_rows'] = total_rows
        data['total_page'] = total_page
        data['limit'] = limit
        data['page'] = page

        return data
