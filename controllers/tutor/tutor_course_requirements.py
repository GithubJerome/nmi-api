"""Course Requirements"""
import time

from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity

class TutorCourseRequirements(Common):
    """Class for TutorCourseRequirements"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for TutorCourseRequirements class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(TutorCourseRequirements, self).__init__()

    def tutor_course_requirements(self):
        """
        This API is for Getting all course requirements
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
          - name: course_id
            in: query
            description: Course ID
            required: true
            type: string
        responses:
          500:
            description: Error
          200:
            description: User Information
          Affected tables:
            description: course_requirements, section_requirements, subsection_requirements, exercise_requirements
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        course_id = request.args.get('course_id')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # VALIDATE TABLES
        data['data'] = self.validate_tables(course_id)

        return self.return_data(data, userid)

    def validate_tables(self, course_id):
        """ VALIDATE TABLES """

        self.validate_course_requirements(course_id)

        sql_str = "SELECT c.course_id, c.course_name, c.course_title, gcr.course_requirement_id, c.exercise_name,"
        sql_str += " gcr.completion, gcr.grade_locking, gcr.on_previous, gcr.is_lock, gcr.is_repeatable,"
        sql_str += " gcr.is_visible, (SELECT array_to_json(array_agg(sections))"
        sql_str += " FROM (SELECT s.section_id, s.section_name,"
        sql_str += " gsr.section_requirement_id, gsr.completion, gsr.is_repeatable,"
        sql_str += " gsr.grade_locking, gsr.on_previous, gsr.is_lock, gsr.is_visible,"
        sql_str += " (SELECT array_to_json(array_agg(subsections)) FROM"
        sql_str += " (SELECT ss.subsection_id, ss.subsection_name,"
        sql_str += " gssr.subsection_requirement_id, gssr.is_repeatable,"
        sql_str += " gssr.completion, gssr.grade_locking, gssr.on_previous, gssr.is_lock, gssr.is_visible,"
        sql_str += " (SELECT array_to_json(array_agg(exercises)) FROM"
        sql_str += " (SELECT e.exercise_id, e.exercise_number, e.exercise_id as key,"
        sql_str += " CASE WHEN c.exercise_name is null OR c.exercise_name = '' then"
        sql_str += " 'Exercise '||e.exercise_number else CONCAT(c.exercise_name, ' ')||e.exercise_number end as exercise_num,"
        sql_str += " ger.exercise_requirement_id, ger.completion, e.is_repeatable,"
        sql_str += " ger.grade_locking, ger.on_previous, ger.is_lock, ger.is_visible FROM exercise e"
        sql_str += " INNER JOIN exercise_requirements ger ON"
        sql_str += " ss.subsection_id=e.subsection_id AND e.exercise_id=ger.exercise_id"
        sql_str += " ORDER BY e.exercise_number::int ASC) AS exercises) AS exercises"
        sql_str += " FROM subsection ss INNER JOIN subsection_requirements gssr ON"
        sql_str += " ss.section_id=s.section_id AND ss.subsection_id=gssr.subsection_id"
        sql_str += " ORDER BY ss.difficulty_level ASC) AS subsections) AS subsections"
        sql_str += " FROM section s INNER JOIN section_requirements gsr ON"
        sql_str += " c.course_id=s.course_id AND s.section_id=gsr.section_id"
        sql_str += " ORDER BY s.difficulty_level ASC) AS sections) AS sections"
        sql_str += " FROM course c INNER JOIN course_requirements gcr ON"
        sql_str += " c.course_id=gcr.course_id"
        sql_str += " WHERE c.course_id='{0}'".format(course_id)

        course_data = self.postgres.query_fetch_one(sql_str)

        if course_data:

            if not course_data['sections']:

                course_data['sections'] = []

            for section in course_data['sections']:

                if not section['subsections']:
                    section['subsections'] = []

        return course_data
