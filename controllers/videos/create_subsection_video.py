"""Add Video to Subsection"""
import string
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity

class CreateSubsectionVideo(Common, ShaSecurity):
    """Class for CreateSubsectionVideo"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CreateSubsectionVideo class"""

        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(CreateSubsectionVideo, self).__init__()

    def create_subsection_video(self):
        """
        This API is for Adding Video to Subsection
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
          - name: subsection_id
            in: query
            description: Subsection ID
            required: true
            type: string
          - name: Video
            in: body
            description: Videos
            required: true
            schema:
              id: Bind Video to Subsection
              properties:
                video_ids:
                    types: array
                    example: []

        responses:
          500:
            description: Error
          200:
            description: Add Exercise Video
        """

        # INIT DATA
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        subsection_id = request.args.get('subsection_id')

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # LINK VIDEO TO SKILL
        self.add_subsection_videos(token, userid, subsection_id, query_json)

        data = {}
        data['message'] = "Subsection has been updated successfully"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def add_subsection_videos(self, token, userid, subsection_id, query_json):
        """ LINK VIDEO TO SUBSECTION"""

        video_ids = set(query_json['video_ids'])

        # INIT CONDITION
        conditions = []

        # CONDITION FOR QUERY
        conditions.append({
            "col": "subsection_id",
            "con": "=",
            "val": subsection_id
            })

        # DELETE EXISTING SKILLS
        self.postgres.delete('video_subsection', conditions)

        # ADD VIDEOS
        for video_id in video_ids:

            data = {}
            data['video_subsection_id'] = self.sha_security.generate_token(False)
            data['subsection_id'] = subsection_id
            data['video_id'] = video_id
            self.postgres.insert('video_subsection', data)

        return 1
