"""Add Video to Skills"""
import string
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity

class CreateSkillVideos(Common, ShaSecurity):
    """Class for CreateSkillVideos"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CreateSkillVideos class"""

        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(CreateSkillVideos, self).__init__()

    def create_skill_videos(self):
        """
        This API is for Adding Videos to Skill
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
          - name: skill_id
            in: query
            description: Skill ID
            required: true
            type: string
          - name: Video
            in: body
            description: Videos
            required: true
            schema:
              id: Bind Video to Skills
              properties:
                video_ids:
                    types: array
                    example: []

        responses:
          500:
            description: Error
          200:
            description: Add Skill Video
        """

        # INIT DATA
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        skill_id = request.args.get('skill_id')

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
        self.add_skill_videos(token, userid, skill_id, query_json)

        data = {}
        data['message'] = "Skill has been updated successfully"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def add_skill_videos(self, token, userid, skill_id, query_json):
        """ LINK VIDEO TO SKILLS"""

        # GET SKILL ID's
        sql_str = "SELECT skill_id FROM skills WHERE skill=("
        sql_str += "SELECT skill FROM skills WHERE"
        sql_str += " skill_id='{0}')".format(skill_id)
        response = self.postgres.query_fetch_all(sql_str)

        skill_ids = [res['skill_id'] for res in response]

        video_ids = set(query_json['video_ids'])

        # INIT CONDITION
        conditions = []

        # CONDITION FOR QUERY
        conditions.append({
            "col": "skill_id",
            "con": "in",
            "val": skill_ids
            })

        # DELETE EXISTING SKILLS
        self.postgres.delete('video_skills', conditions)

        # ADD VIDEOS
        for video_id in video_ids:

            for skillid in skill_ids:

                data = {}
                data['video_skill_id'] = self.sha_security.generate_token(False)
                data['skill_id'] = skillid
                data['video_id'] = video_id
                self.postgres.insert('video_skills', data)

        return 1
