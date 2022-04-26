"""User Group"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class UserGroup(Common):
    """Class for UserGroup"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UserGroup class"""
        self.postgres = PostgreSQL()
        super(UserGroup, self).__init__()

    # LOGIN FUNCTION
    def user_group(self):
        """
        This API is for Getting all user group
        ---
        tags:
          - User Group
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
          - name: selected_ids
            in: query
            description: Selected IDs
            required: false
            type: string
          - name: search
            in: query
            description: Search
            required: false
            type: string
        responses:
          500:
            description: Error
          200:
            description: User Information
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        page = int(request.args.get('page'))
        limit = int(request.args.get('limit'))
        selected_ids = request.args.get('selected_ids')
        # sort_type = request.args.get('sort_type')
        # sort_column = request.args.get('sort_column')
        search = request.args.get('search')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # VALIDATE USER
        if not self.validate_user(userid, 'manager'):
            data["alert"] = "Invalid User"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        datas = self.get_user_group(page, limit, selected_ids, search)
        datas['status'] = 'ok'

        return self.return_data(datas, userid)

    def get_user_group(self, page, limit, selected_ids, search):
        """ RETURN USER GROUP """
        offset = int((page - 1) * limit)

        selected = None
        if selected_ids:
            selected = ','.join("'{0}'".format(selected) for selected in selected_ids.split(","))

        #WHERE STATEMENT
        where_sql = ""
        search_sql = ""

        if search:
            search_ = []
            search_column = ['user_group_name', 'user_group_id', 'students', 'tutors']
            search_json = ['students', 'tutors']
         
            for col in search_column:

                if col in search_json:

                    cast = '"{0}"'.format(col)
                    search_st = "CAST({0} AS text) ILIKE '%{1}%'".format(cast, str(search))

                else:
                    search_st = "ugm.{0} ILIKE '%{1}%'".format(col, str(search))

                search_.append(search_st)

            search_sql = " OR ".join(search_)

        sql_str = "SELECT ugm.user_group_id as key, * FROM user_group_master ugm"
        sql_str += " LEFT JOIN user_group ug ON ugm.user_group_id = ug.user_group_id"

        if selected:
            sql_str += " WHERE ugm.user_group_id IN ({0}) UNION ALL ({1}".format(selected, sql_str)
            sql_str += " WHERE ugm.user_group_id NOT IN ({0})".format(selected)
            if search_sql:
                sql_str += " AND ({0})".format(search_sql)
            sql_str += " ORDER BY ugm.user_group_name DESC)"

        else:
            if search_sql:
                sql_str += " WHERE ({0})".format(search_sql)
            sql_str += " ORDER BY ugm.user_group_name DESC"

        # COUNT
        count_str = "SELECT COUNT(*) FROM ({0}) as user_group".format(sql_str)

        count = self.postgres.query_fetch_one(count_str)

        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)

        rows = []
        res = self.postgres.query_fetch_all(sql_str)

        total_rows = count['count']
        total_page = int((total_rows + limit - 1) / limit)

        if res:
            rows = res

        data = {}
        data['rows'] = rows
        data['total_rows'] = total_rows
        data['total_page'] = total_page
        data['limit'] = limit
        data['page'] = page

        return data
