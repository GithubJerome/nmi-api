"""Remove Course Student"""
import string
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.emailer import Email
from templates.invitation import Invitation

class RemoveCourseStudent(Common, ShaSecurity):
    """Class for RemoveCourseStudent"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for RemoveCourseStudent class"""

        self.postgres = PostgreSQL()
        super(RemoveCourseStudent, self).__init__()

    def remove_course_student(self):
        """
        This API is for Removing course students
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
          - name: query
            in: body
            description: Remove Course students
            required: true
            schema:
              id: Remove Course students
              properties:
                student_ids:
                    types: array
                    example: []
                course_id:
                    type: string
        responses:
          500:
            description: Error
          200:
            description: Create User
        """

        # INIT DATA
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # VALIDATE USER
        if not self.validate_user(userid, 'manager'):
            data["alert"] = "Invalid User"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # REMOVE STUDENT TO A COURSE
        self.run(query_json)

        data = {}
        data['message'] = "Students successfully removed to a course"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def run(self, query_json):
        """ REMOVE STUDENT TO A COURSE """

        course_id = query_json['course_id']

        for student_id in query_json['student_ids']:

            # VALIDATE
            sql_str = "SELECT * FROM student_course WHERE"
            sql_str += " account_id='{0}'".format(student_id)
            sql_str += " AND course_id='{0}'".format(course_id)
            res = self.postgres.query_fetch_one(sql_str)

            if res:

                # REMOVE STUDENT TO A COURSE
                conditions = []

                conditions.append({
                    "col": "account_id",
                    "con": "=",
                    "val": student_id
                    })

                conditions.append({
                    "col": "course_id",
                    "con": "=",
                    "val": course_id
                    })

                self.postgres.delete('student_course', conditions)

        return 1
