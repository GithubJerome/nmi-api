# pylint: disable=too-many-function-args
"""Course"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class Course(Common):
    """Class for Course"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Course class"""
        self.postgresql_query = PostgreSQL()
        super(Course, self).__init__()

    def course(self):
        """
        This API is for Getting All Courses
        ---
        tags:
          - Course
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
          - name: search
            in: query
            description: Search
            required: false
            type: string
        responses:
          500:
            description: Error
          200:
            description: Course
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        page = int(request.args.get('page'))
        limit = int(request.args.get('limit'))
        selected_ids = request.args.get('selected_ids')
        filter_column = request.args.get('filter_column')
        filter_value = request.args.get('filter_value')
        sort_type = request.args.get('sort_type')
        sort_column = request.args.get('sort_column')
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

        datas = self.get_all_courses(page, limit, sort_type, sort_column,
                                     filter_list, filter_value, selected_ids, search)
        datas['status'] = 'ok'

        return self.return_data(datas, userid)

    def get_all_courses(self, page, limit, sort_type, sort_column,
                        filter_list, filter_value, selected_ids, search):
        """Return All Courses"""

        offset = int((page - 1) * limit)

        # SORT ORDER
        self.run_sequence()

        selected = None
        if selected_ids:
            selected = ','.join("'{0}'".format(selected) for selected in selected_ids.split(","))


        #WHERE STATEMENT
        where_sql = ""
        search_sql = ""

        if search:
            search_ = []
            search_column = ['course_name', 'course_title', 'description', 'exercise_name']
         
            for col in search_column:

                search_st = "c.{0} ILIKE '%{1}%'".format(col, str(search))

                search_.append(search_st)

            search_sql = " OR ".join(search_)

        if filter_list and filter_value:

            where = []

            i = 0
            for val in filter_value:

                key = filter_list[i]

                where_st = "c.{0} ILIKE '{1}'".format(key, val)

                i += 1

                where.append(where_st)

            where_sql = " AND ".join(where)


        if where_sql or search_sql:

            if search_sql:
                search_sql = "({0})".format(search_sql)

            if where_sql != '' and search_sql != '':
                search_sql = "AND {0}".format(search_sql)

            condition = " WHERE {0} {1} AND c.status=true".format(where_sql, search_sql)

        else:
            condition = " WHERE c.status=true"

        # DATA
        sql_str = """SELECT c.course_id as key, c.*, cs.sequence,
                    (SELECT array_to_json(array_agg(acct))
                    FROM (SELECT * FROM account WHERE id IN (SELECT sc.account_id
                    FROM student_course sc WHERE sc.course_id=c.course_id)) AS acct)
                    AS students, (SELECT array_to_json(array_agg(groups))
                    FROM (SELECT * FROM user_group WHERE user_group_id IN (SELECT user_group_id FROM
                    user_group_courses ugc WHERE ugc.course_id=c.course_id)) AS groups) AS groups FROM course c
                    LEFT JOIN course_sequence cs ON c.course_id = cs.course_id"""

        if selected:

            sql_str += " WHERE c.status=true AND c.course_id IN ({0}) UNION ALL ({1}".format(selected, sql_str)
            sql_str += "{0} AND c.course_id NOT IN ({1}) AND c.status=true)".format(condition, selected)


        else:
            sql_str += condition

        # COUNT
        count_str = "SELECT COUNT(*) FROM ({0}) as course".format(sql_str)
        count = self.postgres.query_fetch_one(count_str)

         #SORT
        if sort_column and sort_type:

            if sort_column in ['course_name', 'course_title']:
                table = "{0}".format(sort_column)
                sql_str += " ORDER BY  {0} {1} LIMIT {2} OFFSET {3}".format(table, sort_type.lower(), limit, offset)
        else:

            sql_str += " ORDER BY sequence ASC LIMIT {0} OFFSET {1}".format(limit, offset)

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
