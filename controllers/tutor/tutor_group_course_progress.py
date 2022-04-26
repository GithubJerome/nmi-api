"""Tutor Student Course progress"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class TutorGroupCourseProgress(Common):
    """Class for TutorGroupCourseProgress"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for TutorGroupCourseProgress class"""
        self.postgresql_query = PostgreSQL()
        super(TutorGroupCourseProgress, self).__init__()

    def tutor_group_course_progress(self):
        """
        This API is for Getting Group Progress by Course
        ---
        tags:
          - Tutor
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
          - name: group_id
            in: query
            description: Group ID
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
            description: Group Progress
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

        datas = self.get_gc_progress(group_id, course_id, userid)
        if not datas:
            data["alert"] = "No Data Found"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        datas['status'] = 'ok'

        return self.return_data(datas, userid)


    def get_gc_progress(self, group_id, course_id, userid):
        """ RETURN GROUP COURSE PROGRESS """

        sql_str = "SELECT * FROM user_group_master"
        sql_str += " WHERE user_group_id IN"
        sql_str += " (SELECT user_group_id FROM"
        sql_str += " user_group_tutors WHERE"
        sql_str += " tutor_id='{0}') AND user_group_id = '{1}'".format(userid, group_id)
        results = self.postgres.query_fetch_one(sql_str)

        if not results:
            return 0

        exercises = []
        all_exercise = []
        if results['courses']:
            courses = [result['course_id'] for result in results['courses']]
            if course_id in courses:
                all_exercise = self.get_exercise_hierarchy(course_id)
                
                for exercise in all_exercise:
                    exercises.append({"exercise_number": exercise['exercise'], "exercise_id": exercise['exercise_id']})

        group_progress = []
        if results['students']:
            students = [res['student_id'] for res in results['students']]
            students = ','.join("'{0}'".format(student) for student in students)

            # GET ALL EXERCISES
            sql_str = """SELECT a.id as key, a.id, a.first_name, a.last_name, (SELECT array_to_json(array_agg(exercises))
                        AS exercises FROM (SELECT se.exercise_id, se.percent_score, e.passing_criterium, se.score FROM
                        student_course sc LEFT JOIN course c ON sc.course_id = c.course_id 
                        LEFT JOIN student_section ss ON c.course_id = ss.course_id
                        LEFT JOIN section s ON ss.section_id = s.section_id
                        LEFT JOIN student_subsection ssub ON ss.section_id = ssub.section_id
                        LEFT JOIN subsection sub ON ssub.subsection_id = sub.subsection_id
                        LEFT JOIN exercise e ON ssub.subsection_id = e.subsection_id
                        LEFT JOIN student_exercise se ON e.exercise_id = se.exercise_id WHERE
                        ssub.status is True AND ss.status is True AND se.status is True
                        AND sc.account_id = a.id AND ss.account_id = a.id 
                        AND se.account_id = a.id AND ssub.account_id = a.id
                        ORDER BY c.difficulty_level, s.difficulty_level, sub.difficulty_level, e.exercise_number) AS exercises)"""
            sql_str += " FROM account a WHERE a.id IN ({0})".format(students)

            group_progress = self.postgres.query_fetch_all(sql_str)



            for result in group_progress:
                result['exercises'] = self.assess_exercise(all_exercise, result['exercises'])


        data = {}
        data['data'] = group_progress
        data['exercises'] = exercises

        return data

    def assess_exercise(self, all_exercise, student_exercise):
        """ Evaluate Exercise """

        exercises = []
        if student_exercise:
            exercises = [exercise['exercise_id'] for exercise in student_exercise]

        data = []
        score = 0
        for exercise in all_exercise:

            try:

                index = exercises.index(exercise['exercise_id'])
                score = student_exercise[index]['score']
                passing_score = student_exercise[index]['passing_criterium']

                status = "failed"
                if score and score >= passing_score:
                    status = "passed"

                if score is None:
                    status = "unanswered"

            except ValueError:
                status = "unanswered"

            tmp = {}
            tmp['score'] = score
            tmp['status'] = status
            tmp['exercise_id'] = exercise['exercise_id']
            tmp['exercise_number'] = exercise['exercise']
            data.append(tmp)

        return data
