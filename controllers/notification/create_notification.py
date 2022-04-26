# pylint: disable=too-many-function-args
"""Create Notification"""
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity

class CreateNotification(Common):
    """Class for CreateNotification"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CreateNotification class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(CreateNotification, self).__init__()

    def create_notification(self):
        """
        This API is for Creating Notification
        ---
        tags:
          - Notification
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
            description: Create Notification
            required: true
            schema:
              id: Create Notification
              properties:
                notification_name:
                    type: string
                notification_type:
                    type: string
                description:
                    type: string
        responses:
          500:
            description: Error
          200:
            description: Create Notification
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

        if not self.insert_nofif(query_json, userid):

            data["alert"] = "Please check your query!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # SEND EMAIL TO TUTOR

        data['message'] = "Notification successfully created!"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def insert_nofif(self, query_json, userid):
        """Insert Notif"""

        datas = {}
        datas['notification_id'] = self.sha_security.generate_token(False)
        datas['account_id'] = userid
        datas['notification_name'] = query_json['notification_name']
        datas['notification_type'] = query_json['notification_type']
        datas['description'] = query_json['description']
        datas['seen_by_user'] = False
        datas['created_on'] = time.time()

        if self.postgres.insert('notifications', datas, 'notification_id'):

            return 1

        return 0
