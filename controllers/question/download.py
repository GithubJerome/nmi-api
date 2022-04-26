# encoding: utf-8
# pylint: disable=no-self-use, bare-except, too-many-locals, too-many-arguments, too-many-branches, too-many-nested-blocks
"""Question Template"""
import time

from flask import  request
from library.common import Common

class QuestionTemplate(Common):
    """Class for CourseTemplate"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for QuestionTemplate class"""

        super(QuestionTemplate, self).__init__()

    def question_template(self):
        """
        This API is for Download Question Template
        ---
        tags:
          - Download
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
          - name: type
            in: query
            description: Type
            required: true
            type: string
            example: "csv"

        responses:
          500:
            description: Error
          200:
            description: Question Template
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

        data['location'] = "templates/question_templateV1.csv"
        data['status'] = 'ok'

        return data
