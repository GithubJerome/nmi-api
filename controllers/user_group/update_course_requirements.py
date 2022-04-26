"""Update Course Requirements"""
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.emailer import Email
from library.progress import Progress

class UpdateCourseRequirements(Common, ShaSecurity):
    """Class for UpdateCourseRequirements"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateCourseRequirements class"""

        # self.postgres = PostgreSQL()
        self.progress = Progress()
        self.sha_security = ShaSecurity()
        super(UpdateCourseRequirements, self).__init__()

    def update_course_requirements(self):
        """
        This API is for Updating Course requirements
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
          - name: query
            in: body
            description: Updating Course requirements
            required: true
            schema:
              id: Update Updating Course requirements
              properties:
                data:
                    types: object
                    example: {}
        responses:
          500:
            description: Error
          200:
            description: Update User
        """

        # INIT DATA
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

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

        if not self.apply_updates(query_json):

            data["alert"] = "Invalid Data!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)


        data = {}
        data['message'] = "Course requirements successfully updated"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def apply_updates(self, datas):
        """ APPLY UPDATES """

        course = datas['data']

        if not course:

            return 0

        # INIT CONDITION
        conditions = []

        # CONDITION FOR QUERY
        conditions.append({
            "col": "group_course_requirement_id",
            "con": "=",
            "val": course['group_course_requirement_id']
            })

        ucourse = {}
        if 'completion' in course.keys():

            ucourse['completion'] = str(course['completion'])

        if 'grade_locking' in course.keys():

            ucourse['grade_locking'] = course['grade_locking']

        if 'is_lock' in course.keys():

            ucourse['is_lock'] = course['is_lock']

        if 'is_visible' in course.keys():

            ucourse['is_visible'] = course['is_visible']

        if 'on_previous' in course.keys():

            ucourse['on_previous'] = course['on_previous']

        self.postgres.update('group_course_requirements', ucourse, conditions)

        for section in course['sections']:

            # INIT CONDITION
            conditions = []

            # CONDITION FOR QUERY
            conditions.append({
                "col": "group_section_requirement_id",
                "con": "=",
                "val": section['group_section_requirement_id']
                })

            usection = {}
            if 'completion' in section.keys():

                usection['completion'] = str(section['completion'])

            if 'grade_locking' in section.keys():

                usection['grade_locking'] = section['grade_locking']

            if 'is_lock' in section.keys():

                usection['is_lock'] = section['is_lock']

            if 'is_visible' in section.keys():

                usection['is_visible'] = section['is_visible']

            if 'on_previous' in section.keys():

                usection['on_previous'] = section['on_previous']

            self.postgres.update('group_section_requirements', usection, conditions)

            if not 'subsections' in section.keys():

                continue

            for subsection in section['subsections']:

                # INIT CONDITION
                conditions = []

                # CONDITION FOR QUERY
                conditions.append({
                    "col": "group_subsection_requirement_id",
                    "con": "=",
                    "val": subsection['group_subsection_requirement_id']
                    })

                usubsection = {}
                if 'completion' in subsection.keys():

                    usubsection['completion'] = str(subsection['completion'])

                if 'grade_locking' in subsection.keys():

                    usubsection['grade_locking'] = subsection['grade_locking']

                if 'is_lock' in subsection.keys():

                    usubsection['is_lock'] = subsection['is_lock']

                if 'is_visible' in subsection.keys():

                    usubsection['is_visible'] = subsection['is_visible']

                if 'on_previous' in subsection.keys():

                    usubsection['on_previous'] = subsection['on_previous']

                self.postgres.update('group_subsection_requirements', usubsection, conditions)

                if not 'exercises' in subsection.keys():

                    continue

                for exercise in subsection['exercises']:

                    # INIT CONDITION
                    conditions = []

                    # CONDITION FOR QUERY
                    conditions.append({
                        "col": "group_exercise_requirement_id",
                        "con": "=",
                        "val": exercise['group_exercise_requirement_id']
                        })

                    uexercise = {}
                    if 'completion' in exercise.keys():

                        uexercise['completion'] = str(exercise['completion'])

                    if 'grade_locking' in exercise.keys():

                        uexercise['grade_locking'] = exercise['grade_locking']

                    if 'is_lock' in exercise.keys():

                        uexercise['is_lock'] = exercise['is_lock']

                    if 'is_visible' in exercise.keys():

                        uexercise['is_visible'] = exercise['is_visible']

                    if 'on_previous' in exercise.keys():

                        uexercise['on_previous'] = exercise['on_previous']

                    self.postgres.update('group_exercise_requirements', uexercise, conditions)

        return 1
