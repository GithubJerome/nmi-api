# pylint: disable=too-many-function-args
"""Delete Course"""
from flask import  request
from library.common import Common
from library.sha_security import ShaSecurity

class DeleteCourse(Common, ShaSecurity):
    """Class for DeleteCourse"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for DeleteCourse class"""
        self.sha_security = ShaSecurity()
        super(DeleteCourse, self).__init__()

    def delete_course(self):
        """
        This API is for Deleting Course
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
          - name: query
            in: body
            description: Course IDs
            required: true
            schema:
              id: Delete Courses
              properties:
                course_ids:
                    types: array
                    example: []
                delete_questions:
                    type: boolean
        responses:
          500:
            description: Error
          200:
            description: Delete Course
        """
        data = {}

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

        # GET HEADER
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # GET QUERY
        course_ids = query_json["course_ids"]

        delete_questions = False

        if "delete_questions" in query_json.keys():

            delete_questions = query_json['delete_questions']

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # CHECK IF COURSE IS ALREADY IN USE
        if not self.use_course(course_ids, token=token, userid=userid):

            data["alert"] = "Course is in use!"
            data['status'] = 'Failed'

            return self.return_data(data, userid)

        if not self.delete_courses(course_ids, delete_questions):

            data["alert"] = "Please check your query!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        data['message'] = "Course successfully deleted!"
        data['status'] = "ok"
        return self.return_data(data, userid)
