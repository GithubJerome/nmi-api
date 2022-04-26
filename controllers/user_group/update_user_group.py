"""Update User Group"""
import string
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.emailer import Email
from library.progress import Progress

class UpdateUserGroup(Common, ShaSecurity):
    """Class for UpdateUserGroup"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateUserGroup class"""

        # self.postgres = PostgreSQL()
        self.progress = Progress()
        self.sha_security = ShaSecurity()
        super(UpdateUserGroup, self).__init__()

    def update_user_group(self):
        """
        This API is for Updating User Group
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
            description: User Group
            required: true
            schema:
              id: Update User Group
              properties:
                user_group_id:
                    type: string
                user_group_name:
                    type: string
                course_ids:
                    types: array
                    example: []
                student_ids:
                    types: array
                    example: []
                tutor_ids:
                    types: array
                    example: []
                notify_members:
                    type: boolean
                notify_managers:
                    type: boolean
        responses:
          500:
            description: Error
          200:
            description: Update User
        """

        # INIT DATA
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

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

        # VALIDATE USER GROUP NAME
        if not self.validate_group_name(query_json['user_group_id'], query_json['user_group_name']):
            data["alert"] = "Group name already exist"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # CREATE USER GROUP
        self.update_run(token, userid, query_json)

        data = {}
        data['message'] = "User Group successfully updated"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def update_run(self, token, userid, query_json):
        """ UPDATE USER GROUP """

        user_group_id = query_json['user_group_id']

        user_group = {}
        user_group['user_group_name'] = query_json['user_group_name']
        user_group['notify_members'] = query_json['notify_members']
        user_group['notify_managers'] = query_json['notify_managers']
        user_group['update_on'] = time.time()

        # UPDATE
        # INIT CONDITION
        conditions = []

        # CONDITION FOR QUERY
        conditions.append({
            "col": "user_group_id",
            "con": "=",
            "val": user_group_id
            })

        # UPDATE GROUP
        self.postgres.update('user_group', user_group, conditions)

        # STUDENT IDS OF THIS GROUP
        sql_str = "SELECT student_id  FROM user_group_students WHERE"
        sql_str += " user_group_id='{0}'".format(user_group_id)

        old_student_ids = self.postgres.query_fetch_all(sql_str)

        # COURSE IDS OF THIS GROUP
        sql_str = "SELECT course_id  FROM user_group_courses WHERE"
        sql_str += " user_group_id='{0}'".format(user_group_id)

        old_course_ids = self.postgres.query_fetch_all(sql_str)

        old_student_ids = [res['student_id'] for res in old_student_ids]
        old_course_ids = [res['course_id'] for res in old_course_ids]
        new_student_ids = []
        new_course_ids = []

        if 'student_ids' in query_json.keys():
            new_student_ids = query_json['student_ids']

        if 'course_ids' in query_json.keys():
            new_course_ids = query_json['course_ids']

        # GET ALL COURSES THAT IS NOT EXIST IN NEW LIST
        to_remove_courses = []

        for old_course_id in old_course_ids:

            if not old_course_id in new_course_ids:

                to_remove_courses.append(old_course_id)

        # REMOVE ALL STUDENTS IN A COURSE THAT IS NOT EXIST IN NEW LIST
        if to_remove_courses:

            for old_student_id in old_student_ids:

                for to_remove_course in to_remove_courses:

                    # CHECK IF STUDENT IS NOT BOND TO OTHER GROUP WITH THIS COURSE
                    sql_str = " SELECT course_id FROM user_group_courses WHERE"
                    sql_str += " user_group_id IN (SELECT user_group_id"
                    sql_str += "  FROM user_group_students WHERE"
                    sql_str += " student_id='{0}'".format(old_student_id)
                    sql_str += " AND NOT user_group_id='{0}')".format(user_group_id)
                    usergc = self.postgres.query_fetch_all(sql_str)

                    if not usergc:

                        # INIT CONDITION
                        conditions2 = []

                        # CONDITION FOR QUERY
                        conditions2.append({
                            "col": "account_id",
                            "con": "=",
                            "val": old_student_id
                            })

                        conditions2.append({
                            "col": "course_id",
                            "con": "=",
                            "val": to_remove_course
                            })

                        self.postgres.delete('student_course', conditions2)

                        self.regenerate_student_exercise(old_student_id, to_remove_course)

        # GET ALL STUDENTS THAT IS NOT EXIST IN NEW LIST
        to_remove_students = []

        for old_student_id in old_student_ids:

            if not old_student_id in new_student_ids:

                to_remove_students.append(old_student_id)

        # REMOVE ALL STUDENTS THAT IS NOT EXIST IN NEW LIST
        for to_remove_student in to_remove_students:

            for old_course_id in old_course_ids:

                # CHECK IF STUDENT IS NOT BOND TO OTHER GROUP WITH THIS COURSE
                sql_str = " SELECT course_id FROM user_group_courses WHERE"
                sql_str += " user_group_id IN (SELECT user_group_id"
                sql_str += "  FROM user_group_students WHERE"
                sql_str += " student_id='{0}'".format(to_remove_student)
                sql_str += " AND NOT user_group_id='{0}')".format(user_group_id)
                usergc = self.postgres.query_fetch_all(sql_str)

                if not usergc:

                    # INIT CONDITION
                    conditions2 = []

                    # CONDITION FOR QUERY
                    conditions2.append({
                        "col": "account_id",
                        "con": "=",
                        "val": to_remove_student
                        })

                    conditions2.append({
                        "col": "course_id",
                        "con": "=",
                        "val": old_course_id
                        })

                    self.postgres.delete('student_course', conditions2)

                    self.disable_student_section(to_remove_student, old_course_id)
                    self.disable_student_subsection(to_remove_student, old_course_id)
                    self.regenerate_student_exercise(to_remove_student, old_course_id)

        self.postgres.delete('user_group_courses', conditions)
        self.postgres.delete('user_group_students', conditions)
        self.postgres.delete('user_group_tutors', conditions)

        # CREATE USER GROUP COURSES
        for course_id in new_course_ids:
            user_group_courses = {}
            user_group_courses['user_group_courses_id'] = self.generate_token(False)
            user_group_courses['course_id'] = course_id
            user_group_courses['user_group_id'] = user_group_id
            user_group_courses['created_on'] = time.time()

            self.postgres.insert('user_group_courses', user_group_courses)

        # CREATE USER GROUP STUDENTS
        for student_id in new_student_ids:

            user_group_students = {}
            user_group_students['user_group_students_id'] = self.generate_token(False)
            user_group_students['student_id'] = student_id
            user_group_students['user_group_id'] = user_group_id
            user_group_students['created_on'] = time.time()

            self.postgres.insert('user_group_students', user_group_students)

            notif_type = "New Group"
            notif_name = "New Group"
            description = "You have new Group: {0}".format(query_json['user_group_name'])
            self.send_notif(userid, token, student_id, description, notif_type, notif_name)

        # CREATE USER GROUP TUTORS
        if 'tutor_ids' in query_json.keys():

            for tutor_id in query_json['tutor_ids']:

                user_group_tutors = {}
                user_group_tutors['user_group_tutors_id'] = self.generate_token(False)
                user_group_tutors['tutor_id'] = tutor_id
                user_group_tutors['user_group_id'] = user_group_id
                user_group_tutors['created_on'] = time.time()

                self.postgres.insert('user_group_tutors', user_group_tutors)
                notif_type = "New Group"
                notif_name = "New Group"
                description = "You have new Group: {0}".format(query_json['user_group_name'])
                self.send_notif(userid, token, tutor_id, description, notif_type, notif_name)

        # CREATE COURSE STUDENT
        if 'student_ids' in query_json.keys() and 'course_ids' in query_json.keys():

            for student_id in query_json['student_ids']:

                for course_id in query_json['course_ids']:

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
                    description = "You have new Course: {0}".format(course['course_name'])
                    self.send_notif(userid, token, student_id, description, notif_type, notif_name)


        # CREATE COURSE TUTOR
        if 'tutor_ids' in query_json.keys() and 'course_ids' in query_json.keys():

            for tutor_id in query_json['tutor_ids']:

                for course_id in query_json['course_ids']:

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
                    description = "You have new Course: {0}".format(course['course_name'])
                    self.send_notif(userid, token, tutor_id, description, notif_type, notif_name)

        # GET ALL USER PROGRESS IN A GROUP
        sql_str = "SELECT progress FROM account WHERE id IN ("
        sql_str += "SELECT student_id FROM user_group_students WHERE"
        sql_str += " user_group_id='{0}')".format(user_group_id)
        progress = self.postgres.query_fetch_all(sql_str)

        if progress:

            total_prog = 0
            total_student = len(progress) * 100

            for pgrss in progress:

                total_prog = total_prog + float(pgrss['progress'])

            # GET AVERAGE PROGRESS
            average = self.format_progress((total_prog/total_student) * 100)

            # UPDATE PROGRESS
            conditions = []

            conditions.append({
                "col": "user_group_id",
                "con": "=",
                "val": user_group_id
            })

            # GET LEAST PERFORMER
            sql_str = "SELECT id, ROUND(cast(progress as numeric),2) AS progress"
            sql_str += " FROM account WHERE id IN (SELECT student_id FROM"
            sql_str += " user_group_students WHERE"
            sql_str += " user_group_id='{0}')".format(user_group_id)
            sql_str += " ORDER BY progress ASC"
            student = self.postgres.query_fetch_one(sql_str)

            # UPDATE GROUP PROGRESS
            data = {}
            data['least_performer'] = ""

            if student:

                data['least_performer'] = student['id']

            data['progress'] = average
            data['update_on'] = time.time()

            self.postgres.update('user_group', data, conditions)

        if 'tutor_ids' in query_json.keys() or 'student_ids' in query_json.keys():

            if 'course_ids' in query_json.keys():

                for course_id in query_json['course_ids']:

                    self.validate_course_requirements(course_id)

        return 1

    def validate_group_name(self, group_id, group_name):
        """ VALIDATE GROUP NAME """

        sql_str = "SELECT user_group_name FROM user_group WHERE"
        sql_str += " user_group_name='{0}'".format(group_name)
        sql_str += " AND user_group_id !='{0}'".format(group_id)

        user_group_name = self.postgres.query_fetch_one(sql_str)

        if user_group_name:

            return 0

        return 1

    def regenerate_student_exercise(self, user_id, course_id):
        """ Generate New set of exercise for Student """

        sql_str = "SELECT * FROM exercise"
        sql_str += " WHERE course_id = '{0}'".format(course_id)
        results = self.postgres.query_fetch_all(sql_str)

        for result in results:

            course_id = result['course_id']
            exercise_id = result['exercise_id']

            sql_str = "SELECT * FROM student_exercise"
            sql_str += " WHERE exercise_id = '{0}'".format(exercise_id)
            sql_str += " AND account_id = '{0}'".format(user_id)
            sql_str += " AND status is True AND course_id = '{0}'".format(course_id)
            student_exercise = self.postgres.query_fetch_one(sql_str)

            if student_exercise:

                student_exercise_id = student_exercise['student_exercise_id']

                # UPDATE STATUS OF OLD EXERCISE
                tmp = {}
                tmp['status'] = False
                tmp['update_on'] = time.time()

                conditions = []

                conditions.append({
                    "col": "exercise_id",
                    "con": "=",
                    "val": exercise_id
                })

                conditions.append({
                    "col": "student_exercise_id",
                    "con": "=",
                    "val": student_exercise_id
                })

                conditions.append({
                    "col": "account_id",
                    "con": "=",
                    "val": user_id
                })

                self.postgres.update('student_exercise', tmp, conditions)

                # # UPDATE PROGRESS FROM COURSE TO SUBSECTION
                # self.progress.update_course_progress(user_id, exercise_id, "student")
                # self.progress.update_section_progress(user_id, exercise_id, "student")
                # self.progress.update_subsection_progress(user_id, exercise_id, "student")

        return 1

    def disable_student_section(self, user_id, course_id):
        """ Disable Student Section """

        sql_str = "SELECT * FROM section"
        sql_str += " WHERE course_id = '{0}'".format(course_id)
        results = self.postgres.query_fetch_all(sql_str)

        for result in results:

            section_id = result['section_id']

            sql_str = "SELECT * FROM student_section"
            sql_str += " WHERE section_id = '{0}'".format(section_id)
            sql_str += " AND account_id = '{0}'".format(user_id)
            sql_str += " AND status is True AND course_id = '{0}'".format(course_id)
            student_section = self.postgres.query_fetch_one(sql_str)

            if student_section:

                student_section_id = student_section['student_section_id']

                # UPDATE STATUS OF OLD SECTION
                tmp = {}
                tmp['status'] = False
                tmp['update_on'] = time.time()

                conditions = []

                conditions.append({
                    "col": "section_id",
                    "con": "=",
                    "val": section_id
                })

                conditions.append({
                    "col": "student_section_id",
                    "con": "=",
                    "val": student_section_id
                })

                conditions.append({
                    "col": "account_id",
                    "con": "=",
                    "val": user_id
                })

                self.postgres.update('student_section', tmp, conditions)

        return 1

    def disable_student_subsection(self, user_id, course_id):
        """ Dsiable Student Subsection """

        sql_str = "SELECT * FROM subsection"
        sql_str += " WHERE course_id = '{0}'".format(course_id)
        results = self.postgres.query_fetch_all(sql_str)

        for result in results:

            subsection_id = result['subsection_id']

            sql_str = "SELECT * FROM student_subsection"
            sql_str += " WHERE subsection_id = '{0}'".format(subsection_id)
            sql_str += " AND account_id = '{0}'".format(user_id)
            sql_str += " AND status is True AND course_id = '{0}'".format(course_id)
            student_subsection = self.postgres.query_fetch_one(sql_str)

            if student_subsection:

                student_subsection_id = student_subsection['student_subsection_id']

                # UPDATE STATUS OF OLD SUBSECTION
                tmp = {}
                tmp['status'] = False
                tmp['update_on'] = time.time()

                conditions = []

                conditions.append({
                    "col": "subsection_id",
                    "con": "=",
                    "val": subsection_id
                })

                conditions.append({
                    "col": "student_subsection_id",
                    "con": "=",
                    "val": student_subsection_id
                })

                conditions.append({
                    "col": "account_id",
                    "con": "=",
                    "val": user_id
                })

                self.postgres.update('student_subsection', tmp, conditions)

        return 1
