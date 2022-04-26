# pylint: disable=too-many-function-args
"""Course Details"""

from flask import  request
from library.common import Common

class CourseDetails(Common):
    """Class for CourseDetails"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CourseDetails class"""
        super(CourseDetails, self).__init__()

    def course_details(self):
        """
        This API is for Getting Course details
        ---
        tags:
          - Course
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

        responses:
          500:
            description: Error
          200:
            description: Course Hierarchy
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        course_id = request.args.get('course_id')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        if not self.is_tutor_course(userid, course_id):
            data["alert"] = "Course not found"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        # FETCH COURSE DETAILS
        result = self.fetch_course_details(userid, course_id)

        data = {}
        data['data'] = result
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def is_tutor_course(self, user_id, course_id):
        """ Validate Student Course """

        sql_str = "SELECT r.role_name FROM role r INNER JOIN"
        sql_str += " account_role ar ON r.role_id=ar.role_id WHERE"
        sql_str += " r.role_name='manager' AND"
        sql_str += " ar.account_id='{0}'".format(user_id)
        result = self.postgres.query_fetch_one(sql_str)
        if result:
            return 1

        sql_str = "SELECT * FROM tutor_courses WHERE"
        sql_str += " account_id='{0}'".format(user_id)
        sql_str += " AND course_id='{0}'".format(course_id)
        sql_str += " AND status='t'"
        result = self.postgres.query_fetch_one(sql_str)

        if result:
            return 1
        return 0
