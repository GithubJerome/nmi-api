# pylint: disable=too-many-function-args
"""Exercise"""
import random
import time
import json

from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity

class ExerciseQuestionnaire(Common):
    """Class for ExerciseQuestionnaire"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for ExerciseQuestionnaire class"""
        self.postgresql_query = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(ExerciseQuestionnaire, self).__init__()

    def exercise_question(self):
        """
        This API is for Getting Course exercise questionnaire
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
          - name: exercise_id
            in: query
            description: Exercise ID
            required: false
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

        if exercise_id:
            if not self.is_course_exercise(course_id, exercise_id):
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
        sql_str = "SELECT *, (SELECT array_to_json(array_agg(section)) FROM ("
        sql_str += " SELECT * FROM section WHERE course_id = '{0}') AS section)".format(course_id)
        sql_str += " as sections, (SELECT array_to_json(array_agg(subsection)) FROM ("
        sql_str += " SELECT * FROM subsection WHERE section_id IN (SELECT section_id FROM"
        sql_str += " section WHERE course_id='{0}')) as subsection)".format(course_id)
        sql_str += " as subsections FROM course c LEFT JOIN student_course sc"
        sql_str += " ON c.course_id = sc.course_id WHERE sc.account_id = '{0}'".format(userid)
        sql_str += " AND sc.course_id='{0}'".format(course_id)

        result = self.postgres.query_fetch_one(sql_str)

        if result:
            self.remove_key(result, "account_id")
            self.remove_key(result, "update_on")
            self.remove_key(result, "created_on")

            course_id = result['course_id']
            # self.get_exercise_questionnaires(course_id, userid)
            # GET ALL EXERCISE
            result['exercises'] = self.get_assigned_exercise(course_id, exercise_id, userid)

        return result

    def get_exercise_questionnaires(self, course_id, user_id):
        """ Return Exercise with questionnaires"""

        # GET COURSE SUBSECTION ID
        sql_str = "SELECT * FROM subsection sc"
        sql_str += " LEFT JOIN section s ON sc.section_id = s.section_id"
        sql_str += " WHERE s.course_id = '{0}'".format(course_id)
        result = self.postgres.query_fetch_all(sql_str)

        subsections = [res['subsection_id'] for res in result]
        subsection_ids = ','.join("'{0}'".format(subsection) for subsection in subsections)

        sql_str = "SELECT DISTINCT exercise_id FROM exercise"
        sql_str += " WHERE subsection_id IN ({0}) AND exercise_id ".format(subsection_ids)
        sql_str += " NOT IN (SELECT DISTINCT exercise_id FROM student_exercise)"
        result = self.postgres.query_fetch_all(sql_str)

        data = []
        if result:
            exercises = [res['exercise_id'] for res in result]
            for exercise in exercises:
                # GET EXERCISE QUESTIONNAIRE
                data.append(self.get_exercise_info(course_id, exercise))

        data = sorted(data, key=lambda i: i["exercise_number"])

        # SAVE TO STUDENT EXERCISE
        self.add_student_exercise(user_id, course_id, data)

        return data

    def get_exercise_info(self, course_id, exercise_id):
        """ Return Exercise Information """

        sql_str = "SELECT exercise_id, exercise_number, description"
        sql_str += " FROM exercise WHERE exercise_id = '{0}'".format(exercise_id)
        result = self.postgres.query_fetch_one(sql_str)

        if result:
            sql_str = "SELECT course_question_id FROM course_question"
            sql_str += " WHERE course_id = '{0}'".format(course_id)
            sql_str += " AND exercise_id='{0}'".format(exercise_id)
            course_question = self.postgres.query_fetch_all(sql_str)

            questions = [question['course_question_id'] for question in course_question]
            random.shuffle(questions)
            questions = questions[:10]
            question_ids = ','.join("'{0}'".format(question) for question in questions)

            # GET 10 RANDOM QUESTIONS
            sql_str = "SELECT course_question_id, question, question_type, choices,"
            sql_str += " '' as answer, False as answered FROM course_question WHERE"
            sql_str += " course_question_id IN ({0})".format(question_ids)
            questions = self.postgres.query_fetch_all(sql_str)

            result['questions'] = questions

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

    def add_student_exercise(self, user_id, course_id, data):
        """ Assign Exercise to Student """

        if data:

            for exercise in data:

                temp = {}
                temp['exercise_id'] = exercise['exercise_id']
                temp['account_id'] = user_id
                temp['course_id'] = course_id
                temp['exercise_number'] = exercise['exercise_number']
                temp['questions'] = json.dumps(exercise['questions'])
                temp['status'] = True
                temp['created_on'] = time.time()

                self.postgres.insert('student_exercise', temp, 'course_id')

        return 1

    def get_assigned_exercise(self, course_id, exercise_id, user_id):
        """ Return Exercise with questionnaires"""

        # DATA
        sql_str = "SELECT * FROM exercise e"
        sql_str += " LEFT JOIN student_exercise se ON e.exercise_id = se.exercise_id"
        sql_str += " WHERE se.course_id = '{0}' AND se.status is True".format(course_id)

        if exercise_id:
            sql_str += " AND e.exercise_id ='{0}'".format(exercise_id)

        sql_str += " AND se.account_id='{0}' ORDER BY se.exercise_number".format(user_id)

        result = self.postgres.query_fetch_all(sql_str)

        if result:

            i = 0
            for res in result:

                if res['progress'] is not None and int(float(res['progress'])) == 100:
                    res['answered_all'] = True
                else:
                    res['answered_all'] = False

                # PROGRESS
                if res['progress'] is None and res['exercise_number'] == 1:
                    res['progress'] = 0

                if i > 0 and result[i-1]['progress'] is not None \
                    and int(float(result[i-1]['progress'])) == 100 \
                        and res['progress'] is None:

                    res['progress'] = 0

                i += 1

                # ADD CORRECT ANSWER
                res['questions'] = self.with_correct_answer(course_id,
                                                            res['exercise_id'],
                                                            res['questions'])
                self.remove_key(res, "course_id")
                self.remove_key(res, "section_id")
                self.remove_key(res, "account_id")
                self.remove_key(res, "subsection_id")
                self.remove_key(res, "created_on")
                self.remove_key(res, "update_on")

        return result

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
                correct_answer = str(course_questions[index]['correct_answer'])

                if question['answer'] != "":
                    question['correct_answer'] = correct_answer
                else:
                    question['correct_answer'] = ""

            except ValueError:
                pass

        return questions
