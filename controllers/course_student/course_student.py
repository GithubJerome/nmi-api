# pylint: disable=too-many-function-args
"""Course Student"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class CourseStudent(Common):
    """Class for CourseStudent"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CourseStudent class"""
        self.postgresql_query = PostgreSQL()
        super(CourseStudent, self).__init__()

    def course_student(self):
        """
        This API is for Getting All Courses Student
        ---
        tags:
          - Course Student
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
          - name: course_id
            in: query
            description: Course ID
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
            description: Course
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        course_id = request.args.get('course_id')
        page = int(request.args.get('page'))
        limit = int(request.args.get('limit'))

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        datas = self.get_course_students(page, limit, course_id)
        datas['status'] = 'ok'

        return self.return_data(datas)

    def get_course_students(self, page, limit, course_id):
        """Return All Courses"""

        offset = int((page - 1) * limit)

        # COUNT
        sql_str = "SELECT COUNT(*) FROM student_course WHERE"
        sql_str += " course_id='{0}'".format(course_id)

        count = self.postgres.query_fetch_one(sql_str)
        total_rows = count['count']

        # DATA
        sql_str = "SELECT id as key, * FROM account WHERE id IN"
        sql_str += " (SELECT account_id FROM student_course WHERE"
        sql_str += " course_id='{0}')".format(course_id)

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
