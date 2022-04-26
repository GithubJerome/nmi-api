"""Update Course Requirements"""
import time

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.emailer import Email
from library.progress import Progress

class UpdateTutorCourseRequirements(Common, ShaSecurity):
    """Class for UpdateTutorCourseRequirements"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateTutorCourseRequirements class"""

        # self.postgres = PostgreSQL()
        self.progress = Progress()
        self.sha_security = ShaSecurity()
        super(UpdateTutorCourseRequirements, self).__init__()

    def update_tutor_course_requirements(self):
        """
        This API is for Updating Tutor Course requirements
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
          - name: query
            in: body
            description: Updating Tutor Course requirements
            required: true
            schema:
              id: Update Updating Tutor Course requirements
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

        if not self.apply_updates(token, userid, query_json):

            data["alert"] = "Invalid Data!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)


        data = {}
        data['message'] = "Course requirements successfully updated"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def apply_updates(self, token, userid, datas):
        """ APPLY UPDATES """

        # COURSE
        course = datas['data']

        if not course:

            return 0

        course_id = course['course_id']

        sql_str = "SELECT student_id FROM user_group_students"
        sql_str += " WHERE user_group_id IN (SELECT user_group_id"
        sql_str += " FROM user_group_courses WHERE"
        sql_str += " course_id='{0}')".format(course_id)
        user_group_students = self.postgres.query_fetch_all(sql_str)

        student_ids1 = [ugstud['student_id'] for ugstud in user_group_students or []]

        sql_str = "SELECT account_id FROM student_course WHERE"
        sql_str += " course_id='{0}'".format(course_id)
        sql_str += " AND NOT account_id IN (SELECT student_id"
        sql_str += " FROM user_group_students WHERE user_group_id IN"
        sql_str += " (SELECT user_group_id FROM user_group_courses WHERE"
        sql_str += " course_id='{0}'))".format(course_id)
        student_course = self.postgres.query_fetch_all(sql_str)
        student_ids2 = [ugstud1['account_id'] for ugstud1 in student_course or []]

        student_ids = student_ids1 + student_ids2
        s_ids = ','.join("'{0}'".format(selected) for selected in student_ids or [])

        # INIT CONDITION
        conditions = []

        # CONDITION FOR QUERY
        conditions.append({
            "col": "course_requirement_id",
            "con": "=",
            "val": course['course_requirement_id']
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

        if 'is_repeatable' in course.keys():

            ucourse['is_repeatable'] = course['is_repeatable']

        self.postgres.update('course_requirements', ucourse, conditions)

        # SECTION
        for section in course['sections']:

            # INIT CONDITION
            conditions = []

            # CONDITION FOR QUERY
            conditions.append({
                "col": "section_requirement_id",
                "con": "=",
                "val": section['section_requirement_id']
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

            if 'is_repeatable' in section.keys():

                usection['is_repeatable'] = section['is_repeatable']

            self.postgres.update('section_requirements', usection, conditions)

            # UNLOCK STUDENTS
            # GET ALL SECTION REQUIREMENTS
            sql_str = "SELECT * FROM section_requirements WHERE"
            sql_str += " section_requirement_id='{0}'".format(section['section_requirement_id'])
            sec_req = self.postgres.query_fetch_one(sql_str)

            sec_conditions = []
            sec_conditions.append({
                "col": "section_id",
                "con": "=",
                "val": section['section_id']
            })

            # CHECK CONDITION
            if sec_req['is_lock']:

                sql_str = "SELECT DISTINCT account_id FROM student_section WHERE is_unlocked=True"
                sql_str += " AND section_id='{0}'".format(section['section_id'])
                sql_str += " AND account_id IN ({0})".format(s_ids)
                res = self.postgres.query_fetch_all(sql_str)

                if res:

                    account_ids = [act['account_id'] for act in res]

                    sec_conditions.append({
                        "col": "account_id",
                        "con": "in",
                        "val": account_ids
                    })

                    # LOCK ALL STUDENT
                    data = {}
                    data['is_unlocked'] = False
                    data['unlock_criteria'] = "hierarchy"
                    data['unlocked_on'] = time.time()

                    self.postgres.update('student_section', data, sec_conditions)

                    for account_id in account_ids:

                        self.send_notif(userid, token, account_id, "One of your section is Lock!", "Lock Section", "Lock Section")

            elif not sec_req['grade_locking'] and not sec_req['is_lock']:

                sql_str = "SELECT DISTINCT account_id FROM student_section WHERE is_unlocked=False"
                sql_str += " AND section_id='{0}'".format(section['section_id'])
                sql_str += " AND account_id IN ({0})".format(s_ids)
                res = self.postgres.query_fetch_all(sql_str)

                if res:

                    account_ids = [act['account_id'] for act in res]

                    sec_conditions.append({
                        "col": "account_id",
                        "con": "in",
                        "val": account_ids
                    })

                    # UNLOCK ALL STUDENT
                    data = {}
                    data['is_unlocked'] = True
                    data['unlock_criteria'] = "hierarchy"
                    data['unlocked_on'] = time.time()

                    self.postgres.update('student_section', data, sec_conditions)

                    for account_id in account_ids:

                        self.send_notif(userid, token, account_id, "You have new Section!", "New Section", "New Section")

            # SUBSECTION
            if not 'subsections' in section.keys():

                continue

            if not section['subsections']:

                continue

            for subsection in section['subsections']:

                # INIT CONDITION
                conditions = []

                # CONDITION FOR QUERY
                conditions.append({
                    "col": "subsection_requirement_id",
                    "con": "=",
                    "val": subsection['subsection_requirement_id']
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

                if 'is_repeatable' in subsection.keys():

                    usubsection['is_repeatable'] = subsection['is_repeatable']

                self.postgres.update('subsection_requirements', usubsection, conditions)

                # UNLOCK STUDENTS
                # GET ALL SUBSECTION REQUIREMENTS
                sql_str = "SELECT * FROM subsection_requirements WHERE"
                sql_str += " subsection_requirement_id='{0}'".format(subsection['subsection_requirement_id'])
                subsec_req = self.postgres.query_fetch_one(sql_str)

                subsec_conditions = []
                subsec_conditions.append({
                    "col": "subsection_id",
                    "con": "=",
                    "val": subsection['subsection_id']
                })

                # CHECK CONDITION
                if subsec_req['is_lock']:

                    # LOCK ALL STUDENT
                    sql_str = "SELECT DISTINCT account_id FROM student_subsection WHERE is_unlocked=True"
                    sql_str += " AND subsection_id='{0}'".format(subsection['subsection_id'])
                    sql_str += " AND account_id IN ({0})".format(s_ids)
                    res = self.postgres.query_fetch_all(sql_str)

                    if res:

                        account_ids = [act['account_id'] for act in res]

                        subsec_conditions.append({
                            "col": "account_id",
                            "con": "in",
                            "val": account_ids
                        })

                        data = {}
                        data['is_unlocked'] = False
                        data['unlock_criteria'] = "hierarchy"
                        data['unlocked_on'] = time.time()

                        self.postgres.update('student_subsection', data, subsec_conditions)

                        for account_id in account_ids:

                            self.send_notif(userid, token, account_id, "One of your subsection is Lock!", "Lock Subsection", "Lock Subsection")

                elif not subsec_req['grade_locking'] and not subsec_req['is_lock']:

                    # UNLOCK ALL STUDENT
                    sql_str = "SELECT DISTINCT account_id FROM student_subsection WHERE is_unlocked=False"
                    sql_str += " AND subsection_id='{0}'".format(subsection['subsection_id'])
                    sql_str += " AND account_id IN ({0})".format(s_ids)
                    res = self.postgres.query_fetch_all(sql_str)

                    if res:

                        account_ids = [act['account_id'] for act in res]

                        subsec_conditions.append({
                            "col": "account_id",
                            "con": "in",
                            "val": account_ids
                        })

                        data = {}
                        data['is_unlocked'] = True
                        data['unlock_criteria'] = "hierarchy"
                        data['unlocked_on'] = time.time()

                        self.postgres.update('student_subsection', data, subsec_conditions)

                        for account_id in account_ids:

                            self.send_notif(userid, token, account_id, "You have new Subsection!", "New Subsection", "New Subsection")

                # EXERCISE
                if not 'exercises' in subsection.keys():

                    continue

                for exercise in subsection['exercises'] or []:

                    # INIT CONDITION
                    conditions = []

                    # CONDITION FOR QUERY
                    conditions.append({
                        "col": "exercise_requirement_id",
                        "con": "=",
                        "val": exercise['exercise_requirement_id']
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

                    self.postgres.update('exercise_requirements', uexercise, conditions)

                    # UPDATE EXERCISE IS REPEATABLE
                    if 'is_repeatable' in exercise.keys():
                        exercise_condition = []
                        exercise_condition.append({
                            "col": "exercise_id",
                            "con": "=",
                            "val": exercise['exercise_id']
                        })
                        tmp = {}
                        tmp['is_repeatable'] = exercise['is_repeatable']
                        self.postgres.update('exercise', tmp, exercise_condition)

                    # UNLOCK STUDENTS
                    # GET ALL EXERCISE REQUIREMENTS
                    sql_str = "SELECT * FROM exercise_requirements WHERE"
                    sql_str += " exercise_requirement_id='{0}'".format(exercise['exercise_requirement_id'])
                    ex_req = self.postgres.query_fetch_one(sql_str)

                    exercise_id = exercise['exercise_id']
                    ex_conditions = []
                    ex_conditions.append({
                        "col": "exercise_id",
                        "con": "=",
                        "val": exercise_id
                    })

                    # CHECK CONDITION
                    if ex_req['is_lock']:

                        # LOCK ALL STUDENT
                        sql_str = "SELECT DISTINCT account_id FROM student_exercise WHERE is_unlocked=True"
                        sql_str += " AND exercise_id='{0}'".format(exercise_id)
                        sql_str += " AND account_id IN ({0})".format(s_ids)
                        res = self.postgres.query_fetch_all(sql_str)

                        if res:

                            account_ids = [act['account_id'] for act in res]

                            ex_conditions.append({
                                "col": "account_id",
                                "con": "in",
                                "val": account_ids
                            })

                            data = {}
                            data['is_unlocked'] = False
                            data['unlock_criteria'] = "hierarchy"
                            data['unlocked_on'] = time.time()

                            self.postgres.update('student_exercise', data, ex_conditions)

                            for account_id in account_ids:

                                self.send_notif(userid, token, account_id, "One of your exercise is Lock!", "Lock Exercise", "Lock Exercise")

                    elif not ex_req['grade_locking'] and not ex_req['is_lock']:

                        # UNLOCK ALL STUDENT
                        sql_str = "SELECT DISTINCT account_id FROM student_exercise WHERE is_unlocked=False"
                        sql_str += " AND exercise_id='{0}'".format(exercise_id)
                        sql_str += " AND account_id IN ({0})".format(s_ids)
                        res = self.postgres.query_fetch_all(sql_str)

                        if res:

                            account_ids = [act['account_id'] for act in res]

                            ex_conditions.append({
                                "col": "account_id",
                                "con": "in",
                                "val": account_ids
                            })

                            data = {}
                            data['is_unlocked'] = True
                            data['unlock_criteria'] = "hierarchy"
                            data['unlocked_on'] = time.time()

                            self.postgres.update('student_exercise', data, ex_conditions)

                            for account_id in account_ids:

                                self.send_notif(userid, token, account_id, "You have new Exercise!", "New Exercise", "New Exercise")

                    elif not ex_req['is_lock'] and ex_req['grade_locking']:

                        # UNLOCK ALL STUDENT
                        sql_str = "SELECT DISTINCT account_id FROM student_exercise"
                        sql_str += " WHERE exercise_id='{0}'".format(exercise_id)
                        sql_str += " AND account_id IN ({0})".format(s_ids)
                        res = self.postgres.query_fetch_all(sql_str)

                        if res:

                            # CHECK GRADE REQUIREMENTS
                            course_id = course['course_id']
                            account_ids = [act['account_id'] for act in res]
                            user_to_lock = self.check_prev_grade(account_ids, course_id, exercise_id, token)

                            if user_to_lock:
                                ex_conditions.append({
                                    "col": "account_id",
                                    "con": "in",
                                    "val": user_to_lock
                                })

                                data = {}
                                data['is_unlocked'] = False
                                data['unlock_criteria'] = "hierarchy"
                                data['unlocked_on'] = time.time()

                                self.postgres.update('student_exercise', data, ex_conditions)

                                for account_id in user_to_lock:

                                    self.send_notif(userid, token, account_id, "One of your exercise is Lock!", "Lock Exercise", "Lock Exercise")

        return 1

    def check_prev_grade(self, user_ids, course_id, exercise_id, token):
        """ Unlock if Grade Requirements met """

        user_to_lock = []
        # sql_str = "SELECT * FROM exercise e INNER JOIN subsection ss"
        # sql_str += " ON e.subsection_id=ss.subsection_id INNER JOIN section s ON"
        # sql_str += " e.section_id=s.section_id WHERE e.course_id='{0}'".format(course_id)
        # sql_str += " ORDER BY ss.difficulty_level ASC, s.difficulty_level ASC"
        sql_str = "SELECT * FROM exercise e INNER JOIN subsection ss"
        sql_str += " ON e.subsection_id=ss.subsection_id INNER JOIN"
        sql_str += " section s ON e.section_id=s.section_id WHERE"
        sql_str += " e.course_id='{0}'".format(course_id)
        sql_str += " ORDER BY s.difficulty_level ASC,"
        sql_str += " ss.difficulty_level ASC, e.exercise_number ASC"
        result = self.postgres.query_fetch_all(sql_str)

        if not result:
            return user_to_lock

        exercise_ids = [res['exercise_id'] for res in result]

        try:
            index = exercise_ids.index(exercise_id)

            # SELECT PREVIOUS EXERCISE
            if index == 0:
                return user_to_lock

            prev_exercise = result[index-1]['exercise_id']
            passing_criterium = result[index-1]['passing_criterium']

            # CHECK GRADE REQUIREMENTS
            for user_id in user_ids:

                sql_str = "SELECT exercise_id FROM student_exercise_repeat WHERE"
                sql_str += " course_id='{0}'".format(course_id)
                sql_str += " AND account_id='{0}'".format(user_id)
                sql_str += " AND is_passed=true"
                pass_exs = self.postgres.query_fetch_all(sql_str)

                passed_repeat_exercise_ids = [pex['exercise_id'] for pex in pass_exs or []]

                sql_str = "SELECT * FROM student_exercise WHERE status is True AND"
                sql_str += " exercise_id = '{0}'".format(prev_exercise)
                sql_str += " AND account_id = '{0}'".format(user_id)
                exercise = self.postgres.query_fetch_one(sql_str)

                if exercise and exercise['score'] is not None and exercise['score'] >= passing_criterium:

                    # UPDATE UNLOCK
                    # conditions = []
                    # conditions.append({
                    #     "col": "student_exercise_id",
                    #     "con": "=",
                    #     "val": exercise['student_exercise_id']
                    # })
                    conditions = []
                    conditions.append({
                        "col": "status",
                        "con": "=",
                        "val": True
                    })

                    conditions.append({
                        "col": "exercise_id",
                        "con": "=",
                        "val": exercise_id
                    })

                    conditions.append({
                        "col": "account_id",
                        "con": "=",
                        "val": user_id
                    })

                    # UPDATE
                    data = {}
                    data['is_unlocked'] = True
                    data['unlock_criteria'] = "hierarchy"
                    data['unlocked_on'] = time.time()

                    self.postgres.update('student_exercise', data, conditions)

                    if user_id and token:

                        self.send_notif(user_id, token, user_id, "You have new Exercise!", "New Exercise", "New Exercise")

                elif prev_exercise in passed_repeat_exercise_ids:

                    conditions = []
                    conditions.append({
                        "col": "status",
                        "con": "=",
                        "val": True
                    })

                    conditions.append({
                        "col": "exercise_id",
                        "con": "=",
                        "val": exercise_id
                    })

                    conditions.append({
                        "col": "account_id",
                        "con": "=",
                        "val": user_id
                    })

                    # UPDATE
                    data = {}
                    data['is_unlocked'] = True
                    data['unlock_criteria'] = "hierarchy"
                    data['unlocked_on'] = time.time()

                    self.postgres.update('student_exercise', data, conditions)

                else:

                    user_to_lock.append(user_id)

        except:

            pass

        return user_to_lock
