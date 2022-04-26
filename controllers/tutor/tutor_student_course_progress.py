"""Tutor Student Course progress"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class TutorStudentCourseProgress(Common):
    """Class for TutorStudentCourseProgress"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for TutorStudentCourseProgress class"""
        self.postgresql_query = PostgreSQL()
        super(TutorStudentCourseProgress, self).__init__()

    def tutor_student_course_progress(self):
        """
        This API is for Getting Student Skills
        ---
        tags:
          - Tutor
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
          - name: student_id
            in: query
            description: Student ID
            required: true
            type: string
          - name: course_id
            in: query
            description: Course ID
            required: true
            type: string
          - name: limit
            in: query
            description: Limit
            required: true
            type: integer
          - name: page
            in: query
            description: Page
            required: true
            type: integer
        responses:
          500:
            description: Error
          200:
            description: Student Skills
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        course_id = request.args.get('course_id')
        student_id = request.args.get('student_id')
        page = int(request.args.get('page'))
        limit = int(request.args.get('limit'))

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        datas = self.get_sc_progress(student_id, page, limit, course_id, userid)
        datas['student_details'] = self.get_account_details(student_id)
        datas['status'] = 'ok'

        return self.return_data(datas, userid)

    def get_course_progess(self, student_id, course_id):
        """ RETURN COURSE PROGRESS """

        sql_str = "SELECT c.course_name, c.description, c.course_title,"
        sql_str += " ROUND(cast(sc.progress as numeric),2) AS progress,"
        sql_str += " ROUND(cast(sc.percent_score as numeric),2) AS score"
        sql_str += " FROM student_course sc INNER JOIN course c ON sc.course_id=c.course_id WHERE"
        sql_str += " sc.account_id='{0}'".format(student_id)
        sql_str += " AND c.course_id='{0}'".format(course_id)

        return self.postgres.query_fetch_one(sql_str)

    def get_sc_progress(self, student_id, page, limit, course_id, userid):
        """ RETURN STUDENT COURSE PROGRESS """

        offset = int((page - 1) * limit)

        sql_str = "SELECT COUNT(*) FROM section_master WHERE"
        sql_str += " account_id='{0}'".format(student_id)
        sql_str += " AND course_id ='{0}'".format(course_id)
        sql_str += " AND status =true"
        count = self.postgres.query_fetch_one(sql_str)

        # SECTIONS
        sql_str = "SELECT * FROM section_master WHERE"
        sql_str += " account_id='{0}'".format(student_id)
        sql_str += " AND course_id ='{0}'".format(course_id)
        sql_str += " AND status =true"
        sql_str += " ORDER BY difficulty_level"
        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)

        results = self.postgres.query_fetch_all(sql_str)

        sql_str = "SELECT language FROM account WHERE"
        sql_str += " id='{0}'".format(userid)
        language = self.postgres.query_fetch_one(sql_str)

        exercise_name = self.translate_key(language, 'Exercise')
        question_name = self.translate_key(language, 'Question')

        if results:

            results = self.section_master_translation(results, userid, language=language, exercise_name=exercise_name, question_name=question_name)

            for section in results:
                for subsection in section['children']:
                    self.get_correct_answer(userid, subsection['children'], language=language)

        total_rows = count['count']
        total_page = int((total_rows + limit - 1) / limit)

        data = {}
        data['course'] = self.get_course_progess(student_id, course_id)
        data['rows'] = results
        data['total_rows'] = total_rows
        data['total_page'] = total_page
        data['limit'] = limit
        data['page'] = page

        return data


    def get_correct_answer(self, user_id, exercises, language):
        """ Return Correct Answer """

        for exercise in exercises:

            exercise['time_studied'] = self.time_studied(user_id, exercise['started_on'], exercise['update_on'], language)

            if exercise['children']:

                for question in exercise['children']:

                    if question['children']:

                        # CORRECT ANSWER
                        answer = question['children'][1]['value']
                        question_id = question['children'][1]['course_question_id']

                        if answer not in [None, ""]:

                            correct_answer = self.check_answer(question_id, answer, flag=True)

                            # UPDATE CORRECT ANSWER
                            question['children'][2]['value'] = self.swap_decimal_symbol(user_id, correct_answer['correct_answer'], language=language)

                        # QUESTION
                        question['children'][0]['value'] = self.swap_decimal_symbol(user_id, question['children'][0]['value'], language=language)

                        # ANSWER
                        question['children'][1]['value'] = self.swap_decimal_symbol(user_id, question['children'][1]['value'], language=language)
