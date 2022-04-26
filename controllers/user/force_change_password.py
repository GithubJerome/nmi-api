"""Force Change Password"""
import time
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class ForceChangePassword(Common):
    """Class for ForceChangePassword"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for ForceChangePassword class"""

        self.postgres = PostgreSQL()
        super(ForceChangePassword, self).__init__()

    def force_change_password(self):
        """
        This API is for Force Change Password
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
            description: Force Change Password
            required: true
            schema:
              id: Force Change Password
              properties:
                email:
                    type: string
                new_password:
                    type: string
                old_password:
                    type: string

        responses:
          500:
            description: Error
          200:
            description: Force Change Password
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

        if not self.update_password(userid, query_json):

            data["alert"] = "Please check your query!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        data['message'] = "Password successfully updated!"
        data['status'] = "ok"
        return self.return_data(data, userid)

    def update_password(self, user_id, query_json):
        """Update Password"""

        tmp = {}
        # GET CURRENT TIME
        tmp['update_on'] = time.time()
        tmp['password'] = query_json['new_password']
        tmp['force_change_password'] = False

        # UPDATE
        # INIT CONDITION
        conditions = []

        # CONDITION FOR QUERY
        conditions.append({
            "col": "id",
            "con": "=",
            "val": user_id
            })

        if self.postgres.update('account', tmp, conditions):
            # RETURN
            return 1

        # RETURN
        return 0
