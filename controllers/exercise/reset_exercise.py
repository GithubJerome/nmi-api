# pylint: disable=no-self-use, too-many-function-args
"""Reset Exercise"""
import time

from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.questions import Questions
from library.progress import Progress

class ResetExercise(Common):
    """Class for ResetExercise"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for ResetExercise class"""
        self.sha_security = ShaSecurity()
        self.questionnaires = Questions()
        self.progress = Progress()
        super(ResetExercise, self).__init__()

    def reset_exercise(self):
        """
        This API is for Resetting Exercise
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
          - name: exercise_id
            in: query
            description: Exercise ID
            required: true
            type: string

        responses:
          500:
            description: Error
          200:
            description: Reset Exercise
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        exercise_id = request.args.get('exercise_id')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        if not self.check_exercise(exercise_id, userid):
            data["alert"] = "No Exercise ID found"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        if not self.regenerate_questions(userid, exercise_id):
            data["alert"] = "Failed to generate questions"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        data['message'] = "New set of questions has been successfully generated"
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def check_exercise(self, exercise_id, user_id):
        """ Validate Exercise ID """

        # DATA
        sql_str = "SELECT * FROM student_exercise"
        sql_str += " WHERE exercise_id = '{0}' AND status is True".format(exercise_id)
        sql_str += " AND account_id = '{0}'".format(user_id)
        result = self.postgres.query_fetch_one(sql_str)
        if result:
            return 1
        return 0

    def regenerate_questions(self, user_id, exercise_id):
        """ Generate New Exercise Question """

        sql_str = "SELECT * FROM student_exercise"
        sql_str += " WHERE exercise_id = '{0}'".format(exercise_id)
        sql_str += " AND account_id = '{0}'".format(user_id)
        sql_str += " AND status = true"
        result = self.postgres.query_fetch_one(sql_str)

        if result:

            course_id = result['course_id']
            exercise_id = result['exercise_id']
            student_exercise_id = result['student_exercise_id']

            # SAVE STUDENT EXERCISE REPEAT
            self.insert_std_ex_rep(user_id, exercise_id, result)

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

            data = self.remove_key(tmp, "exercise_id")
            data = self.remove_key(tmp, "student_exercise_id")
            self.postgres.update('student_exercise', data, conditions)

            # ADD NEW EXERCISE
            if self.questionnaires.generate_questions(user_id, course_id,
                                                      exercise_id, "student", reset=True):
                # UPDATE PROGRESS FROM COURSE TO SUBSECTION
                self.progress.update_course_progress(user_id, exercise_id, "student")
                self.progress.update_section_progress(user_id, exercise_id, "student")
                self.progress.update_subsection_progress(user_id, exercise_id, "student")

            return 1

        return 0

    def insert_std_ex_rep(self, account_id, exercise_id, ex_data):
        """ INSERT STUDENT EXERCISE REPEAT """

        course_id = ex_data['course_id']
        sql_str = "SELECT student_exercise_repeat_id, is_passed"
        sql_str += " FROM student_exercise_repeat"
        sql_str += " WHERE exercise_id='{0}'".format(exercise_id)
        sql_str += " AND account_id='{0}'".format(account_id)
        std_ex_rep = self.postgres.query_fetch_one(sql_str)

        if std_ex_rep:

            if not std_ex_rep['is_passed']:

                student_exercise_repeat_id = std_ex_rep['student_exercise_repeat_id']
                # UPDATE
                tmp_data = {}
                tmp_data['is_passed'] = True
                tmp_data['update_on'] = time.time()

                conditions = []

                conditions.append({
                    "col": "student_exercise_repeat_id",
                    "con": "=",
                    "val": student_exercise_repeat_id
                })

                self.postgres.update('student_exercise_repeat', tmp_data, conditions)

            return 1

        # INSERT
        sql_str = "SELECT passing_criterium FROM exercise WHERE"
        sql_str += " exercise_id='{0}'".format(exercise_id)
        pcriterium = self.postgres.query_fetch_one(sql_str)

        rep_data = {}
        rep_data['student_exercise_repeat_id'] = self.sha_security.generate_token(False)
        rep_data['course_id'] = course_id
        rep_data['exercise_id'] = exercise_id
        rep_data['account_id'] = account_id

        rep_data['is_passed'] = False

        if int(pcriterium['passing_criterium']) <= int(ex_data['score']):

            rep_data['is_passed'] = True

        rep_data['created_on'] = time.time()

        self.postgres.insert('student_exercise_repeat', rep_data)

        return 1
