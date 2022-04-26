# pylint: disable=too-many-function-args
"""Instruction"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.aws_s3 import AwsS3

class Instruction(Common):
    """Class for Instruction"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Instruction class"""
        self.aws3 = AwsS3()
        self.postgresql_query = PostgreSQL()
        super(Instruction, self).__init__()

    def instruction(self):
        """
        This API is for Getting All Instruction
        ---
        tags:
          - Instruction
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
            required: true
            type: string
        responses:
          500:
            description: Error
          200:
            description: Instruction
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        exercise_id = request.args.get('exercise_id')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        datas = self.get_instruction(exercise_id)
        datas['status'] = 'ok'

        return self.return_data(datas)

    def get_instruction(self, exercise_id):
        """Return All Instruction"""

        sql_str = "SELECT * FROM instruction WHERE"
        sql_str += " exercise_id='{0}'".format(exercise_id)
        sql_str += " ORDER BY page_number ASC"
        result = self.postgres.query_fetch_all(sql_str)

        for res in result:

            res['image_url'] = ""

            if res['image_id']:
                res['image_url'] = self.aws3.get_instruction_image(res['image_id'])

        data = {}
        data['rows'] = result

        return data
