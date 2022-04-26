# pylint: disable=too-many-function-args
"""Upload Questions"""
import re
import os
import csv
import time
import json

from flask import request
from flask import send_file
from flask import send_from_directory
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from werkzeug.utils import secure_filename
from configparser import ConfigParser
from library.config_parser import config_section_parser

class UploadQuestions(Common):
    """Class for UploadCourseTemplate"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UploadQuestions class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        self.config = ConfigParser()
        self.config.read("config/config.cfg")
        super(UploadQuestions, self).__init__()

    def upload_questions(self):
        """
        This API is for Upload Question
        ---
        tags:
          - Question
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
            description: File temp
            required: true
            type: file
        consumes:
          - multipart/form-data
        responses:
          500:
            description: Error
          200:
            description: Upload Questions
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
        filename = '/question_' + str(int(time.time())) + "." + ext
        # filename = secure_filename(filename)
        # file.save(os.path.join(uploads, filename))

        file_dir = uploads + filename
        file.save(file_dir)
        # rows = csv.DictReader(open(file_dir))

        # with open(file_dir, 'r', encoding='UTF-8', newline='') as csvarchive:
        #     entrada = csv.reader(csvarchive)
        #     for reg in entrada:
        #         print("reg: {0}".format(reg))

        # rows = csv.DictReader(open(file_dir, encoding='unicode_escape'))
        rows = csv.DictReader(open(file_dir, encoding='UTF-8', errors='ignore'))

        if not self.insert_questions(rows):

            data['message'] = "An error occured while uploading the file!"
            data['status'] = "failed"
            return self.return_data(data, userid)

        data['message'] = "Questions successfully uploaded!"
        data['status'] = "ok"

        return self.return_data(data, userid)
