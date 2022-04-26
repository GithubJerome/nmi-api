# pylint: disable=too-many-function-args
"""CourseByIDs"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class CourseByIDs(Common):
    """Class for CourseByIDs"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CourseByIDs class"""
        self.postgresql_query = PostgreSQL()
        super(CourseByIDs, self).__init__()

    def course_by_ids(self):
        """
        This API is for Getting All Courses
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
          - name: selected_ids
            in: query
            description: Selected IDs
            required: false
            type: string
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
        selected_ids = request.args.get('selected_ids')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        datas = self.get_all_courses(selected_ids)
        datas['status'] = 'ok'

        return self.return_data(datas, userid)

    def get_all_courses(self, selected_ids):
        """Return All Courses"""
        
        rows = []

        if selected_ids:
            selected = ','.join("'{0}'".format(selected) for selected in selected_ids.split(","))

            sql_str = "SELECT * FROM course WHERE"
            sql_str += " course_id IN ({0})".format(selected)
            sql_str += " ORDER BY created_on DESC"

            rows = self.postgres.query_fetch_all(sql_str)

        data = {}
        data['rows'] = rows

        return data
