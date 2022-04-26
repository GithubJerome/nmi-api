# pylint: disable=too-many-function-args
"""Delete Videos"""
from flask import  request
from library.common import Common

class DeleteVideos(Common):
    """Class for DeleteVideos"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for DeleteVideos class"""
        super(DeleteVideos, self).__init__()

    def delete_videos(self):
        """
        This API is for Deleting Videos
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
            description: Video IDs
            required: true
            schema:
              id: Delete Videos
              properties:
                video_ids:
                    types: array
                    example: []
        responses:
          500:
            description: Error
          200:
            description: Delete Videos
        """
        data = {}

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

        # GET HEADER
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # GET QUERY
        video_ids = query_json["video_ids"]

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        if not self.remove_vid(video_ids):

            data["alert"] = "You can't delete video that bound to a Skil, Subsection or exercise!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        data['message'] = "Video successfully deleted!"
        data['status'] = "ok"
        return self.return_data(data, userid)

    def remove_vid(self, video_ids):
        """Delete Video"""

        conditions = []

        conditions.append({
            "col": "video_id",
            "con": "in",
            "val": video_ids
            })

        if not self.postgres.delete('videos', conditions):

            return 0

        return 1
