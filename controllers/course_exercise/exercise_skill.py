# pylint: disable=too-many-function-args
"""Exercise Skill"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class ExerciseSkill(Common):
    """Class for ExerciseSkill"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for ExerciseSkill class"""
        self.postgresql_query = PostgreSQL()
        super(ExerciseSkill, self).__init__()

    def exercise_skill(self):
        """
        This API is for Getting All Exercise Skill
        ---
        tags:
          - Exercise
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
            required: false
            type: string
        responses:
          500:
            description: Error
          200:
            description: Exercise
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        exercise_id = request.args.get('exercise_id')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        data['skill'] = self.get_exercise_skill(exercise_id)
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def get_exercise_skill(self, exercise_id):
        """Return All Exercises"""

        sql_str = "SELECT e.exercise_id, ss.subsection_name, s.section_name FROM"
        sql_str += " exercise e INNER JOIN subsection ss ON e.subsection_id=ss.subsection_id"
        sql_str += " INNER JOIN section s ON e.section_id=s.section_id WHERE"
        sql_str += " exercise_id='{0}'".format(exercise_id)

        exercise = self.postgres.query_fetch_one(sql_str)

        skill = "{0} - {1}".format(exercise['section_name'], exercise['subsection_name'])

        return skill
