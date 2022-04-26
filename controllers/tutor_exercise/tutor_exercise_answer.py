# pylint: disable=no-self-use, too-many-function-args, too-many-locals
"""Tutor Exercise Answer"""
import json
import time

from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.progress import Progress

class TutorAnswer(Common):
    """Class for TutorAnswer"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for TutorAnswer class"""
        self.postgresql_query = PostgreSQL()
        self.progress = Progress()
        super(TutorAnswer, self).__init__()

    def tutor_answer(self):
        """
        This API is for Getting the correct answer
        ---
        tags:
          - Tutor / Manager Exercise
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
          - name: question_id
            in: query
            description: Question ID
            required: true
            type: string
          - name: query
            in: body
            description: Exercise Answer
            required: true
            schema:
              id: exercise-answer
              properties:
                answer:
                    type: string
        responses:
          500:
            description: Error
          200:
            description: Exercise Answer
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        question_id = request.args.get('question_id')
        exercise_id = request.args.get('exercise_id')

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

        answer = ''

        if 'answer' in query_json.keys():

            answer = query_json['answer']

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

        if not self.check_question(question_id):
            data["alert"] = "No Question ID found"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        message = self.check_answer(question_id, answer, userid=userid, swap=True)

        # UPDATE TUTOR COURSE TABLE FOR ANSWER
        self.update_tutor_answer(userid, exercise_id, question_id, answer, message)

        # UPDATE SCORE
        self.progress.update_score_progress(userid, exercise_id, "tutor")

        # UPDATE PROGRESS
        self.progress.update_course_progress(userid, exercise_id, "tutor")
        self.progress.update_section_progress(userid, exercise_id, "tutor")
        self.progress.update_subsection_progress(userid, exercise_id, "tutor")

        data['data'] = message
        data['status'] = 'ok'

        return self.return_data(data, userid)

    
    def update_tutor_answer(self, user_id, exercise_id, question_id, answer, message):
        """ SAVE ANSWER """

        sql_str = "SELECT * FROM tutor_exercise"
        sql_str += " WHERE exercise_id='{0}' AND account_id='{1}'".format(exercise_id, user_id)
        sql_str += " AND status='true'"
        result = self.postgres.query_fetch_one(sql_str)

        if result:

            # UPDATE ANSWER
            sql_str = "SELECT * FROM tutor_exercise_questions teq LEFT JOIN course_question cq"
            sql_str += " ON teq.course_question_id = cq.course_question_id WHERE"
            sql_str += " teq.tutor_exercise_id='{0}'".format(result['tutor_exercise_id'])
            sql_str += " AND teq.course_question_id='{0}'".format(question_id)
            result = self.postgres.query_fetch_one(sql_str)

            skip_times = 0
            if result['question_type'] == 'FITBT':
                question = result['question']['question'].replace("<ans>", "")
                if question == answer:
                    answer = ""
                    if result['skip_times'] is None:
                        skip_times = 1
                    else:
                        skip_times = result['skip_times'] + 1

            if answer in [None, '', str([""]), str([]), str(['']), [], ['']]:
                if result['skip_times'] is None:
                    skip_times = 1
                else:
                    skip_times = result['skip_times'] + 1

            tmp = {}
            tmp['answer'] = json.dumps(answer)
            tmp['progress'] = 100
            tmp['percent_score'] = 0

            if message['isCorrect']:
                tmp['percent_score'] = 100

            tmp['is_correct'] = message['isCorrect']
            tmp['skip_times'] = skip_times
            tmp['answered_on'] = time.time()
            tmp['update_on'] = time.time()
            conditions = []

            conditions.append({
                "col": "tutor_exercise_id",
                "con": "=",
                "val": result['tutor_exercise_id']
            })

            conditions.append({
                "col": "course_question_id",
                "con": "=",
                "val": result['course_question_id']
            })

            data = self.remove_key(tmp, "tutor_exercise_id")
            data = self.remove_key(tmp, "course_question_id")

            self.postgres.update('tutor_exercise_questions', data, conditions)

        return 1
