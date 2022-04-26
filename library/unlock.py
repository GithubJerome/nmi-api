# pylint: disable=too-many-arguments, no-self-use, too-many-locals
""" Unlock """
import random
import json
import time
import math

from library.postgresql_queries import PostgreSQL
from library.common import Common
from library.sha_security import ShaSecurity
from library.questions import Questions

class Unlock(Common):
    """Class for Questions"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Unlock class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        self.questionnaires = Questions()
        super(Unlock, self).__init__()

    def unlock_next(self, user_id, token, exercise_id, in_group):
        """ Unlock """

        self.unlock_next_exercise(user_id, token, exercise_id, in_group=in_group)
        self.unlock_next_subsection(user_id, token, exercise_id, in_group=in_group)
        self.unlock_next_section(user_id, token, exercise_id, in_group=in_group)
        # self.unlock_next_course(user_id, token, exercise_id)

        return 1

    def generate_course_set(self, user_id, course_id):
        """ Return Course Set """

        sql_str = "SELECT sc.course_id, s.section_id, ss.subsection_id, e.exercise_id"
        sql_str += " FROM student_course sc LEFT JOIN section s ON sc.course_id = s.course_id"
        sql_str += " LEFT JOIN subsection ss ON s.section_id = ss.section_id"
        sql_str += " LEFT JOIN exercise e ON ss.subsection_id = e.subsection_id"
        sql_str += " WHERE sc.course_id = '{0}'".format(course_id)
        sql_str += " AND account_id = '{0}'".format(user_id)
        sql_str += " AND exercise_id NOT IN (SELECT exercise_id FROM student_exercise"
        sql_str += " WHERE account_id = '{0}')".format(user_id)
        sql_str += " GROUP BY sc.course_id, s.section_id, ss.subsection_id, e.exercise_id"
        results = self.postgres.query_fetch_all(sql_str)

        if results:
            sections = set(result['section_id'] for result in results)
            subsections = set(result['subsection_id'] for result in results)
            exercises = set(result['exercise_id'] for result in results)

            # ADD DATA TO STUDENT SECTION TABLE
            self.add_student_section(user_id, course_id, sections)

            # ADD DATA TO STUDENT SUBSECTION TABLE
            self.add_student_subsection(user_id, course_id, subsections)

            for exercise_id in exercises:

                # GENERATE EXERCISE
                self.questionnaires.generate_questions(user_id, course_id, exercise_id,
                                                       "student")

        return 1

    def add_student_section(self, user_id, course_id, section_ids):
        """ Add Student Section """

        sids = ','.join("'{0}'".format(sid) for sid in section_ids)
        sql_str = "SELECT * FROM student_section WHERE section_id IN ({0})".format(sids)
        sql_str += " AND account_id = '{0}'".format(user_id)
        result = self.postgres.query_fetch_all(sql_str)

        db_section_ids = [res['section_id'] for res in result]
        db_section_ids = set(db_section_ids)
        section_ids = set(section_ids)

        section_ids.difference_update(db_section_ids)
        for section_id in section_ids:

            # ADD EXERCISE
            temp = {}
            temp['student_section_id'] = self.sha_security.generate_token(False)
            temp['account_id'] = user_id
            temp['course_id'] = course_id
            temp['section_id'] = section_id
            temp['status'] = True
            temp['created_on'] = time.time()

            self.postgres.insert('student_section', temp, 'student_section_id')

        return 1

    def add_student_subsection(self, user_id, course_id, subsection_ids):
        """ Add Student Section """

        sids = ','.join("'{0}'".format(sid) for sid in subsection_ids)
        sql_str = "SELECT * FROM student_subsection WHERE subsection_id IN ({0})".format(sids)
        sql_str += " AND account_id = '{0}'".format(user_id)
        result = self.postgres.query_fetch_all(sql_str)

        db_section_ids = [res['subsection_id'] for res in result]
        db_subsection_ids = set(db_section_ids)
        subsection_ids = set(subsection_ids)

        subsection_ids.difference_update(db_subsection_ids)

        ids = ','.join("'{0}'".format(subsection_id) for subsection_id in subsection_ids)
        sql_str = "SELECT * FROM subsection WHERE"
        sql_str += " subsection_id IN({0})".format(ids)
        results = self.postgres.query_fetch_all(sql_str)

        if results:

            for result in results:
                temp = {}
                temp['student_subsection_id'] = self.sha_security.generate_token(False)
                temp['account_id'] = user_id
                temp['course_id'] = course_id
                temp['section_id'] = result['section_id']
                temp['subsection_id'] = result['subsection_id']
                temp['status'] = True
                temp['created_on'] = time.time()

                self.postgres.insert('student_subsection', temp, 'student_subsection_id')

            return 1

        return 0

    def unlock_next_exercise(self, user_id, token, exercise_id, subsection=None, in_group=True):
        """ Unlock Next Exercise """

        # PROGRESS OF CURRENT EXERCISE
        sql_str = "SELECT * FROM exercise e LEFT JOIN student_exercise se ON e.exercise_id"
        sql_str += " = se.exercise_id WHERE se.status is True AND se.progress = '100' AND"
        sql_str += " se.exercise_id = '{0}' AND se.account_id ='{1}'".format(exercise_id, user_id)
        result = self.postgres.query_fetch_one(sql_str)

        if not result:
            return 1

        # NEXT EXERCISE
        exercise_number = int(result['exercise_number']) + 1
        subsection_id = result['subsection_id']

        if subsection:
            subsection_id = subsection
            exercise_number = 1

        sql_str = "SELECT * FROM exercise e LEFT JOIN student_exercise se"
        sql_str += " ON e.exercise_id = se.exercise_id WHERE se.status is True AND"
        sql_str += " account_id ='{0}' AND e.exercise_number='{1}'".format(user_id, exercise_number)
        sql_str += " AND e.subsection_id='{0}'".format(subsection_id)
        next_exercise = self.postgres.query_fetch_one(sql_str)

        if not next_exercise:
            return 1

        # CHECK NEXT EXERCISE SETTING
        next_exercise_id = next_exercise['exercise_id']
        sql_str = "SELECT * FROM exercise_requirements WHERE"
        sql_str += " exercise_id='{0}'".format(next_exercise_id)
        next_reqs = self.postgres.query_fetch_one(sql_str)

        if not next_reqs:
            return 1

        if not in_group:

            next_reqs['is_lock'] = False

        if next_reqs['is_lock'] is False:
            if next_reqs['grade_locking'] is True:
                if result['score'] >= result['passing_criterium']:

                    if not self.unlock_instruction(user_id, next_exercise['exercise_id'], user_id, token):
                        self.unlock_exercise(next_exercise['student_exercise_id'], user_id, token)
            else:

                if not self.unlock_instruction(user_id, next_exercise['exercise_id'], user_id, token):
                    self.unlock_exercise(next_exercise['student_exercise_id'], user_id, token)

        return 1

    def unlock_exercise(self, student_exercise_id, userid=None, token=None, account_id=None):
        """ Unlock Exercise """
        assert student_exercise_id, "Student Exercise ID is required."

        sql_str = "SELECT is_unlocked FROM student_exercise WHERE"
        sql_str += " student_exercise_id='{0}'".format(student_exercise_id)
        response = self.postgres.query_fetch_one(sql_str)

        if not response['is_unlocked']:

            # UPDATE UNLOCK
            conditions = []
            conditions.append({
                "col": "student_exercise_id",
                "con": "=",
                "val": student_exercise_id
            })

            # UPDATE
            data = {}
            data['is_unlocked'] = True
            data['unlock_criteria'] = "hierarchy"
            data['unlocked_on'] = time.time()

            self.postgres.update('student_exercise', data, conditions)

            if userid and token:

                if not account_id:

                    account_id = userid

                self.send_notif(userid, token, account_id, "You have new Exercise!", "New Exercise", "New Exercise", )

        return 1

    def unlock_instruction(self, user_id, exercise_id, userid=None, token=None):
        """ Unlock Instruction """

        sql_str = "SELECT * FROM student_instruction WHERE"
        sql_str += "account_id = '{0}' AND exercise_id = '{1}'".format(user_id, exercise_id)
        instructions = self.postgres.query_fetch_all(sql_str)

        if instructions:

            for instruction in instructions:

                sql_str = "SELECT is_unlocked FROM student_instruction WHERE"
                sql_str += " student_instruction_id='{0}'".format(instruction['student_instruction_id'])
                sql_str += " AND account_id='{0}'".format(user_id)
                response = self.postgres.query_fetch_one(sql_str)

                if not response['is_unlocked']:

                    conditions = []
                    conditions.append({
                        "col": "account_id",
                        "con": "=",
                        "val": user_id
                    })

                    conditions.append({
                        "col": "student_instruction_id",
                        "con": "=",
                        "val": instruction['student_instruction_id']
                    })

                    # UPDATE
                    data = {}
                    data['is_unlocked'] = True
                    data['unlock_criteria'] = "hierarchy"
                    data['unlocked_on'] = time.time()

                    self.postgres.update('student_instruction', data, conditions)

                    if userid and token:

                        self.send_notif(userid, token, user_id, "You have new Instruction!", "New Instruction", "New Instruction", )

            return 1

        return 0

    def unlock_next_subsection(self, user_id, token, exercise_id, section=None, in_group=True):
        """ Unlock Next Subsection """

        sql_str = "SELECT * FROM subsection s LEFT JOIN student_subsection ss ON"
        sql_str += " s.subsection_id = ss.subsection_id WHERE ss.subsection_id IN ("
        sql_str += " SELECT e.subsection_id FROM exercise e LEFT JOIN student_exercise se"
        sql_str += " ON e.exercise_id = se.exercise_id WHERE se.status is True AND"
        sql_str += " se.exercise_id = '{0}' AND se.account_id ='{1}')".format(exercise_id, user_id)
        sql_str += " AND ss.account_id = '{0}' AND ss.status is True".format(user_id)
        subsection = self.postgres.query_fetch_one(sql_str)

        section_id = subsection['section_id']
        subsection_id = subsection['subsection_id']

        # CHECK SUBSECTION EXERCISE IF COMPLETED
        sql_str = " SELECT * FROM student_subsection WHERE progress = '100' AND"
        sql_str += " subsection_id ='{0}' AND account_id ='{1}'".format(subsection_id, user_id)
        result = self.postgres.query_fetch_one(sql_str)

        if result:

            sql_str = "SELECT * FROM subsection_requirements WHERE"
            sql_str += " subsection_id='{0}'".format(subsection_id)
            reqs = self.postgres.query_fetch_one(sql_str)

            # NEXT SUBSECTION
            difficulty_level = int(subsection['difficulty_level']) + 1

            if section:
                section_id = section
                difficulty_level = 1

            sql_str = "SELECT * FROM subsection s LEFT JOIN student_subsection ss ON"
            sql_str += " s.subsection_id = ss.subsection_id WHERE ss.status is True AND"
            sql_str += " s.difficulty_level = '{0}' AND".format(difficulty_level)
            sql_str += " ss.account_id = '{0}' AND ss.section_id ='{1}'".format(user_id, section_id)
            next_subsection = self.postgres.query_fetch_one(sql_str)

            if not next_subsection:
                return 1

            # NEXT SUBSECTION SETTINGS
            next_sub = next_subsection['subsection_id']

            sql_str = "SELECT * FROM subsection_requirements WHERE"
            sql_str += " subsection_id='{0}'".format(next_sub)
            next_reqs = self.postgres.query_fetch_one(sql_str)

            if not next_reqs:
                return 1

            if not in_group:

                next_reqs['is_lock'] = False

            if next_reqs['is_lock'] is False:
                if next_reqs['grade_locking'] is True:
                    if reqs and int(float(result['percent_score'])) >= int(float(reqs['completion'])):

                        sql_str = "SELECT is_unlocked FROM student_subsection WHERE"
                        sql_str += " student_subsection_id='{0}'".format(next_subsection['student_subsection_id'])
                        sql_str += " AND account_id='{0}'".format(user_id)
                        response = self.postgres.query_fetch_one(sql_str)

                        if not response['is_unlocked']:

                            conditions = []
                            conditions.append({
                                "col": "account_id",
                                "con": "=",
                                "val": user_id
                            })

                            conditions.append({
                                "col": "student_subsection_id",
                                "con": "=",
                                "val": next_subsection['student_subsection_id']
                            })

                            # UPDATE
                            data = {}
                            data['is_unlocked'] = True
                            data['unlock_criteria'] = "hierarchy"
                            data['unlocked_on'] = time.time()

                            self.postgres.update('student_subsection', data, conditions)

                            if user_id and token:

                                self.send_notif(user_id, token, user_id, "You have new Subsection!", "New Subsection", "New Subsection", )

                            # UNLOCK NEXT EXERCISE
                            self.unlock_next_exercise(user_id, token, exercise_id, next_sub, in_group=in_group)
                            return 1

                # UNLOCK NEXT EXERCISE
                self.unlock_next_exercise(user_id, token, exercise_id, next_sub, in_group=in_group)
    
        return 1

    def unlock_next_section(self, user_id, token, exercise_id, in_group=True):
        """ Unlock next section """

        sql_str = "SELECT * FROM section s LEFT JOIN student_section ss ON"
        sql_str += " s.section_id = ss.section_id WHERE ss.section_id IN ("
        sql_str += " SELECT e.section_id FROM exercise e LEFT JOIN student_exercise se"
        sql_str += " ON e.exercise_id = se.exercise_id WHERE se.status is True AND"
        sql_str += " se.exercise_id = '{0}' AND se.account_id ='{1}')".format(exercise_id, user_id)
        sql_str += " AND ss.account_id = '{0}'".format(user_id)
        section = self.postgres.query_fetch_one(sql_str)

        section_id = section['section_id']
        course_id = section['course_id']

        # CHECK SUBSECTION EXERCISE IF COMPLETED
        sql_str = " SELECT * FROM student_section WHERE progress = '100' AND"
        sql_str += " section_id ='{0}' AND account_id ='{1}'".format(section_id, user_id)
        result = self.postgres.query_fetch_one(sql_str)

        if not result:
            return 1

        sql_str = "SELECT * FROM section_requirements WHERE"
        sql_str += " section_id='{0}'".format(section_id)
        reqs = self.postgres.query_fetch_one(sql_str)

        difficulty_level = int(section['difficulty_level']) + 1

        sql_str = "SELECT * FROM section s LEFT JOIN student_section ss ON"
        sql_str += " s.section_id = ss.section_id WHERE ss.status is True AND"
        sql_str += " s.difficulty_level = '{0}' AND".format(difficulty_level)
        sql_str += " ss.account_id = '{0}' AND ss.course_id ='{1}'".format(user_id, course_id)
        next_section = self.postgres.query_fetch_one(sql_str)

        if not next_section:
            return 1

        # NEXT SECTION SETTINGS
        next_sec = next_section['section_id']

        sql_str = "SELECT * FROM section_requirements WHERE"
        sql_str += " section_id='{0}'".format(next_sec)
        next_reqs = self.postgres.query_fetch_one(sql_str)

        if not next_reqs:
            return 1

        if not in_group:

            next_reqs['is_lock'] = False

        if  next_reqs['is_lock'] is False:

            if next_reqs['grade_locking'] is True:
                if reqs and int(float(result['percent_score'])) >= int(float(reqs['completion'])):

                    sql_str = "SELECT is_unlocked FROM student_section WHERE"
                    sql_str += " student_section_id='{0}'".format(next_section['student_section_id'])
                    sql_str += " AND account_id='{0}'".format(user_id)
                    response = self.postgres.query_fetch_one(sql_str)

                    if not response['is_unlocked']:

                        conditions = []
                        conditions.append({
                            "col": "account_id",
                            "con": "=",
                            "val": user_id
                        })

                        conditions.append({
                            "col": "student_section_id",
                            "con": "=",
                            "val": next_section['student_section_id']
                        })

                        # UPDATE
                        data = {}
                        data['is_unlocked'] = True
                        data['unlock_criteria'] = "hierarchy"
                        data['unlocked_on'] = time.time()

                        self.postgres.update('student_section', data, conditions)

                        if user_id and token:

                            self.send_notif(user_id, token, user_id, "You have new Section!", "New Section", "New Section")

                        self.unlock_next_subsection(user_id, token, exercise_id, next_sec, in_group=in_group)
                        return 1

            self.unlock_next_subsection(user_id, token, exercise_id, next_sec, in_group=in_group)

        return 1

    # NEED TO REVIEW IF YOU WANT TO USE THIS FUNCTION
    def unlock_next_course(self, user_id, token, exercise_id):
        """ Unlock Next Course """
        sql_str = "SELECT * FROM course c LEFT JOIN student_course sc ON"
        sql_str += " c.course_id = sc.course_id WHERE sc.course_id IN ("
        sql_str += " SELECT e.course_id FROM exercise e LEFT JOIN student_exercise se"
        sql_str += " ON e.exercise_id = se.exercise_id WHERE se.status is True AND"
        sql_str += " se.exercise_id = '{0}' AND se.account_id ='{1}')".format(exercise_id, user_id)
        sql_str += " AND sc.account_id = '{0}'".format(user_id) 
        result = self.postgres.query_fetch_one(sql_str)

        # CURRENT COURSE SETTINGS
        sql_str = "SELECT * FROM user_group_students ugs LEFT JOIN group_course_requirements"
        sql_str += " gcr ON ugs.user_group_id = gsr.user_group_id WHERE"
        sql_str += " ugs.student_id = '{0}' AND gcr.course_id = '{1}'".format(user_id, result['course_id'])
        reqs = self.postgres.query_fetch_one(sql_str)

        # UNLOCK NEXT COURSE
        difficulty_level = int(result['difficulty_level']) + 1

        sql_str = "SELECT * FROM course c LEFT JOIN student_course sc ON"
        sql_str += " c.course_id = sc.course_id WHERE sc.status is True AND"
        sql_str += " c.difficulty_level = '{0}' AND".format(difficulty_level)
        sql_str += " sc.account_id = '{0}'".format(user_id)
        next_course = self.postgres.query_fetch_one(sql_str)

        if next_course and next_course['is_unlocked'] is False:

            # NEXT COURSE SETTINGS
            course_id = next_course['course_id']
            sql_str = "SELECT * FROM user_group_students ugs LEFT JOIN group_course_requirements"
            sql_str += " gsr ON ugs.user_group_id = gsr.user_group_id WHERE"
            sql_str += " ugs.student_id = '{0}' AND gsr.section_id = '{1}'".format(user_id, course_id)
            next_reqs = self.postgres.query_fetch_one(sql_str)

            if next_reqs and next_reqs['grade_locking'] is True:

                if reqs and result['progress'] >= reqs['completion']:

                    sql_str = "SELECT is_unlocked FROM student_course WHERE"
                    sql_str += " course_id='{0}'".format(course_id)
                    sql_str += " AND account_id='{0}'".format(user_id)
                    response = self.postgres.query_fetch_one(sql_str)

                    if not response['is_unlocked']:

                        conditions = []
                        conditions.append({
                            "col": "account_id",
                            "con": "=",
                            "val": user_id
                        })

                        conditions.append({
                            "col": "course_id",
                            "con": "=",
                            "val": course_id
                        })

                        # UPDATE
                        data = {}
                        data['is_unlocked'] = True
                        data['unlock_criteria'] = "hierarchy"
                        data['unlocked_on'] = time.time()

                        self.postgres.update('student_course', data, conditions)

                        if user_id and token:

                            self.send_notif(user_id, token, user_id, "You have new course!", "New Course", "New Course", )

                        # GENERATE COURSE SET
                        self.generate_course_set(user_id, course_id)

        return 1

    # def validate_lock_unlock(self, token, account_id, course_id):
    #     """ VALIDATE LOCK/UNLOCK """

    #     # GET COURSE
    #     sql_str = "SELECT c.course_id, c.course_name, gcr.course_requirement_id,"
    #     sql_str += " gcr.completion, gcr.grade_locking, gcr.on_previous, gcr.is_lock,"
    #     sql_str += " gcr.is_visible, (SELECT array_to_json(array_agg(sections))"
    #     sql_str += " FROM (SELECT s.section_id, s.section_name,"
    #     sql_str += " gsr.section_requirement_id, gsr.completion,"
    #     sql_str += " gsr.grade_locking, gsr.on_previous, gsr.is_lock, gsr.is_visible,"
    #     sql_str += " (SELECT array_to_json(array_agg(subsections)) FROM"
    #     sql_str += " (SELECT ss.subsection_id, ss.subsection_name,"
    #     sql_str += " gssr.subsection_requirement_id,"
    #     sql_str += " gssr.completion, gssr.grade_locking, gssr.on_previous, gssr.is_lock, gssr.is_visible,"
    #     sql_str += " (SELECT array_to_json(array_agg(exercises)) FROM"
    #     sql_str += " (SELECT e.exercise_id, e.exercise_number, e.exercise_id as key,"
    #     sql_str += " ger.exercise_requirement_id, ger.completion,"
    #     sql_str += " ger.grade_locking, ger.on_previous, ger.is_lock, ger.is_visible FROM exercise e"
    #     sql_str += " INNER JOIN exercise_requirements ger ON"
    #     sql_str += " ss.subsection_id=e.subsection_id AND e.exercise_id=ger.exercise_id) AS exercises) AS exercises"
    #     sql_str += " FROM subsection ss INNER JOIN subsection_requirements gssr ON"
    #     sql_str += " ss.section_id=s.section_id AND ss.subsection_id=gssr.subsection_id) AS subsections) AS subsections"
    #     sql_str += " FROM section s INNER JOIN section_requirements gsr ON"
    #     sql_str += " c.course_id=s.course_id AND s.section_id=gsr.section_id) AS sections) AS sections"
    #     sql_str += " FROM course c INNER JOIN course_requirements gcr ON"
    #     sql_str += " c.course_id=gcr.course_id"
    #     sql_str += " WHERE c.course_id='{0}'".format(course_id)

    #     course = self.postgres.query_fetch_one(sql_str)

    #     # SECTION
    #     if not 'sections' in course.keys():

    #         return 1

    #     if not course['sections']:

    #         return 1

    #     # EACH SECTION
    #     for section in course['sections']:

    #         section_id = section['section_id']
    #         # GET ALL SECTION REQUIREMENTS
    #         section_requirement_id = section['section_requirement_id']
    #         sql_str = "SELECT * FROM section_requirements WHERE"
    #         sql_str += " section_requirement_id='{0}'".format(section_requirement_id)
    #         sec_req = self.postgres.query_fetch_one(sql_str)

    #         # IF GREADE LOCKING
    #         if sec_req['grade_locking'] and not sec_req['is_lock']:

    #             # GET PREVIOUS SECTION
    #             sql_str = "SELECT section_id, difficulty_level FROM section WHERE"
    #             sql_str += " course_id='{0}'".format(course_id)
    #             sql_str += " ORDER BY difficulty_level ASC"
    #             all_section = self.postgres.query_fetch_all(sql_str)

    #             if not all_section:

    #                 continue

    #             previous_secid = ""
    #             flag = False
    #             for item in all_section:

    #                 if item['section_id'] == section_id:

    #                     flag = True
    #                     break

    #                 else:

    #                     previous_secid = item['section_id']
    #                     flag = False

    #             if flag and previous_secid:

    #                 sql_str = " SELECT * FROM student_section WHERE progress = '100' AND"
    #                 sql_str += " section_id ='{0}'".format(previous_secid)
    #                 sql_str += " AND account_id ='{0}'".format(account_id)
    #                 result = self.postgres.query_fetch_one(sql_str)

    #                 if int(float(result['percent_score'])) >= int(float(sec_req['completion'])):

    #                     sql_str = "SELECT is_unlocked FROM student_section WHERE"
    #                     sql_str += " section_id='{0}'".format(section_id)
    #                     sql_str += " AND account_id='{0}'".format(account_id)
    #                     response = self.postgres.query_fetch_one(sql_str)

    #                     if not response['is_unlocked']:

    #                         conditions = []
    #                         conditions.append({
    #                             "col": "account_id",
    #                             "con": "=",
    #                             "val": account_id
    #                         })

    #                         conditions.append({
    #                             "col": "section_id",
    #                             "con": "=",
    #                             "val": section_id
    #                         })

    #                         # UPDATE
    #                         data = {}
    #                         data['is_unlocked'] = True
    #                         data['unlock_criteria'] = "hierarchy"
    #                         data['unlocked_on'] = time.time()

    #                         self.postgres.update('student_section', data, conditions)

    #                         if account_id and token:

    #                             self.send_notif(account_id, token, account_id, "You have new Section!", "New Section", "New Section")

    #         # SUBSECTION
    #         if not 'subsections' in section.keys():

    #             continue

    #         if not section['subsections']:

    #             continue

    #         # EACH SUBSECTION
    #         for subsection in section['subsections']:

    #             subsection_id = subsection['subsection_id']
    #             # GET ALL SECTION REQUIREMENTS
    #             subsection_requirement_id = subsection['subsection_requirement_id']
    #             sql_str = "SELECT * FROM subsection_requirements WHERE"
    #             sql_str += " subsection_requirement_id='{0}'".format(subsection_requirement_id)
    #             subsec_req = self.postgres.query_fetch_one(sql_str)

    #             # IF GREADE LOCKING
    #             if subsec_req['grade_locking'] and not subsec_req['is_lock']:

    #                 # GET PREVIOUS SUBSECTION
    #                 sql_str = "SELECT subsection_id, difficulty_level FROM subsection WHERE"
    #                 sql_str += " section_id='{0}'".format(section_id)
    #                 sql_str += " ORDER BY difficulty_level ASC"
    #                 all_subsection = self.postgres.query_fetch_all(sql_str)

    #                 if not all_subsection:

    #                     continue

    #                 previous_subsecid = ""
    #                 flag = False
    #                 for item in all_subsection:

    #                     if item['subsection_id'] == subsection_id:

    #                         flag = True
    #                         break

    #                     else:

    #                         previous_subsecid = item['subsection_id']
    #                         flag = False

    #                 if flag and previous_subsecid:

    #                     sql_str = " SELECT * FROM student_subsection WHERE progress = '100' AND"
    #                     sql_str += " subsection_id ='{0}'".format(previous_subsecid)
    #                     sql_str += " AND account_id ='{0}'".format(account_id)
    #                     result = self.postgres.query_fetch_one(sql_str)

    #                     if int(float(result['percent_score'])) >= int(float(subsec_req['completion'])):

    #                         sql_str = "SELECT is_unlocked FROM student_subsection WHERE"
    #                         sql_str += " subsection_id='{0}'".format(subsection_id)
    #                         sql_str += " AND account_id='{0}'".format(account_id)
    #                         response = self.postgres.query_fetch_one(sql_str)

    #                         if not response['is_unlocked']:

    #                             conditions = []
    #                             conditions.append({
    #                                 "col": "account_id",
    #                                 "con": "=",
    #                                 "val": account_id
    #                             })

    #                             conditions.append({
    #                                 "col": "subsection_id",
    #                                 "con": "=",
    #                                 "val": subsection_id
    #                             })

    #                             # UPDATE
    #                             data = {}
    #                             data['is_unlocked'] = True
    #                             data['unlock_criteria'] = "hierarchy"
    #                             data['unlocked_on'] = time.time()

    #                             self.postgres.update('student_subsection', data, conditions)

    #                             if account_id and token:

    #                                 self.send_notif(account_id, token, account_id, "You have new Subsection!", "New Subsection", "New Subsection")

    #             # EXERCISE
    #             if not 'exercises' in subsection.keys():

    #                 continue

    #             if not subsection['exercises']:

    #                 continue

    #             # EACH EXERCISE
    #             for exercise in subsection['exercises']:

    #                 exercise_id = exercise['exercise_id']
    #                 # GET ALL SECTION REQUIREMENTS
    #                 exercise_requirement_id = exercise['exercise_requirement_id']
    #                 sql_str = "SELECT * FROM exercise_requirements WHERE"
    #                 sql_str += " exercise_requirement_id='{0}'".format(exercise_requirement_id)
    #                 ex_req = self.postgres.query_fetch_one(sql_str)

    #                 # IF GREADE LOCKING
    #                 if ex_req['grade_locking'] and not ex_req['is_lock']:

    #                     # GET PREVIOUS EXERCISE
    #                     sql_str = "SELECT exercise_id, exercise_number FROM exercise WHERE"
    #                     sql_str += " subsection_id='{0}'".format(subsection_id)
    #                     sql_str += " ORDER BY exercise_number ASC"
    #                     all_exercise = self.postgres.query_fetch_all(sql_str)

    #                     if not all_exercise:

    #                         continue

    #                     previous_exid = ""
    #                     flag = False
    #                     for item in all_exercise:

    #                         if item['exercise_id'] == exercise_id:

    #                             flag = True
    #                             break

    #                         else:

    #                             previous_exid = item['exercise_id']
    #                             flag = False

    #                     if flag and previous_exid:

    #                         sql_str = " SELECT * FROM student_exercise WHERE progress = '100' AND"
    #                         sql_str += " exercise_id ='{0}'".format(previous_exid)
    #                         sql_str += " AND account_id ='{0}'".format(account_id)
    #                         result = self.postgres.query_fetch_one(sql_str)

    #                         if int(float(result['percent_score'])) >= int(float(ex_req['completion'])):

    #                             sql_str = "SELECT is_unlocked FROM student_exercise WHERE"
    #                             sql_str += " exercise_id='{0}'".format(exercise_id)
    #                             sql_str += " AND account_id='{0}'".format(account_id)
    #                             response = self.postgres.query_fetch_one(sql_str)

    #                             if not response['is_unlocked']:

    #                                 conditions = []
    #                                 conditions.append({
    #                                     "col": "account_id",
    #                                     "con": "=",
    #                                     "val": account_id
    #                                 })

    #                                 conditions.append({
    #                                     "col": "exercise_id",
    #                                     "con": "=",
    #                                     "val": exercise_id
    #                                 })

    #                                 # UPDATE
    #                                 data = {}
    #                                 data['is_unlocked'] = True
    #                                 data['unlock_criteria'] = "hierarchy"
    #                                 data['unlocked_on'] = time.time()

    #                                 self.postgres.update('student_exercise', data, conditions)

    #                                 if account_id and token:

    #                                     self.send_notif(account_id, token, account_id, "You have new Exercise!", "New Exercise", "New Exercise")

    #     return 1

    def validate_lock_unlock2(self, token, account_id, course_id, in_group, subsect_id=None):
        """ VALIDATE LOCK/UNLOCK """

        sql_str = "SELECT exercise_id FROM student_exercise_repeat WHERE"
        sql_str += " course_id='{0}'".format(course_id)
        sql_str += " AND account_id='{0}'".format(account_id)
        sql_str += " AND is_passed=true"
        pass_exs = self.postgres.query_fetch_all(sql_str)

        passed_repeat_exercise_ids = [pex['exercise_id'] for pex in pass_exs or []]

        # GET COURSE
        sql_str = "SELECT c.course_id, c.course_name, gcr.course_requirement_id,"
        sql_str += " gcr.completion, gcr.grade_locking, gcr.on_previous, gcr.is_lock,"
        sql_str += " gcr.is_visible, (SELECT array_to_json(array_agg(sections))"
        sql_str += " FROM (SELECT s.section_id, s.section_name,"
        sql_str += " gsr.section_requirement_id, gsr.completion,"
        sql_str += " gsr.grade_locking, gsr.on_previous, gsr.is_lock, gsr.is_visible,"
        sql_str += " (SELECT array_to_json(array_agg(subsections)) FROM"
        sql_str += " (SELECT ss.subsection_id, ss.subsection_name,"
        sql_str += " gssr.subsection_requirement_id,"
        sql_str += " gssr.completion, gssr.grade_locking, gssr.on_previous, gssr.is_lock, gssr.is_visible,"
        sql_str += " (SELECT array_to_json(array_agg(exercises)) FROM"
        sql_str += " (SELECT e.exercise_id, e.exercise_number, e.exercise_id as key,"
        sql_str += " ger.exercise_requirement_id, ger.completion,"
        sql_str += " ger.grade_locking, ger.on_previous, ger.is_lock, ger.is_visible FROM exercise e"
        sql_str += " INNER JOIN exercise_requirements ger ON"
        sql_str += " ss.subsection_id=e.subsection_id AND e.exercise_id=ger.exercise_id) AS exercises) AS exercises"
        sql_str += " FROM subsection ss INNER JOIN subsection_requirements gssr ON"
        sql_str += " ss.section_id=s.section_id AND ss.subsection_id=gssr.subsection_id) AS subsections) AS subsections"
        sql_str += " FROM section s INNER JOIN section_requirements gsr ON"
        sql_str += " c.course_id=s.course_id AND s.section_id=gsr.section_id) AS sections) AS sections"
        sql_str += " FROM course c INNER JOIN course_requirements gcr ON"
        sql_str += " c.course_id=gcr.course_id"
        sql_str += " WHERE c.course_id='{0}'".format(course_id)

        course = self.postgres.query_fetch_one(sql_str)

        if not course:

            return 1

        # SECTION
        if not 'sections' in course.keys():

            return 1

        if not course['sections']:

            return 1


        # sql_str = "SELECT e.exercise_id, e.exercise_number, ss.difficulty_level,"
        # sql_str += " ss.subsection_name, s.difficulty_level AS section_diff"
        # sql_str += " FROM exercise e INNER JOIN subsection ss ON"
        # sql_str += " e.subsection_id=ss.subsection_id"
        # sql_str += " INNER JOIN section s ON e.section_id=s.section_id WHERE"
        # sql_str += " e.course_id ='{0}'".format(course_id)
        # sql_str += " ORDER BY s.difficulty_level ASC, ss.difficulty_level ASC,"
        # sql_str += " e.exercise_number ASC"
        # all_exercise = self.postgres.query_fetch_all(sql_str)
        all_exercise = self.get_exercise_hierarchy(course_id)
        previous_obj = {}

        # EACH SECTION
        for section in course['sections']:

            # SUBSECTION
            if not 'subsections' in section.keys():

                continue

            if not section['subsections']:

                continue

            # EACH SUBSECTION
            for subsection in section['subsections']:

                subsection_id = subsection['subsection_id']

                if subsect_id:

                    if not subsect_id == subsection_id:

                        continue

                # EXERCISE
                if not 'exercises' in subsection.keys():

                    continue

                if not subsection['exercises']:

                    continue

                # EACH EXERCISE
                for exercise in subsection['exercises']:

                    exercise_id = exercise['exercise_id']

                    # sql_str = "SELECT * FROM exercise e LEFT JOIN student_exercise se ON e.exercise_id"
                    # sql_str += " = se.exercise_id WHERE se.status is True AND"
                    # sql_str += " se.exercise_id = '{0}' AND se.account_id ='{1}'".format(exercise_id, account_id)
                    sql_str = "SELECT *, (SELECT array_to_json(array_agg(instruc))"
                    sql_str += " FROM (SELECT * FROM student_instruction WHERE"
                    sql_str += " account_id=se.account_id AND exercise_id=e.exercise_id)"
                    sql_str += " AS instruc) AS instructions FROM exercise e INNER JOIN"
                    sql_str += " student_exercise se ON e.exercise_id = se.exercise_id"
                    sql_str += " WHERE se.status is True AND"
                    sql_str += " se.exercise_id = '{0}'".format(exercise_id)
                    sql_str += " AND se.account_id ='{0}'".format(account_id)

                    current_data = self.postgres.query_fetch_one(sql_str)

                    if not current_data:

                        continue

                    previous_obj[exercise_id] = current_data
                    # student_exercise_id = current_data['student_exercise_id']

                    # GET ALL SECTION REQUIREMENTS
                    # exercise_requirement_id = exercise['exercise_requirement_id']
                    # sql_str = "SELECT * FROM exercise_requirements WHERE"
                    # sql_str += " exercise_requirement_id='{0}'".format(exercise_requirement_id)
                    # ex_req = self.postgres.query_fetch_one(sql_str)

                    if not in_group:

                        # ex_req['is_lock'] = False
                        exercise['is_lock'] = False

                    # IF GREADE LOCKING
                    # if ex_req['grade_locking'] and not ex_req['is_lock']:
                    if exercise['grade_locking'] and not exercise['is_lock']:

                        # GET PREVIOUS EXERCISE
                        # sql_str = "SELECT exercise_id, exercise_number FROM exercise WHERE"
                        # sql_str += " subsection_id='{0}'".format(subsection_id)
                        # sql_str += " ORDER BY exercise_number ASC"
                        # all_exercise = self.postgres.query_fetch_all(sql_str)

                        if not all_exercise:

                            continue

                        previous_exid = ""
                        flag = False
                        for item in all_exercise:

                            if item['exercise_id'] == exercise_id:

                                flag = True
                                break

                            else:

                                previous_exid = item['exercise_id']
                                flag = False

                        if flag and previous_exid:

                            self.unlock_next_exercise2(account_id,
                                                       token,
                                                       exercise,
                                                       previous_exid,
                                                       in_group,
                                                       current_data,
                                                       previous_obj,
                                                       passed_repeat_exercise_ids)

                    # if not ex_req['grade_locking'] and not ex_req['is_lock']:
                    if not exercise['grade_locking'] and not exercise['is_lock']:

                        # PROGRESS OF CURRENT EXERCISE
                        self.unlock_exercise2(current_data, account_id, token)

        return 1

    def unlock_next_exercise2(self, user_id,
                              token, exercise,
                              previous_exid,
                              in_group,
                              current_data,
                              previous_obj,
                              passed_repeat_exercise_ids):
        """ Unlock Next Exercise """

        # student_exercise_id = current_data['student_exercise_id']
        exercise_id = exercise['exercise_id']
        prev_data = {}

        if previous_exid in previous_obj.keys():
            prev_data = previous_obj[previous_exid]
        else:

            # PROGRESS OF PREVIOUS EXERCISE
            sql_str = "SELECT se.score, e.passing_criterium FROM"
            sql_str += " exercise e LEFT JOIN student_exercise se ON e.exercise_id"
            sql_str += " = se.exercise_id WHERE se.status is True AND"
            sql_str += " se.exercise_id = '{0}' AND se.account_id ='{1}'".format(previous_exid, user_id)
            prev_data = self.postgres.query_fetch_one(sql_str)

        if not prev_data:
            return 1

        # PROGRESS OF CURRENT EXERCISE
        # sql_str = "SELECT * FROM exercise e LEFT JOIN student_exercise se ON e.exercise_id"
        # sql_str += " = se.exercise_id WHERE se.status is True AND"
        # sql_str += " se.exercise_id = '{0}' AND se.account_id ='{1}'".format(exercise_id, user_id)
        # current = self.postgres.query_fetch_one(sql_str)

        # if not current:
        #     return 1

        # CHECK NEXT EXERCISE SETTING
        # current_id = current['exercise_id']
        # sql_str = "SELECT * FROM exercise_requirements WHERE"
        # sql_str += " exercise_id='{0}'".format(exercise_id)
        # next_reqs = self.postgres.query_fetch_one(sql_str)

        # if not next_reqs:

        #     return 1

        if not in_group:

            exercise['is_lock'] = False

        if exercise['is_lock'] is False:
            if exercise['grade_locking'] is True:

                if not prev_data['score']:

                    prev_data['score'] = 0

                if prev_data['score'] >= prev_data['passing_criterium']:

                    if not self.unlock_instruction2(user_id, exercise_id, current_data, user_id, token):
                        # self.unlock_exercise2(current_data, user_id, token)
                        self.unlock_exercise2(current_data, user_id, token)

                elif previous_exid in passed_repeat_exercise_ids:

                    if not self.unlock_instruction2(user_id, exercise_id, current_data, user_id, token):
                        # self.unlock_exercise2(current_data, user_id, token)
                        self.unlock_exercise2(current_data, user_id, token)

                else:
                    # LOCK
                    # self.lock_exercise(current_data, user_id, token)
                    self.lock_exercise(current_data, user_id, token)
            else:

                if not self.unlock_instruction2(user_id, exercise_id, current_data, user_id, token):
                    # self.unlock_exercise2(current_data, user_id, token)
                    self.unlock_exercise2(current_data, user_id, token)

        return 1


    def lock_exercise(self, current_data, userid=None, token=None, account_id=None):
        """ Lock Exercise """

        student_exercise_id = current_data['student_exercise_id']

        # sql_str = "SELECT is_unlocked FROM student_exercise WHERE"
        # sql_str += " student_exercise_id='{0}'".format(student_exercise_id)
        # response = self.postgres.query_fetch_one(sql_str)

        # if response['is_unlocked']:
        if current_data['is_unlocked']:

            # UPDATE UNLOCK
            conditions = []
            conditions.append({
                "col": "student_exercise_id",
                "con": "=",
                "val": student_exercise_id
            })

            # UPDATE
            data = {}
            data['is_unlocked'] = False
            data['unlock_criteria'] = "hierarchy"
            data['unlocked_on'] = time.time()

            self.postgres.update('student_exercise', data, conditions)

            if userid and token:

                if not account_id:

                    account_id = userid

                self.send_notif(userid, token, account_id, "You have new Exercise!", "New Exercise", "New Exercise", )

        return 1

    def unlock_exercise2(self, current_data, userid=None, token=None, account_id=None):
        """ Unlock Exercise """

        student_exercise_id = current_data['student_exercise_id']

        # sql_str = "SELECT is_unlocked FROM student_exercise WHERE"
        # sql_str += " student_exercise_id='{0}'".format(student_exercise_id)
        # response = self.postgres.query_fetch_one(sql_str)

        if not current_data['is_unlocked']:

            # UPDATE UNLOCK
            conditions = []
            conditions.append({
                "col": "student_exercise_id",
                "con": "=",
                "val": student_exercise_id
            })

            # UPDATE
            data = {}
            data['is_unlocked'] = True
            data['unlock_criteria'] = "hierarchy"
            data['unlocked_on'] = time.time()

            self.postgres.update('student_exercise', data, conditions)

            if userid and token:

                if not account_id:

                    account_id = userid

                self.send_notif(userid, token, account_id, "You have new Exercise!", "New Exercise", "New Exercise", )

        return 1

    def unlock_instruction2(self, user_id, exercise_id, current_data, userid=None, token=None):
        """ Unlock Instruction """

        # sql_str = "SELECT * FROM student_instruction WHERE"
        # sql_str += "account_id = '{0}' AND exercise_id = '{1}'".format(user_id, exercise_id)
        # instructions = self.postgres.query_fetch_all(sql_str)
        instructions = current_data['instructions']

        for instruction in instructions or []:

            # sql_str = "SELECT is_unlocked FROM student_instruction WHERE"
            # sql_str += " student_instruction_id='{0}'".format(instruction['student_instruction_id'])
            # sql_str += " AND account_id='{0}'".format(user_id)
            # response = self.postgres.query_fetch_one(sql_str)

            if not instruction['is_unlocked']:

                conditions = []
                conditions.append({
                    "col": "account_id",
                    "con": "=",
                    "val": user_id
                })

                conditions.append({
                    "col": "student_instruction_id",
                    "con": "=",
                    "val": instruction['student_instruction_id']
                })

                # UPDATE
                data = {}
                data['is_unlocked'] = True
                data['unlock_criteria'] = "hierarchy"
                data['unlocked_on'] = time.time()

                self.postgres.update('student_instruction', data, conditions)

                if userid and token:

                    self.send_notif(userid, token, user_id, "You have new Instruction!", "New Instruction", "New Instruction", )

        return 1
