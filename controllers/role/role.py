"""Role"""
import math
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class Role(Common):
    """Class for Role"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Role class"""
        self.postgres = PostgreSQL()
        super(Role, self).__init__()

    def role(self):
        """
        This API is for Getting Role
        ---
        tags:
          - Role
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
            description: Role
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

        datas = self.get_role(userid, page, limit)

        datas['status'] = 'ok'

        return self.return_data(datas)

    def get_role(self, user_id, page, limit):
        """Return Role"""

        # # GET SUPER ADMIN ID
        # sql_str = "SELECT * FROM account_role WHERE account_id='{0}'".format(user_id)
        # sql_str += " AND role_id=(SELECT role_id FROM role WHERE role_name='super admin')"
        # super_admin = self.postgres.query_fetch_one(sql_str)

        offset = int((page - 1) * limit)

        # COUNT
        sql_str = "SELECT COUNT(*) FROM role"

        count = self.postgres.query_fetch_one(sql_str)
        total_rows = count['count']

        # DATA
        sql_str = """
                    SELECT r.role_id, r.role_name, r.role_details,
                    r.role_id as value, r.role_name as label, (
                    SELECT array_to_json(array_agg(p ORDER BY p.permission_name))
                    FROM permission p INNER JOIN role_permission rp ON
                    rp.permission_id = p.permission_id WHERE rp.role_id = r.role_id)
                  """
        sql_str += " AS permissions FROM role r WHERE role_name != 'parent'"

        # if not super_admin:

        #     sql_str += " WHERE r.role_name != 'super admin' "
        sql_str += " ORDER BY r.role_name"
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
