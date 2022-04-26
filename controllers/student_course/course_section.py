# pylint: disable=too-many-function-args
"""Course Section"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class CourseSection(Common):
    """Class for CourseSection"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CourseSection class"""
        self.postgresql_query = PostgreSQL()
        super(CourseSection, self).__init__()

    def course_section(self):
        """
        This API is for Getting All Course Section
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
          - name: section_id
            in: query
            description: Section ID
            required: false
            type: string
        responses:
          500:
            description: Error
          200:
            description: Course Section
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

        datas = self.get_course_section(userid, course_id, section_id)
        datas['status'] = 'ok'

        return self.return_data(datas, userid)

    def get_course_section(self, user_id, course_id, section_id):
        """Return All Course Section"""

        # DATA
        sql_str = " SELECT s.*, ss.is_unlocked, c.course_name, c.course_title, ss.progress, (SELECT array_to_json("
        sql_str += " array_agg(subsection)) FROM (SELECT sub.*, ssub.* FROM student_subsection ssub"
        sql_str += " LEFT JOIN subsection sub ON ssub.subsection_id = sub.subsection_id WHERE"
        sql_str += " sub.section_id  = s.section_id AND ssub.account_id = '{0}'".format(user_id)
        sql_str += " AND ssub.status is True ORDER BY difficulty_level) AS subsection) as subsection"
        sql_str += " FROM section s LEFT JOIN student_section ss ON s.section_id = ss.section_id"
        sql_str += " LEFT JOIN course c ON s.course_id = c.course_id WHERE ss.status is True AND"
        sql_str += " s.course_id = '{0}'  AND ss.account_id = '{1}'".format(course_id, user_id)

        if section_id:
            sql_str += " AND s.section_id = '{0}'".format(section_id)
        sql_str += " AND s.status is True"

        result = self.postgres.query_fetch_all(sql_str)

        for res in result:
            self.get_sub_exercise(user_id, res['subsection'], course_id)
            res['course_name'] = self.translate(user_id, res['course_name'])
            res['requirements'] = self.get_section_requirements(user_id, res['section_id'])

        data = {}
        data['data'] = result

        return data

    def get_sub_exercise(self, user_id, subsection, course_id):
        """ Return Subsection exercises """

        assert subsection, "Subsection ID is required"

        for sub in subsection:
            sub_id = sub['subsection_id']
            sub['exercises'] = self.exercise_questionnaires(user_id, course_id, sub_id)
            sub['requirements'] = self.get_subsection_requirements(user_id, sub_id)
            self.remove_key(sub, "course_id")

        return subsection

    def exercise_questionnaires(self, user_id, course_id, subsection_id):
        """ Return Exercise with questionnaires"""

        # DATA
        sql_str = "SELECT e.*, se.*, c.exercise_name FROM exercise e"
        sql_str += " LEFT JOIN student_exercise se ON e.exercise_id = se.exercise_id"
        sql_str += " LEFT JOIN course c ON se.course_id = c.course_id"
        sql_str += " WHERE se.course_id = '{0}' AND e.status is True".format(course_id)
        sql_str += " AND se.status is True AND se.account_id = '{0}'".format(user_id)
        sql_str += " AND e.exercise_id IN (SELECT exercise_id FROM exercise WHERE"
        sql_str += " subsection_id='{0}') ORDER BY e.exercise_number".format(subsection_id)

        result = self.postgres.query_fetch_all(sql_str)

        if result:

            i = 0
            for res in result:

                res['exercise_num'] = "Exercise {0}".format(res['exercise_number'])
                if res['exercise_name']:
                    res['exercise_num'] = "{0} {1}".format(res['exercise_name'], res['exercise_number'])

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

                # REQUIREMENTS
                res['requirements'] = self.get_exercise_requirements(user_id, res['exercise_id'])

                i += 1

                res['questions'] = self.get_questions(res['student_exercise_id'])

                # ADD CORRECT ANSWER
                res['questions'] = self.with_correct_answer(course_id,
                                                            res['exercise_id'],
                                                            res['questions'])

                # GET INSTRUCTION
                res['instructions'] = self.get_instruction(res['exercise_id'])

                self.remove_key(res, "course_id")
                self.remove_key(res, "section_id")
                self.remove_key(res, "account_id")
                self.remove_key(res, "subsection_id")
                self.remove_key(res, "created_on")
                self.remove_key(res, "update_on")

                if not res['score']:

                    res['is_passed'] = False

                elif not res['passing_criterium']:

                    res['is_passed'] = True

                elif int(res['passing_criterium']) <= int(res['score']):

                    res['is_passed'] = True

                else:

                    res['is_passed'] = False

            result = sorted(result, key=lambda i: int(i['exercise_number']))

        return result

    def get_questions(self, student_exercise_id):
        """ Return Set of Questions """

        sql_str = "SELECT question, choices, description, False as answered, question_type, seq.*"
        sql_str += " FROM student_exercise_questions seq LEFT JOIN course_question"
        sql_str += " cq ON seq.course_question_id = cq.course_question_id WHERE"
        sql_str += " student_exercise_id ='{0}'".format(student_exercise_id)
        sql_str += " ORDER BY course_question_id"
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

    def get_instruction(self, exercise_id):
        """ Return Instruction by Exercise """

        sql_str = "SELECT * FROM instruction WHERE exercise_id = '{0}'".format(exercise_id)
        result = self.postgres.query_fetch_all(sql_str)
        return result
