"""Student Skills"""
import time

import datetime
import dateutil.relativedelta

from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from socketIO_client import SocketIO, LoggingNamespace

class StudentSkills(Common):
    """Class for StudentSkills"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for StudentSkills class"""
        self.postgresql_query = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(StudentSkills, self).__init__()

    def student_skills(self):
        """
        This API is for Getting Student Skills
        ---
        tags:
          - Progress
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
          - name: limit
            in: query
            description: Limit
            required: true
            type: integer
          - name: page
            in: query
            description: Page
            required: true
            type: integer
          - name: sort_type
            in: query
            description: Sort Type
            required: false
            type: string
          - name: sort_column
            in: query
            description: Sort Column
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
        page = int(request.args.get('page'))
        limit = int(request.args.get('limit'))
        sort_type = request.args.get('sort_type')
        sort_column = request.args.get('sort_column')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # INSERT student_skills
        self.insert_student_skills(userid)

        # INSERT student_subskills
        self.insert_student_subskills(userid)

        # UPDATE student_subskills
        # self.update_skill_subskills(userid)

        # datas = self.get_student_skills(userid, page, limit)
        datas = self.fetch_student_skills(token, userid, page, limit, sort_type, sort_column)
        datas['status'] = 'ok'

        return self.return_data(datas, userid)

    def fetch_student_skills(self, token, userid, page, limit, sort_type, sort_column):
        """ FETCT STUDENT SKILLS """

        offset = int((page - 1) * limit)

        # COUNT
        count_str = "SELECT COUNT(*) FROM student_all_skills WHERE"
        count_str += " account_id='{0}'".format(userid)
        count = self.postgres.query_fetch_one(count_str)

        # sql_str = "SELECT *, skills.skill, (SELECT array_to_json(array_agg(sbskll))"
        # sql_str += " FROM (SELECT * FROM skill_subskills skllsskll"
        # sql_str += " INNER JOIN student_subskills stdntsskll ON"
        # sql_str += " skllsskll.subskill_id=stdntsskll.subskill_id"
        # sql_str += " WHERE skllsskll.skill_id=sskill.skill_id AND"
        # sql_str += " stdntsskll.account_id='{0}'".format(userid)
        # sql_str += ") AS sbskll) AS subskills FROM student_skills sskill"
        # sql_str += " INNER JOIN skills ON sskill.skill_id=skills.skill_id WHERE"
        # sql_str += " sskill.account_id='{0}'".format(userid)
        # sql_str += " ORDER BY sskill.skill_id ASC LIMIT {0} OFFSET {1}".format(limit, offset)

        sql_str = """SELECT sas.*,ms.master_skill_id, ms.master_skill_id AS skill_id,
        (SELECT array_to_json(array_agg(subs)) FROM (SELECT * FROM
        student_all_subskills WHERE subskill IN (SELECT subskill FROM master_subskills
        WHERE master_subskill_id IN (SELECT master_subskill_id FROM master_skill_subskills
        WHERE master_skill_id=ms.master_skill_id)) AND
        account_id='{0}')""".format(userid)
        sql_str += """ AS subs) AS subskills FROM student_all_skills
        sas INNER JOIN master_skills ms ON ms.skill=sas.skill WHERE"""
        sql_str += """ account_id='{0}'""".format(userid)
        # sql_str += """ ORDER BY sas.skill ASC LIMIT {0} OFFSET {1}""".format(limit, offset)

        #SORT
        if sort_column and sort_type:

            # if sort_column in ['skill', 'time_studied', 'created_on']:
            if sort_column.lower() == "time_studied":
                sort_column = "created_on"

            if sort_column == "skill":
                sql_str += " ORDER BY  upper(sas.{0}) {1}".format(sort_column.lower(), sort_type.lower())

            else:
                sql_str += " ORDER BY  sas.{0}::float {1}".format(sort_column.lower(), sort_type.lower())

        else:
            sql_str += " ORDER BY upper(sas.skill) ASC"

        sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)

        master_skills = self.postgres.query_fetch_all(sql_str)
        master_skill_ids = [ms['master_skill_id'] for ms in master_skills or []]

        self.update_skill_subskills(userid, master_skill_ids)

        # TRIGGER SOCKETIO NOTIFICATION
        message = {}
        message['token'] = token
        message['userid'] = userid
        message['type'] = 'notification'
        # message['data'] = notif
        # message['notification_id'] = notification_id
        # message['notification_type'] = notification_type

        # socketio = SocketIO('0.0.0.0', 5000, LoggingNamespace)
        # socketio.emit('notification', message)
        # socketio.disconnect()

        results = self.postgres.query_fetch_all(sql_str)

        for res in results or []:

            try:

                res['section_name'] = res['skill'].split(' - ')[0]
                res['subsection_name'] = res['skill'].split(' - ')[1]

            except:

                res['section_name'] = res['skill']
                res['subsection_name'] = ""

            try:

                time_studied = self.date_difference(res['created_on'], time.time())

                res['time_studied'] = "{0} day(s)".format(time_studied)

            except:

                res['time_studied'] = '0 day'

            # if res['subskills']:

            #     for sskill in res['subskills']:

            #         sskill['subskill'] = self.get_subskill(sskill['subskill_id'])


        total_rows = count['count']
        total_page = int((total_rows + limit - 1) / limit)


        if not results:

            results = []

        data = {}
        data['rows'] = results
        data['total_rows'] = total_rows
        data['total_page'] = total_page
        data['limit'] = limit
        data['page'] = page

        return data

    def get_subskill(self, subskill_id):

        sql_str = "SELECT subskill FROM subskills WHERE"
        sql_str += " subskill_id='{0}'".format(subskill_id)
        subskills = self.postgres.query_fetch_one(sql_str)

        return subskills['subskill']

    def get_student_skills(self, user_id, page, limit):
        """Return Student Skills"""


        # COUNT
        count_str = "SELECT COUNT(*) FROM student_subsection ssub"
        count_str += " LEFT JOIN section s ON ssub.section_id = s.section_id"
        count_str += " LEFT JOIN subsection sub ON ssub.subsection_id = sub.subsection_id"
        count_str += " WHERE ssub.account_id = '{0}'".format(user_id)
        count = self.postgres.query_fetch_one(count_str)

        offset = int((page - 1) * limit)

        # DATA
        # sql_str = "SELECT * FROM student_subsection  ssub"
        # sql_str += " LEFT JOIN section s ON ssub.section_id = s.section_id"
        # sql_str += " LEFT JOIN subsection sub ON ssub.subsection_id = sub.subsection_id"
        # sql_str += " WHERE ssub.account_id = '{0}'".format(user_id)
        # sql_str += " ORDER BY s.difficulty_level, sub.difficulty_level"
        # sql_str += " LIMIT {0} OFFSET {1}".format(limit, offset)

        sql_str = "SELECT section_name, subsection_name, s.difficulty_level,"
        sql_str += " sub.difficulty_level, (SELECT array_to_json(array_agg(subsection_id)) FROM"
        sql_str += " (SELECT subsection_id FROM subsection sub2 LEFT JOIN section s2"
        sql_str += " ON sub2.section_id = s2.section_id WHERE s2.section_name = s.section_name"
        sql_str += " AND sub2.subsection_name = sub.subsection_name)"
        sql_str += " as subsection_id) as subsection_ids FROM student_subsection ssub"
        sql_str += " LEFT JOIN subsection sub ON ssub.subsection_id = sub.subsection_id"
        sql_str += " LEFT JOIN section s ON sub.section_id = s.section_id"
        sql_str += " WHERE ssub.account_id = '{0}' GROUP BY s.section_name,".format(user_id)
        sql_str += " sub.subsection_name, s.difficulty_level, sub.difficulty_level"
        sql_str += " ORDER BY s.difficulty_level, sub.difficulty_level"

        results = self.postgres.query_fetch_all(sql_str)

        result = []
        for res in results:

            # GET SKILL ON EXERCISE BY SUBSECTION ID
            datas = self.skills_by_exercise(user_id, res['subsection_ids'])
            datas['skill'] = "{0} - {1}".format(res['section_name'], res['subsection_name'])
            datas['section_name'] = res['section_name']
            datas['subsection_name'] = res['subsection_name']
            result.append(datas)

        total_rows = count['count']
        total_page = int((total_rows + limit - 1) / limit)

        data = {}
        data['rows'] = result
        data['total_rows'] = total_rows
        data['total_page'] = total_page
        data['limit'] = limit
        data['page'] = page

        return data

    def skills_by_exercise(self, user_id, subsection_ids):
        """ Return Skills by Exercise """

        assert subsection_ids, "Subsection IDs are required"

        subsection_ids = ','.join("'{0}'".format(sub_id) for sub_id in subsection_ids)

        sql_str = "SELECT * FROM student_exercise_questions"
        sql_str += " WHERE student_exercise_id IN (SELECT student_exercise_id "
        sql_str += " FROM student_exercise WHERE status is True AND"
        sql_str += " account_id='{0}' AND".format(user_id)
        sql_str += " exercise_id IN (SELECT exercise_id FROM exercise WHERE"
        sql_str += " subsection_id IN ({0}) AND status is True))".format(subsection_ids)
        student_exercise_questions = self.postgres.query_fetch_all(sql_str)

        answer = [dta['answer'] for dta in student_exercise_questions]
        total = len(answer)
        not_answer = [None, '', []]

        # ANSWERED QUESTIONS
        total_answer = len([ans for ans in answer if ans not in not_answer])

        # PROGRESS
        progress = 0
        if total_answer:
            progress = self.format_progress((total_answer / total) * 100)

        progress = round(progress, 2)

        # CORRECT ANSWER
        score = 0
        for question in student_exercise_questions:
            ans = self.check_answer(question['course_question_id'], question['answer'])

            if ans['isCorrect'] is True:
                score += 1

        correct_answer = 0
        if total:
            correct_answer = self.format_progress((score / total) * 100)
        correct_answer = round(correct_answer, 2)

        result = {}
        result['answered_questions'] = total_answer
        result['correct'] = correct_answer
        result['progress'] = progress
        result['time_studied'] = "2 days"

        return result

    def date_difference(self, start, end):
        """ DATE DIFFERENCE """
        try:

            dt1 = datetime.datetime.fromtimestamp(start)
            dt2 = datetime.datetime.fromtimestamp(end)
            rd = dateutil.relativedelta.relativedelta (dt2, dt1)

            return rd.days

        except:

            return 0
