"""Create User Group"""
import string
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.emailer import Email
from templates.invitation import Invitation

class CreateUserGroup(Common, ShaSecurity):
    """Class for CreateUserGroup"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CreateUserGroup class"""

        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(CreateUserGroup, self).__init__()

    def create_user_group(self):
        """
        This API is for Creating User Group
        ---
        tags:
          - User Group
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
            description: User Group
            required: true
            schema:
              id: Add User Group
              properties:
                user_group_name:
                    type: string
                course_ids:
                    types: array
                    example: []
                student_ids:
                    types: array
                    example: []
                tutor_ids:
                    types: array
                    example: []
                notify_members:
                    type: boolean
                notify_managers:
                    type: boolean
        responses:
          500:
            description: Error
          200:
            description: Create User
        """

        # INIT DATA
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # VALIDATE USER
        if not self.validate_user(userid, 'manager'):
            data["alert"] = "Invalid User"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # VALIDATE USER GROUP NAME
        if not self.validate_group_name(query_json['user_group_name']):
            data["alert"] = "Group name already exist"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # CREATE USER GROUP
        self.create_new_group(query_json, token=token, userid=userid)

        data = {}
        data['message'] = "User Group successfully created"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def validate_group_name(self, group_name):
        """ VALIDATE GROUP NAME """

        sql_str = "SELECT user_group_name FROM user_group WHERE"
        sql_str += " user_group_name='{0}'".format(group_name)

        user_group_name = self.postgres.query_fetch_one(sql_str)

        if user_group_name:

            return 0

        return 1
