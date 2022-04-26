# pylint: disable=no-self-use, too-many-function-args, too-many-locals
"""Exercise Answer"""
import json
import time

from flask import  request
from library.common import Common
# from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.progress import Progress
from library.unlock import Unlock

class ExerciseAnswer(Common):
    """Class for ExerciseAnswer"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for ExerciseAnswer class"""
        # self.postgresql_query = PostgreSQL()
        self.sha_security = ShaSecurity()
        self.progress = Progress()
        self.unlock = Unlock()

        super(ExerciseAnswer, self).__init__()

    def exercise_answer(self):
        """
        This API is for Getting the correct answer
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

        if not self.check_question(question_id):
            data["alert"] = "No Question ID found"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        message = self.check_answer(question_id, answer, userid=userid, swap=True)

        # UPDATE STUDENT COURSE TABLE FOR ANSWER
        self.update_student_answer(userid, exercise_id, question_id, answer, message)

        # UPDATE SCORE
        self.progress.update_score_progress(userid, exercise_id, "student")

        sql_str = "SELECT course_id, section_id, subsection_id FROM exercise WHERE"
        sql_str += " exercise_id='{0}'".format(exercise_id)
        result = self.postgres.query_fetch_one(sql_str)

        course_id = result['course_id']
        section_id = result['section_id']
        subsection_id = result['subsection_id']

        in_group = self.student_in_group(userid, course_id)

        # UPDATE PROGRESS
        self.progress.update_course_progress(userid, exercise_id, "student", course_id=course_id)
        self.progress.update_section_progress(userid, exercise_id, "student", course_id=course_id,
                                              section_id=section_id)
        self.progress.update_subsection_progress(userid, exercise_id, "student",
                                                 course_id=course_id, section_id=section_id,
                                                 subsection_id=subsection_id)

        # UNLOCK NEXT EXERCISE
        self.unlock.unlock_next(userid, token, exercise_id, in_group)

        # VALIDATE LOCK/UNLOCK
        self.unlock.validate_lock_unlock2(token, userid, course_id, in_group, subsect_id=subsection_id)

        data['data'] = message
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def update_student_answer(self, user_id, exercise_id, question_id, answer, message):
        """ SAVE ANSWER """

        sql_str = "SELECT * FROM student_exercise"
        sql_str += " WHERE exercise_id='{0}' AND account_id='{1}'".format(exercise_id, user_id)
        sql_str += " AND status='true'"
        result = self.postgres.query_fetch_one(sql_str)

        if result:

            # UPDATE ANSWER
            sql_str = "SELECT * FROM student_exercise_questions seq LEFT JOIN course_question cq"
            sql_str += " ON seq.course_question_id = cq.course_question_id LEFT JOIN"
            sql_str += " questions q ON cq.question_id = q.question_id WHERE"
            sql_str += " seq.student_exercise_id='{0}'".format(result['student_exercise_id'])
            sql_str += " AND seq.course_question_id='{0}'".format(question_id)
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

            if result['num_eval']:
                answer = self.swap_decimal_symbol(user_id, answer)

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
            tmp['end_on'] = time.time()
            conditions = []

            conditions.append({
                "col": "student_exercise_id",
                "con": "=",
                "val": result['student_exercise_id']
            })

            conditions.append({
                "col": "course_question_id",
                "con": "=",
                "val": result['course_question_id']
            })

            data = self.remove_key(tmp, "student_exercise_id")
            data = self.remove_key(tmp, "course_question_id")

            self.postgres.update('student_exercise_questions', data, conditions)

            # UPDATE TOTAL EXPERIENCE
            self.update_exercise_experience(user_id, result['student_exercise_id'])

        return 1

    def update_exercise_experience(self, user_id, student_exercise_id):
        """ Update Student Exercise Total Experience """

        # QUESTIONS
        # sql_str = "SELECT * FROM student_exercise_questions seq LEFT JOIN"
        # sql_str += " course_question cq ON seq.course_question_id = cq.course_question_id"
        # sql_str += " WHERE student_exercise_id = '{0}'".format(student_exercise_id)
        # print("sqL: {0}".format(sql_str))

        sql_str = """SELECT cq.*, seq.*, e.moving_allowed, q.gain_experience FROM
        student_exercise_questions seq INNER JOIN course_question cq ON
        seq.course_question_id = cq.course_question_id INNER JOIN exercise e ON
        e.exercise_id=cq.exercise_id INNER JOIN questions q ON q.question_id=cq.question_id
        """
        sql_str += " WHERE student_exercise_id = '{0}'".format(student_exercise_id)
        questions = self.postgres.query_fetch_all(sql_str)

        experience = 0
        for question in questions:

            ans = self.check_answer(question['course_question_id'], question['answer'], userid=user_id, result=question, translate=False)

            if ans['isCorrect'] is True:
                # experience += self.get_question_experience(question['question_id'])
                
                expe = 10
                if question['gain_experience']:
                    expe = question['gain_experience']
                experience += expe

        # UPDATE TOTAL EXPERIENCE
        tmp = {}
        tmp['total_experience'] = experience

        conditions = []

        conditions.append({
            "col": "student_exercise_id",
            "con": "=",
            "val": student_exercise_id
        })

        self.postgres.update('student_exercise', tmp, conditions)

    def get_question_experience(self, question_id):
        """ Return Equivalent Experience """

        sql_str = "SELECT * FROM questions WHERE question_id ='{0}'".format(question_id)
        result = self.postgres.query_fetch_one(sql_str)

        if result:

            experience = 10
            if result['gain_experience']:
                experience = result['gain_experience']

            return experience

        return 0

