# pylint: disable=too-many-function-args
"""Create Issue"""
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity

class CreateIssue(Common):
    """Class for CreateIssue"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CreateIssue class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(CreateIssue, self).__init__()

    def create_issue(self):
        """
        This API is for Creating Issue
        ---
        tags:
          - Issue
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
          - name: query
            in: body
            description: Create Issue
            required: true
            schema:
              id: Create Issue
              properties:
                url:
                    type: string
                description:
                    type: string
                course_id:
                    type: string
                section_id:
                    type: string
                subsection_id:
                    type: string
                exercise_id:
                    type: string
                course_question_id:
                    type: string
        responses:
          500:
            description: Error
          200:
            description: Create Issue
        """
        data = {}

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

        # GET HEADER
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        if not self.insert_issue(query_json, userid):

            data["alert"] = "Please check your query!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # SEND EMAIL TO TUTOR

        data['message'] = "Issue successfully created!"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def insert_issue(self, query_json, userid):
        """Insert Issue"""

        if not query_json['course_id']:

            self.remove_key(query_json, "course_id")

        if not query_json['section_id']:

            self.remove_key(query_json, "section_id")

        if not query_json['subsection_id']:

            self.remove_key(query_json, "subsection_id")

        if not query_json['exercise_id']:

            self.remove_key(query_json, "exercise_id")

        if not query_json['course_question_id']:

            self.remove_key(query_json, "course_question_id")


        query_json['issue_id'] = self.sha_security.generate_token(False)
        query_json['account_id'] = userid
        query_json['status'] = True
        query_json['created_on'] = time.time()

        if self.postgres.insert('issue', query_json, 'issue_id'):

            return 1

        return 0
