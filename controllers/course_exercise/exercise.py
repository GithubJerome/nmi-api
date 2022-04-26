# pylint: disable=too-many-function-args
"""Exercise"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class Exercise(Common):
    """Class for Exercise"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Exercise class"""
        self.postgresql_query = PostgreSQL()
        super(Exercise, self).__init__()

    def exercise(self):
        """
        This API is for Getting All Exercise Questions
        ---
        tags:
          - Exercise
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
          - name: exercise_id
            in: query
            description: Exercise ID
            required: false
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
            description: Exercise
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        page = int(request.args.get('page'))
        limit = int(request.args.get('limit'))

        exercise_id = request.args.get('exercise_id')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        datas = self.get_exercise(exercise_id, page, limit)
        datas['status'] = 'ok'

        return self.return_data(datas, userid)

    def get_exercise(self, exercise_id, page, limit):
        """Return All Exercises"""

        offset = int((page - 1) * limit)

        # COUNT
        sql_str = "SELECT COUNT(*) FROM exercise"
        count = self.postgres.query_fetch_one(sql_str)
        total_rows = count['count']

        # DATA
        # sql_str = "SELECT exercise_id as key, '' as questions, * FROM exercise"

        sql_str = """SELECT e.exercise_id as key, '' as questions, c.exercise_name, 
                    CASE WHEN c.exercise_name is null OR c.exercise_name = '' then
                    'Exercise '||e.exercise_number else CONCAT(c.exercise_name, ' ')||e.exercise_number end as exercise_num,
                    e.* FROM exercise e LEFT JOIN course c ON e.course_id = c.course_id"""

        if exercise_id:
            sql_str += " WHERE exercise_id = '{0}'".format(exercise_id)

        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)

        result = self.postgres.query_fetch_all(sql_str)

        for res in result:
            res['questions'] = self.get_questions(res['exercise_id'])

        total_page = int((total_rows + limit - 1) / limit)

        data = {}
        data['rows'] = result
        data['total_rows'] = total_rows
        data['total_page'] = total_page
        data['limit'] = limit
        data['page'] = page

        return data

    def get_questions(self, exercise_id):
        """ Return questions """

        sql_str = "SELECT * FROM course_question WHERE exercise_id = '{0}'".format(exercise_id)
        result = self.postgres.query_fetch_all(sql_str)

        return result
