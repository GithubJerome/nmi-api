"""Instruction Image Upload """
import time

from flask import request
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.common import Common
from library.aws_s3 import AwsS3

class Upload(Common):
    """Class for Instruction Upload"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Instruction Upload class"""

        self.sha_security = ShaSecurity()
        self.postgres = PostgreSQL()
        self.aws3 = AwsS3()

        super(Upload, self).__init__()

    # GET VESSEL FUNCTION
    def instruction_upload(self):
        """
        This API is for Instruction Image Upload
        ---
        tags:
          - Instruction
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
            description: Instruction image
            required: true
            type: file
        consumes:
          - multipart/form-data
        responses:
          500:
            description: Error
          200:
            description: Instruction Image Upload
        """
        # INIT DATA
        data = {}

        # # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        try:

            filename = request.files['upfile'].filename
            ext = filename.split(".")[-1]

            if not self.allowed_image_type(filename):

                data["alert"] = "File Type Not Allowed!"
                data['status'] = 'Failed'
                return self.return_data(data, userid)

        except ImportError:
            data["alert"] = "No image!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        filename = self.rename_instruction_image(filename)

        img_data = {}
        img_data['image_id'] = self.sha_security.generate_token(False)
        img_data['image_name'] = filename
        img_data['status'] = "active"
        img_data['created_on'] = time.time()

        # # VERIFY IF IMAGE EXISTS FOR INSTRUCTION
        # sql_str = "SELECT * FROM device_image"
        # sql_str += " WHERE 
        # sql_str += " AND status = 'active'"

        # device = self.postgres.query_fetch_one(sql_str)

        # if device:

        #     # INIT CONDITION
        #     conditions = []

        #     # CONDITION FOR QUERY
        #     conditions.append({
        #         "col": "device_image_id",
        #         "con": "=",
        #         "val": device['device_image_id']
        #         })

        #     update_column = {}
        #     update_column['status'] = "inactive"

        #     self.postgres.update('device_image', update_column, conditions)

        image_id = self.postgres.insert('instruction_image', img_data, 'image_id')

        # IMAGE FILE NAME
        file_name = str(image_id) + "." + ext
        img_file = 'Instruction/' + "NMI_" + str(file_name)
        body = request.files['upfile']

        # SAVE TO S3
        image_url = ""
        if self.aws3.save_file(img_file, body):
            image_url = self.aws3.get_url(img_file)

        tmp = {}
        tmp['image_url'] = image_url
        tmp['image_id'] = image_id

        data["status"] = "ok"
        data['data'] = tmp

        # RETURN
        return self.return_data(data, userid)

    def allowed_image_type(self, filename):
        """ Check Allowed File Extension """

        allowed_extensions = set(['png', 'jpg', 'jpeg', 'gif'])

        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

    def rename_instruction_image(self, filename):
        """Rename Image"""

        sql_str = "SELECT * FROM instruction_image"
        sql_str += " WHERE image_name='{0}'".format(filename)

        img = self.postgres.query_fetch_one(sql_str)

        if img:
            new_name = self.file_replace(img['image_name'])

            return self.rename_instruction_image(new_name)

        return filename
