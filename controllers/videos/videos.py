# pylint: disable=too-few-public-methods
""" VIDEOS """
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class Videos(Common):
    """Class for Videos"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Videos class"""
        self.postgresql_query = PostgreSQL()
        super(Videos, self).__init__()

    def videos(self):
        """
        This API is for Getting All Video
        ---
        tags:
          - Video
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
          - name: video_id
            in: query
            description: Video ID
            required: false
            type: string
          - name: page
            in: query
            description: Page
            required: false
            type: string
          - name: limit
            in: query
            description: Limit
            required: false
            type: string
        responses:
          500:
            description: Error
          200:
            description: Videos
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        video_id = request.args.get('video_id')
        page = 1
        limit = 10

        if not video_id:

            page = int(request.args.get('page'))
            limit = int(request.args.get('limit'))

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:

            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        if not video_id:

            datas = self.get_videos(page, limit)
            datas['status'] = 'ok'

            return self.return_data(datas)

        sql_str = "SELECT url FROM videos WHERE"
        sql_str += " video_id='{0}'".format(video_id)
        response = self.postgres.query_fetch_one(sql_str)

        if not response:

            data["alert"] = "Video not exist!"
            data['status'] = 'Failed'

            return self.return_data(data, userid)

        data['data'] = response
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def get_videos(self, page, limit):
        """Return Videos"""

        offset = int((page - 1) * limit)

        # COUNT
        sql_str = "SELECT COUNT(*) FROM videos"

        count = self.postgres.query_fetch_one(sql_str)
        total_rows = count['count']

        # DATA
        sql_str = "SELECT * FROM videos"
        sql_str += " ORDER BY created_on ASC"
        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)

        res = self.postgres.query_fetch_all(sql_str)

        total_page = int((total_rows + limit - 1) / limit)

        data = {}
        data['rows'] = res
        data['total_rows'] = total_rows
        data['total_page'] = total_page
        data['limit'] = limit
        data['page'] = page

        return data
