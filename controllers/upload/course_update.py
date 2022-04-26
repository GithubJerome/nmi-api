# pylint: disable=too-many-function-args
"""Upload Course Update"""
import os
import csv
import time
import copy

from flask import request
from flask import send_file
from flask import send_from_directory
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from werkzeug.utils import secure_filename
from configparser import ConfigParser
from library.config_parser import config_section_parser
from socketIO_client import SocketIO, LoggingNamespace

class UploadCourseUpdate(Common):
    """Class for UploadCourseUpdate"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UploadCourseUpdate class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        self.config = ConfigParser()
        self.config.read("config/config.cfg")
        super(UploadCourseUpdate, self).__init__()

    def upload_course_update(self):
        """
        This API is for Upload Course Update
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
          - name: upfile
            in: formData
            description: File
            required: true
            type: file
        consumes:
          - multipart/form-data
        responses:
          500:
            description: Error
          200:
            description: Upload Course Update
        """
        data = {}

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

        ext = ""
        try:

            filename = request.files['upfile'].filename
            ext = filename.split(".")[-1]

            if not self.allowed_file_type(filename):

                data["alert"] = "File Type Not Allowed!"
                data['status'] = 'Failed'
                return self.return_data(data, userid)

        except ImportError:

            data["alert"] = "No File!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        uploads = config_section_parser(self.config, "APPDIR")['dir']

        # SOURCE:
        # https://riptutorial.com/flask/example/19418/save-uploads-on-the-server

        file = request.files['upfile']
        filename = '/course_' + str(int(time.time())) + "." + ext
        # filename = secure_filename(filename)
        # file.save(os.path.join(uploads, filename))

        file_dir = uploads + filename
        file.save(file_dir)
        csv_data = csv.DictReader(open(file_dir, encoding='unicode_escape'))

        # headers = []
        # for head in reader:

        #     headers = head.key()
        #     break

        headers = next(csv.reader(open(file_dir, encoding='unicode_escape')))

        if not self.check_headers(csv_data, headers):

            data["alert"] = "Invalid File!"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        course_id = ""
        course_ids = []

        for row in csv_data:

            course_id = row['Course ID']

            if not course_id in course_ids:

                course_ids.append(course_id)

        if not course_ids:

            data["alert"] = "Invalid File!"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        # CHECK IF COURSE IS ALREADY IN USE
        if not self.use_course(course_ids):

            data["alert"] = "Course is in use!"
            data['status'] = 'Failed'

            return self.return_data(data, userid)

        if not self.delete_courses(course_ids, True):

            data["alert"] = "Invalid File!"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        channel = {}
        channel['file_dir'] = file_dir
        channel['state'] = 'update course'
        channel['old_course_id'] = course_id

        # TRIGGER SOCKETIO UPDATE COURSE
        message = {}
        message['token'] = token
        message['userid'] = userid
        message['type'] = 'course_update'
        message['data'] = channel

        socketio = SocketIO('0.0.0.0', 5000, LoggingNamespace)
        socketio.emit('course_update', message)
        socketio.disconnect()

        # # DO NOT REMOVE THIS LINE
        # new_csv_data = csv.DictReader(open(file_dir, encoding='unicode_escape'))

        # updates = self.run_course_update(new_csv_data, old_course_id=course_id)

        # if updates['status'] == "Failed":

        #     # RETURN ALERT
        #     return self.return_data(updates)

        # data['message'] = "Course successfully updated!"
        data['message'] = "Please wait for the email to confirm course is updated!"
        data['status'] = "ok"

        return self.return_data(data, userid)

    # def use_course(self, course_ids):
    #     """ CHECK IF COURSE IN USE """

    #     for course_id in course_ids:

    #         sql_str = "SELECT * FROM student_course WHERE"
    #         sql_str += " course_id='{0}'".format(course_id)

    #         if not self.postgres.query_fetch_one(sql_str):

    #             return 1

    #     return 0
