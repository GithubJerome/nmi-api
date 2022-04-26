"""UPDATE SIDEBAR"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class UpdateSidebar(Common):
    """Class for """

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateSidebar class"""
        self.postgres = PostgreSQL()

        super(UpdateSidebar, self).__init__()

    # LOGIN FUNCTION
    def update_sidebar(self):
        """
        This API is for Getting User Sidebar
        ---
        tags:
          - Sidebar
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
            description: Updating User Sidebar
            required: true
            schema:
              id: Updating Side bar
              properties:
                sidebar:
                    type: boolean
        responses:
          500:
            description: Error
          200:
            description: User Sidebar
        """
        datas = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        query_json = request.get_json(force=True)
        sidebar = query_json['sidebar']

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            datas["alert"] = "Invalid Token"
            datas['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(datas, userid)

        self.update_user_sidebar(userid, sidebar)

        datas['message'] = "User sidebar successfully updated!"
        datas['status'] = 'ok'

        return self.return_data(datas)

    def update_user_sidebar(self, userid, sidebar):
        """Update User Sidebar"""

        status = True

        if not sidebar:

            status = False

        # UPDATE
        updates = {}
        updates['sidebar'] = status
        # INIT CONDITION
        conditions = []

        # CONDITION FOR QUERY
        conditions.append({
            "col": "id",
            "con": "=",
            "val": userid
            })

        self.postgres.update('account', updates, conditions)

        return 1
