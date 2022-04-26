# pylint: disable=too-many-function-args
"""Exercise"""
import time
import random

from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.questions import Questions

class TutorExercise(Common):
    """Class for TutorExercise"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for TutorExercise class"""
        self.postgresql_query = PostgreSQL()
        self.sha_security = ShaSecurity()
        self.questionnaires = Questions()
        super(TutorExercise, self).__init__()

    def tutor_exercise(self):
        """
        This API is for Getting Tutor Course Exercise questionnaires
        ---
        tags:
          - Tutor / Manager
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
          - name: exercise_id
            in: query
            description: Exercise ID
            required: true
            type: string
        responses:
          500:
            description: Error
          200:
            description: Tutor Exercise Questionnaire
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        course_id = request.args.get('course_id')
        exercise_id = request.args.get('exercise_id')


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

        if not self.is_tutor_course(userid, course_id):
            data["alert"] = "Course not found"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        if not self.is_course_exercise(userid, course_id, exercise_id):
            data["alert"] = "Course exercise not found"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        result = self.get_course_exercise(userid, course_id, exercise_id)

        data = {}
        data['data'] = result
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def get_course_exercise(self, userid, course_id, exercise_id):
        """ Return Course Exercise """

        # COURSE DATA

        sql_str = "SELECT c.*, e.*, te.*, c.course_name, c.exercise_name,s.section_id, s.section_name,"
        sql_str += " sub.subsection_id, sub.subsection_name FROM tutor_exercise te"
        sql_str += " LEFT JOIN course c ON te.course_id = c.course_id"
        sql_str += " LEFT JOIN exercise e ON te.exercise_id = e.exercise_id"
        sql_str += " LEFT JOIN subsection sub ON e.subsection_id = sub.subsection_id"
        sql_str += " LEFT JOIN section s ON e.section_id = s.section_id"
        sql_str += " WHERE c.course_id='{0}'".format(course_id)
        sql_str += " AND te.exercise_id ='{0}' AND te.status is True".format(exercise_id)
        sql_str += " AND te.account_id='{0}'".format(userid)
        result = self.postgres.query_fetch_one(sql_str)

        if result:
            self.remove_key(result, "account_id")
            self.remove_key(result, "update_on")
            self.remove_key(result, "created_on")
            self.remove_key(result, "questions")

            course_id = result['course_id']

            # GET ALL EXERCISE
            result['exercises'] = self.get_assigned_exercise(course_id, exercise_id, userid)
            if result['progress'] is not None:
                result['progress'] = self.format_progress(round(float(result['progress']), 2))

            result['exercise_num'] = "Exercise {0}".format(result['exercise_number'])
            if result['exercise_name']:
                result['exercise_num'] = "{0} {1}".format(result['exercise_name'], result['exercise_number'])

        return result

    def is_tutor_course(self, user_id, course_id):
        """ Validate Student Course """

        sql_str = "SELECT r.role_name FROM role r INNER JOIN"
        sql_str += " account_role ar ON r.role_id=ar.role_id WHERE"
        sql_str += " r.role_name='manager' AND"
        sql_str += " ar.account_id='{0}'".format(user_id)
        result = self.postgres.query_fetch_one(sql_str)
        if result:
            return 1

        sql_str = "SELECT * FROM course c"
        sql_str += " LEFT JOIN tutor_courses tc ON c.course_id = tc.course_id"
        sql_str += " WHERE tc.account_id = '{0}'".format(user_id)
        sql_str += " AND tc.course_id='{0}'".format(course_id)
        result = self.postgres.query_fetch_one(sql_str)

        if result:
            return 1
        return 0

    def is_course_exercise(self, userid, course_id, exercise_id):
        """ Validate Student Course Exercise """

        sql_str = "SELECT r.role_name FROM role r INNER JOIN"
        sql_str += " account_role ar ON r.role_id=ar.role_id WHERE"
        sql_str += " r.role_name='manager' AND"
        sql_str += " ar.account_id='{0}'".format(userid)
        result = self.postgres.query_fetch_one(sql_str)
        if result:
            return 1

        sql_str = "SELECT * FROM tutor_exercise"
        sql_str += " WHERE course_id = '{0}'".format(course_id)
        sql_str += " AND exercise_id='{0}'".format(exercise_id)
        sql_str += " AND account_id='{0}'".format(userid)
        result = self.postgres.query_fetch_one(sql_str)

        if result:

            return 1

        # sql_str = "SELECT * FROM tutor_courses"
        # sql_str += " WHERE course_id = '{0}'".format(course_id)
        # sql_str += " AND account_id='{0}'".format(userid)
        # result = self.postgres.query_fetch_one(sql_str)

        # if result:

        #     sql_str = "SELECT * FROM exercise WHERE "
        #     sql_str += "exercise_id='{0}'".format(exercise_id)
        #     exercise = self.postgres.query_fetch_one(sql_str)

        #     if exercise:

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

    def get_assigned_exercise(self, course_id, exercise_id, user_id):
        """ Return Exercise with questionnaires"""

        # DATA
        results = []
        sql_str = "SELECT te.exercise_id, te.exercise_number, te.score,"
        sql_str += " te.tutor_exercise_id, e.description as exercise_description,"
        sql_str += " te.progress, e.save_seed, e.shuffled FROM tutor_exercise te"
        sql_str += " LEFT JOIN exercise e ON te.exercise_id = e.exercise_id"
        sql_str += " WHERE te.course_id = '{0}' AND te.status is True".format(course_id)
        sql_str += " AND te.exercise_id ='{0}'".format(exercise_id)
        sql_str += " AND te.account_id='{0}' ORDER BY exercise_number".format(user_id)
        result = self.postgres.query_fetch_one(sql_str)

        if result:
    
            # PROGRESS
            if result['progress'] is None and result['exercise_number'] == 1:
                result['progress'] = 0

            result['answered_all'] = False
            if result['progress'] is not None:
                result['progress'] = self.format_progress(round(float(result['progress']), 2))

                if result['progress'] == 100:
                    result['answered_all'] = True

            # CHECK SAVE SEED IF FALSE
            if result['save_seed'] is False:
                self.questionnaires.regenerate_questions(exercise_id, user_id, "tutor")

            # QUESTIONS
            result['questions'] = self.get_questions(result['tutor_exercise_id'], user_id)

            # ADD CORRECT ANSWER
            result['questions'] = self.with_correct_answer(course_id,
                                                           result['exercise_id'],
                                                           result['questions'])
            results.append(result)
        return results

    def get_questions(self, tutor_exercise_id, user_id):
        """ Return Set of Questions """

        sql_str = "SELECT question, choices, description, False as answered,"
        sql_str += " correct_answer, question_type, teq.*,"
        sql_str += " cq.shuffle_options, cq.num_eval FROM tutor_exercise_questions teq LEFT JOIN"
        sql_str += " course_question cq ON teq.course_question_id = cq.course_question_id WHERE"
        sql_str += " tutor_exercise_id ='{0}'".format(tutor_exercise_id)
        sql_str += " ORDER BY sequence"
        course_questions = self.postgres.query_fetch_all(sql_str)

        if course_questions:
            for question in course_questions:

                question['question'] = question['question']['question']
                if question['num_eval']:
                    question['question'] = self.swap_decimal_symbol(user_id, question['question'])
                    question['choices'] = self.swap_decimal_symbol(user_id, question['choices'])

                if question['shuffle_options'] is not None and \
                   question['shuffle_options'] is True:

                    random.shuffle(question['choices'])

                self.remove_key(question, "shuffle_options")

                question['is_mfraction'] = False
                question['mfraction'] = ""

                if len(question['correct_answer']['answer']) == 3:

                    mfraction = question['correct_answer']['answer'][2]
                    mfraction = mfraction.replace("\"", "")
                    mfraction = mfraction.replace("\'", "")

                    question['is_mfraction'] = True
                    question['mfraction'] = mfraction.upper()

                del question['correct_answer']

        return course_questions

    def with_correct_answer(self, course_id, exercise_id, questions):
        """ RETURN WITH CORRECT ANSWER """

        sql_str = "SELECT * FROM course_question"
        sql_str += " WHERE course_id='{0}'".format(course_id)
        sql_str += " AND exercise_id='{0}'".format(exercise_id)
        course_questions = self.postgres.query_fetch_all(sql_str)
        question_ids = [cquestion['course_question_id'] for cquestion in course_questions]

        for question in questions:

            try:
                index = question_ids.index(question['course_question_id'])
                correct_answer = str(course_questions[index]['correct_answer']['answer'])

                if question['answer'] not in [None, '', []]:
                    question['correct_answer'] = correct_answer
                    question['answered'] = True
                else:
                    question['correct_answer'] = ""

                question['is_skip'] = False
                if question['answer'] == "":
                    question['is_skip'] = True

            except ValueError:
                pass

        # questions = sorted(questions, key=lambda i: i['is_skip'])
        questions = sorted(questions, key=lambda i: i['skip_times'])

        return questions
