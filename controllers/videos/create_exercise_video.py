"""Add Video to Skills"""
import string
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity

class CreateExerciseVideo(Common, ShaSecurity):
    """Class for CreateExerciseVideo"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CreateExerciseVideo class"""

        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(CreateExerciseVideo, self).__init__()

    def create_exercise_video(self):
        """
        This API is for Adding Video to Exercise
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
          - name: exercise_id
            in: query
            description: Exercise ID
            required: true
            type: string
          - name: Video
            in: body
            description: Videos
            required: true
            schema:
              id: Bind Video to Exercise
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
        exercise_id = request.args.get('exercise_id')

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
        self.add_exercise_videos(token, userid, exercise_id, query_json)

        data = {}
        data['message'] = "Exercise has been updated successfully"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def add_exercise_videos(self, token, userid, exercise_id, query_json):
        """ LINK VIDEO TO SKILLS"""

        video_ids = set(query_json['video_ids'])

        # INIT CONDITION
        conditions = []

        # CONDITION FOR QUERY
        conditions.append({
            "col": "exercise_id",
            "con": "=",
            "val": exercise_id
            })

        # DELETE EXISTING SKILLS
        self.postgres.delete('video_exercise', conditions)

        # ADD VIDEOS
        for video_id in video_ids:

            data = {}
            data['video_exercise_id'] = self.sha_security.generate_token(False)
            data['exercise_id'] = exercise_id
            data['video_id'] = video_id
            self.postgres.insert('video_exercise', data)

        return 1
