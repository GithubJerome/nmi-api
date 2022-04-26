# pylint: disable=too-many-function-args
"""Exercise"""
import time
import random

from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.questions import Questions

class StudentExercise(Common):
    """Class for StudentExercise"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for StudentExercise class"""
        self.postgresql_query = PostgreSQL()
        self.sha_security = ShaSecurity()
        self.questionnaires = Questions()
        super(StudentExercise, self).__init__()

    def student_exercise(self):
        """
        This API is for Getting Course Exercise questionnaires
        ---
        tags:
          - Student Course
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
            description: Exercise Questionnaire
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

        if not self.is_student_course(userid, course_id):
            data["alert"] = "Course not found"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        if not self.is_course_exercise(course_id, exercise_id):
            data["alert"] = "Course exercise not found"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        result = self.get_course_exercise(userid, course_id, exercise_id)

        # EXERCISE LOG
        self.exercise_log(exercise_id, userid)

        data = {}
        data['data'] = result
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def get_course_exercise(self, userid, course_id, exercise_id):
        """ Return Course Exercise """

        # COURSE DATA

        sql_str = "SELECT c.*, e.*, se.*, c.course_name, s.section_id, s.section_name,"
        sql_str += " sub.subsection_id, sub.subsection_name FROM student_exercise se"
        sql_str += " LEFT JOIN course c ON se.course_id = c.course_id"
        sql_str += " LEFT JOIN exercise e ON se.exercise_id = e.exercise_id"
        sql_str += " LEFT JOIN subsection sub ON e.subsection_id = sub.subsection_id"
        sql_str += " LEFT JOIN section s ON e.section_id = s.section_id"
        sql_str += " WHERE c.course_id='{0}'".format(course_id)
        sql_str += " AND se.exercise_id ='{0}' AND se.status is True".format(exercise_id)
        sql_str += " AND se.account_id='{0}'".format(userid)

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

    def is_student_course(self, user_id, course_id):
        """ Validate Student Course """

        sql_str = "SELECT * FROM course c"
        sql_str += " LEFT JOIN student_course sc ON c.course_id = sc.course_id"
        sql_str += " WHERE sc.account_id = '{0}'".format(user_id)
        sql_str += " AND sc.course_id='{0}'".format(course_id)
        result = self.postgres.query_fetch_one(sql_str)

        if result:
            return 1
        return 0

    def is_course_exercise(self, course_id, exercise_id):
        """ Validate Student Course Exercise """

        sql_str = "SELECT * FROM student_exercise"
        sql_str += " WHERE course_id = '{0}'".format(course_id)
        sql_str += " AND exercise_id='{0}'".format(exercise_id)
        result = self.postgres.query_fetch_one(sql_str)

        if result:
            return 1
        return 0

    def get_assigned_exercise(self, course_id, exercise_id, user_id):
        """ Return Exercise with questionnaires"""

        # DATA
        results = []
        sql_str = "SELECT se.exercise_id, se.exercise_number, se.score, c.exercise_name,"
        sql_str += " se.student_exercise_id, e.description as exercise_description,"
        sql_str += " se.progress, e.save_seed, e.shuffled FROM student_exercise se"
        sql_str += " LEFT JOIN exercise e ON se.exercise_id = e.exercise_id"
        sql_str += " LEFT JOIN course c ON se.course_id = c.course_id"
        sql_str += " WHERE se.course_id = '{0}' AND se.status is True".format(course_id)
        sql_str += " AND se.exercise_id ='{0}'".format(exercise_id)
        sql_str += " AND se.account_id='{0}' ORDER BY exercise_number".format(user_id)
        result = self.postgres.query_fetch_one(sql_str)

        if result:

            result['exercise_num'] = "Exercise {0}".format(result['exercise_number'])
            if result['exercise_name']:
                result['exercise_num'] = "{0} {1}".format(result['exercise_name'], result['exercise_number'])

            result['answered_all'] = False
            if result['progress'] is not None:
                result['progress'] = self.format_progress(round(float(result['progress']), 2))

                if result['progress'] == 100:
                    result['answered_all'] = True

            # PROGRESS
            if result['progress'] is None and result['exercise_number'] == 1:
                result['progress'] = 0

            # CHECK SAVE SEED IF FALSE
            # print("Seed: ", result['save_seed'])
            if result['save_seed'] is False:
                self.questionnaires.regenerate_questions(exercise_id, user_id, "student")

            # QUESTIONS
            result['questions'] = self.get_questions(result['student_exercise_id'], user_id)

            # ADD CORRECT ANSWER
            result['questions'] = self.with_correct_answer(course_id,
                                                           result['exercise_id'],
                                                           result['questions'])

            # GET INSTRUCTION
            result['instructions'] = self.get_instruction(result['exercise_id'])

            # UPDATE DATE
            self.update_date(result['questions'])

            results.append(result)
        return results

    def get_questions(self, student_exercise_id, user_id):
        """ Return Set of Questions """

        sql_str = "SELECT language FROM account WHERE"
        sql_str += " id='{0}'".format(user_id)
        language = self.postgres.query_fetch_one(sql_str)

        sql_str = "SELECT question, choices, description, False as answered, "
        sql_str += "correct_answer, question_type, seq.*,"
        sql_str += " cq.shuffle_options, cq.num_eval FROM student_exercise_questions seq LEFT JOIN"
        sql_str += " course_question cq ON seq.course_question_id = cq.course_question_id WHERE"
        sql_str += " student_exercise_id ='{0}'".format(student_exercise_id)
        sql_str += " ORDER BY sequence"
        course_questions = self.postgres.query_fetch_all(sql_str)

        if course_questions:
            for question in course_questions:

                question['question'] = question['question']['question']
                if question['num_eval']:
                    question['question'] = self.swap_decimal_symbol(user_id, question['question'], language=language)
                    question['choices'] = self.swap_decimal_symbol(user_id, question['choices'], language=language)

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

    def update_date(self, questions):
        """ UPDATE update_on FOR STUDENT QUESTIONS """

        for question in questions:

            if not question['answer']:

                sql_str = "SELECT started_on FROM student_exercise_questions WHERE"
                sql_str += " student_exercise_id='{0}'".format(question['student_exercise_id'])
                sql_str += " AND course_question_id='{0}'".format(question['course_question_id'])
                sql_str += " AND account_id='{0}'".format(question['account_id'])
                started_on = self.postgres.query_fetch_one(sql_str)

                if not started_on['started_on']:

                    tmp = {}
                    tmp['started_on'] = time.time()

                    conditions = []

                    conditions.append({
                        "col": "student_exercise_id",
                        "con": "=",
                        "val": question['student_exercise_id']
                    })

                    conditions.append({
                        "col": "course_question_id",
                        "con": "=",
                        "val": question['course_question_id']
                    })

                    conditions.append({
                        "col": "account_id",
                        "con": "=",
                        "val": question['account_id']
                    })

                    self.postgres.update('student_exercise_questions', tmp, conditions)

                break

        return 1

    def get_instruction(self, exercise_id):
        """ Return Instruction by Exercise """

        sql_str = "SELECT * FROM instruction WHERE exercise_id = '{0}'".format(exercise_id)
        result = self.postgres.query_fetch_all(sql_str)
        return result

    def exercise_log(self, exercise_id, user_id):
        """ EXERCISE LOG """

        sql_str = "UPDATE student_exercise SET"
        sql_str += " started_on={0},".format(time.time())
        sql_str += " update_on={0} WHERE".format(time.time())
        sql_str += " account_id='{0}'".format(user_id)
        sql_str += " AND exercise_id='{0}'".format(exercise_id)
        sql_str += " AND status=True"
        sql_str += " AND started_on IS NULL"

        self.postgres.connection()
        self.postgres.exec_query(sql_str, False)
        self.postgres.conn.commit()
        self.postgres.close_connection()

        return 1
