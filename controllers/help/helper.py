# pylint: disable=too-few-public-methods
""" Help """
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class Help(Common):
    """Class for Help"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Help class"""
        self.postgresql_query = PostgreSQL()
        super(Help, self).__init__()

    def help(self):
        """
        This API is for Getting All Help
        ---
        tags:
          - Help
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
          - name: subsection_id
            in: query
            description: Subsection ID
            required: false
            type: string
          - name: exercise_id
            in: query
            description: Exercise ID
            required: false
            type: string
          - name: page
            in: query
            description: Page
            required: true
            type: string
          - name: limit
            in: query
            description: Limit
            required: true
            type: string
        responses:
          500:
            description: Error
          200:
            description: Help
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        exercise_id = request.args.get('exercise_id')
        subsection_id = request.args.get('subsection_id')
        page = int(request.args.get('page'))
        limit = int(request.args.get('limit'))

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:

            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        response = self.get_page_video(subsection_id, exercise_id, page, limit)

        if not response:
            data["alert"] = "No available video!"
            data["status"] = "Failed"
            return self.return_data(data, userid)

        data['data'] = response
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def get_page_video(self, subsection_id, exercise_id, page, limit):
        """ Return Page Video(s) """

        if subsection_id:
            return self.get_subsection_video(subsection_id, page, limit)

        offset = int((page - 1) * limit)

        # COUNT
        sql_str = "SELECT COUNT(*) FROM video_exercise WHERE exercise_id = '{0}'".format(exercise_id)
        count = self.postgres.query_fetch_one(sql_str)
        total_rows = count['count']

        sql_str = "SELECT * FROM video_exercise ve"
        sql_str += " LEFT JOIN videos v ON ve.video_id = v.video_id"
        sql_str += " WHERE exercise_id = '{0}'".format(exercise_id)
        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)
        result = self.postgres.query_fetch_all(sql_str)

        if result:

            total_page = int((total_rows + limit - 1) / limit)

            data = {}
            data['rows'] = result
            data['total_rows'] = total_rows
            data['total_page'] = total_page
            data['limit'] = limit
            data['page'] = page
            return data

        # GET SKILL VIDEO
        # sql_str = "SELECT COUNT(*) FROM video_skills WHERE skill_id IN"
        # sql_str += " (SELECT skill_id FROM exercise_skills WHERE exercise_id='{0}')".format(exercise_id)
        # count = self.postgres.query_fetch_one(sql_str)
        # total_rows = count['count']

        # sql_str = "SELECT * FROM video_skills vs LEFT JOIN videos v ON"
        # sql_str += " vs.video_id = v.video_id WHERE skill_id IN (SELECT skill_id FROM exercise_skills"
        # sql_str += " WHERE exercise_id='{0}')".format(exercise_id)
        # sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)
        # result = self.postgres.query_fetch_all(sql_str)

        sql_str = "SELECT COUNT(*) FROM videos WHERE video_id IN"
        sql_str += " (SELECT DISTINCT (video_id) FROM video_skills WHERE"
        sql_str += " skill_id IN (SELECT skill_id FROM skills WHERE skill IN"
        sql_str += " (SELECT skill FROM skills WHERE skill_id IN"
        sql_str += " (SELECT skill_id FROM exercise_skills WHERE"
        sql_str += " exercise_id='{0}'))))".format(exercise_id)
        count = self.postgres.query_fetch_one(sql_str)
        total_rows = count['count']

        sql_str = "SELECT * FROM videos WHERE video_id IN"
        sql_str += " (SELECT DISTINCT (video_id) FROM video_skills"
        sql_str += " WHERE skill_id IN (SELECT skill_id FROM skills"
        sql_str += " WHERE skill IN (SELECT skill FROM skills WHERE"
        sql_str += " skill_id IN (SELECT skill_id FROM exercise_skills WHERE"
        sql_str += " exercise_id='{0}'))))".format(exercise_id)
        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)
        result = self.postgres.query_fetch_all(sql_str)

        if result:
            total_page = int((total_rows + limit - 1) / limit)

            data = {}
            data['rows'] = result
            data['total_rows'] = total_rows
            data['total_page'] = total_page
            data['limit'] = limit
            data['page'] = page
            return data

        return 0

    def get_subsection_video(self, subsection_id, page, limit):
        """ Return Exercise Video(s) """

        offset = int((page - 1) * limit)

        # COUNT
        sql_str = "SELECT COUNT(*) FROM video_subsection"
        sql_str += " WHERE subsection_id = '{0}'".format(subsection_id)
        count = self.postgres.query_fetch_one(sql_str)
        total_rows = count['count']

        sql_str = "SELECT * FROM video_subsection vs"
        sql_str += " LEFT JOIN videos v ON vs.video_id = v.video_id"
        sql_str += " WHERE subsection_id = '{0}'".format(subsection_id)
        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)
        result = self.postgres.query_fetch_all(sql_str)

        if result:

            total_page = int((total_rows + limit - 1) / limit)

            data = {}
            data['rows'] = result
            data['total_rows'] = total_rows
            data['total_page'] = total_page
            data['limit'] = limit
            data['page'] = page
            return data

        return 0

    def get_help(self, page, limit):
        """Return Skills"""

        offset = int((page - 1) * limit)

        # COUNT
        sql_str = "SELECT COUNT(*) FROM help"

        count = self.postgres.query_fetch_one(sql_str)
        total_rows = count['count']

        # DATA
        sql_str = "SELECT * FROM help"
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
