# pylint: disable=too-few-public-methods
""" Skill """
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class Skill(Common):
    """Class for Skill"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Skill class"""
        self.postgresql_query = PostgreSQL()
        super(Skill, self).__init__()

    def skill(self):
        """
        This API is for Getting All Skill
        ---
        tags:
          - Skill
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
            description: Skill
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

        datas = self.get_skill(page, limit)
        datas['status'] = 'ok'

        return self.return_data(datas)

    def get_skill(self, page, limit):
        """Return Skills"""

        offset = int((page - 1) * limit)

        # COUNT
        sql_str = "SELECT COUNT(*) FROM skill_master"

        count = self.postgres.query_fetch_one(sql_str)
        total_rows = count['count']

        # DATA
        sql_str = "SELECT * FROM skill_master"
        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)

        res = self.postgres.query_fetch_all(sql_str)

        total_page = int((total_rows + limit - 1) / limit)

        data = {}
        data['rows'] = res
        data['total_rows'] = total_rows
        data['total_page'] = total_page
        data['limit'] = limit
        data['page'] = page

        return data
