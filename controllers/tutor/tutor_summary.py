# pylint: disable=no-self-use, too-many-function-args
"""Tutor Summary"""
import time

from flask import  request
from library.common import Common
from library.sha_security import ShaSecurity
from library.postgresql_queries import PostgreSQL

class TutorSummary(Common):
    """Class for TutorSummary"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for ExerciseSummary class"""
        self.postgresql_query = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(TutorSummary, self).__init__()

    def tutor_summary(self):
        """
        This API is for Getting the tutor's exercise summary
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
        responses:
          500:
            description: Error
          200:
            description: Tutor Exercise Summary
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

        if not self.is_tutor_exercise(userid, exercise_id):
            data["alert"] = "Exercise not found"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        data['data'] = self.get_exercise_summary(exercise_id, userid)
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def get_exercise_summary(self, exercise_id, user_id):
        """ RETURN EXERCISE SUMMARY """

        sql_str = "SELECT se.*, e.passing_criterium, c.course_name, c.exercise_name, s.section_name,"
        sql_str += " ss.subsection_name, c.requirements, c.course_title FROM tutor_exercise se"
        sql_str += " LEFT JOIN exercise e ON se.exercise_id = e.exercise_id"
        sql_str += " LEFT JOIN course c ON e.course_id = c.course_id"
        sql_str += " LEFT JOIN section s ON e.section_id = s.section_id"
        sql_str += " LEFT JOIN subsection ss ON e.subsection_id = ss.subsection_id"
        sql_str += " WHERE se.exercise_id='{0}'".format(exercise_id)
        sql_str += " AND se.status is True AND se.account_id = '{0}'".format(user_id)
        result = self.postgres.query_fetch_one(sql_str)

        if result:

            sql_str = "SELECT seq.*, question, question_type, correct_answer,"
            sql_str += " correct, incorrect, feedback, description, status"
            sql_str += " FROM tutor_exercise_questions seq LEFT JOIN course_question"
            sql_str += " cq ON seq.course_question_id = cq.course_question_id"
            sql_str += " WHERE seq.tutor_exercise_id='{0}'".format(result['tutor_exercise_id'])
            sql_str += " ORDER BY seq.sequence"

            questions = self.postgres.query_fetch_all(sql_str)

            for question in questions:

                ans = self.check_answer(question['course_question_id'], question['answer'], flag=True)
                question['message'] = ans['message']
                question['isCorrect'] = ans['isCorrect']
                # question['correct_answer'] = question['correct_answer']['answer']
                question['correct_answer'] = ans['correct_answer']
                question['question'] = question['question']['question']

                self.remove_key(question, "correct")
                self.remove_key(question, "incorrect")
                self.remove_key(question, "tutor_exercise_id")

            if result['progress'] and result['percent_score']:
                result['progress'] = self.format_progress(round(float(result['progress']), 2))
                result['percent_score'] =  self.format_progress(round(float(result['percent_score']), 2))

            result['exercise_num'] = "Exercise {0}".format(result['exercise_number'])
            if result['exercise_name']:
                result['exercise_num'] = "{0} {1}".format(result['exercise_name'], result['exercise_number'])

            result['questions'] = questions

            # CHECK IF PASS
            result['pass'] = "Not Pass"
            if result['score'] is not None:
                if result['score'] >= result['passing_criterium']:
                    result['pass'] = "Pass"
            result['pass'] = self.translate(user_id, result['pass'])

            # TIME USED
            time_used = "15 minutes"
            time_used = time_used.split(" ")
            period = self.translate(user_id, time_used[-1])
            result['time_used'] = "{0} {1}".format(time_used[0], period)

            self.remove_key(result, "tutor_exercise_id")
            self.remove_key(result, "account_id")
            self.remove_key(result, "course_id")

        result['next_exercise'] = self.next_exercise(exercise_id)

        return result

    def next_exercise(self, exercise_id):
        """ Return Next Exercise """

        next_exercise_id = None

        sql_str = "SELECT subsection_id, exercise_number FROM exercise WHERE"
        sql_str += " exercise_id='{0}'".format(exercise_id)
        exercise = self.postgres.query_fetch_one(sql_str)

        if exercise:

            exercise_number = int(exercise['exercise_number']) + 1
            sql_str = "SELECT exercise_id FROM"
            sql_str += " exercise WHERE exercise_number='{0}'".format(exercise_number)
            sql_str += " AND subsection_id='{0}'".format(exercise['subsection_id'])
            exercise_id = self.postgres.query_fetch_one(sql_str)

            if exercise_id:

                return exercise_id['exercise_id']

        return next_exercise_id

    def is_tutor_exercise(self, userid, exercise_id):
        """ RETURN IF TUTOR EXERCISE """

        sql_str = "SELECT r.role_name FROM role r INNER JOIN"
        sql_str += " account_role ar ON r.role_id=ar.role_id WHERE"
        sql_str += " r.role_name='manager' AND"
        sql_str += " ar.account_id='{0}'".format(userid)
        result = self.postgres.query_fetch_one(sql_str)
        if result:
            return 1

        sql_str = "SELECT * FROM tutor_exercise WHERE"
        sql_str += " exercise_id = '{0}' AND account_id= '{1}'".format(exercise_id, userid)
        sql_str += " AND status is True"
        result = self.postgres.query_fetch_one(sql_str)

        if result:
            return 1

        # sql_str = "SELECT * FROM exercise WHERE "
        # sql_str += "exercise_id='{0}'".format(exercise_id)
        # exercise = self.postgres.query_fetch_one(sql_str)

        # if exercise:
        #     course_id = exercise['course_id']

        #     sql_str = "SELECT * FROM tutor_courses"
        #     sql_str += " WHERE course_id = '{0}'".format(course_id)
        #     sql_str += " AND account_id='{0}'".format(userid)
        #     result = self.postgres.query_fetch_one(sql_str)

        #     if result:

        #         sql_str = "SELECT * FROM tutor_section WHERE"
        #         sql_str += " section_id='{0}'".format(exercise['section_id'])
        #         sql_str += " AND account_id='{0}'".format(userid)
        #         section = self.postgres.query_fetch_one(sql_str)

        #         if not section:

        #             temp = {}
        #             temp['tutor_section_id'] = self.sha_security.generate_token(False)
        #             temp['account_id'] = userid
        #             temp['course_id'] = course_id
        #             temp['section_id'] = exercise['section_id']
        #             temp['progress'] = 0
        #             temp['percent_score'] = 0
        #             temp['status'] = True
        #             temp['created_on'] = time.time() 
        #             self.postgres.insert('tutor_section', temp, 'tutor_exercise_id')

        #         sql_str = "SELECT * FROM tutor_subsection WHERE"
        #         sql_str += " subsection_id='{0}'".format(exercise['subsection_id'])
        #         sql_str += " AND account_id='{0}'".format(userid)
        #         subsection = self.postgres.query_fetch_one(sql_str)

        #         if not subsection:

        #             temp = {}
        #             temp['tutor_subsection_id'] = self.sha_security.generate_token(False)
        #             temp['account_id'] = userid
        #             temp['course_id'] = course_id
        #             temp['section_id'] = exercise['section_id']
        #             temp['subsection_id'] = exercise['subsection_id']
        #             temp['progress'] = 0
        #             temp['percent_score'] = 0
        #             temp['status'] = True
        #             temp['created_on'] = time.time()
        #             self.postgres.insert('tutor_subsection', temp, 'tutor_exercise_id')

        #         tmp = {}
        #         tmp['tutor_exercise_id'] = self.sha_security.generate_token(False)
        #         tmp['exercise_id'] = exercise_id
        #         tmp['account_id'] = userid
        #         tmp['course_id'] = course_id
        #         tmp['exercise_number'] = exercise['exercise_number']
        #         tmp['time_used'] = 0
        #         tmp['score'] = 0
        #         tmp['progress'] = 0
        #         tmp['percent_score'] = 0
        #         tmp['status'] = True
        #         tmp['created_on'] = time.time()
        #         self.postgres.insert('tutor_exercise', tmp, 'tutor_exercise_id')
            
        #         return 1

        return 0