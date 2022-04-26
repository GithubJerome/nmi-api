"""Course Requirements"""
import time

from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity

class CourseVideos(Common):
    """Class for CourseVideos"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CourseVideos class"""
        self.sha_security = ShaSecurity()
        super(CourseVideos, self).__init__()

    def course_videos(self):
        """
        This API is for Getting all Course Videos
        ---
        tags:
          - Video
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
            description: Course Videos
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
        data['data'] = self.get_course_videos(course_id)

        return self.return_data(data, userid)

    def get_course_videos(self, course_id):
        """ Return All videos inside course """

        sql_str = """SELECT c.course_id as key, c.course_id, c.course_name, c.course_title,
                    c.exercise_name, (SELECT array_to_json(array_agg(sections))
                    FROM (SELECT s.section_id, s.section_name, s.section_id as key, (SELECT
                    array_to_json(array_agg(subsections)) FROM (SELECT ss.subsection_id,
                    ss.subsection_name, ss.subsection_id as key, (SELECT array_to_json(array_agg(videos))
                    FROM (SELECT * FROM video_subsection vsub LEFT JOIN videos v ON
                    vsub.video_id = v.video_id WHERE vsub.subsection_id = ss.subsection_id) videos) as
                    videos, (SELECT array_to_json(array_agg(exercises)) FROM (SELECT e.exercise_id,
                    e.exercise_number, CASE WHEN c.exercise_name is null OR c.exercise_name = '' then
                    'Exercise '||e.exercise_number else CONCAT(c.exercise_name, ' ')||e.exercise_number end as exercise_num,
                    e.exercise_id as key, (SELECT array_to_json(array_agg(videos))
                    FROM (SELECT * FROM video_exercise ve INNER JOIN videos v ON ve.video_id =
                    v.video_id WHERE ve.exercise_id = e.exercise_id) videos) as videos FROM exercise e
                    WHERE e.subsection_id = ss.subsection_id ORDER BY e.exercise_number ASC) AS exercises)
                    AS exercises FROM subsection ss  WHERE ss.section_id = s.section_id
                    ORDER BY ss.difficulty_level ASC) AS subsections) AS subsections FROM section s
                    WHERE s.course_id = c.course_id ORDER BY s.difficulty_level ASC) AS sections)
                    AS sections FROM course c"""
        sql_str += " WHERE course_id = '{0}'".format(course_id)

        course_data = self.postgres.query_fetch_one(sql_str)

        return course_data
