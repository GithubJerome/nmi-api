""" ADD VIDEO """
import string
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.emailer import Email
from templates.invitation import Invitation

class AddVideo(Common, ShaSecurity):
    """Class for AddVideo"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for AddVideo class"""

        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(AddVideo, self).__init__()

    def add_video(self):
        """
        This API is for Add Video
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
          - name: query
            in: body
            description: Add Video
            required: true
            schema:
              id: Add Video
              properties:
                video_name:
                    type: string
                description:
                    type: string
                url:
                    type: string
        responses:
          500:
            description: Error
          200:
            description: Create Video
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

        # CREATE VIDEO
        if not self.run(query_json):
            data["alert"] = "Video already exist!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)


        data = {}
        data['message'] = "Video successfully added!"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def run(self, query_json):
        """ CREATE VIDEO """

        # VALIDATE VIDEO
        if not self.validate(query_json):

            # ADD VIDEO
            vid = {}
            vid['video_id'] = self.sha_security.generate_token(False)
            vid['video_name'] = query_json['video_name']

            if 'description' in query_json.keys():

                vid['description'] = query_json['description']

            vid['url'] = query_json['url']
            vid['status'] = True
            vid['created_on'] = time.time()

            self.postgres.insert('videos', vid, 'video_id')

            return 1

        return 0

    def validate(self, query):
        """ VALIDATE VIDEO """

        sql_str = "SELECT url FROM videos WHERE"
        sql_str += " url='{0}' AND status=True".format(query['url'])

        url = self.postgres.query_fetch_one(sql_str)

        if url:

            return 1

        return 0
