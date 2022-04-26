"""Student Skills"""
import time

import datetime
import dateutil.relativedelta

from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity

class SkillUpdates(Common):
    """Class for SkillUpdates"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for SkillUpdates class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(SkillUpdates, self).__init__()

    def skill_updates(self):
        """
        This API is for Getting Student Skills
        ---
        tags:
          - IO
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
          - name: question_id
            in: query
            description: Question ID
            required: false
            type: string
        responses:
          500:
            description: Error
          200:
            description: Student Skills
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        question_id = request.args.get('question_id')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        sql_str = "SELECT master_skill_id FROM master_skills WHERE"
        sql_str += " skill IN (SELECT skill FROM skills WHERE skill_id IN"
        sql_str += " (SELECT skill_id FROM question_skills WHERE"
        sql_str += " question_id='{0}'))".format(question_id)
        master_skills = self.postgres.query_fetch_all(sql_str)

        master_skill_ids = [ms['master_skill_id'] for ms in master_skills or []]

        # self.update_skill_subskills(userid, master_skill_ids)

        print("master_skill_ids: {0}".format(master_skill_ids))
        datas = {}
        datas['status'] = 'ok'

        return self.return_data(datas, userid)
