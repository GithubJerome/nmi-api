# pylint: disable=too-many-function-args
"""Delete User Group"""
from flask import  request
from library.common import Common

class DeleteUserGroup(Common):
    """Class for DeleteUserGroup"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for DeleteUserGroup class"""
        super(DeleteUserGroup, self).__init__()

    def delete_user_group(self):
        """
        This API is for Deleting User Group
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
          - name: query
            in: body
            description: User IDs
            required: true
            schema:
              id: Delete User Group
              properties:
                user_group_ids:
                    types: array
                    example: []
        responses:
          500:
            description: Error
          200:
            description: Delete User Group
        """
        data = {}

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

        # GET HEADER
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # GET QUERY
        user_group_ids = query_json["user_group_ids"]

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        if self.check_use_group(user_group_ids):
            data["alert"] = "Group is in use!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        if not self.delete_user_groups(user_group_ids):

            data["alert"] = "Please check your query!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        data['message'] = "User group(s) successfully deleted!"
        data['status'] = "ok"
        return self.return_data(data, userid)

    def delete_user_groups(self, user_group_ids):
        """Delete Users"""

        for user_group_id in user_group_ids:

            conditions = []

            conditions.append({
                "col": "user_group_id",
                "con": "=",
                "val": user_group_id
                })

            # USER GROUP COURSES
            if not self.postgres.delete('user_group_courses', conditions):

                return 0

            # USER GROUP STUDENTS
            if not self.postgres.delete('user_group_students', conditions):

                return 0

            # USER GROUP TUTORS
            if not self.postgres.delete('user_group_tutors', conditions):

                return 0

            # USER GROUP
            if not self.postgres.delete('group_course_requirements', conditions):

                return 0

            # USER GROUP
            if not self.postgres.delete('group_section_requirements', conditions):

                return 0

            # USER GROUP
            if not self.postgres.delete('group_subsection_requirements', conditions):

                return 0

            # USER GROUP
            if not self.postgres.delete('group_exercise_requirements', conditions):

                return 0

            # USER GROUP
            if not self.postgres.delete('user_group', conditions):

                return 0

        return 1

    def check_use_group(self, user_group_ids):
        """ CHECK USE GROUP """

        ids = ','.join("'{0}'".format(ugid) for ugid in user_group_ids)
        sql_str = "SELECT student_id FROM user_group_students WHERE"
        sql_str += " user_group_id IN ({0})".format(ids)
        user_group_students = self.postgres.query_fetch_one(sql_str)

        if not user_group_students:
            return 0

        return 1
