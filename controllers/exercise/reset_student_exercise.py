# pylint: disable=no-self-use, too-many-function-args
"""Reset Exercise"""
import time
import json
import random

from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.questions import Questions
from library.progress import Progress

class ResetStudentExercise(Common):
    """Class for ResetExercise"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for ResetExercise class"""
        self.postgresql_query = PostgreSQL()
        self.sha_security = ShaSecurity()
        self.questionnaires = Questions()
        self.progress = Progress()
        super(ResetStudentExercise, self).__init__()

    def reset_student_exercise(self):
        """
        This API is for Resetting Student's Exercise
        ---
        tags:
          - Student Exercise
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
            description: Reset Student Exercise by course ID (admin use only)
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

        if not self.regenerate_student_exercise(userid, course_id):
            data["alert"] = "Failed to generate exercise"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        data['message'] = "New set of questions has been successfully generated"
        data['status'] = 'ok'

        return self.return_data(data, userid)


    def regenerate_student_exercise(self, user_id, course_id):
        """ Generate New set of exercise for Student """

        sql_str = "SELECT * FROM exercise"
        sql_str += " WHERE course_id IN (SELECT course_id FROM student_course"
        sql_str += " WHERE account_id = '{0}' AND course_id = '{1}')".format(user_id, course_id)
        results = self.postgres.query_fetch_all(sql_str)

        for result in results:

            course_id = result['course_id']
            exercise_id = result['exercise_id']

            sql_str = "SELECT * FROM student_exercise"
            sql_str += " WHERE exercise_id = '{0}'".format(exercise_id)
            sql_str += " AND account_id = '{0}'".format(user_id)
            sql_str += " AND status = true"
            student_exercise = self.postgres.query_fetch_one(sql_str)

            if student_exercise:

                student_exercise_id = student_exercise['student_exercise_id']

                # UPDATE STATUS OF OLD EXERCISE
                tmp = {}
                tmp['status'] = False
                tmp['update_on'] = time.time()

                conditions = []

                conditions.append({
                    "col": "exercise_id",
                    "con": "=",
                    "val": exercise_id
                })

                conditions.append({
                    "col": "student_exercise_id",
                    "con": "=",
                    "val": student_exercise_id
                })

                conditions.append({
                    "col": "account_id",
                    "con": "=",
                    "val": user_id
                })

                # data = self.remove_key(tmp, "exercise_id")
                # data = self.remove_key(tmp, "account_id")
                self.postgres.update('student_exercise', tmp, conditions)

            # ADD NEW EXERCISE
            self.questionnaires.generate_questions(user_id, course_id,
                                                   exercise_id, "student")
            # UPDATE PROGRESS FROM COURSE TO SUBSECTION
            self.progress.update_course_progress(user_id, exercise_id, "student")
            self.progress.update_section_progress(user_id, exercise_id, "student")
            self.progress.update_subsection_progress(user_id, exercise_id, "student")

        return 1
