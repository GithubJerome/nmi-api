
"""TUTOR GROUPS"""
import time

from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class TutorGroups(Common):
    """Class for Tutor GROUPS"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Tutor GROUPS class"""
        self.postgres = PostgreSQL()
        super(TutorGroups, self).__init__()

    def tutor_groups(self):
        """
        This API is for Getting Tutor Groups
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

        datas = self.get_groups(userid, page, limit)

        datas['status'] = 'ok'

        return self.return_data(datas, userid)

    def get_groups(self, user_id, page, limit):
        """Return Role"""

        offset = int((page - 1) * limit)

        # COUNT
        sql_str = "SELECT COUNT(user_group_id) FROM user_group WHERE"
        sql_str += " user_group_id IN (SELECT user_group_id FROM"
        sql_str += " user_group_tutors WHERE"
        sql_str += " tutor_id='{0}')".format(user_id)

        count = self.postgres.query_fetch_one(sql_str)
        total_rows = count['count']

        # FETCH DATA
        sql_str = "SELECT *, (SELECT array_to_json(array_agg(student)) FROM ("
        sql_str += "SELECT * FROM account a WHERE ug.least_performer=a.id ) AS student)"
        sql_str += " AS least_performer_student, ug.user_group_id AS key,"
        sql_str += " ROUND(cast(ug.progress as numeric),2) AS round_progress"
        sql_str += " FROM user_group ug WHERE ug.user_group_id IN (SELECT user_group_id"
        sql_str += " FROM user_group_tutors WHERE"
        sql_str += " tutor_id='{0}')".format(user_id)
        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)

        response = self.postgres.query_fetch_all(sql_str)

        for res in response:

            oneday = 86400
            today = time.time()
            created_on = res['created_on']
            lapse = today - int(created_on)

            days = int(lapse / oneday)

            if days > 7:
                
                res['age'] = str(int(days / 7)) + ' week(s)'

            else:

                res['age'] = str(days) + ' day(s)'

            # TEMPORARY
            if not res['next_class']:
                res['next_class'] = self.days_update(time.time(), 30, True)

        total_page = int((total_rows + limit - 1) / limit)

        data = {}
        data['rows'] = response
        data['total_rows'] = total_rows
        data['total_page'] = total_page
        data['limit'] = limit
        data['page'] = page

        return data
