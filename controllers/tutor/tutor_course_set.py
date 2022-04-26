"""Tutor Course set"""

import time

from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.questions import Questions

class TutorCourseSet(Common):
    """Class for TutorCourseSet"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for TutorCourseSet class"""
        self.postgresql_query = PostgreSQL()
        self.sha_security = ShaSecurity()
        self.questionnaires = Questions()
        super(TutorCourseSet, self).__init__()

    def tutor_course_set(self):
        """
        This API is for Getting Tutor Course set of Questionnaires
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

        responses:
          500:
            description: Error
          200:
            description: Tutor Course Set
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        course_id = request.args.get('course_id')

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

        # GENERATE COURSE SET EXERCISE
        # if not self.is_assigned_exercise(userid, course_id):
        self.generate_course_set(userid, course_id)

        # GET COURSE SET
        result = self.get_course_set(userid, course_id)

        data = {}
        data['data'] = result
        data['children'] = self.fetch_course_details(userid, course_id)
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def generate_course_set(self, user_id, course_id):
        """ Return Course Set """

        sql_str = "SELECT exercise_id FROM tutor_exercise WHERE"
        sql_str += " account_id = '{0}'".format(user_id)
        sql_str += " AND course_id = '{0}'".format(course_id)
        exr = self.postgres.query_fetch_all(sql_str)
        results = []

        if exr:

            sql_str = "SELECT tc.course_id, s.section_id, ss.subsection_id, e.exercise_id"
            sql_str += " FROM tutor_courses tc LEFT JOIN section s ON tc.course_id = s.course_id"
            sql_str += " LEFT JOIN subsection ss ON s.section_id = ss.section_id"
            sql_str += " LEFT JOIN exercise e ON ss.subsection_id = e.subsection_id"
            sql_str += " WHERE tc.course_id = '{0}'".format(course_id)
            sql_str += " AND account_id = '{0}'".format(user_id)
            sql_str += " AND exercise_id NOT IN (SELECT exercise_id FROM tutor_exercise"
            sql_str += " WHERE account_id = '{0}')".format(user_id)
            sql_str += " GROUP BY tc.course_id, s.section_id, ss.subsection_id, e.exercise_id"
            results = self.postgres.query_fetch_all(sql_str)

        else:

            sql_str = "SELECT tc.course_id, s.section_id, ss.subsection_id, e.exercise_id"
            sql_str += " FROM tutor_courses tc LEFT JOIN section s ON tc.course_id = s.course_id"
            sql_str += " LEFT JOIN subsection ss ON s.section_id = ss.section_id"
            sql_str += " LEFT JOIN exercise e ON ss.subsection_id = e.subsection_id"
            sql_str += " WHERE tc.course_id = '{0}'".format(course_id)
            sql_str += " AND account_id = '{0}'".format(user_id)
            sql_str += " GROUP BY tc.course_id, s.section_id,"
            sql_str += " ss.subsection_id, e.exercise_id"
            results = self.postgres.query_fetch_all(sql_str)

        if results:
            sections = set(result['section_id'] for result in results)
            subsections = set(result['subsection_id'] for result in results)
            exercises = set(result['exercise_id'] for result in results)

            # ADD DATA TO TUTOR SECTION TABLE
            self.add_tutor_section(user_id, course_id, sections)

            # ADD DATA TO TUTOR SUBSECTION TABLE
            self.add_tutor_subsection(user_id, course_id, subsections)

            for exercise_id in exercises:

                # GENERATE EXERCISE
                self.questionnaires.generate_questions(user_id, course_id, exercise_id, "tutor")

        return 1

    def add_tutor_section(self, user_id, course_id, section_ids):
        """ Add Tutor Section """

        sids = ','.join("'{0}'".format(sid) for sid in section_ids)
        sql_str = "SELECT * FROM tutor_section WHERE section_id IN ({0})".format(sids)
        sql_str += " AND account_id = '{0}'".format(user_id)
        result = self.postgres.query_fetch_all(sql_str)

        db_section_ids = [res['section_id'] for res in result]
        db_section_ids = set(db_section_ids)
        section_ids = set(section_ids)

        section_ids.difference_update(db_section_ids)

        for section_id in section_ids:

            # ADD EXERCISE
            temp = {}
            temp['tutor_section_id'] = self.sha_security.generate_token(False)
            temp['account_id'] = user_id
            temp['course_id'] = course_id
            temp['section_id'] = section_id
            temp['status'] = True
            temp['created_on'] = time.time()

            self.postgres.insert('tutor_section', temp, 'tutor_section_id')

        return 1

    def add_tutor_subsection(self, user_id, course_id, subsection_ids):
        """ Add Tutor Section """

        sids = ','.join("'{0}'".format(sid) for sid in subsection_ids)
        sql_str = "SELECT * FROM tutor_subsection WHERE subsection_id IN ({0})".format(sids)
        sql_str += " AND account_id = '{0}'".format(user_id)
        result = self.postgres.query_fetch_all(sql_str)

        db_section_ids = [res['subsection_id'] for res in result]
        db_subsection_ids = set(db_section_ids)
        subsection_ids = set(subsection_ids)

        subsection_ids.difference_update(db_subsection_ids)

        ids = ','.join("'{0}'".format(subsection_id) for subsection_id in subsection_ids)
        sql_str = "SELECT * FROM subsection WHERE subsection_id IN({0})".format(ids)
        results = self.postgres.query_fetch_all(sql_str)

        if results:

            for result in results:

                temp = {}
                temp['tutor_subsection_id'] = self.sha_security.generate_token(False)
                temp['account_id'] = user_id
                temp['course_id'] = course_id
                temp['section_id'] = result['section_id']
                temp['subsection_id'] = result['subsection_id']
                temp['status'] = True
                temp['created_on'] = time.time()

                self.postgres.insert('tutor_subsection', temp, 'tutor_subsection_id')

            return 1

        return 0

    def get_course_set(self, userid, course_id):
        """ Return Course Set Hierarchy """

        # COURSE DATA
        sql_str = "SELECT * FROM tutor_courses tc LEFT JOIN course c ON"
        sql_str += " tc.course_id = c.course_id WHERE tc.account_id = '{0}'".format(userid)
        sql_str += " AND tc.course_id='{0}'".format(course_id)

        result = self.postgres.query_fetch_one(sql_str)

        if result:
            self.remove_key(result, "account_id")
            self.remove_key(result, "update_on")
            self.remove_key(result, "created_on")
            result['sections'] = self.get_sections(userid, course_id)

        return result

    def get_sections(self, user_id, course_id):
        """ Return Course Section """

        sql_str = "SELECT * FROM tutor_section ts"
        sql_str += " LEFT JOIN section s ON  ts.section_id = s.section_id"
        sql_str += " WHERE ts.course_id='{0}'".format(course_id)
        sql_str += " AND ts.account_id='{0}'".format(user_id)
        sql_str += " ORDER BY s.difficulty_level"
        result = self.postgres.query_fetch_all(sql_str)

        for res in result:

            res['subsection'] = []

            # GET SUBSECTION
            section_id = res['section_id']
            sql_str = "SELECT * FROM tutor_subsection ts LEFT JOIN"
            sql_str += " subsection sub ON ts.subsection_id = sub.subsection_id"
            sql_str += " WHERE ts.section_id='{0}'".format(section_id)
            sql_str += " AND ts.account_id='{0}'".format(user_id)
            sql_str += " ORDER BY sub.difficulty_level"
            subsection = self.postgres.query_fetch_all(sql_str)

            if subsection:

                res['subsection'] = self.get_sub_exercise(user_id, subsection, course_id)

        return result

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
        sql_str += " AND te.account_id = '{0}' AND te.status is True".format(user_id)
        sql_str += " AND e.exercise_id IN (SELECT exercise_id FROM exercise WHERE"
        sql_str += " subsection_id='{0}') ORDER BY e.exercise_number".format(subsection_id)

        result = self.postgres.query_fetch_all(sql_str)

        if result:

            i = 0
            for res in result:

                # PROGRESS
                if res['progress'] is None and res['exercise_number'] == 1:
                    res['progress'] = 0

                if i > 0 and result[i-1]['progress'] is not None \
                    and int(float(result[i-1]['progress'])) == 100 \
                        and res['progress'] is None:

                    res['progress'] = 0

                res['answered_all'] = False
                if res['progress'] is not None:
                    res['progress'] = self.format_progress(round(float(res['progress']), 2))
    
                    if res['progress'] == 100:
                        res['answered_all'] = True

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

            result = sorted(result, key=lambda i: int(i['exercise_number']))

        return result

    def get_questions(self, tutor_exercise_id):
        """ Return Set of Questions """

        responses = []

        sql_str = "SELECT question, choices, description, False as answered, question_type, teq.*"
        sql_str += " FROM tutor_exercise_questions teq LEFT JOIN course_question"
        sql_str += " cq ON teq.course_question_id = cq.course_question_id WHERE"
        sql_str += " tutor_exercise_id ='{0}' ORDER BY sequence".format(tutor_exercise_id)
        course_questions = self.postgres.query_fetch_all(sql_str)

        if course_questions:

            for question in course_questions:

                question['question'] = question['question']['question']

            responses = course_questions

        return responses

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

            except ValueError:
                pass

        return questions

    def is_tutor_course(self, user_id, course_id):
        """ Validate Tutor Course """

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

    # def is_assigned_exercise(self, user_id, course_id):
    #     """ Check if Assigned questions"""

    #     sql_str = "SELECT * FROM tutor_exercise WHERE exercise_id"
    #     sql_str += " IN (SELECT exercise_id FROM exercise WHERE"
    #     sql_str += " course_id = '{0}')".format(course_id)
    #     sql_str += " AND account_id = '{0}'".format(user_id)
    #     result = self.postgres.query_fetch_all(sql_str)

    #     if result:
    #         return 1

    #     return 0
