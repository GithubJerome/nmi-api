# pylint: disable=too-many-locals, ungrouped-imports
"""Instruction Images"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.aws_s3 import AwsS3

class InstructionImages(Common):
    """Class for InstructionImages"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for InstructionImages class"""
        self.postgres = PostgreSQL()
        self.aws3 = AwsS3()
        super(InstructionImages, self).__init__()

    def get_images(self):
        """
        This API is for Getting All Instruction Images
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
        responses:
          500:
            description: Error
          200:
            description: Instruction Images
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data['alert'] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        instruction_images = self.get_instruction_images()

        for i_image in instruction_images:
            i_image['image_url'] = self.aws3.get_instruction_image(i_image['image_id'])

        data['instruction_images'] = instruction_images
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def get_instruction_images(self):
        """Get Instruction Images"""

        sql_str = "SELECT * FROM instruction_image"
        sql_str += " WHERE status = 'active' ORDER BY created_on DESC"

        images = self.postgres.query_fetch_all(sql_str)

        return images
