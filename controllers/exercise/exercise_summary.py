# pylint: disable=no-self-use, too-many-function-args
"""Exercise Summary"""
import time
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class ExerciseSummary(Common):
    """Class for ExerciseSummary"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for ExerciseSummary class"""
        self.postgresql_query = PostgreSQL()
        super(ExerciseSummary, self).__init__()

    def summary(self):
        """
        This API is for Getting the exercise summary
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
            description: Exercise Summary
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

        if not self.is_student_exercise(userid, exercise_id):
            data["alert"] = "Exercise not found"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        sql_str = "SELECT language FROM account WHERE"
        sql_str += " id='{0}'".format(userid)
        language = self.postgres.query_fetch_one(sql_str)

        data['data'] = self.get_exercise_summary(exercise_id, userid, language)
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def get_exercise_summary(self, exercise_id, user_id, language):
        """ RETURN EXERCISE SUMMARY """

        sql_str = "SELECT se.*, e.passing_criterium, c.course_name, s.section_name, e.is_repeatable,"
        sql_str += " ss.subsection_name, c.exercise_name, c.requirements, c.course_title FROM student_exercise se"
        sql_str += " LEFT JOIN exercise e ON se.exercise_id = e.exercise_id"
        sql_str += " LEFT JOIN course c ON e.course_id = c.course_id"
        sql_str += " LEFT JOIN section s ON e.section_id = s.section_id"
        sql_str += " LEFT JOIN subsection ss ON e.subsection_id = ss.subsection_id"
        sql_str += " WHERE se.exercise_id='{0}'".format(exercise_id)
        sql_str += " AND se.status is True AND se.account_id = '{0}'".format(user_id)
        result = self.postgres.query_fetch_one(sql_str)

        if result:

            result['exercise_num'] = "Exercise {0}".format(result['exercise_number'])
            if result['exercise_name']:
                result['exercise_num'] = "{0} {1}".format(result['exercise_name'], result['exercise_number'])

            sql_str = "SELECT seq.*, question, question_type, correct_answer, num_eval,"
            sql_str += " correct, incorrect, feedback, description, status"
            sql_str += " FROM student_exercise_questions seq LEFT JOIN course_question"
            sql_str += " cq ON seq.course_question_id = cq.course_question_id"
            sql_str += " WHERE seq.student_exercise_id='{0}'".format(result['student_exercise_id'])
            sql_str += " ORDER BY seq.sequence"

            questions = self.postgres.query_fetch_all(sql_str)

            for question in questions:

                ans = self.check_answer(question['course_question_id'], question['answer'], flag=True)
                question['message'] = ans['message']
                question['is_correct'] = ans['isCorrect']

                question['is_mfraction'] = False
                question['mfraction'] = ""

                if len(question['correct_answer']['answer']) == 3:

                    mfraction = question['correct_answer']['answer'][2]
                    mfraction = mfraction.replace("\"", "")
                    mfraction = mfraction.replace("\'", "")

                    question['is_mfraction'] = True
                    question['mfraction'] = mfraction.upper()

                # question['correct_answer'] = question['correct_answer']['answer']
                question['correct_answer'] = ans['correct_answer']
                question['question'] = question['question']['question']
                if question['num_eval']:
                    question['question'] = self.swap_decimal_symbol(user_id, question['question'], language=language)
                    question['answer'] = self.swap_decimal_symbol(user_id, question['answer'], language=language)
                    question['correct_answer'] = self.swap_decimal_symbol(user_id, ans['correct_answer'], language=language)
                    
                question['answered'] = False
                if question['answer'] not in [None, '', []]:
                    question['answered'] = True

                self.remove_key(question, "correct")
                self.remove_key(question, "incorrect")
                self.remove_key(question, "student_exercise_id")

            if result['progress'] and result['percent_score']:
                result['progress'] = self.format_progress(round(float(result['progress']), 2))
                result['percent_score'] =  self.format_progress(round(float(result['percent_score']), 2))

            result['questions'] = questions

            # CHECK IF PASS
            result['pass'] = "Not Pass"
            if result['score'] is not None:
                if result['score'] >= result['passing_criterium']:
                    result['pass'] = "Pass"
            result['pass'] = self.translate(user_id, result['pass'], language=language)

            # TIME USED
            # time_used = "15 minutes"
            # time_used = time_used.split(" ")
            # period = self.translate(user_id, time_used[-1], language=language)
            result['time_used'] = self.time_studied(user_id, result['started_on'], result['end_on'], language)

            self.remove_key(result, "student_exercise_id")
            self.remove_key(result, "account_id")
            self.remove_key(result, "course_id")

        result['next_exercise'] = self.next_exercise(user_id, exercise_id)

        if result['progress']:

            if int(float(result['progress'])) == 100:

                self.exercise_log(exercise_id, user_id)

        return result

    def next_exercise(self, user_id, exercise_id):
        """ Return Next Exercise """

        next_exercise = {}

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

                exercise_id = exercise_id['exercise_id']
                sql_str = "SELECT * FROM student_exercise WHERE status is True AND"
                sql_str += " exercise_id = '{0}' AND account_id = '{1}'".format(exercise_id, user_id)
                next_exercise = self.postgres.query_fetch_one(sql_str)

                # REQUIREMENTS
                next_exercise['requirements'] = self.get_exercise_requirements(user_id, exercise_id)
                next_exercise['instructions'] = self.get_exercise_instruction(exercise_id)

                return next_exercise

        return next_exercise

    def get_exercise_instruction(self, exercise_id):
        """ Return Instruction by Exercise """

        sql_str = "SELECT * FROM instruction WHERE exercise_id = '{0}'".format(exercise_id)
        result = self.postgres.query_fetch_all(sql_str)
        return result

    def is_student_exercise(self, user_id, exercise_id):
        """ RETURN IF STUDENT EXERCISE """

        sql_str = "SELECT * FROM student_exercise WHERE"
        sql_str += " exercise_id = '{0}' AND account_id= '{1}'".format(exercise_id, user_id)
        sql_str += " AND status is True"
        result = self.postgres.query_fetch_one(sql_str)

        if result:
            return 1

        return 0

    def exercise_log(self, exercise_id, user_id):
        """ EXERCISE LOG """

        sql_str = "UPDATE student_exercise SET"
        sql_str += " end_on={0},".format(time.time())
        sql_str += " update_on={0} WHERE".format(time.time())
        sql_str += " account_id='{0}'".format(user_id)
        sql_str += " AND exercise_id='{0}'".format(exercise_id)
        sql_str += " AND status=True"
        sql_str += " AND end_on IS NULL"

        self.postgres.connection()
        self.postgres.exec_query(sql_str, False)
        self.postgres.conn.commit()
        self.postgres.close_connection()

        return 1
