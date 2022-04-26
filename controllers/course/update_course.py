# pylint: disable=too-many-function-args
"""Update Course"""
import time
import copy
from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from socketIO_client import SocketIO, LoggingNamespace

class UpdateCourse(Common):
    """Class for UpdateCourse"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateCourse class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(UpdateCourse, self).__init__()

    def update_course(self):
        """
        This API is for Updating Course
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
            description: Update Course
            required: true
            schema:
              id: Update Course
              properties:
                course_id:
                    type: string
                course_name:
                    type: string
                course_title:
                    type: string
                description:
                    type: string
                difficulty_level:
                    type: integer
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
            description: Update Course
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

        course_id = query_json['course_id']

        if not self.edit_course(token, userid, query_json):

            data["alert"] = "Please check your query!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        self.validate_course_requirements(course_id)

        data['message'] = "Course successfully updated!"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def edit_course(self, token, userid, query_json):
        """Update Course"""

        course_id = query_json['course_id']

        # CHECK EXISTING STUDENT
        # sql_str = "SELECT * FROM student_course WHERE course_id='{0}' AND status is True".format(course_id)
        # results = self.postgres.query_fetch_all(sql_str)

        # course_students = [res['account_id'] for res in results]
        # new_students = set(query_json['student_ids'])
        # db_students = set(course_students)

        # db_students.difference_update(new_students)
        # trim_students = list(db_students)

        # conditions = []
        # conditions.append({
        #     "col": "course_id",
        #     "con": "=",
        #     "val": course_id
        #     })

        # conditions.append({
        #     "col": "account_id",
        #     "con": "IN",
        #     "val": trim_students
        #     })

        # conditions2 = copy.deepcopy(conditions)
        # conditions3 = copy.deepcopy(conditions)
        # conditions4 = copy.deepcopy(conditions)

        # if trim_students:

        #     self.postgres.delete('student_course', conditions)
        #     self.postgres.delete('student_section', conditions2)
        #     self.postgres.delete('student_subsection', conditions3)
        #     self.postgres.delete('student_exercise', conditions4)

        #  STUDENTS
        for student_id in query_json['student_ids']:

            # VALIDATE
            sql_str = "SELECT * FROM student_course WHERE"
            sql_str += " account_id='{0}'".format(student_id)
            sql_str += " AND course_id='{0}' AND status is True".format(course_id)
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
        if "user_group_ids" in query_json:

            # CHECK EXISTING
            sql_str = "SELECT * FROM user_group_courses WHERE course_id='{0}'".format(course_id)
            results = self.postgres.query_fetch_all(sql_str)

            user_groups = [res['user_group_id'] for res in results]
            new_user_groups = set(query_json['user_group_ids'])
            db_user_groups = set(user_groups)

            db_user_groups.difference_update(new_user_groups)
            trim_user_groups = list(db_user_groups)

            conditions = []
            conditions.append({
                "col": "course_id",
                "con": "=",
                "val": course_id
                })

            conditions.append({
                "col": "user_group_id",
                "con": "IN",
                "val": trim_user_groups
                })


            if trim_user_groups:

                trim_user_groups2 = copy.deepcopy(trim_user_groups)

                # GET OLD STUDENTS
                usergid = ','.join("'{0}'".format(userg) for userg in trim_user_groups2)
                sql_str = "SELECT student_id FROM user_group_students WHERE"
                sql_str += " user_group_id IN ({0})".format(usergid)
                usergstudents = self.postgres.query_fetch_all(sql_str)

                student_ids = [usergs['student_id'] for usergs in usergstudents or []]

                for student_id in student_ids:

                    # GET STUDENT GROUPS
                    sql_str = "SELECT user_group_id FROM user_group_students WHERE"
                    sql_str += " student_id='{0}'".format(student_id)
                    sgroups = self.postgres.query_fetch_all(sql_str)
                    student_groups = {sg['user_group_id'] for sg in sgroups or []}

                    set_userg_ids = set(query_json['user_group_ids'])
                    # IF STUDENT NOT IN THE NEW GROUPS REMOVE THE COURSE TO STUDENT
                    if not student_groups.intersection(query_json['user_group_ids']):

                        # REMOVE STUDENT TO THIS COURSE
                        conditions = []
                        conditions.append({
                            "col": "course_id",
                            "con": "=",
                            "val": course_id
                            })

                        conditions.append({
                            "col": "account_id",
                            "con": "=",
                            "val": student_id
                            })

                        conditions2 = copy.deepcopy(conditions)
                        conditions3 = copy.deepcopy(conditions)
                        conditions4 = copy.deepcopy(conditions)

                        self.postgres.delete('student_course', conditions)
                        self.postgres.delete('student_section', conditions2)
                        self.postgres.delete('student_subsection', conditions3)
                        self.postgres.delete('student_exercise', conditions4)

                conditions = []
                conditions.append({
                    "col": "course_id",
                    "con": "=",
                    "val": course_id
                    })

                conditions.append({
                    "col": "user_group_id",
                    "con": "IN",
                    "val": trim_user_groups
                    })

                self.postgres.delete('user_group_courses', conditions)

            for user_group_id in query_json['user_group_ids']:
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

                if self.postgres.insert('user_group_courses', temp, 'user_group_id'):
                    self.bind_course_group(user_group_id, course_id, userid, token)

        # COURSE
        query_json['update_on'] = time.time()

        conditions = []

        conditions.append({
            "col": "course_id",
            "con": "=",
            "val": course_id
            })

        data = self.remove_key(query_json, "user_group_ids")
        data = self.remove_key(query_json, "student_ids")
        data = self.remove_key(query_json, "course_id")

        if self.postgres.update('course', data, conditions):
            return 1

        return 0

    def bind_course_group(self, user_group_id, course_id, userid, token):
        """ CREATE STUDENT COURSE """

        sql_str = "SELECT * FROM user_group_master WHERE user_group_id='{0}'".format(user_group_id)
        result = self.postgres.query_fetch_one(sql_str)

        if not result:
            return 0

        student_ids = []
        tutor_ids = []

        if result['students']:
            student_ids = [res['student_id'] for res in result['students']]
        
        if result['tutors']:
            tutor_ids = [res['tutor_id'] for res in result['tutors']]

        # CREATE COURSE STUDENT
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

            # GET COURSE NAME
            sql_str = "SELECT course_name FROM course WHERE"
            sql_str += " course_id='{0}'".format(course_id)
            course = self.postgres.query_fetch_one(sql_str)

            notif_type = "New Course"
            notif_name = "New Course"
            description = "You have new course: {0}".format(course['course_name'])
            self.send_notif(userid, token, student_id, description, notif_type, notif_name)


        # CREATE COURSE TUTOR
        for tutor_id in tutor_ids:

            # VALIDATE
            sql_str = "SELECT * FROM tutor_courses WHERE"
            sql_str += " account_id='{0}'".format(tutor_id)
            sql_str += " AND course_id='{0}'".format(course_id)
            res = self.postgres.query_fetch_one(sql_str)

            if res:
                continue

            data = {}
            data['account_id'] = tutor_id
            data['course_id'] = course_id
            data['status'] = True
            data['created_on'] = time.time()

            self.postgres.insert('tutor_courses', data)

            # GET COURSE NAME
            sql_str = "SELECT course_name FROM course WHERE"
            sql_str += " course_id='{0}'".format(course_id)
            course = self.postgres.query_fetch_one(sql_str)

            notif_type = "New Course"
            notif_name = "New Course"
            description = "You have new course: {0}".format(course['course_name'])
            self.send_notif(userid, token, tutor_id, description, notif_type, notif_name)

        return 1
