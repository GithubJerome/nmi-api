# pylint: disable=too-many-function-args
"""Upload Course Template"""
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

class UploadCourseTemplate(Common):
    """Class for UploadCourseTemplate"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UploadCourseTemplate class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        self.config = ConfigParser()
        self.config.read("config/config.cfg")
        super(UploadCourseTemplate, self).__init__()

    def upload_course_template(self):
        """
        This API is for Upload Course Template
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
            description: File temp
            required: true
            type: file
        consumes:
          - multipart/form-data
        responses:
          500:
            description: Error
          200:
            description: Upload Course Template
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

        # reader = csv.DictReader(open(file_dir, encoding='unicode_escape'))

        # headers = next(csv.reader(open(file_dir, encoding='unicode_escape')))

        reader = []
        headers = []

        try:

          reader = csv.DictReader(open(file_dir, encoding='utf-8'))

          headers = next(csv.reader(open(file_dir, encoding='utf-8')))

        except:

            data["alert"] = "Invalid File!"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        if not self.check_headers(reader, headers):

            data["alert"] = "Invalid File!"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        channel = {}
        channel['file_dir'] = file_dir
        channel['state'] = 'new course'

        # TRIGGER SOCKETIO UPDATE COURSE
        message = {}
        message['token'] = token
        message['userid'] = userid
        message['type'] = 'course_update'
        message['data'] = channel

        socketio = SocketIO('0.0.0.0', 5000, LoggingNamespace)
        socketio.emit('course_update', message)
        socketio.disconnect()

        # updates = self.run_course_update(reader)

        # if updates['status'] == "Failed":

        #     # RETURN ALERT
        #     return self.return_data(updates)

        # data['message'] = "Course successfully uploaded!"
        data['message'] = "Please wait for the email to confirm course is uploaded!"
        data['status'] = "ok"

        return self.return_data(data, userid)
