# pylint: disable=too-many-function-args
"""Notification"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class Notification(Common):
    """Class for Notification"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Notification class"""
        self.postgresql_query = PostgreSQL()
        super(Notification, self).__init__()

    def notification(self):
        """
        This API is for Getting All Notifications
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
          - name: limit
            in: query
            description: Limit
            required: true
            type: integer
          - name: page
            in: query
            description: Page
            required: true
            type: integer
        responses:
          500:
            description: Error
          200:
            description: Notification
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        page = int(request.args.get('page'))
        limit = int(request.args.get('limit'))

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        datas = self.get_all_notif(userid, page, limit)
        datas['status'] = 'ok'

        return self.return_data(datas, userid)

    def get_all_notif(self, userid, page, limit):
        """Return All Notification"""

        sql_str = "SELECT language FROM account WHERE"
        sql_str += " id='{0}'".format(userid)
        language = self.postgres.query_fetch_one(sql_str)

        offset = int((page - 1) * limit)

        # COUNT
        sql_str = "SELECT COUNT(*) FROM notifications"
        sql_str += " WHERE account_id ='{0}'".format(userid)

        count = self.postgres.query_fetch_one(sql_str)
        total_rows = count['count']

        # UNSEEN
        sql_str = "SELECT COUNT(*) FROM notifications"
        sql_str += " WHERE account_id ='{0}'".format(userid)
        sql_str += " AND seen_by_user=False"

        count = self.postgres.query_fetch_one(sql_str)
        unseen = count['count']

        # DATA
        sql_str = "SELECT * FROM notifications WHERE"
        sql_str += " account_id='{0}'".format(userid)
        sql_str += " ORDER BY created_on DESC"
        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)

        rows = self.postgres.query_fetch_all(sql_str)

        notifs = []
        for row in rows:

            if 'You have new Course' in row['description']:
            
                row['description'] = row['description'].replace("You have new Course", 'You have new course')

            if 'You have new course' in row['description']:

                messaged = self.translate(userid, 'You have new course', language=language)
                row['description'] = row['description'].replace("You have new course", messaged)

            if 'You have new Group' in row['description']:

                row['description'] = row['description'].replace("You have new Group", 'You have new group')

            if 'You have new group' in row['description']:

                messaged = self.translate(userid, 'You have new group', language=language)
                row['description'] = row['description'].replace("You have new group", messaged)

            notifs.append(row)

        total_page = int((total_rows + limit - 1) / limit)

        data = {}
        data['rows'] = notifs
        data['unseen'] = unseen
        data['total_rows'] = total_rows
        data['total_page'] = total_page
        data['limit'] = limit
        data['page'] = page

        return data
