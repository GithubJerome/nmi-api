# pylint: disable=too-many-function-args
"""Create Course"""
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from socketIO_client import SocketIO, LoggingNamespace

class CreateCourse(Common):
    """Class for CreateCourse"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CreateCourse class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(CreateCourse, self).__init__()

    def create_course(self):
        """
        This API is for Creating Course
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
            description: Create Course
            required: true
            schema:
              id: Create Course
              properties:
                course_name:
                    type: string
                course_title:
                    type: string
                description:
                    type: string
                requirements:
                    type: string
                exercise_name:
                    type: string
                student_ids:
                    types: array
                    example: []
                user_group_ids:
                    types: array
                    example: []
                status:
                    type: boolean
        responses:
          500:
            description: Error
          200:
            description: Create Course
        """
        data = {}

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

        # GET HEADER
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        if not self.insert_course(token, userid, query_json):

            data["alert"] = "Please check your query!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        data['message'] = "Course successfully created!"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def insert_course(self, token, userid, query_json):
        """Insert Course"""
        course_id = self.sha_security.generate_token(False)

        student_ids = query_json['student_ids']
        query_json = self.remove_key(query_json, "student_ids")

        user_group_ids = query_json['user_group_ids']
        query_json = self.remove_key(query_json, "user_group_ids")

        # COURSE
        query_json['course_id'] = course_id
        query_json['created_on'] = time.time()

        if self.postgres.insert('course', query_json, 'course_id'):

            #  STUDENTS
            for student_id in student_ids:

                # VALIDATE
                sql_str = "SELECT * FROM student_course WHERE"
                sql_str += " account_id='{0}'".format(student_id)
                sql_str += " AND course_id='{0}'".format(course_id)
                res = self.postgres.query_fetch_one(sql_str)

                if res:

                    continue

                # ADD STUDENT TO A COURSE
                temp = {}
                temp['account_id'] = student_id
                temp['course_id'] = course_id
                temp['progress'] = 0
                temp['expiry_date'] = int(time.time()) + (86400 * 90)
                temp['status'] = True
                temp['created_on'] = time.time()

                self.postgres.insert('student_course', temp)

                # NOTIFICATION
                notification_id = self.sha_security.generate_token(False)
                notification_type = "New Task"
                notif = {}
                notif['notification_id'] = notification_id
                notif['account_id'] = student_id
                notif['notification_name'] = "New Task"
                notif['notification_type'] = notification_type
                notif['description'] = "You have new course: {0}".format(query_json['course_name'])
                notif['seen_by_user'] = False
                notif['created_on'] = time.time()
                self.postgres.insert('notifications', notif)

                # TRIGGER SOCKETIO NOTIFICATION
                message = {}
                message['token'] = token
                message['userid'] = userid
                message['type'] = 'notification'
                message['data'] = notif
                message['notification_id'] = notification_id
                message['notification_type'] = notification_type

                socketio = SocketIO('0.0.0.0', 5000, LoggingNamespace)
                socketio.emit('notification', message)
                socketio.disconnect()

            # USER GROUP
            if "user_group_ids" in query_json['user_group_ids']:
                for user_group_id in user_group_ids:
                    # VALIDATE
                    sql_str = "SELECT * FROM user_group_courses WHERE"
                    sql_str += " course_id='{0}'".format(course_id)
                    sql_str += " AND user_group_id='{0}'".format(user_group_id)
                    res = self.postgres.query_fetch_one(sql_str)

                    if res:

                        continue

                    # ADD COURSE TO USER GROUP
                    temp = {}
                    temp['user_group_courses_id'] = self.sha_security.generate_token(False)
                    temp['course_id'] = course_id
                    temp['user_group_id'] = user_group_id
                    temp['created_on'] = time.time()

                    self.postgres.insert('user_group_courses', temp)

            return 1

        return 0
