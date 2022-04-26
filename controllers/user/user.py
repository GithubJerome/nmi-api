"""User"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class User(Common):
    """Class for User"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for User class"""
        self.postgres = PostgreSQL()
        super(User, self).__init__()

    # LOGIN FUNCTION
    def user(self):
        """
        This API is for Getting All User by type
        ---
        tags:
          - User
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
          - name: sort_type
            in: query
            description: Sort Type
            required: false
            type: string
          - name: sort_column
            in: query
            description: Sort Column
            required: false
            type: string
          - name: filter_column
            in: query
            description: Filter Column
            required: false
            type: string
          - name: filter_value
            in: query
            description: Filter Value
            required: false
            type: string
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
        sort_type = request.args.get('sort_type')
        sort_column = request.args.get('sort_column')
        filter_column = request.args.get('filter_column')
        filter_value = request.args.get('filter_value')
        selected_ids = request.args.get('selected_ids')
        search = request.args.get('search')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        if filter_column and filter_value:

            filter_list = []
            for col in filter_column.split(","):
                filter_list.append(col)

            filter_val = []
            for val in filter_value.split(","):
                filter_val.append(val)

            filter_value = tuple(filter_val)

        else:

            filter_list = filter_column

        datas = self.get_users(page, limit, sort_type, sort_column,
                               filter_list, filter_value, selected_ids, search)

        keys = ['username', 'email', 'status']

        for key in keys:

            user_data = self.get_account_data(key)
            format_data = self.data_filter(user_data, key)

            if key == "username":
                usernames = format_data

            if key == "email":
                emails = format_data

            if key == "status":
                status = format_data

        datas['username'] = usernames
        datas['email'] = emails
        datas['status2'] = status
        datas['status'] = 'ok'

        return self.return_data(datas)

    def get_users(self, page, limit, sort_type, sort_column,
                  filter_list, filter_value, selected_ids, search):
        """Return Users"""

        offset = int((page - 1) * limit)

        selected = None
        if selected_ids:
            selected = ','.join("'{0}'".format(selected) for selected in selected_ids.split(","))

        sql_str = "SELECT * FROM account_master"

        if selected:
            sql_str += " WHERE id IN ({0}) UNION ALL (SELECT * FROM account_master".format(selected)

        #WHERE STATEMENT
        where_sql = ""
        search_sql = ""

        if search:
            search_ = []
            search_column = ['username', 'email', 'first_name', 'middle_name', 'last_name', 'roles']
            search_json = ['role', 'roles', 'role_name']

            for col in search_column:

                if col.upper() == "ROLES":

                    cast = '"{0}"'.format(col)
                    search_st = "CAST({0} AS text) ILIKE '%{1}%'".format(cast, str(search))

                else:
                     search_st = "{0} ILIKE '%{1}%'".format(col, str(search))

                search_.append(search_st)

            search_sql = " OR ".join(search_)

        if filter_list and filter_value:

            where = []

            i = 0
            for val in filter_value:

                key = filter_list[i]

                if key in ['roles', 'role', 'role_name']:
                    where_st = """id in (SELECT account_id FROM role r
                        LEFT JOIN account_role ar ON r.role_id = ar.role_id
                        WHERE r.role_name ILIKE '{0}')""".format(val)

                elif key == "status":
                    status = bool(val == "Enabled")

                    where_st = "status = '{0}'".format(status)

                else:
                    where_st = "{0} ILIKE '{1}'".format(key, val)

                i += 1

                where.append(where_st)

            where_sql = " AND ".join(where)

        
        if where_sql or search_sql:

            if where_sql != '' and search_sql != '':
                search_sql = "AND ({0})".format(search_sql)

            sql_str += " WHERE {0} {1}".format(where_sql, search_sql)

            if selected:
                sql_str += "  AND id NOT IN ({0})".format(selected)

        else:
            if selected:
                sql_str += " WHERE id NOT IN ({0})".format(selected)


        #SORT
        if sort_column and sort_type:

            if sort_column in ['username', 'email', 'status']:
                table = "{0}".format(sort_column)
                sql_str += " ORDER BY  {0} {1}".format(table, sort_type.lower())

        else:
            sql_str += " ORDER BY created_on desc"

        if selected:
            sql_str += ")"

        # COUNT
        count_str = "SELECT COUNT(*) FROM ({0}) as accounts".format(sql_str)
        count = self.postgres.query_fetch_one(count_str)

        #LIMIT
        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)

        accounts = self.postgres.query_fetch_all(sql_str)

        # CHECK USERNAME
        if accounts:

            for account in accounts:
                if "no_username" in account['username']:
                    account['username'] = ""

                # REMOVE PASSWORD
                self.remove_key(account, "password")

        total_rows = count['count']
        total_page = int((total_rows + limit - 1) / limit)
        data = {}
        data['rows'] = accounts
        data['total_rows'] = total_rows
        data['total_page'] = total_page
        data['limit'] = limit
        data['page'] = page

        return data


    def get_account_data(self, key):
        """Return Account Data"""

        if key:

            # DATA
            sql_str = "SELECT DISTINCT {0} FROM account".format(key)

            datas = self.postgres.query_fetch_all(sql_str)

            data = {}

            k = "{0}s".format(key)

            temp_data = [temp_data[key] for temp_data in datas]

            data[k] = temp_data

        return data
