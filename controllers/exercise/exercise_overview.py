# pylint: disable=no-self-use, too-many-function-args, too-many-locals
"""Exercise Overview"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class ExerciseOverview(Common):
    """Class for ExerciseOverview"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for ExerciseOverview class"""
        self.postgresql_query = PostgreSQL()
        super(ExerciseOverview, self).__init__()

    def exercise_overview(self):
        """
        This API is for Getting the exercise overview
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
            description: Exercise Overview
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
            data["alert"] = "Exercise ID not found"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        result = self.get_exercise_overview(userid, exercise_id)

        data['data'] = result
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def is_student_exercise(self, user_id, exercise_id):
        """ Validate Student Course Exercise """

        sql_str = "SELECT * FROM student_exercise"
        sql_str += " WHERE account_id = '{0}'".format(user_id)
        sql_str += " AND exercise_id='{0}'".format(exercise_id)
        sql_str += " AND status is True"
        result = self.postgres.query_fetch_one(sql_str)

        if result:
            return 1
        return 0

    def get_exercise_overview(self, user_id, exercise_id):
        """Return Exercise Overview"""

        # DATA
        sql_str = "SELECT e.*, se.*, c.course_name, c.exercise_name, s.section_name, ss.subsection_name,"
        sql_str += " c.requirements, c.course_title FROM exercise e LEFT JOIN student_exercise se"
        sql_str += " ON e.exercise_id = se.exercise_id"
        sql_str += " LEFT JOIN course c ON e.course_id = c.course_id"
        sql_str += " LEFT JOIN section s ON e.section_id = s.section_id"
        sql_str += " LEFT JOIN subsection ss ON e.subsection_id = ss.subsection_id WHERE"
        sql_str += " se.exercise_id ='{0}' AND se.account_id ='{1}'".format(exercise_id, user_id)
        sql_str += " AND se.status is True"
        result = self.postgres.query_fetch_one(sql_str)

        if result:

            result['exercise_num'] = "Exercise {0}".format(result['exercise_number'])
            if result['exercise_name']:
                result['exercise_num'] = "{0} {1}".format(result['exercise_name'], result['exercise_number'])

            result['numberOfQuestions'] = result['number_to_draw']

            # GET TYPE OF QUESTIONS
            result['question_type'] = self.exercise_question_type(result['student_exercise_id'])
            result['estimate_time'] = "9 minutes"
            result['exercise_difficulty'] = 80

            result['questions'] = self.get_exercise_questions(user_id, exercise_id)

            self.remove_key(result, "update_on")
            self.remove_key(result, "created_on")
            self.remove_key(result, "text_after_end")
            self.remove_key(result, "text_before_start")
            self.remove_key(result, "save_seed")
            self.remove_key(result, "seed")
            self.remove_key(result, "shuffled")

            self.remove_key(result, "student_exercise_id")
            self.remove_key(result, "draw_by_tag")
            self.remove_key(result, "instant_feedback")
            self.remove_key(result, "number_to_draw")

        return result

    def exercise_question_type(self, student_exercise_id):
        """ Return Exercise Question Type"""

        result = []

        sql_str = "SELECT question_type, count(question_type) as number_of_items"
        sql_str += " FROM course_question WHERE course_question_id IN"
        sql_str += "(SELECT course_question_id FROM student_exercise_questions"
        sql_str += " WHERE student_exercise_id='{0}')".format(student_exercise_id)
        sql_str += " GROUP BY question_type"
        responses = self.postgres.query_fetch_all(sql_str)

        if responses:

            for res in responses:

                if res['question_type'] == 'FITBT':

                    result.append("Fill in the Blanks")

                elif res['question_type'] == 'MULCH':

                    result.append("Multiple Choice")

                elif res['question_type'] == 'MATCH':

                    result.append("Matching-type")

                elif res['question_type'] == 'MULRE':

                    result.append("Multiple Response")

                elif res['question_type'] == 'FITBD':

                    result.append("Fill in the Blanks Drag and Drop")

        return result

    def get_exercise_questions(self, user_id, exercise_id):
        """ Return Exercise Questions """
    
        sql_str = "SELECT seq.*, question,  num_eval, correct, incorrect,  status"
        sql_str += " FROM student_exercise_questions seq LEFT JOIN course_question"
        sql_str += " cq ON seq.course_question_id = cq.course_question_id"
        sql_str += " WHERE seq.student_exercise_id IN (SELECT student_exercise_id FROM student_exercise"
        sql_str += " WHERE exercise_id='{0}' AND account_id='{1}' AND status is True)".format(exercise_id, user_id)
        sql_str += " ORDER BY seq.sequence"
        questions = self.postgres.query_fetch_all(sql_str)

        for question in questions:

            ans = self.check_answer(question['course_question_id'], question['answer'], flag=True)
            question['message'] = ans['message']
            question['is_correct'] = ans['isCorrect']
            question['question'] = question['question']['question']
                
            question['answered'] = False
            if question['answer'] not in [None, '', []]:
                question['answered'] = True

            self.remove_key(question, "correct")
            self.remove_key(question, "incorrect")
            self.remove_key(question, "student_exercise_id")
            self.remove_key(question, "question")
            self.remove_key(question, "course_question_id")
            self.remove_key(question, "account_id")
            self.remove_key(question, "answer")

        return questions
