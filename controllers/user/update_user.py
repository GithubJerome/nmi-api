"""Update User"""
import time
import copy
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.emailer import Email
from library.sha_security import ShaSecurity
from templates.email_update import EmailUpdate

class UpdateUser(Common, ShaSecurity):
    """Class for UpdateUser"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateUser class"""

        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(UpdateUser, self).__init__()

    def update_user(self):
        """
        This API is for Updating User
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
          - name: query
            in: body
            description: Updating User
            required: true
            schema:
              id: Updating User
              properties:
                account_id:
                    type: string
                first_name:
                    type: string
                last_name:
                    type: string
                middle_name:
                    type: string
                username:
                    type: string
                url:
                    type: string
                email:
                    type: string
                address:
                    type: string
                zip_code:
                    type: integer
                city:
                    type: string
                country:
                    type: string
                language:
                    type: string
                timezone:
                    type: string
                is_send_email:
                    type: boolean
                is_license_renewable:
                    type: boolean
                force_change_password:
                    type: boolean
                roles:
                    types: array
                    example: []
                receive_messages:
                    type: boolean
                receive_assignments:
                    type: boolean
                receive_progress:
                    type: boolean
                receive_updates:
                    type: boolean
                receive_reminders:
                    type: boolean
                receive_events:
                    type: boolean
                receive_discussions:
                    type: boolean
                receive_newly_available:
                    type: boolean
                receive_certificate_notifications:
                    type: boolean
                receive_memo_training:
                    type: boolean
                receive_other:
                    type: boolean
                email_frequency:
                    type: string
                biography:
                    type: string
                faceboot_url:
                    type: string
                linkedin_url:
                    type: string
                twitter_url:
                    type: string
                skype_username:
                    type: string
                student_group_ids:
                    types: array
                    example: []
                tutor_group_ids:
                    types: array
                    example: []
        responses:
          500:
            description: Error
          200:
            description: Updating User
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

        # CHECK USERNAME
        if self.recheck_username(query_json['account_id'], query_json['username']):
            data['alert'] = "Username is already taken!"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        if not self.update_users(query_json, token):

            data["alert"] = "Please check your query!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        data['message'] = "User successfully updated!"
        data['status'] = "ok"
        return self.return_data(data, userid)

    def update_users(self, query_json, token):
        """Update Users"""

        # GET CURRENT TIME
        query_json['update_on'] = time.time()

        account_id = query_json['account_id']

        if "student_group_ids" in query_json.keys():
            self.assign_student_group(account_id, query_json['student_group_ids'], token)

        if "tutor_group_ids" in query_json.keys():
            self.assign_tutor_group(account_id, query_json['tutor_group_ids'], token)

        roles = []

        if 'roles' in query_json.keys():
            roles = query_json['roles']

        # UPDATE
        # INIT CONDITION
        conditions = []

        # CONDITION FOR QUERY
        conditions.append({
            "col": "id",
            "con": "=",
            "val": account_id
            })

        # REMOVE KEYS
        query_json = self.remove_key(query_json, "account_id")
        query_json = self.remove_key(query_json, "roles")
        query_json = self.remove_key(query_json, "student_group_ids")
        query_json = self.remove_key(query_json, "tutor_group_ids")

        # CHECK EMAIL
        sql_str = "SELECT * FROM account WHERE id='{0}'".format(account_id)
        result = self.postgres.query_fetch_one(sql_str)
        current_email = result['email']
        current_username = result['username']

        # UPDATE ROLE
        if self.postgres.update('account', query_json, conditions):

            # ADD TO ACCOUNT OLD EMAIL TABLE
            if current_email != query_json['email']:
                tmp = {}
                tmp['account_id'] = account_id
                tmp['email'] = current_email
                tmp['created_on'] = time.time()

                self.postgres.insert('account_old_email', tmp)

                # SEND EMAIL
                # self.send_email_update(query_json['email'], current_email, query_json['email'])

            if current_username != query_json['username']:
                # SEND EMAIL
                self.send_email_update(query_json['username'], current_username, query_json['username'])

            # INIT CONDITION
            conditions = []

            # CONDITION FOR QUERY
            conditions.append({
                "col": "account_id",
                "con": "=",
                "val": account_id
                })

            # ROLES
            if roles:

                # DELETE OLD PERMISSION
                self.postgres.delete('account_role', conditions)

                # LOOP NEW PERMISSIONS
                for role_id in roles:

                    # INIT NEW PERMISSION
                    temp = {}
                    temp['account_id'] = account_id
                    temp['role_id'] = role_id

                    # INSERT NEW PERMISSION OF ROLE
                    self.postgres.insert('account_role', temp)

            # RETURN
            return 1

        # RETURN
        return 0

    def recheck_username(self, user_id, username):
        """Check Username"""

        sql_str = "SELECT * FROM account WHERE "
        sql_str += " username = '{0}'".format(username)
        sql_str += " AND id != '{0}'".format(user_id)

        res = self.postgres.query_fetch_one(sql_str)

        if res:

            return res

        return 0

    def send_email_update(self, username, old_email, new_email):
        """Send Email Update"""

        emailer = Email()
        email_temp = EmailUpdate()

        message = email_temp.message_temp(username, old_email, new_email)
        subject = "Email Update"
        emailer.send_email(old_email, message, subject)
        emailer.send_email(new_email, message, subject)

        return 1

    def assign_student_group(self, account_id, student_group_ids, token):
        """ Assign Student Group """

        # CHECK EXISTING
        new_student_groups = student_group_ids
        sql_str = "SELECT * FROM user_group_students WHERE student_id='{0}'".format(account_id)
        results = self.postgres.query_fetch_all(sql_str)

        if results:
            user_groups = [res['user_group_id'] for res in results]
            new_student_groups = set(new_student_groups)

            db_tutor_groups = set(user_groups)
            new_student_groups.difference_update(db_tutor_groups)
            new_student_groups = list(new_student_groups)

            # REMOVE OLD USER GROUP
            to_remove_group = []

            for user_group_id in user_groups:

                if not user_group_id in student_group_ids:

                    to_remove_group.append(user_group_id)

            if to_remove_group:

                # GET ALL COURSES IN TO REMOVE GROUPS
                old_group_ids = ','.join("'{0}'".format(group_id) for group_id in to_remove_group)
                sql_str = "SELECT * FROM user_group_courses WHERE user_group_id IN ({0})".format(old_group_ids)
                results = self.postgres.query_fetch_all(sql_str)

                old_course_ids = [res['course_id'] for res in results]

                for old_course_id in old_course_ids:

                    # CHECK IF STUDENT IS NOT BOND TO OTHER GROUP WITH THIS COURSE
                    sql_str = " SELECT course_id FROM user_group_courses WHERE"
                    sql_str += " user_group_id IN (SELECT user_group_id"
                    sql_str += "  FROM user_group_students WHERE"
                    sql_str += " student_id='{0}'".format(account_id)
                    sql_str += " AND NOT user_group_id IN '{0}')".format(old_group_ids)
                    usergc = self.postgres.query_fetch_all(sql_str)

                    if not usergc:

                        # REMOVE STUDENT TO THIS COURSE
                        conditions = []
                        conditions.append({
                            "col": "course_id",
                            "con": "=",
                            "val": old_course_id
                            })

                        conditions.append({
                            "col": "account_id",
                            "con": "=",
                            "val": account_id
                            })

                        conditions2 = copy.deepcopy(conditions)
                        conditions3 = copy.deepcopy(conditions)
                        conditions4 = copy.deepcopy(conditions)

                        self.postgres.delete('student_course', conditions)
                        self.postgres.delete('student_section', conditions2)
                        self.postgres.delete('student_subsection', conditions3)
                        self.postgres.delete('student_exercise', conditions4)

                # DELETE STUDENT TO USER GROUP
                conditions = []
                conditions.append({
                    "col": "user_group_id",
                    "con": "IN",
                    "val": to_remove_group
                    })

                conditions.append({
                    "col": "student_id",
                    "con": "=",
                    "val": account_id
                    })

                self.postgres.delete('user_group_students', conditions)

        if new_student_groups:

            # GET GROUP COURSES
            for user_group_id in new_student_groups:

                user_group_student = {}
                user_group_student['user_group_students_id'] = self.generate_token(False)
                user_group_student['student_id'] = account_id
                user_group_student['user_group_id'] = user_group_id
                user_group_student['created_on'] = time.time()

                self.postgres.insert('user_group_students', user_group_student)

            new_group_ids = ','.join("'{0}'".format(group_id) for group_id in new_student_groups)
            sql_str = "SELECT * FROM user_group_courses WHERE"
            sql_str += " user_group_id IN ({0})".format(new_group_ids)
            results = self.postgres.query_fetch_all(sql_str)

            if not results:
                pass

            for result in results:

                course_id = result['course_id']

                sql_str = "SELECT * FROM student_course WHERE"
                sql_str += " account_id='{0}'".format(account_id)
                sql_str += " AND course_id='{0}'".format(course_id)
                res = self.postgres.query_fetch_one(sql_str)

                if res:
                    continue

                # ADD STUDENT TO A COURSE
                temp = {}
                temp['account_id'] = account_id
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
                self.send_notif(account_id, token, account_id, description, notif_type, notif_name)

        return 1

    def assign_tutor_group(self, account_id, tutor_group_ids, token):
        """ Assign Tutor Group """

        # CHECK EXISTING
        sql_str = "SELECT * FROM user_group_tutors WHERE tutor_id='{0}'".format(account_id)
        results = self.postgres.query_fetch_all(sql_str)

        new_tutor_groups = tutor_group_ids
        if results:
            tutor_groups = [res['user_group_id'] for res in results]
            new_tutor_groups = set(new_tutor_groups)

            db_tutor_groups = set(tutor_groups)
            new_tutor_groups.difference_update(db_tutor_groups)
            new_tutor_groups = list(new_tutor_groups)

            # REMOVE OLD USER GROUP
            to_remove_group = []

            for tutor_group_id in tutor_groups:

                if not tutor_group_id in tutor_group_ids:

                    to_remove_group.append(tutor_group_id)

            if to_remove_group:

                # GET ALL COURSES IN TO REMOVE GROUPS
                old_group_ids = ','.join("'{0}'".format(group_id) for group_id in to_remove_group)
                sql_str = "SELECT * FROM user_group_courses WHERE user_group_id IN ({0})".format(old_group_ids)
                results = self.postgres.query_fetch_all(sql_str)

                old_course_ids = [res['course_id'] for res in results]

                for old_course_id in old_course_ids:

                    # CHECK IF TUTOR IS NOT BOND TO OTHER GROUP WITH THIS COURSE
                    sql_str = " SELECT course_id FROM user_group_courses WHERE"
                    sql_str += " user_group_id IN (SELECT user_group_id"
                    sql_str += " FROM user_group_tutors WHERE"
                    sql_str += " tutor_id='{0}'".format(account_id)
                    sql_str += " AND NOT user_group_id IN '{0}')".format(old_group_ids)
                    usergc = self.postgres.query_fetch_all(sql_str)

                    if not usergc:

                        # REMOVE TUTOR TO THIS COURSE
                        conditions = []
                        conditions.append({
                            "col": "course_id",
                            "con": "=",
                            "val": old_course_id
                            })

                        conditions.append({
                            "col": "account_id",
                            "con": "=",
                            "val": account_id
                            })

                        self.postgres.delete('tutor_courses', conditions)

                # DELETE TUTOR TO USER GROUP
                conditions = []
                conditions.append({
                    "col": "user_group_id",
                    "con": "IN",
                    "val": to_remove_group
                    })

                conditions.append({
                    "col": "tutor_id",
                    "con": "=",
                    "val": account_id
                    })

                self.postgres.delete('user_group_tutors', conditions)

        if new_tutor_groups:

            # GET GROUP COURSES
            for tutor_group_id in new_tutor_groups:

                user_group_tutor = {}
                user_group_tutor['user_group_tutors_id'] = self.generate_token(False)
                user_group_tutor['tutor_id'] = account_id
                user_group_tutor['user_group_id'] = tutor_group_id
                user_group_tutor['created_on'] = time.time()

                self.postgres.insert('user_group_tutors', user_group_tutor)

            new_group_ids = ','.join("'{0}'".format(group_id) for group_id in new_tutor_groups)
            sql_str = "SELECT * FROM user_group_courses WHERE"
            sql_str += " user_group_id IN ({0})".format(new_group_ids)
            results = self.postgres.query_fetch_all(sql_str)

            if not results:
                pass

            for result in results:

                course_id = result['course_id']

                # VALIDATE
                sql_str = "SELECT * FROM tutor_courses WHERE"
                sql_str += " account_id='{0}'".format(account_id)
                sql_str += " AND course_id='{0}'".format(course_id)
                res = self.postgres.query_fetch_one(sql_str)

                if res:
                    continue

                data = {}
                data['account_id'] = account_id
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
                self.send_notif(account_id, token, account_id, description, notif_type, notif_name)

        return 1