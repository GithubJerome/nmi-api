# pylint: disable=too-many-function-args
"""Update Notification"""
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity

class UpdateNotification(Common):
    """Class for UpdateNotification"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateNotification class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(UpdateNotification, self).__init__()

    def update_notification(self):
        """
        This API is for Updating Notification
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
            description: Update Notification
            required: true
            schema:
              id: Update Notification
              properties:
                notification_ids:
                    types: array
                    example: []

        responses:
          500:
            description: Error
          200:
            description: Update Notification
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

        if not self.edit_notif(query_json):

            data["alert"] = "Please check your query!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # UNSEEN
        sql_str = "SELECT COUNT(*) FROM notifications"
        sql_str += " WHERE account_id ='{0}'".format(userid)
        sql_str += " AND seen_by_user=False"

        count = self.postgres.query_fetch_one(sql_str)
        unseen = count['count']

        data['message'] = "Notification successfully updated!"
        data['status'] = "ok"
        data['unseen'] = unseen

        return self.return_data(data, userid)

    def edit_notif(self, query_json):
        """Update Notification"""

        query_json['update_on'] = time.time()

        conditions = []

        conditions.append({
            "col": "notification_id",
            "con": "in",
            "val": query_json['notification_ids']
            })

        data = {}
        data['seen_by_user'] = True

        if self.postgres.update('notifications', data, conditions):

            return 1

        return 0
