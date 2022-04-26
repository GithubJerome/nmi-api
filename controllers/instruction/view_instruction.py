# pylint: disable=too-many-function-args
"""View Instruction"""
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity

class ViewInstruction(Common):
    """Class for ViewInstruction"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for ViewInstruction class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(ViewInstruction, self).__init__()

    def view_instruction(self):
        """
        This API is to update is_view of Student Instruction
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
          - name: exercise_id
            in: query
            description: Exercise ID
            required: true
            type: string
          - name: instruction_id
            in: query
            description: Instruction ID
            required: true
            type: string
        responses:
          500:
            description: Error
          200:
            description: View Instruction
        """
        data = {}

        # # GET JSON REQUEST
        # query_json = request.get_json(force=True)

        # GET HEADER
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        exercise_id = request.args.get('exercise_id')
        instruction_id = request.args.get('instruction_id')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        if not self.update_student_instruction(userid, exercise_id, instruction_id):

            data["alert"] = "Please check your query!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # SEND EMAIL TO TUTOR

        data['message'] = "Instruction has been viewed!"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def update_student_instruction(self, user_id, exercise_id, instruction_id):
        """Update Instruction"""

        conditions = []

        conditions.append({
            "col": "account_id",
            "con": "=",
            "val": user_id
        })

        conditions.append({
            "col": "exercise_id",
            "con": "=",
            "val": exercise_id
        })

        conditions.append({
            "col": "instruction_id",
            "con": "=",
            "val": instruction_id
        })

        data = {}
        data['is_viewed'] = True
        data['update_on'] = time.time()

        self.postgres.update('student_instruction', data, conditions)

        # UNLOCK EXERCISE
        self.view_all_instructions(user_id, exercise_id)

        return 1

    def view_all_instructions(self, user_id, exercise_id):
        """ View all instructions """

        sql_str = "SELECT * FROM student_instruction"
        sql_str += " WHERE account_id = '{0}' AND exercise_id = '{1}'".format(user_id, exercise_id)
        result = self.postgres.query_fetch_all(sql_str)

        # CHECK IF ALL IS_VIEW IS TRUE
        total = [res['is_viewed'] for res in result]
        is_viewed = [res['is_viewed'] for res in result if res['is_viewed'] is True]

        if total == is_viewed:
            # UNLOCK EXERCISE
            sql_str = "SELECT * FROM student_exercise WHERE"
            sql_str += " account_id = '{0}' AND exercise_id = '{1}'".format(user_id, exercise_id)
            result = self.postgres.query_fetch_one(sql_str)

            if result:

                conditions = []
                conditions.append({
                    "col": "student_exercise_id",
                    "con": "=",
                    "val": result['student_exercise_id']
                })

                # UPDATE
                data = {}
                data['is_unlocked'] = True
                data['unlock_criteria'] = "hierarchy"
                data['unlocked_on'] = time.time()

                self.postgres.update('student_exercise', data, conditions)

        return 1
