# pylint: disable=too-many-function-args
"""Course Subsection"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class TutorSubsection(Common):
    """Class for CourseSection"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for TutorSubsection class"""
        self.postgresql_query = PostgreSQL()
        super(TutorSubsection, self).__init__()

    def tutor_subsection(self):
        """
        This API is for Getting All Tutor Course Subsection
        ---
        tags:
          - Tutor / Manager
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
          - name: section_id
            in: query
            description: Section ID
            required: true
            type: string
          - name: subsection_id
            in: query
            description: Subsection ID
            required: false
            type: string
        responses:
          500:
            description: Error
          200:
            description: Tutor Subsection
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        section_id = request.args.get('section_id')
        subsection_id = request.args.get('subsection_id')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # CHECK ACCESS RIGHTS
        if not self.can_access_tutorenv(userid):
            data['alert'] = "Sorry, you have no rights to access this!"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        datas = self.get_subsection(userid, section_id, subsection_id)
        datas['children'] = self.get_subsection_child(userid, section_id, subsection_id)
        datas['status'] = 'ok'

        return self.return_data(datas)

    def get_subsection(self, user_id, section_id, subsection_id):
        """Return All Course Section"""

        # DATA

        sql_str = "SELECT s.*, c.course_name, c.course_title, sec.section_name, (SELECT"
        sql_str += " array_to_json(array_agg(exercise)) FROM (SELECT * FROM exercise e"
        sql_str += " INNER JOIN tutor_exercise te ON e.exercise_id = te.exercise_id WHERE"
        sql_str += " e.subsection_id = s.subsection_id AND te.account_id = '{0}')".format(user_id)
        sql_str += " AS exercise) as exercise FROM subsection s"
        sql_str += " LEFT JOIN tutor_section ts ON s.section_id = ts.section_id"
        sql_str += " LEFT JOIN section sec ON s.section_id = sec.section_id"
        sql_str += " LEFT JOIN course c ON sec.course_id = c.course_id WHERE s.status is True AND"
        sql_str += " s.section_id = '{0}' AND ts.account_id = '{1}'".format(section_id, user_id)

        if subsection_id:
            sql_str += " AND s.subsection_id='{0}'".format(subsection_id)

        res = self.postgres.query_fetch_all(sql_str)

        data = {}
        data['data'] = res

        return data

    def get_subsection_child(self, user_id, section_id, subsection_id):
        """ Return Section Child """

        # GET COURSE ID
        sql_str = "SELECT course_id FROM section WHERE section_id = '{0}'".format(section_id)
        course_id = self.postgres.query_fetch_one(sql_str)

        data = []

        course = self.fetch_course_details(user_id, course_id['course_id'])

        if course:

            data = course[0]['children']
            section_ids = [dta['section_id'] for dta in data]

            try:
                section_index = section_ids.index(section_id)
                data = data[section_index]
                if subsection_id:

                    subsection_ids = [dta['subsection_id'] for dta in data['children']]
                    sub_index = subsection_ids.index(subsection_id)
                    data = data['children'][sub_index]

            except ValueError:
                pass

        return data
