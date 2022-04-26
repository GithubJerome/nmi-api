"""Tutor Group Course progress"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class TutorGroupCourse(Common):
    """Class for TutorGroupCourse"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for TutorGroupCourse class"""
        self.postgresql_query = PostgreSQL()
        super(TutorGroupCourse, self).__init__()

    def tutor_group_course(self):
        """
        This API is for Getting Courses by Course
        ---
        tags:
          - Tutor
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
          - name: group_id
            in: query
            description: Group ID
            required: true
            type: string

        responses:
          500:
            description: Error
          200:
            description: Group Course(s)
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        group_id = request.args.get('group_id')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        datas = self.get_group_course(group_id, userid)
        if not datas:
            data["alert"] = "No Data Found"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        datas['status'] = 'ok'

        return self.return_data(datas, userid)


    def get_group_course(self, group_id, userid):
        """ RETURN GROUP COURSE PROGRESS """

        sql_str = "SELECT * FROM user_group_master"
        sql_str += " WHERE user_group_id IN"
        sql_str += " (SELECT user_group_id FROM"
        sql_str += " user_group_tutors WHERE"
        sql_str += " tutor_id='{0}') AND user_group_id = '{1}'".format(userid, group_id)
        results = self.postgres.query_fetch_one(sql_str)

        courses = []
        if results:

            courses = results['courses']

        data = {}
        data['data'] = courses

        return data
