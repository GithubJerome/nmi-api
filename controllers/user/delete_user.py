# pylint: disable=too-many-function-args
"""Delete User"""
from flask import  request
from library.common import Common

class DeleteUser(Common):
    """Class for DeleteUser"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for DeleteUser class"""
        super(DeleteUser, self).__init__()

    def delete_user(self):
        """
        This API is for Deleting User
        ---
        tags:
          - User
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
            description: User IDs
            required: true
            schema:
              id: Delete Users
              properties:
                user_ids:
                    types: array
                    example: []
        responses:
          500:
            description: Error
          200:
            description: Delete Users
        """
        data = {}

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

        # GET HEADER
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # GET QUERY
        user_ids = query_json["user_ids"]

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        if not self.delete_users(user_ids):

            data["alert"] = "Please check your query!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        data['message'] = "User(s) successfully deleted!"
        data['status'] = "ok"
        return self.return_data(data, userid)

    def delete_users(self, user_ids):
        """Delete Users"""

        for user_id in user_ids:

            conditions = []

            conditions.append({
                "col": "id",
                "con": "=",
                "val": user_id
                })

            if not self.postgres.delete('account', conditions):

                return 0

        return 1
