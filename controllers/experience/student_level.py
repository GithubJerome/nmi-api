# pylint: disable=too-many-function-args
"""Student Level"""
import math
from datetime import datetime
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class StudentLevel(Common):
    """Class for StudentLevel"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for StudentLevel class"""
        self.postgresql_query = PostgreSQL()
        super(StudentLevel, self).__init__()

    def student_level(self):
        """
        This API is for Getting Student Level
        ---
        tags:
          - Experience
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
            description: Student Level
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

        result = self.get_student_level(userid)

        data['data'] = result
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def get_student_level(self, user_id):
        """ Return Student Level """

        sql_str = "SELECT sum(total_experience) as experience FROM student_exercise WHERE status is True"
        sql_str += " AND progress = '100' AND account_id='{0}'".format(user_id)
        result = self.postgres.query_fetch_one(sql_str)

        total_experience = result['experience']
        if result['experience'] is None:
            total_experience = 0

        # LEVELS
        level = 5
        levels = []
        xp_level = 0
        for lvl in range(level):
            if lvl > 0:
                xp_level += 1000

                if lvl > 1:
                    xp_level += math.ceil(levels[lvl-1] * .10)

            levels.append(xp_level)

        counter = 1
        data = {}

        for lvl in levels:

            if total_experience >= levels[-1]:
                data['level'] = levels.index(levels[-1]) + 1
                data['experience'] = total_experience
                data['need_more'] = 0
                return data

            if total_experience >= lvl:
                data['level'] = counter
                data['experience'] = total_experience
                data['need_more'] = levels[counter] - total_experience

            if counter > 1:

                if total_experience >= lvl and total_experience <= levels[counter-1]:
                    data['level'] = counter
                    data['experience'] = total_experience

                    if counter < 5:
                        data['need_more'] = levels[counter] - total_experience

            counter +=1

        return data
