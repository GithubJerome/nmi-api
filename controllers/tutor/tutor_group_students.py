
"""TUTOR GROUP STUDENTS"""
import time

from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class TutorGroupStudents(Common):
    """Class for Tutor Group Students"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for TutorGroupStudents class"""
        self.postgres = PostgreSQL()
        super(TutorGroupStudents, self).__init__()

    def tutor_group_students(self):
        """
        This API is for Getting Tutor Group Students
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
          - name: group_id
            in: query
            description: Group ID
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
        group_id = request.args.get('group_id')
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

        datas = self.get_group_students(userid, group_id, page, limit)

        datas['status'] = 'ok'

        return self.return_data(datas)

    def get_group_students(self, user_id, group_id, page, limit):
        """Return Role"""

        offset = int((page - 1) * limit)

        # COUNT
        sql_str = "SELECT COUNT(student_id) FROM user_group_students WHERE"
        sql_str += " user_group_id='{0}'".format(group_id)

        count = self.postgres.query_fetch_one(sql_str)
        total_rows = count['count']

        # FETCH DATA
        cols = "email, first_name, id, id as key, last_name, middle_name,"
        cols += " ROUND(cast(progress as numeric),2) AS progress,"
        cols += " status, username, created_on"
        sql_str = "SELECT {0}".format(cols)
        sql_str += " FROM account WHERE id IN ("
        sql_str += "SELECT student_id FROM user_group_students WHERE"
        sql_str += " user_group_id='{0}')".format(group_id)
        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)

        response = self.postgres.query_fetch_all(sql_str)

        group = self.get_group(group_id)
        for res in response:

            res['struggles_with'] = self.get_struggles_with(res['id'])
            res['mood'] = "Good"
            res['group'] = group

            oneday = 86400
            today = time.time()

            sql_str = "SELECT update_on, end_on FROM student_course"
            sql_str += " WHERE account_id='{0}' AND update_on IS NOT NULL ORDER BY update_on DESC".format(res['id'])
            result = self.postgres.query_fetch_one(sql_str)

            created_on = res['created_on']

            if result:

                if result['end_on']:
                    created_on = result['end_on']
                else:
    
                    if result['update_on']:
                        created_on = result['update_on']

            lapse = today - int(created_on)

            days = int(lapse / oneday)

            if days > 7:
                
                res['last_active'] = str(int(days / 7)) + ' week(s)'

            else:

                # res['last_active'] = str(days) + ' day(s)'
                res['last_active'] = self.convert_last_active(lapse)

        total_page = int((total_rows + limit - 1) / limit)

        data = {}
        data['rows'] = response
        data['total_rows'] = total_rows
        data['total_page'] = total_page
        data['limit'] = limit
        data['page'] = page

        return data

    def get_group(self, group_id):
        """ GET GROUP """
        sql_str = "SELECT * FROM user_group WHERE"
        sql_str += " user_group_id='{0}'".format(group_id)
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

    def convert_last_active(self, data):
        """ Return Day/ Hours/ Minutes/ Seconds"""

        day = data // (24 * 3600)
        time = data % (24 * 3600)
        hour = time // 3600
        time %= 3600
        minutes = time // 60
        time %= 60
        seconds = time

        days = ""
        hours = ""
        mins = ""


        days = "{0} day(s)".format(int(day))
        if not day:

            if hour:
                hours = "{0} hour(s) ".format(str(int(hour)))
            

            if minutes:
                mins = "{0} minute(s)".format(int(float(minutes)))

            return "{0}{1}".format(hours, mins)

        return days
