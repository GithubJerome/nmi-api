# pylint: disable=no-self-use, too-many-function-args
"""Quick Start"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class QuickStart(Common):
    """Class for QuickStart"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for QuickStart class"""
        self.postgresql_query = PostgreSQL()
        super(QuickStart, self).__init__()

    def quick_start(self):
        """
        This API is for Quick Start
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

        responses:
          500:
            description: Error
          200:
            description: Quick Start
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        data['data'] = self.get_started(userid)
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def get_started(self, user_id):
        """ RETURN QUICK START """

        sql_str = "SELECT * FROM student_course sc"
        sql_str += " LEFT JOIN course c ON sc.course_id = c.course_id"
        sql_str += " LEFT JOIN student_section ss ON c.course_id = ss.course_id"
        sql_str += " LEFT JOIN section s ON ss.section_id = s.section_id"
        sql_str += " LEFT JOIN student_subsection ssub ON ss.section_id = ssub.section_id"
        sql_str += " LEFT JOIN subsection sub ON ssub.subsection_id = sub.subsection_id"
        sql_str += " LEFT JOIN exercise e ON ssub.subsection_id = e.subsection_id"
        sql_str += " LEFT JOIN student_exercise se ON e.exercise_id = se.exercise_id"
        sql_str += " WHERE sc.account_id = '{0}' AND ss.account_id ='{0}'".format(user_id)
        sql_str += " AND se.account_id = '{0}' AND ssub.account_id = '{0}'".format(user_id)
        sql_str += " AND ssub.status is True AND ss.status is True AND se.status is True"
        sql_str += " AND (se.progress IS NULL OR se.progress != '100') ORDER BY c.difficulty_level,"
        sql_str += " s.difficulty_level, sub.difficulty_level, e.exercise_number LIMIT 1"
        course_result = self.postgres.query_fetch_one(sql_str)

        data = {}

        if course_result:
            course_exercise = self.get_exercise_hierarchy(course_result['course_id'])
            exercises  = ','.join("'{0}'".format(res['exercise_id']) for res in course_exercise)

            sql_str = "SELECT * FROM student_exercise WHERE account_id='{0}' AND status is True".format(user_id)
            sql_str += " AND course_id = '{0}' AND exercise_id IN ({1})".format(course_result['course_id'], exercises)
            results = self.postgres.query_fetch_all(sql_str)

            student_exercise = [res['exercise_id'] for res in results]

            for result in course_exercise:

                try:
                    
                    index = student_exercise.index(result['exercise_id'])
                    progress = results[index]['progress']
                    
                    if progress == '100':
                        continue

                    result['course_name'] = self.translate(user_id, course_result['course_name'])
                    if course_result['course_title']:
                        result['course_name'] = self.translate(user_id, course_result['course_title'])

                    translate_exercise = self.translate(user_id, "Exercise")
                    exercise = "{0} - {1} - {2} - {3} {4}".format(result['course_name'],
                                                                  result['section_name'],
                                                                  result['subsection_name'],
                                                                  translate_exercise,
                                                                  result['exercise_number'])

                    data['exercise_id'] = result['exercise_id']
                    data['course_id'] = course_result['course_id']
                    data['exercise'] = exercise
                    data['is_unlocked'] = results[index]['is_unlocked']

                    break

                except ValueError:
                    pass
            
        return data
