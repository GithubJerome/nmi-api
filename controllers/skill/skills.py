# pylint: disable=too-few-public-methods
""" Skills """
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class Skills(Common):
    """Class for Skills"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Skills class"""
        self.postgresql_query = PostgreSQL()
        super(Skills, self).__init__()

    def skills(self):
        """
        This API is for Getting All Skills
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
            description: Skills
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

        datas = self.get_skills(page, limit)
        datas['status'] = 'ok'

        return self.return_data(datas)

    def get_skills(self, page, limit):
        """Return Skills"""

        offset = int((page - 1) * limit)

        # COUNT
        sql_str = "SELECT COUNT(DISTINCT skill) FROM skills"

        count = self.postgres.query_fetch_one(sql_str)
        total_rows = count['count']

        # DATA
        sql_str = """SELECT *, (SELECT array_to_json(array_agg(videos)) FROM (
                    SELECT v.* FROM video_skills vs
                    LEFT JOIN videos v ON vs.video_id = v.video_id
                    WHERE skill_id = s.skill_id) videos) as videos
                    FROM skills s WHERE skill_id IN (SELECT MAX(skill_id) 
                    FROM skills GROUP BY skill) ORDER BY created_on"""

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
