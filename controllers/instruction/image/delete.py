"""Delete Instruction Image"""
import time
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class DeleteInstructionImage(Common):
    """Class for Delete"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for DeleteInstructionImage class"""
        self.postgres = PostgreSQL()
        super(DeleteInstructionImage, self).__init__()

    def delete_instruction_image(self):
        """
        This API is for Deleting Instruction Images
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
          - name: query
            in: body
            description: Instruction Image
            required: true
            schema:
              id: DeleteInstructionImage
              properties:
                image_ids:
                    types: array
                    example: []
        responses:
          500:
            description: Error
          200:
            description: Instruction Device Images
        """
        data = {}

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

        # GET HEADER
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # GET QUERY
        image_ids = query_json["image_ids"]

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        if not self.delete_instruction_images(image_ids):

            data["alert"] = "Please check your query! | Failed to Delete Image"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        data['message'] = "Images successfully Deleted!"
        data['status'] = "ok"
        return self.return_data(data, userid)

    def delete_instruction_images(self, image_ids):
        """Delete Instruction Image ids"""

        for image_id in image_ids:

            # VERIFY IF IMAGE EXISTS FOR Instruction
            sql_str = "SELECT * FROM instruction_image"
            sql_str += " WHERE image_id='{0}'".format(image_id)
            sql_str += " AND status = 'active'"

            img_instruction = self.postgres.query_fetch_one(sql_str)

            if img_instruction:

                # INIT CONDITION
                conditions = []

                # CONDITION FOR QUERY
                conditions.append({
                    "col": "image_id",
                    "con": "=",
                    "val": img_instruction['image_id']
                    })

                update_column = {}
                update_column['update_on'] = time.time()
                update_column['status'] = "inactive"

                if not self.postgres.update('instruction_image', update_column, conditions):
                    return 0

        return 1
