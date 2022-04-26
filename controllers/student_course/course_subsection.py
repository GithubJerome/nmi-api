# pylint: disable=too-many-function-args
"""Course Subsection"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class CourseSubsection(Common):
    """Class for CourseSection"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CCourseSubsection class"""
        self.postgresql_query = PostgreSQL()
        super(CourseSubsection, self).__init__()

    def subsection(self):
        """
        This API is for Getting All Course Subsection
        ---
        tags:
          - Student Course
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
            description: Course Subsection
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

        datas = self.get_subsection(userid, section_id, subsection_id)
        datas['status'] = 'ok'

        return self.return_data(datas, userid)

    def get_subsection(self, user_id, section_id, subsection_id):
        """Return All Course Section"""

        # DATA
        sql_str = "SELECT s.*, c.course_name, c.exercise_name, sec.section_name, ss.is_unlocked, ss.student_subsection_id,"
        sql_str += " c.course_title, ss.progress, ssec.is_unlocked AS is_section_unlocked, (SELECT array_to_json(array_agg(exercise))"
        sql_str += " FROM (SELECT e.*, se.*, (CASE WHEN se.progress = '100' THEN true ELSE false END ) AS answered_all,"
        sql_str += " (SELECT array_to_json(array_agg(instructions))  FROM"
        sql_str += " (SELECT i.* FROM instruction i LEFT JOIN exercise e2 ON"
        sql_str += " i.exercise_id = e2.exercise_id WHERE i.exercise_id = e.exercise_id"
        sql_str += " ORDER BY page_number) AS instructions) as instructions FROM exercise e"
        sql_str += " LEFT JOIN student_exercise se ON e.exercise_id = se.exercise_id WHERE"
        sql_str += " e.subsection_id = s.subsection_id AND se.account_id = '{0}'".format(user_id)
        sql_str += " AND se.status is True ORDER BY se.exercise_number) AS exercise) as exercise"
        sql_str += " FROM subsection s LEFT JOIN student_subsection ss ON s.subsection_id = ss.subsection_id"
        sql_str += " LEFT JOIN section sec ON s.section_id = sec.section_id"
        sql_str += " LEFT JOIN student_section ssec ON sec.section_id = ssec.section_id"
        sql_str += " LEFT JOIN course c ON sec.course_id = c.course_id WHERE s.status is True AND"
        sql_str += " s.section_id = '{0}' AND ss.status is True AND ssec.status is True ".format(section_id)
        sql_str += " AND ss.account_id = '{0}' AND ssec.account_id = '{0}'".format(user_id)

        if subsection_id:
            sql_str += " AND s.subsection_id='{0}'".format(subsection_id)

        responses = self.postgres.query_fetch_all(sql_str)

        if responses:

            for res in responses:

                res['requirements'] = self.get_subsection_requirements(user_id, res['subsection_id'])

                if not 'exercise' in res.keys():

                    continue

                for exercise in res['exercise']:


                    exercise['exercise_num'] = "Exercise {0}".format(exercise['exercise_number'])
                    if res['exercise_name']:
                        exercise['exercise_num'] = "{0} {1}".format(res['exercise_name'], exercise['exercise_number'])

                    if not exercise['score']:

                        exercise['is_passed'] = False

                    elif not exercise['passing_criterium']:

                        exercise['is_passed'] = True

                    elif int(exercise['passing_criterium']) <= int(exercise['score']):

                        exercise['is_passed'] = True

                    else:

                        exercise['is_passed'] = False

                    # REQUIREMENTS
                    exercise['requirements'] = self.get_exercise_requirements(user_id, exercise['exercise_id'])

        data = {}
        data['data'] = responses

        return data
