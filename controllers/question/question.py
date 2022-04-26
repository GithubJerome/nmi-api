# pylint: disable=too-many-function-args
"""Question"""
import json
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class Question(Common):
    """Class for Question"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Question class"""
        self.postgresql_query = PostgreSQL()
        super(Question, self).__init__()

    def question(self):
        """
        This API is for Getting All Questions
        ---
        tags:
          - Question
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
          - name: search
            in: query
            description: Search
            required: false
            type: string
        responses:
          500:
            description: Error
          200:
            description: Question
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
                filter_val.append(self.swap_decimal_symbol(userid, val))

            filter_value = tuple(filter_val)

        else:

            filter_list = filter_column

        # if search:
        #     search = self.swap_decimal_symbol(userid, search)

        datas = self.get_all_questions(page, limit, sort_type, sort_column,
                                       filter_list, filter_value, search)
        keys = ['question_type', 'tags', 'question_id']

        for key in keys:

            key_data = self.get_key_data(key)
            format_data = self.data_filter(key_data, key)

            if key == "question_type":
                question_types = format_data

            # if key == "question_id":
            #     question_ids = format_data

            if key == "tags":
                tags = format_data

        datas['question_type'] = question_types
        # datas['question_id'] = question_ids
        datas['tags'] = tags
        datas['status'] = 'ok'

        return self.return_data(datas, userid)

    def get_all_questions(self, page, limit, sort_type, sort_column,
                          filter_list, filter_value, search):
        """Return All Questions"""

        offset = int((page - 1) * limit)

        search_sql = ""

        # SEARCH
        if search:

            search_ = []
            search_column = ['question_id', 'question_type', 'correct_answer',
                             'correct', 'incorrect', 'feedback', 'description',
                             'question', 'correct_answer', 'tags', 'choices']

            search_json = ['question', 'correct_answer', 'tags', 'choices']

            for col in search_column:

                if col in search_json:

                    cast = '"{0}"'.format(col)

                    new_search = search
                    
                    search_val = [val.lstrip() for val in search.split(",")]

                    search_st = "CAST({0} AS text) ILIKE '%{1}%'".format(cast, str(new_search))
                    if len(search_val) > 1:
                        # new_search = json.dumps(search_val)
                        new_search = ', '.join('"{0}"'.format(val) for val in search_val)
                    # search_st = "CAST({0} AS text) ILIKE '%{1}%'".format(cast, str(new_search))
                        search_st = "CAST({0} AS text) ILIKE '%[{1}]%'".format(cast, str(new_search))
                    

                else:
                     search_st = "{0} ILIKE '%{1}%'".format(col, str(search))

                search_.append(search_st)

            search_sql = " OR ".join(search_)


    	# WHERE STATEMENT
        where_sql = ""

        # FILTER
        if filter_list and filter_value:

            where = []

            if filter_list[0].upper() in ['TAGS', 'QUESTION', 'CHOICES']:

                if len(filter_value) > 1:
                    filter_val = [val.lstrip() for val in filter_value]
                    filter_value = []
                    filter_value.append(filter_val)

            i = 0
            for val in filter_value:

                key = filter_list[i]

                if key in ['shuffle_options', 'shuffle_answers', 'num_eval', 'status']:
                    where_st = "{0} is {1}".format(key, val)

                elif key in ['question', 'correct_answer']:
                    key = '"{0}"'.format(key)
                   
                    where_st = "CAST({0} AS text) ILIKE '%{1}%'".format(key, str(val))
                    if type(val) == list:
                        val = ', '.join('"{0}"'.format(sval) for sval in val)
                        where_st = "CAST({0} AS text) ILIKE '%[{1}]%'".format(key, str(val))

                elif key in ['tags', 'choices']:
                    key = '"{0}"'.format(key)
                    tag = ', '.join('"{0}"'.format(tag) for tag in val)
                    where_st = "CAST({0} AS text) ILIKE '%[{1}]%'".format(key, tag)

                else:

                    where_st = "{0} ILIKE '{1}'".format(key, val)

                i += 1

                where.append(where_st)

            where_sql = " AND ".join(where)

        condition = ""
        if where_sql or search_sql:

            if where_sql != '' and search_sql != '':
                search_sql = "AND {0}".format(search_sql)

            condition = " WHERE {0} {1}".format(where_sql, search_sql)

        # COUNT
        sql_str = "SELECT COUNT(*) FROM questions"
        sql_str += "{0}".format(condition)
        count = self.postgres.query_fetch_one(sql_str)

        # DATA
        sql_str = "SELECT question_id as key, * FROM questions {0}".format(condition)

        #SORT
        if sort_column and sort_type:

            if sort_column in ['question_id', 'question_type', 'tags', 'status']:
                table = "{0}".format(sort_column)
                sql_str += " ORDER BY  {0} {1}".format(table, sort_type.lower())

        else:
            sql_str += " ORDER BY created_on desc"

        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)

        result = self.postgres.query_fetch_all(sql_str)

        for res in result or []:
            res['question'] = res['question']['question']
            res['correct_answer'] = res['correct_answer']['answer']

        rows = []
        total_rows = 0
        if result:
            total_rows = count['count']
            rows = result

        total_page = int((total_rows + limit - 1) / limit)

        data = {}
        data['rows'] = rows
        data['total_rows'] = total_rows
        data['total_page'] = total_page
        data['limit'] = limit
        data['page'] = page

        return data

    def get_key_data(self, key):
        """Return Account Data"""

        if key:

            # DATA
            sql_str = "SELECT DISTINCT {0} FROM questions".format(key)

            datas = self.postgres.query_fetch_all(sql_str)

            data = {}

            k = "{0}s".format(key)

            temp_data = [temp_data[key] for temp_data in datas]

            data[k] = temp_data

        return data
