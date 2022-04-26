# pylint: disable=too-many-function-args
"""Student Course"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class StudentCourse(Common):
    """Class for StudentCourse"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for StudentCourse class"""
        self.postgresql_query = PostgreSQL()
        super(StudentCourse, self).__init__()

    def student_course(self):
        """
        This API is for Getting All Student Course
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
            description: Student Course
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

        datas = self.get_student_course(userid, page, limit)
        datas['status'] = 'ok'

        return self.return_data(datas, userid)

    def get_student_course(self, user_id, page, limit):
        """Return All Courses"""

        offset = int((page - 1) * limit)

        # COUNT
        sql_str = "SELECT COUNT(*) FROM student_course WHERE account_id='{0}'".format(user_id)

        count = self.postgres.query_fetch_one(sql_str)
        total_rows = count['count']

        # DATA
        # sql_str = "SELECT c.course_id, c.course_name, c.description, c.requirements,"
        # sql_str += " c.difficulty_level, sc.account_id, sc.course_id, sc.is_unlocked,"
        # sql_str += " ROUND(cast(sc.progress as numeric),2) AS progress,"
        # sql_str += " sc.expiry_date, sc.status, sc.update_on, sc.created_on FROM"
        # sql_str += " course c LEFT JOIN student_course sc ON"
        # sql_str += " c.course_id = sc.course_id WHERE"
        # sql_str += " sc.account_id = '{0}'".format(user_id)
        # sql_str += " ORDER BY c.difficulty_level"
        # sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)
        # result = self.postgres.query_fetch_all(sql_str)

        # DISPLAY COURSE FIRST ON GROUP
        # sql_str = "SELECT * FROM (SELECT DISTINCT c.course_id, c.course_name, c.course_title, c.description,"
        # sql_str += " c.requirements, c.difficulty_level, sc.account_id, sc.course_id, sc.is_unlocked,"
        # sql_str += " ROUND(cast(sc.progress as numeric),2) AS progress, sc.expiry_date,"
        # sql_str += " sc.status, sc.update_on, sc.created_on FROM user_group_courses ugc"
        # sql_str += " LEFT JOIN student_course sc ON ugc.course_id = sc.course_id"
        # sql_str += " LEFT JOIN course c ON ugc.course_id = c.course_id WHERE"
        # sql_str += " ugc.user_group_id IN (SELECT  user_group_id FROM user_group_students"
        # sql_str += " WHERE student_id = '{0}') AND account_id = '{0}'".format(user_id)
        # sql_str += " ORDER BY c.difficulty_level) a UNION ALL SELECT * FROM ("
        # sql_str += " SELECT c.course_id, c.course_name, c.course_title, c.description, c.requirements,"
        # sql_str += " c.difficulty_level, sc.account_id, sc.course_id, sc.is_unlocked,"
        # sql_str += " ROUND(cast(sc.progress as numeric),2) AS progress, sc.expiry_date, sc.status,"
        # sql_str += " sc.update_on, sc.created_on FROM course c LEFT JOIN student_course sc"
        # sql_str += " ON c.course_id = sc.course_id WHERE sc.account_id ='{0}'".format(user_id)
        # sql_str += " AND sc.course_id NOT IN (SELECT ugc.course_id FROM user_group_courses ugc"
        # sql_str += " LEFT JOIN student_course sc ON ugc.course_id = sc.course_id"
        # sql_str += " WHERE ugc.user_group_id IN (SELECT  user_group_id FROM user_group_students"
        # sql_str += " WHERE student_id = '{0}') AND account_id = '{0}'".format(user_id)
        # sql_str += " ) ORDER BY c.difficulty_level) b LIMIT {0} OFFSET {1}".format(limit, offset)

        sql_str = "SELECT DISTINCT c.course_id, c.course_name, c.course_title, c.description,"
        sql_str += " c.requirements, c.difficulty_level, sc.account_id, sc.course_id, sc.is_unlocked,"
        sql_str += " cs.sequence,ROUND(cast(sc.progress as numeric),2) AS progress, sc.expiry_date,"
        sql_str += " sc.status, sc.update_on, sc.created_on FROM user_group_courses ugc"
        sql_str += " LEFT JOIN student_course sc ON ugc.course_id = sc.course_id"
        sql_str += " LEFT JOIN course c ON ugc.course_id = c.course_id"
        sql_str += " LEFT JOIN course_sequence cs ON c.course_id = cs.course_id WHERE"
        sql_str += " ugc.user_group_id IN (SELECT  user_group_id FROM user_group_students"
        sql_str += " WHERE student_id = '{0}') AND account_id = '{0}'".format(user_id)
        sql_str += "  ORDER BY cs.sequence LIMIT {0} OFFSET {1}".format(limit, offset)
        result = self.postgres.query_fetch_all(sql_str)

        total_page = int((total_rows + limit - 1) / limit)

        data = {}
        data['rows'] = result
        data['total_rows'] = total_rows
        data['total_page'] = total_page
        data['limit'] = limit
        data['page'] = page

        return data
