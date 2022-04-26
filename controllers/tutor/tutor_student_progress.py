# pylint: disable=too-many-function-args
"""Tutor Student Course Progress"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class TutorStudentProgress(Common):
    """Class for TutorStudentProgress"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for TutorStudentProgress class"""
        self.postgresql_query = PostgreSQL()
        super(TutorStudentProgress, self).__init__()

    def tutor_student_progress(self):
        """
        This API is for Getting Tutor Student Course Progress
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
            description: Tutor Student Course Progress
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        page = int(request.args.get('page'))
        limit = int(request.args.get('limit'))
        student_id = request.args.get('student_id')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        datas = self.get_student_course(student_id, page, limit)
        datas['status'] = 'ok'

        return self.return_data(datas, userid)

    def get_student_course(self, student_id, page, limit):
        """Return All Courses"""

        offset = int((page - 1) * limit)

        # COUNT
        sql_str = "SELECT COUNT(*) FROM student_course WHERE account_id='{0}'".format(student_id)

        count = self.postgres.query_fetch_one(sql_str)
        total_rows = count['count']

        # DATA
        sql_str = "SELECT *,"
        sql_str += " ROUND(cast(sc.progress as numeric),2) AS progress,"
        sql_str += " ROUND(cast(sc.percent_score as numeric),2) AS score"
        sql_str += " FROM student_course sc"
        sql_str += " LEFT JOIN course c ON sc.course_id = c.course_id"
        sql_str += " LEFT JOIN course_sequence cs ON c.course_id = cs.course_id"
        sql_str += " WHERE sc.account_id = '{0}'".format(student_id)
        sql_str += " ORDER BY cs.sequence"
        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)
        results = self.postgres.query_fetch_all(sql_str)

        total_page = int((total_rows + limit - 1) / limit)

        for result in results:
            exercise = self.get_total_exercise(student_id, result['course_id'])
            result['total_exercise'] = "{0}/{1}".format(exercise['total_answer'], exercise['total'])
            result['started'] = exercise['started']
            result['last_active'] = exercise['last_active']
            # result['progress'] = exercise['progress']

        data = {}
        data['student_details'] = self.get_account_details(student_id)
        data['rows'] = results
        data['total_rows'] = total_rows
        data['total_page'] = total_page
        data['limit'] = limit
        data['page'] = page

        return data

    def get_total_exercise(self, student_id, course_id):
        """ Return Total Exercise """

        sql_str = "SELECT * FROM student_exercise se"
        sql_str += " LEFT JOIN exercise e ON se.exercise_id = e.exercise_id"
        sql_str += " WHERE se.status is True AND e.status is True AND"
        sql_str += " se.account_id = '{0}' AND se.course_id = '{1}'".format(student_id, course_id)
        results = self.postgres.query_fetch_all(sql_str)

        data = {}
        total = 0
        started = None
        last_active = None
        total_answer = 0
        # progress = 0

        if results:
            # total_exercise = sum(result['number_to_draw'] for result in results)

            student_exercise_ids = ','.join("'{0}'".format(result['student_exercise_id']) \
                                            for result in results)

            sql_str = "SELECT * FROM student_exercise_questions"
            sql_str += " WHERE student_exercise_id IN ({0})".format(student_exercise_ids)
            sql_str += " ORDER BY answered_on"
            questions = self.postgres.query_fetch_all(sql_str)

            not_answer = [None, '', []]
            total = len(questions)
            total_answer = len([question['answer'] for question in questions \
                               if question['answer'] not in not_answer])
            started = questions[0]['answered_on']
            last_active = questions[-1]['answered_on']
            # progress = self.format_progress((total_answer / total) * 100)

            sql_str = "SELECT ROUND(cast(sc.progress as numeric),2) AS progress"
            sql_str += " FROM student_course sc INNER JOIN course c ON sc.course_id=c.course_id WHERE"
            sql_str += " sc.account_id='{0}'".format(student_id)
            sql_str += " AND c.course_id='{0}'".format(course_id)
            response = self.postgres.query_fetch_one(sql_str)

            # if response:

            #     progress = response['progress']

        data['total'] = total
        data['total_answer'] = total_answer
        data['started'] = started
        data['last_active'] = last_active
        # data['progress'] = progress

        return data
