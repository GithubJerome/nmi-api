"""Course Requirements"""
import time

from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity

class SetCourseRequirements(Common):
    """Class for CourseRequirements"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CourseRequirements class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        super(SetCourseRequirements, self).__init__()

    def set_course_requirements(self):
        """
        This API is for setting default requirements
        ---
        tags:
          - User Group
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
          - name: group_id
            in: query
            description: Group ID
            required: true
            type: string
        responses:
          500:
            description: Error
          200:
            description: Default Settings for Penn and Lyjen use only
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        course_id = request.args.get('course_id')
        group_id = request.args.get('group_id')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # VALIDATE USER
        if not self.validate_user(userid, 'manager'):
            data["alert"] = "Invalid User"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)


        # VALIDATE TABLES
        data['data'] = self.set_requirements(course_id, group_id)

        return self.return_data(data, userid)

    def set_requirements(self, course_id, group_id):
        """ VALIDATE TABLES """


        # VALIDATE COURSE TABLE
        sql_str = "SELECT * FROM group_course_requirements WHERE"
        sql_str += " course_id='{0}'".format(course_id)
        sql_str += " AND user_group_id='{0}'".format(group_id)

        # VALIDATE COURSE TABLE
        if not self.postgres.query_fetch_one(sql_str):

            # INSERT REQUIREMENTS (COURSE TABLE)
            temp = {}
            temp['group_course_requirement_id'] =  self.sha_security.generate_token(False)
            temp['user_group_id'] = group_id
            temp['course_id'] = course_id
            temp['completion'] = 80
            temp['grade_locking'] = False
            temp['on_previous'] = False
            temp['is_lock'] = False
            temp['is_visible'] = True
            temp['created_on'] = time.time()
            self.postgres.insert('group_course_requirements', temp)

        # CHECK SECTION TABLE
        sql_str = "SELECT * FROM section WHERE"
        sql_str += " course_id='{0}'".format(course_id)
        sections = self.postgres.query_fetch_all(sql_str)
        
        # EACH SECTION
        for section in sections:

            # VALIDATE SECTION TABLE
            sql_str = "SELECT * FROM group_section_requirements WHERE"
            sql_str += " section_id='{0}'".format(section['section_id'])
            sql_str += " AND user_group_id='{0}'".format(group_id)
            req = self.postgres.query_fetch_one(sql_str)

            # CONDITION FOR QUERY
            conditions = []
            conditions.append({
                "col": "group_section_requirement_id",
                "con": "=",
                "val": req['group_section_requirement_id']
            })

            temp = {}
            temp['grade_locking'] = False
            temp['on_previous'] = False
            if section['difficulty_level'] > 1:
                temp['grade_locking'] = True
                temp['on_previous'] = True
            temp['is_lock'] = False
            temp['is_visible'] = True
            temp['update_on'] = time.time()
            self.postgres.update('group_section_requirements', temp, conditions)

        # CHECK SUBSECTION TABLE
        sql_str = "SELECT *, s.difficulty_level as secdiff, ss.difficulty_level as subdiff"
        sql_str += " FROM subsection ss LEFT JOIN section s ON ss.section_id = s.section_id WHERE"
        sql_str += " ss.course_id='{0}'".format(course_id)
        subsections = self.postgres.query_fetch_all(sql_str)
        
        # EACH SUBSECTION
        for subsection in subsections:

            # VALIDATE SUBSECTION TABLE
            sql_str = "SELECT * FROM group_subsection_requirements WHERE"
            sql_str += " subsection_id='{0}'".format(subsection['subsection_id'])
            sql_str += " AND user_group_id='{0}'".format(group_id)
            req = self.postgres.query_fetch_one(sql_str)

            # CONDITION FOR QUERY
            conditions = []
            conditions.append({
                "col": "group_subsection_requirement_id",
                "con": "=",
                "val": req['group_subsection_requirement_id']
            })

            temp = {}
            temp['completion'] = 80
            temp['grade_locking'] = True
            temp['on_previous'] = True
            if subsection['secdiff'] == 1 and subsection['subdiff'] == 1:
                temp['grade_locking'] = False
                temp['on_previous'] = False

            temp['is_lock'] = False
            temp['is_visible'] = True
            temp['update_on'] = time.time()
            self.postgres.update('group_subsection_requirements', temp, conditions)

        # CHECK EXERCISE TABLE
        sql_str = "SELECT *, s.difficulty_level as secdiff, ss.difficulty_level as subdiff"
        sql_str += " FROM exercise e LEFT JOIN subsection ss ON e.subsection_id"
        sql_str += " = ss.subsection_id LEFT JOIN section s ON ss.section_id = s.section_id"
        sql_str += " WHERE e.course_id='{0}'".format(course_id)
        exercises = self.postgres.query_fetch_all(sql_str)

        # EACH EXERCISE
        for exercise in exercises:

            # VALIDATE EXERCISE TABLE
            sql_str = "SELECT * FROM group_exercise_requirements WHERE"
            sql_str += " exercise_id='{0}'".format(exercise['exercise_id'])
            sql_str += " AND user_group_id='{0}'".format(group_id)
            req = self.postgres.query_fetch_one(sql_str)

            # CONDITION FOR QUERY
            conditions = []
            conditions.append({
                "col": "group_exercise_requirement_id",
                "con": "=",
                "val": req['group_exercise_requirement_id']
            })

            temp = {}
            temp['completion'] = 80

            temp['grade_locking'] = True
            temp['on_previous'] = True
    
            if exercise['subdiff'] == 1 and int(exercise['exercise_number']) == 1 \
                and exercise['secdiff'] == 1:
                temp['grade_locking'] = False
                temp['on_previous'] = False

            temp['is_lock'] = False
            temp['is_visible'] = True
            temp['update_on'] = time.time()
            self.postgres.update('group_exercise_requirements', temp, conditions)

        # GET ALL DATA FROM COURSE TO EXERCISES

        sql_str = "SELECT c.course_id, c.course_name, gcr.group_course_requirement_id,"
        sql_str += " gcr.user_group_id, gcr.completion, gcr.grade_locking, gcr.on_previous, gcr.is_lock,"
        sql_str += " gcr.is_visible, (SELECT array_to_json(array_agg(sections))"
        sql_str += " FROM (SELECT s.section_id, s.section_name,"
        sql_str += " gsr.group_section_requirement_id, gsr.user_group_id, gsr.completion,"
        sql_str += " gsr.grade_locking, gsr.on_previous, gsr.is_lock, gsr.is_visible,"
        sql_str += " (SELECT array_to_json(array_agg(subsections)) FROM"
        sql_str += " (SELECT ss.subsection_id, ss.subsection_name,"
        sql_str += " gssr.group_subsection_requirement_id, gssr.user_group_id,"
        sql_str += " gssr.completion, gssr.grade_locking, gssr.on_previous, gssr.is_lock, gssr.is_visible,"
        sql_str += " (SELECT array_to_json(array_agg(exercises)) FROM"
        sql_str += " (SELECT e.exercise_id, e.exercise_number,"
        sql_str += " ger.group_exercise_requirement_id, ger.user_group_id, ger.completion,"
        sql_str += " ger.grade_locking, ger.on_previous, ger.is_lock, ger.is_visible FROM exercise e"
        sql_str += " INNER JOIN group_exercise_requirements ger ON"
        sql_str += " ss.subsection_id=e.subsection_id AND e.exercise_id=ger.exercise_id AND"
        sql_str += " ger.user_group_id=gcr.user_group_id) AS exercises) AS exercises"
        sql_str += " FROM subsection ss INNER JOIN group_subsection_requirements gssr ON"
        sql_str += " ss.section_id=s.section_id AND ss.subsection_id=gssr.subsection_id AND"
        sql_str += " gssr.user_group_id=gcr.user_group_id) AS subsections) AS subsections"
        sql_str += " FROM section s INNER JOIN group_section_requirements gsr ON"
        sql_str += " c.course_id=s.course_id AND s.section_id=gsr.section_id AND"
        sql_str += " gsr.user_group_id=gcr.user_group_id) AS sections) AS sections"
        sql_str += " FROM course c INNER JOIN group_course_requirements gcr ON"
        sql_str += " c.course_id=gcr.course_id AND"
        sql_str += " gcr.user_group_id='{0}'".format(group_id)
        sql_str += " WHERE c.course_id='{0}'".format(course_id)

        course_data = self.postgres.query_fetch_one(sql_str)

        return course_data
