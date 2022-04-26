# pylint: disable=too-many-function-args
"""Create Instruction"""
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity

class CreateInstruction(Common):
    """Class for CreateInstruction"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CreateInstruction class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(CreateInstruction, self).__init__()

    def create_instruction(self):
        """
        This API is for Creating Instruction
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
          - name: query
            in: body
            description: Create Instruction
            required: true
            schema:
              id: Create Instruction
              properties:
                instructions:
                    types: array
                    example: [{
                        text: string,
                        video_url: string,
                        sound_url: string,
                        image_id: string,
                        page_number: 1
                    }]
        responses:
          500:
            description: Error
          200:
            description: Create Instruction
        """
        data = {}

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

        # GET HEADER
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

        if not self.insert_instruction(exercise_id, query_json):

            data["alert"] = "Please check your query!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # SEND EMAIL TO TUTOR

        data['message'] = "Instruction successfully created!"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def insert_instruction(self, exercise_id, query_json):
        """Insert Instruction"""

        for item in query_json['instructions']:

            data = {}
            data['instruction_id'] = self.sha_security.generate_token(False)
            data['exercise_id'] = exercise_id
            data['text'] = item['text'].replace("'", "`")
            data['video_url'] = item['video_url']
            data['sound_url'] = item['sound_url']
            data['image_id'] = item['image_id']
            data['page_number'] = item['page_number']
            data['created_on'] = time.time()

            self.postgres.insert('instruction', data, 'instruction_id')

        return 1
