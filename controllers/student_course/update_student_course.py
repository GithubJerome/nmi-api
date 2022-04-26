# pylint: disable=too-many-function-args
"""Student Course"""

import random
import json
import time

from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.questions import Questions
from library.unlock import Unlock
from socketIO_client import SocketIO, LoggingNamespace

class UpdateStudentCourse(Common):
    """Class for UpdateStudentCourse"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateStudentCourse class"""
        self.postgresql_query = PostgreSQL()
        self.sha_security = ShaSecurity()
        self.questionnaires = Questions()
        self.unlock = Unlock()
        super(UpdateStudentCourse, self).__init__()

    def update_course_exercise(self):
        """
        This API is for Getting Updating Student Course
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

        responses:
          500:
            description: Error
          200:
            description: Course Hierarchy
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        course_id = request.args.get('course_id')
        print("token: {0}".format(token))
        print("userid: {0}".format(userid))
        print("course_id: {0}".format(course_id))


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

        in_group = self.student_in_group(userid, course_id)

        # GENERATE COURSE SET EXERCISE
        self.generate_course_set(userid, course_id, in_group)

        # VALIDATE LOCK/UNLOCK
        self.unlock.validate_lock_unlock2(token, userid, course_id, in_group)

        # GET COURSE SET
        result = self.get_course_set(userid, course_id) or []

        print("result: {0}".format(result))
        # save here student_course_master_data

        # ADD EXERCISE
        temp = {}
        temp['student_course_master_data_id'] = self.sha_security.generate_token(False)
        temp['account_id'] = userid
        temp['course_id'] = course_id
        temp['datas'] = json.dumps(result)

        self.postgres.insert('student_course_master_data', temp)

        data = {}
        data['data'] = result
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def generate_course_set(self, user_id, course_id, in_group):
        """ Return Course Set """

        sql_str = "SELECT sc.course_id, s.section_id, ss.subsection_id, e.exercise_id"
        sql_str += " FROM student_course sc LEFT JOIN section s ON sc.course_id = s.course_id"
        sql_str += " LEFT JOIN subsection ss ON s.section_id = ss.section_id"
        sql_str += " LEFT JOIN exercise e ON ss.subsection_id = e.subsection_id"
        sql_str += " WHERE sc.course_id = '{0}'".format(course_id)
        sql_str += " AND account_id = '{0}'".format(user_id)
        sql_str += " AND exercise_id NOT IN (SELECT exercise_id FROM student_exercise"
        sql_str += " WHERE account_id = '{0}' AND status is True)".format(user_id)
        sql_str += " GROUP BY sc.course_id, s.section_id, ss.subsection_id, e.exercise_id"
        results = self.postgres.query_fetch_all(sql_str)

        if results:

            sections = set(result['section_id'] for result in results)
            subsections = set(result['subsection_id'] for result in results)
            exercises = set(result['exercise_id'] for result in results)

            # ADD DATA TO STUDENT SECTION TABLE
            self.add_student_section(user_id, course_id, sections, in_group)

            # ADD DATA TO STUDENT SUBSECTION TABLE
            self.add_student_subsection(user_id, course_id, subsections, in_group)

            for exercise_id in exercises:

                # GENERATE EXERCISE
                self.questionnaires.generate_questions(user_id, course_id, exercise_id,
                                                       "student")

        return 1

    def add_student_section(self, user_id, course_id, section_ids, in_group):
        """ Add Student Section """

        sids = ','.join("'{0}'".format(sid) for sid in section_ids)
        sql_str = "SELECT * FROM student_section WHERE section_id IN ({0})".format(sids)
        sql_str += " AND account_id = '{0}' AND status is True".format(user_id)
        result = self.postgres.query_fetch_all(sql_str)

        db_section_ids = [res['section_id'] for res in result]
        db_section_ids = set(db_section_ids)
        section_ids = set(section_ids)

        section_ids.difference_update(db_section_ids)

        for section_id in section_ids:

            sql_str = "SELECT * FROM section_requirements WHERE"
            sql_str += " section_id='{0}'".format(section_id)
            reqs = self.postgres.query_fetch_one(sql_str)

            # ADD EXERCISE
            temp = {}
            temp['student_section_id'] = self.sha_security.generate_token(False)
            temp['account_id'] = user_id
            temp['course_id'] = course_id
            temp['section_id'] = section_id
            temp['status'] = True
            temp['created_on'] = time.time()
            
            temp['is_unlocked'] = True
            if reqs:
                
                if not in_group:

                    reqs['is_lock'] = False

                if reqs['is_lock'] is True:
                    temp['is_unlocked'] = False
                else:
                    if reqs['grade_locking'] is True:
                        temp['is_unlocked'] = False

            self.postgres.insert('student_section', temp, 'student_section_id')

        return 1

    def add_student_subsection(self, user_id, course_id, subsection_ids, in_group):
        """ Add Student Section """

        sids = ','.join("'{0}'".format(sid) for sid in subsection_ids)
        sql_str = "SELECT * FROM student_subsection WHERE subsection_id IN ({0})".format(sids)
        sql_str += " AND account_id = '{0}' AND status is True".format(user_id)
        result = self.postgres.query_fetch_all(sql_str)

        db_section_ids = [res['subsection_id'] for res in result]
        db_subsection_ids = set(db_section_ids)
        subsection_ids = set(subsection_ids)

        subsection_ids.difference_update(db_subsection_ids)

        ids = ','.join("'{0}'".format(subsection_id) for subsection_id in subsection_ids)
        sql_str = "SELECT * FROM subsection WHERE"
        sql_str += " subsection_id IN({0})".format(ids)
        results = self.postgres.query_fetch_all(sql_str)

        if results:

            for result in results:

                sql_str = "SELECT * FROM subsection_requirements WHERE"
                sql_str += " subsection_id='{0}'".format(result['subsection_id'])
                reqs = self.postgres.query_fetch_one(sql_str)

                temp = {}
                temp['student_subsection_id'] = self.sha_security.generate_token(False)
                temp['account_id'] = user_id
                temp['course_id'] = course_id
                temp['section_id'] = result['section_id']
                temp['subsection_id'] = result['subsection_id']
                temp['status'] = True
                temp['created_on'] = time.time()

                temp['is_unlocked'] = True
                if reqs:
                
                    if not in_group:

                        reqs['is_lock'] = False

                    if reqs['is_lock'] is True:
                        temp['is_unlocked'] = False
                    else:
                        if reqs['grade_locking'] is True:
                            temp['is_unlocked'] = False


                self.postgres.insert('student_subsection', temp, 'student_subsection_id')

            return 1

        return 0

    def get_course_set(self, userid, course_id):
        """ Return Course Set Hierarchy """

        # COURSE DATA
        # sql_str = "SELECT sc.account_id, sc.course_id,"
        # sql_str += " ROUND(cast(sc.progress as numeric),2) AS progress,"
        # sql_str += " sc.expiry_date, sc.status, sc.update_on, sc.created_on,"
        # sql_str += " c.course_id, c.course_name, c.description, c.requirements,"
        # sql_str += " c.difficulty_level FROM student_course sc LEFT JOIN"
        # sql_str += " course c ON sc.course_id = c.course_id WHERE"
        # sql_str += " sc.account_id ='{0}'".format(userid)
        # sql_str += " AND sc.course_id='{0}'".format(course_id)
        sql_str = "SELECT * FROM student_course_master WHERE"
        sql_str += " account_id ='{0}'".format(userid)
        sql_str += " AND course_id='{0}'".format(course_id)

        result = self.postgres.query_fetch_one(sql_str)

        if result:
            self.remove_key(result, "account_id")
            self.remove_key(result, "update_on")
            self.remove_key(result, "created_on")
            # result['sections'] = self.get_sections(userid, course_id)

            for subsection_row in result['sections']:

                if not subsection_row['subsection']:

                    continue

                for exercises in subsection_row['subsection']:

                    if not exercises['exercises']:

                        continue

                    exercises['exercises'] = self.exercise_questionnaires2(userid, course_id, exercises['exercises'])

        return result

    def get_sections(self, user_id, course_id):
        """ Return Course Section """

        sql_str = "SELECT s.*, ss.* FROM student_section ss"
        sql_str += " LEFT JOIN section s ON  ss.section_id = s.section_id"
        sql_str += " WHERE ss.course_id='{0}'".format(course_id)
        sql_str += " AND ss.account_id='{0}' AND ss.status is True".format(user_id)
        sql_str += " ORDER BY s.difficulty_level"
        result = self.postgres.query_fetch_all(sql_str)

        for res in result:

            # GET SUBSECTION
            section_id = res['section_id']
            sql_str = "SELECT sub.*, ss.* FROM student_subsection ss LEFT JOIN"
            sql_str += " subsection sub ON ss.subsection_id = sub.subsection_id"
            sql_str += " WHERE ss.section_id='{0}'".format(section_id)
            sql_str += " AND ss.account_id='{0}' AND ss.status is True".format(user_id)
            sql_str += " ORDER BY sub.difficulty_level"
            subsection = self.postgres.query_fetch_all(sql_str)

            res['subsection'] = self.get_sub_exercise(user_id, subsection, course_id)
            res['requirements'] = self.get_section_requirements(user_id, section_id)

        return result

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
        sql_str = "SELECT * FROM exercise e"
        sql_str += " LEFT JOIN student_exercise se ON e.exercise_id = se.exercise_id"
        sql_str += " WHERE se.course_id = '{0}' AND e.status is True".format(course_id)
        sql_str += " AND se.account_id = '{0}' AND se.status is True".format(user_id)
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

            
                # REQUIREMENTS
                res['requirements'] = self.get_exercise_requirements(user_id, res['exercise_id'])

        return result

    def get_instruction(self, exercise_id):
        """ Return Instruction by Exercise """

        sql_str = "SELECT * FROM instruction WHERE exercise_id = '{0}'".format(exercise_id)
        result = self.postgres.query_fetch_all(sql_str)
        return result

    def get_questions(self, student_exercise_id):
        """ Return Set of Questions """

        responses = []

        sql_str = "SELECT question, choices, description, False as answered, question_type, seq.*"
        sql_str += " FROM student_exercise_questions seq LEFT JOIN course_question"
        sql_str += " cq ON seq.course_question_id = cq.course_question_id WHERE"
        sql_str += " student_exercise_id ='{0}' ORDER BY sequence".format(student_exercise_id)
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

    def exercise_questionnaires2(self, user_id, course_id, result):
        """ Return Exercise with questionnaires"""

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
            
                # REQUIREMENTS
                res['requirements'] = self.get_exercise_requirements(user_id, res['exercise_id'])

        return result
