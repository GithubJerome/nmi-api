# pylint: disable=too-many-function-args
"""Tutor Section"""
from flask import  request
from library.common import Common
# from library.postgresql_queries import PostgreSQL

class TutorSection(Common):
    """Class for TutorSection"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for TutorSection class"""
        # self.postgresql_query = PostgreSQL()
        super(TutorSection, self).__init__()

    def tutor_section(self):
        """
        This API is for Getting All Tutor Section
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
          - name: section_id
            in: query
            description: Section ID
            required: false
            type: string
        responses:
          500:
            description: Error
          200:
            description: Tutor Course Section
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        course_id = request.args.get('course_id')
        section_id = request.args.get('section_id')

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

        datas = self.fetch_section(userid, course_id, section_id)
        datas['children'] = self.get_section_child(userid, course_id, section_id)
        datas['status'] = 'ok'

        return self.return_data(datas)

    def fetch_section(self, user_id, course_id, section_id):
        """Return All Course Section"""

        # DATA
        sql_str = " SELECT s.*, c.course_name, c.course_title, (SELECT array_to_json(array_agg(subsection)) FROM ("
        sql_str += " SELECT * FROM tutor_subsection tsub LEFT JOIN subsection"
        sql_str += " sub ON tsub.subsection_id = sub.subsection_id WHERE"
        sql_str += " sub.section_id  = s.section_id AND tsub.account_id = '{0}'".format(user_id)
        sql_str += " ORDER BY subsection_name) AS subsection) as subsection FROM section s"
        sql_str += " LEFT JOIN tutor_section ts ON s.section_id = ts.section_id"
        sql_str += " LEFT JOIN course c ON s.course_id = c.course_id WHERE"
        sql_str += " s.course_id = '{0}'  AND ts.account_id = '{1}'".format(course_id, user_id)

        if section_id:
            sql_str += " AND s.section_id = '{0}'".format(section_id)
        sql_str += " AND s.status is True"

        result = self.postgres.query_fetch_all(sql_str)

        for res in result:
            self.get_sub_exercise(user_id, res['subsection'], course_id)

        data = {}
        data['data'] = result

        return data

    def get_sub_exercise(self, user_id, subsection, course_id):
        """ Return Subsection exercises """

        assert subsection, "Subsection ID is required"

        for sub in subsection:
            sub_id = sub['subsection_id']
            sub['exercises'] = self.exercise_questionnaires(user_id, course_id, sub_id)

            self.remove_key(sub, "course_id")

        return subsection

    def exercise_questionnaires(self, user_id, course_id, subsection_id):
        """ Return Exercise with questionnaires"""

        # DATA
        sql_str = "SELECT * FROM exercise e"
        sql_str += " LEFT JOIN tutor_exercise te ON e.exercise_id = te.exercise_id"
        sql_str += " WHERE te.course_id = '{0}' AND e.status is True".format(course_id)
        sql_str += " AND te.account_id = '{0}'".format(user_id)
        sql_str += " AND e.exercise_id IN (SELECT exercise_id FROM exercise WHERE"
        sql_str += " subsection_id='{0}') ORDER BY e.exercise_number".format(subsection_id)

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

                res['questions'] = self.get_questions(res['tutor_exercise_id'])

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

    def get_questions(self, tutor_exercise_id):
        """ Return Set of Questions """

        sql_str = "SELECT question, choices, description, False as answered, question_type, teq.*"
        sql_str += " FROM tutor_exercise_questions teq LEFT JOIN course_question"
        sql_str += " cq ON teq.course_question_id = cq.course_question_id WHERE"
        sql_str += " tutor_exercise_id ='{0}' ORDER BY course_question_id".format(tutor_exercise_id)
        course_questions = self.postgres.query_fetch_all(sql_str)

        for question in course_questions:
            question['question'] = question['question']['question']

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
                correct_answer = str(course_questions[index]['correct_answer'])

                if question['answer'] != "":
                    question['correct_answer'] = correct_answer
                else:
                    question['correct_answer'] = ""

            except ValueError:
                pass

        return questions

    def get_section_child(self, user_id, course_id, section_id):
        """ Return Section Child """

        data = []

        course = self.fetch_course_details(user_id, course_id)

        if course:

            data = course[0]['children']

            if section_id:

                section_ids = [dta['section_id'] for dta in data]

                try:
                    section_index = section_ids.index(section_id)
                    data = data[section_index]

                except ValueError:
                    pass

        return data
