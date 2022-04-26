# pylint: disable=too-many-function-args
"""Delete Help"""
from flask import  request
from library.common import Common

class DeleteHelp(Common):
    """Class for DeleteHelp"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for DeleteHelp class"""
        super(DeleteHelp, self).__init__()

    def delete_help(self):
        """
        This API is for Deleting Help
        ---
        tags:
          - Help
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
            description: Help IDs
            required: true
            schema:
              id: Delete Help
              properties:
                help_ids:
                    types: array
                    example: []
        responses:
          500:
            description: Error
          200:
            description: Delete Help
        """
        data = {}

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

        # GET HEADER
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # GET QUERY
        help_ids = query_json["help_ids"]

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        if not self.del_help(help_ids):

            data["alert"] = "Please check your query!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        data['message'] = "Help successfully deleted!"
        data['status'] = "ok"
        return self.return_data(data, userid)

    def del_help(self, help_ids):
        """Delete Help"""

        conditions = []

        conditions.append({
            "col": "help_id",
            "con": "in",
            "val": help_ids
            })

        if not self.postgres.delete('help', conditions):

            return 0

        return 1
