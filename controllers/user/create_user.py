
# pylint: disable=no-self-use
"""Create User"""
import string
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.emailer import Email
from templates.invitation import Invitation

class CreateUser(Common, ShaSecurity):
    """Class for CreateUser"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CreateUser class"""

        self.postgresql_query = PostgreSQL()
        self.sha_security = ShaSecurity()

        super(CreateUser, self).__init__()

    def create_user(self):
        """
        This API is for Creating User
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
            description: Invite
            required: true
            schema:
              id: Add User
              properties:
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

        responses:
          500:
            description: Error
          200:
            description: Create User
        """

        # INIT DATA
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

        # GET REQUEST PARAMS
        email = query_json["email"]
        username = query_json['username']

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # CHECK LANGUAGE
        if not 'language' in query_json.keys():

            query_json['language'] = 'en-US'

        if not query_json['language']:

            query_json['language'] = 'en-US'

        # INIT IMPORTANT KEYS
        important_keys = {}
        important_keys['roles'] = []
        important_keys['email'] = "string"
        important_keys['username'] = "string"
        important_keys['url'] = "string"
        important_keys['is_send_email'] = True

        # CHECK IMPORTANT KEYS IN REQUEST JSON
        if not self.check_request_json(query_json, important_keys):

            data["alert"] = "Invalid query, Missing parameter!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        url = query_json["url"]

        # CHECK ACCESS RIGHTS
        if not self.is_admin(userid):
            data['alert'] = "Sorry, you have no rights to add user!"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        # # CHECK EMAIL
        # if self.check_user(email):
        #     data["alert"] = "Email already exists!"
        #     data['status'] = 'Failed'

        #     # RETURN ALERT
        #     return self.return_data(data, userid)

        # CHECK USERNAME
        if self.check_username(username):
            data['alert'] = "Username is already taken!"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        password = self.generate_password()

        # CHECK ROLES
        if not self.check_role_ids(query_json):

            data = {}
            data['message'] = "Invalid Role ID!"
            data['status'] = "Failed"

            return self.return_data(data, userid)

        # INSERT INVITATION
        account_id = self.add_user(password, query_json)

        if not account_id:

            data = {}
            data['message'] = "Invalid email!"
            data['status'] = "Failed"

            return self.return_data(data, userid)

        # # FORCE CHANGE PASSWORD
        # if query_json['force_change_password'] is True:
        #     url = "{0}user/force/change-password".format(url)

        # SEND INVITATION
        if query_json['is_send_email'] is True:
            self.send_invitation(email, username, password, url)

        data = {}
        data['message'] = "User successfully created"
        data['status'] = "ok"

        return self.return_data(data, userid)

    # def check_user(self, email):
    #     """Check Invitation"""

    #     sql_str = "SELECT * FROM account WHERE "
    #     sql_str += " email = '" + email + "'"

    #     res = self.postgres.query_fetch_one(sql_str)

    #     if res:

    #         return res

    #     return 0

    def check_username(self, username):
        """Check Invitation"""

        sql_str = "SELECT * FROM account WHERE "
        sql_str += " username = '" + username + "'"

        res = self.postgres.query_fetch_one(sql_str)

        if res:

            return res

        return 0

    def add_user(self, password, query_json):
        """Insert Invitation"""

        # token = self.generate_token(True)

        roles = query_json['roles']
        data = query_json

        data = self.remove_key(data, "roles")

        # username = "no_username_{0}".format(int(time.time()))
        # if not self.check_username(username):
        #     username += self.random_str_generator(5)

        data['id'] = self.sha_security.generate_token(False)
        data['username'] = query_json['username']
        data['status'] = True
        data['state'] = False
        data['password'] = self.string_to_sha_plus(password)
        data['created_on'] = time.time()

        # SET DEFAULT LANGUAGE
        data['language'] = "nl-NL"

        account_id = self.postgres.insert('account', data, 'id')

        if not account_id:
            return 0

        for role_id in roles:

            # ACCOUNT COMPANY
            temp = {}
            temp['account_id'] = account_id
            temp['role_id'] = role_id
            self.postgres.insert('account_role', temp)

            # # BIND COURSE TEMPORARILY
            # if self.is_student(role_id):
            #     self.bind_student_course(account_id)

        return account_id

    def send_invitation(self, email, username, password, url):
        """Send Invitation"""

        emailer = Email()
        email_temp = Invitation()

        message = email_temp.message_temp(username, password, url)
        subject = "Invitation"
        emailer.send_email(email, message, subject)

        return 1

    def generate_password(self):
        """Generate Password"""

        char = string.ascii_uppercase
        char += string.ascii_lowercase
        char += string.digits

        return self.random_str_generator(8, char)

    def is_admin(self, user_id):
        """ Check if admin """

        sql_str = "SELECT * FROM account_role ac"
        sql_str += " LEFT JOIN role r ON ac.role_id = r.role_id"
        sql_str += " WHERE account_id = '{0}'".format(user_id)
        result = self.postgres.query_fetch_one(sql_str)

        if result['role_name'].upper() == "MANAGER":
            return 1

        return 0


    def is_student(self, role_id):
        """ Check if role is student """

        sql_str = "SELECT * FROM role WHERE role_id = '{0}'".format(role_id)
        result = self.postgres.query_fetch_one(sql_str)

        if result['role_name'].upper() == "STUDENT":
            return 1

        return 0

    def bind_student_course(self, user_id):
        """ BIND COURSE """

        # BIND ONE COURSE TEMPORARILY
        # GET THE EASIEST COURSE
        sql_str = "SELECT course_id FROM course WHERE difficulty_level = 1"
        course = self.postgres.query_fetch_one(sql_str)

        if course:

            # STUDENT 1
            sql_str = "SELECT * FROM student_course WHERE"
            sql_str += " account_id='{0}'".format(user_id)
            sql_str += " AND course_id='{0}'".format(course['course_id'])
            student_course = self.postgres.query_fetch_all(sql_str)

            if not student_course:
                # BIND COURSE TO STUDENT
                data = {}
                data['account_id'] = user_id
                data['course_id'] = course['course_id']
                data['progress'] = 0
                data['expiry_date'] = int(time.time()) + (86400 * 90)
                data['status'] = True
                data['created_on'] = time.time()
                self.postgres.insert('student_course', data)

    def check_role_ids(self, query_json):
        """ CHECK ROLES """

        roles = query_json['roles']

        if not roles:

            return 1

        for role_id in roles:

            sql_str = "SELECT role_name FROM role WHERE"
            sql_str += " role_id='{0}'".format(role_id)
            role = self.postgres.query_fetch_one(sql_str)

            if not role:

                return 0

        return 1
