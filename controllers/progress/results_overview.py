# pylint: disable=too-many-function-args
"""Results Overviews"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class ResultsOverview(Common):
    """Class for CourseProgress"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CourseProgress class"""
        self.postgresql_query = PostgreSQL()
        super(ResultsOverview, self).__init__()

    def results_overview(self):
        """
        This API is for Getting Results Overview
        ---
        tags:
          - Progress
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

        responses:
          500:
            description: Error
          200:
            description: Results Overview
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        data['data'] = self.get_student_course(userid)
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def get_student_course(self, user_id):
        """Return All Courses"""

        # DATA
        sql_str = "SELECT * FROM student_course sc"
        sql_str += " LEFT JOIN course c ON sc.course_id = c.course_id"
        sql_str += " WHERE sc.account_id = '{0}'".format(user_id)
        sql_str += " ORDER BY c.difficulty_level"

        results = self.postgres.query_fetch_all(sql_str)

        for result in results:

            activity = self.get_course_activity(user_id, result['course_id'])

            result['activity'] = activity
            self.remove_key(result, "account_id")

        # COMPUTE GENERAL PROGRES]
        not_in = [None, 0]
        progress = [float(res['progress']) for res in results if float(res['progress']) not in not_in]

        total = int(len(progress))

        general_progress = sum(progress)
        if total > 1:
            general_progress = int((sum(progress) / total) * 100)

        data = {}
        data['course'] = results
        data['general_progress'] = general_progress

        return data

    def get_course_activity(self, user_id, course_id):
        """ Return Course Activity """

        sql_str = "SELECT s.section_name, sub.subsection_name, se.* FROM student_exercise se"
        sql_str += " LEFT JOIN exercise e ON se.exercise_id = e.exercise_id"
        sql_str += " LEFT JOIN subsection sub ON e.subsection_id = sub.subsection_id"
        sql_str += " LEFT JOIN section s ON sub.section_id = s.section_id"
        sql_str += " LEFT JOIN course c ON s.course_id = c.course_id"
        sql_str += " WHERE se.status is True AND account_id = '{0}'".format(user_id)
        sql_str += " AND c.course_id ='{0}'".format(course_id)
        sql_str += " ORDER BY c.difficulty_level, s.difficulty_level,"
        sql_str += " sub.difficulty_level, e.exercise_number"
        result = self.postgres.query_fetch_all(sql_str)

        if result:
            for res in result:

                res['activity'] =  "{0} (Exercise {1})".format(res['subsection_name'],
                                                                res['exercise_number'])
                res['section'] =  res['section_name']
                res['completed_on'] = res['update_on']

                exercise = self.get_activity_details(res['student_exercise_id'])
                res['start_date'] = exercise['start_date']

                score = res['score']
                if res['score'] is None:
                    score = 0

                res['score_progress'] = 0
                if exercise['total']:
                    res['score_progress'] = (score / exercise['total']) * 100

                self.remove_key(res, "account_id")
                self.remove_key(res, "exercise_number")
                self.remove_key(res, "student_exercise_id")
                self.remove_key(res, "subsection_name")
                self.remove_key(res, "section_name")

                self.remove_key(res, "update_on")
                self.remove_key(res, "created_on")
    
        return result

    def get_activity_details(self, student_exercise_id):
        """ Return Exercise Details """

        sql_str = "SELECT * FROM student_exercise_questions"
        sql_str += " WHERE student_exercise_id = '{0}'".format(student_exercise_id)
        # sql_str += " ORDER BY sequence, started_on"
        sql_str += " ORDER BY sequence, answered_on"
        result = self.postgres.query_fetch_all(sql_str)

        start_date = None
        answered_on = None
        total = 0

        if result:
            start_date = result[0]['started_on']
            answered_on = result[0]['answered_on']
            total = len(result)

        data = {}
        # We can use later the start date
        data['start_date'] = answered_on
        data['total'] = total

        return data
