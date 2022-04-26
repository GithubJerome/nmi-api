
"""TUTOR STUDENT"""
import time

from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class TutorStudents(Common):
    """Class for Tutor Student"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Tutor Student class"""
        self.postgres = PostgreSQL()
        super(TutorStudents, self).__init__()

    def tutor_students(self):
        """
        This API is for Getting Tutor Student
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
            description: Tutor
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        page = int(request.args.get('page'))
        limit = int(request.args.get('limit'))

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

        datas = self.get_students(userid, page, limit)

        datas['status'] = 'ok'

        return self.return_data(datas, userid)

    def get_students(self, user_id, page, limit):
        """Return Role"""

        offset = int((page - 1) * limit)

        # COUNT
        sql_str = "SELECT count(student_id) FROM user_group_students"
        sql_str += " WHERE user_group_id IN (SELECT user_group_id FROM"
        sql_str += " user_group_tutors WHERE"
        sql_str += " tutor_id='{0}')".format(user_id)

        count = self.postgres.query_fetch_one(sql_str)
        total_rows = count['count']

        # FETCH DATA
        cols = "email, first_name, id, id as key, last_name, middle_name,"
        cols += " ROUND(cast(progress as numeric),2) AS progress,"
        cols += " status, username, update_on"
        sql_str = "SELECT {0}".format(cols)
        sql_str += " FROM account WHERE id IN (SELECT student_id"
        sql_str += " FROM user_group_students WHERE user_group_id IN"
        sql_str += " (SELECT user_group_id FROM user_group_tutors WHERE"
        sql_str += " tutor_id='{0}'))".format(user_id)
        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)

        response = self.postgres.query_fetch_all(sql_str)

        for res in response:


            res['struggles_with'] = self.get_struggles_with(res['id'])
            res['mood'] = "Good"
            res['groups'] = self.get_group(res['id'], user_id)

            oneday = 86400
            today = time.time()
            created_on = res['update_on']
            if not created_on:
              created_on = 0
            lapse = today - int(created_on)

            days = int(lapse / oneday)

            if days > 7:
                
                res['last_active'] = str(int(days / 7)) + ' week(s)'

            else:

                res['last_active'] = str(days) + ' day(s)'

        total_page = int((total_rows + limit - 1) / limit)

        data = {}
        data['rows'] = response
        data['total_rows'] = total_rows
        data['total_page'] = total_page
        data['limit'] = limit
        data['page'] = page

        return data

    def get_group(self, student_id, tutor_id):
        """ GET GROUP """

        sql_str = "SELECT * FROM user_group WHERE user_group_id IN ("
        sql_str += "SELECT user_group_id FROM user_group_students WHERE"
        sql_str += " user_group_id IN (SELECT user_group_id FROM"
        sql_str += " user_group_tutors WHERE"
        sql_str += " tutor_id='{0}')".format(tutor_id)
        sql_str += " AND student_id='{0}')".format(student_id)

        response = self.postgres.query_fetch_all(sql_str)

        return response

    def get_struggles_with(self, user_id):
        """ RETURN QUICK START """

        sql_str = "SELECT * FROM student_course sc"
        sql_str += " LEFT JOIN course c ON sc.course_id = c.course_id"
        sql_str += " LEFT JOIN student_section ss ON c.course_id = ss.course_id"
        sql_str += " LEFT JOIN section s ON ss.section_id = s.section_id"
        sql_str += " LEFT JOIN student_subsection ssub ON ss.section_id = ssub.section_id"
        sql_str += " LEFT JOIN subsection sub ON ssub.subsection_id = sub.subsection_id"
        sql_str += " LEFT JOIN exercise e ON ssub.subsection_id = e.subsection_id"
        sql_str += " LEFT JOIN student_exercise se ON e.exercise_id = se.exercise_id"
        sql_str += " WHERE sc.account_id = '{0}' AND ss.account_id ='{0}'".format(user_id)
        sql_str += " AND se.account_id = '{0}' AND ssub.account_id = '{0}'".format(user_id)
        sql_str += " AND se.status is True AND (se.progress IS NULL OR se.progress != '100')"
        sql_str += " ORDER BY c.difficulty_level, s.difficulty_level, sub.difficulty_level,"
        sql_str += " e.exercise_number LIMIT 1"
        result = self.postgres.query_fetch_one(sql_str)

        data = ""

        if result:

            data = "{0}, {1}".format(result['section_name'],result['subsection_name'])

        return data
