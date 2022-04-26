# pylint: disable=too-many-function-args
"""IO Course Uploader"""
import csv
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from werkzeug.utils import secure_filename
from configparser import ConfigParser
from library.config_parser import config_section_parser
from socketIO_client import SocketIO, LoggingNamespace
from library.emailer import Email
from templates.message import Message

class IOCourseUploader(Common):
    """Class for IOCourseUploader"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for IOCourseUploader class"""
        # self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        self.config = ConfigParser()
        self.config.read("config/config.cfg")
        super(IOCourseUploader, self).__init__()

    def io_course_uploader(self):
        """
        This API is for IO Course uploader
        ---
        tags:
          - Upload
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
            description: IO Course uploader
            required: true
            schema:
              id: IO Course uploader
              properties:
                file_dir:
                    type: string
                old_course_id:
                    type: string
        responses:
          500:
            description: Error
          200:
            description: IO Course uploader
        """
        data = {}

        # GET HEADER
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

        file_dir = query_json['file_dir']
        course_state = query_json['state']
        old_course_id = None

        if 'old_course_id' in query_json:

            old_course_id = query_json['old_course_id']

        # new_csv_data = csv.DictReader(open(file_dir, encoding='unicode_escape'))
        new_csv_data = csv.DictReader(open(file_dir, encoding='utf-8'))

        updates = self.run_course_update(new_csv_data, old_course_id=old_course_id)

        sql_str = "SELECT email, username FROM account WHERE"
        sql_str += " id='{0}'".format(userid)
        account = self.postgres.query_fetch_one(sql_str)

        email = account['email']
        username = account['username']
        message = ""
        subject = ""

        if updates['status'] == "Failed":

            if course_state == 'update course':

                message = updates['alert']
                subject = "Update Course: {0}".format(updates['course_name'])

            else:

                message = updates['alert']
                subject = "New Course: {0}".format(updates['course_name'])

            self.email_user_update(email, username, message, subject)

            # RETURN ALERT
            return self.return_data(updates)

        if course_state == 'update course':

            message = "Course successfully updated!"
            subject = "Update Course: {0}".format(updates['course_name'])

        else:

            message = "Course successfully uploaded!"
            subject = "New Course: {0}".format(updates['course_name'])

        self.email_user_update(email, username, message, subject)

        data['message'] = "Course successfully uploaded!"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def email_user_update(self, email, username, msg, subject):
        """ EMAIL USER FOR COURSE UPDATE """

        emailer = Email()
        email_temp = Message()

        # msg = email_temp.message_temp(username, "Your password is successfully changed.")
        message = email_temp.message_temp(username, msg)
        # subject = "Reset password confirmation"
        emailer.send_email(email, message, subject)

        return 1
