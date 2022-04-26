# pylint: disable=too-many-function-args
"""Update Course Sequence"""
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from socketIO_client import SocketIO, LoggingNamespace

class UpdateCourseSequence(Common):
    """Class for CourseSequence"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CourseSequence class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(UpdateCourseSequence, self).__init__()

    def update_course_sequence(self):
        """
        This API is for Updating Course Sequence
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
          - name: query
            in: body
            description: Course Sequence
            required: true
            schema:
              id: Course Sequence
              properties:
                course_id:
                    type: string
                sequence_before:
                    type: string
                sequence_after:
                    type: string
        responses:
          500:
            description: Error
          200:
            description: Course Sequence
        """
        data = {}

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

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

        if not self.update_sequence(userid, query_json):

            data["alert"] = "Please check your query!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        data['message'] = "Sequence successfully updated!"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def update_sequence(self, userid, query_json):
        """Update Course Sequence"""

        course_id = query_json['course_id']
        sequence_before = query_json['sequence_before']
        sequence_after = query_json['sequence_after']


        sql_str = "SELECT * FROM course_sequence ORDER BY sequence"
        results = self.postgres.query_fetch_all(sql_str)

        if not results:
            return 0

        courses = [result['course_id'] for result in results]
        course_index = courses.index(course_id)
        courses.remove(course_id)

        if sequence_before:
            prev_index = courses.index(sequence_before)
            sequence_index = prev_index + 10

        if sequence_after:
            next_index = courses.index(sequence_after)
            sequence_index = next_index

        courses.insert(sequence_index, course_id)
        new_index = courses.index(course_id)

        # UPDATE COURSE SEQUENCE
        until_sequence = new_index + 1
        from_index = course_index

        sequence = course_index + 1
        if new_index < course_index:
            from_index = new_index
            until_sequence = course_index + new_index
            sequence = new_index + 1

            if not sequence_before:
                until_sequence = course_index + 1
                from_index = new_index

        slice_sequence = slice(from_index, until_sequence)
        course_sequence = courses[slice_sequence]
        
        for course in course_sequence:

            self.update_item_sequence(course, sequence)
            sequence += 1

        return 1

    def update_item_sequence(self, course_id, sequence):
        """ Update Item Sequence """

        conditions = []
        conditions.append({
            "col": "course_id",
            "con": "=",
            "val": course_id
            })

        data = {}
        data['sequence'] = sequence
        self.postgres.update('course_sequence', data, conditions)
        return 1
