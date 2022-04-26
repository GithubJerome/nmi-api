# encoding: utf-8
# pylint: disable=no-self-use, bare-except, too-many-locals, too-many-arguments, too-many-branches, too-many-nested-blocks
"""Course Update"""
import csv
import json
import time

from flask import  request
from library.common import Common
from configparser import ConfigParser
from library.config_parser import config_section_parser

class CourseUpdate(Common):
    """Class for CourseUpdate"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CourseUpdate class"""

        self.config = ConfigParser()
        self.config.read("config/config.cfg")
        super(CourseUpdate, self).__init__()

    def course_update(self):
        """
        This API is for Download Course Base
        ---
        tags:
          - Download
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
          - name: type
            in: query
            description: Type
            required: true
            type: string
            example: "csv"
          - name: course_id
            in: query
            description: Course ID
            required: true
            type: string

        responses:
          500:
            description: Error
          200:
            description: Download Course Base
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

        # CHECK COURSE
        if not self.check_tutor_course(userid, course_id):
            data["alert"] = "Invalid Course"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # CHECK IF COURSE IS ALREADY IN USE
        # if not self.use_course(course_id):

        #     # RETURN IF USED
        #     data["alert"] = "Course is in use!"
        #     data['status'] = 'Failed'

        #     # RETURN ALERT
        #     return self.return_data(data, userid)

        filename = 'course_' + str(int(time.time())) + '.csv'
        downloads = config_section_parser(self.config, "APPDIR")['downloads']
        path = downloads + '/' + filename

        with open(path, 'w', newline='') as file:
            writer = csv.writer(file)
            # writer.writerow(self.course_header())
            writer.writerow(self.course_temp_headers())

            # INSERT DATA (CSV FILE)
            for course in self.course_master(course_id):

                course_flag = False

                if not 'children' in course.keys():

                    continue

                if not course['children']:

                    writer.writerow([
                        course['course_id'],
                        course['course_name'],
                        course['course_title'],
                        course['description'],
                        course['difficulty_level'],
                        course['requirements']
                    ])
                    continue

                for section in course['children']:

                    section_flag = False

                    if not 'children' in section.keys():

                        continue

                    if not section['children']:

                        writer.writerow([
                            course['course_id'],
                            course['course_name'],
                            course['course_title'],
                            course['description'],
                            course['difficulty_level'],
                            course['requirements'],
                            # section['section_id'],
                            section['section_name'],
                            section['description'],
                            section['difficulty_level']
                        ])
                        continue

                    for subsection in section['children']:

                        subsection_flag = False

                        if not 'children' in subsection.keys():

                            continue

                        if not subsection['children']:

                            writer.writerow([
                                course['course_id'],
                                course['course_name'],
                                course['course_title'],
                                course['description'],
                                course['difficulty_level'],
                                course['requirements'],
                                # section['section_id'],
                                section['section_name'],
                                section['description'],
                                section['difficulty_level'],
                                # subsection['subsection_id'],
                                subsection['subsection_name'],
                                subsection['description'],
                                subsection['difficulty_level']
                            ])
                            continue

                        for exercise in subsection['children']:

                            exercise_id = exercise['exercise_id']

                            sql_str = "SELECT s.skill, ("
                            sql_str += "SELECT array_to_json(array_agg(sskill)) FROM ("
                            sql_str += "SELECT ss.subskill FROM skill_subskills sss "
                            sql_str += "INNER JOIN subskills ss ON"
                            sql_str += " sss.subskill_id=ss.subskill_id WHERE"
                            sql_str += " sss.skill_id=s.skill_id) AS sskill)"
                            sql_str += " AS sskill FROM exercise_skills es INNER JOIN skills s ON"
                            sql_str += " es.skill_id=s.skill_id WHERE"
                            sql_str += " es.exercise_id='{0}'".format(exercise_id)

                            db_skills = self.postgres.query_fetch_all(sql_str)

                            skills = []
                            if db_skills:

                                for skill in db_skills or []:

                                    new_skill = {}
                                    new_skill['skill'] = skill['skill']
                                    new_skill['subskills'] = []
                                    # [sskll['subskill'] for sskll in skill['sskill']]

                                    for sskll in skill['sskill'] or []:

                                        if sskll:

                                            new_skill['subskills'].append(sskll['subskill'])

                                    skills.append(new_skill)

                                skills = json.dumps(skills)
                            if not skills:

                                skills = ""

                            # exercise_flag = False

                            # sql_str = "SELECT cq.question_id, q.question, q.question_type,"
                            # sql_str += " q.tags, q.choices, q.shuffle_options, q.shuffle_answers,"
                            # sql_str += " q.num_eval, q.correct_answer, q.correct, q.incorrect,"
                            # sql_str += " q.feedback, q.description FROM course_question cq"
                            # sql_str += " INNER JOIN questions q ON"
                            # sql_str += " cq.question_id=q.question_id WHERE"
                            # sql_str += " cq.exercise_id ='{0}'".format(exercise['exercise_id'])
                            # questions = self.postgres.query_fetch_all(sql_str)

                            sql_str = "SELECT qs.* FROM uploaded_exercise_question uexq"
                            sql_str += " INNER JOIN questions qs ON uexq.question_id=qs.question_id WHERE"
                            sql_str += " uexq.exercise_id='{0}'".format(exercise['exercise_id'])
                            sql_str += " ORDER BY uexq.sequence"
                            questions = self.postgres.query_fetch_all(sql_str)

                            if not questions:

                                writer.writerow([
                                    course['course_id'],
                                    course['course_name'],
                                    course['course_title'],
                                    course['description'],
                                    course['difficulty_level'],
                                    course['requirements'],
                                    # section['section_id'],
                                    section['section_name'],
                                    section['description'],
                                    section['difficulty_level'],
                                    # subsection['subsection_id'],
                                    subsection['subsection_name'],
                                    subsection['description'],
                                    subsection['difficulty_level'],
                                    # exercise['exercise_id'],
                                    exercise['exercise_number'],
                                    exercise['question_types'],
                                    exercise['tags'],
                                    exercise['description'],
                                    exercise['draw_by_skills'],
                                    exercise['draw_by_tag'],
                                    exercise['editing_allowed'],
                                    exercise['help'],
                                    exercise['instant_feedback'],
                                    exercise['moving_allowed'],
                                    exercise['number_to_draw'],
                                    exercise['passing_criterium'],
                                    exercise['save_seed'],
                                    exercise['seed'],
                                    exercise['shuffled'],
                                    exercise['text_before_start'],
                                    exercise['text_after_end'],
                                    exercise['timed_limit'],
                                    exercise['timed_type'],
                                    skills,
                                    exercise['is_repeatable'],
                                    ])
                            else:

                                for question in questions:

                                    orig_question = ""
                                    if question['orig_question']:
                                        orig_question = question['orig_question']['question']

                                    orig_answer = ""
                                    if question['orig_answer']:
                                        orig_answer = question['orig_answer']['answer']

                                    orig_tags = ""
                                    if question['orig_tags']:
                                        orig_tags = question['orig_tags']['tags']

                                    orig_choices = ""
                                    if question['orig_choices']:
                                        orig_choices = question['orig_choices']['choices']

                                    orig_skills = ""
                                    if question['orig_skills']:
                                        orig_skills = question['orig_skills']['skills']

                                    writer.writerow([
                                        course['course_id'],
                                        course['course_name'],
                                        course['course_title'],
                                        course['description'],
                                        course['difficulty_level'],
                                        course['requirements'],
                                        # section['section_id'],
                                        section['section_name'],
                                        section['description'],
                                        section['difficulty_level'],
                                        # subsection['subsection_id'],
                                        subsection['subsection_name'],
                                        subsection['description'],
                                        subsection['difficulty_level'],
                                        # exercise['exercise_id'],
                                        exercise['exercise_number'],
                                        exercise['question_types'],
                                        exercise['tags'],
                                        exercise['description'],
                                        exercise['draw_by_skills'],
                                        exercise['draw_by_tag'],
                                        exercise['editing_allowed'],
                                        exercise['help'],
                                        exercise['instant_feedback'],
                                        exercise['moving_allowed'],
                                        exercise['number_to_draw'],
                                        exercise['passing_criterium'],
                                        exercise['save_seed'],
                                        exercise['seed'],
                                        exercise['shuffled'],
                                        exercise['text_before_start'],
                                        exercise['text_after_end'],
                                        exercise['timed_limit'],
                                        exercise['timed_type'],
                                        skills,
                                        exercise['is_repeatable'],
                                        # question['question_id'],
                                        orig_question,
                                        question['question_type'],
                                        orig_tags,
                                        # question['choices'],
                                        orig_choices,
                                        question['shuffle_options'],
                                        question['shuffle_answers'],
                                        question['num_eval'],
                                        orig_answer,
                                        question['correct'],
                                        question['incorrect'],
                                        question['feedback'],
                                        orig_skills,
                                        question['description']
                                        ])

                            #         if not course_flag:

                            #             course_flag = True
                            #             course['course_id'] = ""
                            #             course['course_name'] = ""
                            #             course['description'] = ""
                            #             course['difficulty_level'] = ""
                            #             course['requirements'] = ""

                            #         if not section_flag:

                            #             course_flag = True
                            #             section['section_id'] = ""
                            #             section['section_name'] = ""
                            #             section['description'] = ""
                            #             section['difficulty_level'] = ""

                            #         if not subsection_flag:

                            #             course_flag = True
                            #             subsection['subsection_id'] = ""
                            #             subsection['subsection_name'] = ""
                            #             subsection['description'] = ""
                            #             subsection['difficulty_level'] = ""

                            #         if not exercise_flag:

                            #             course_flag = True
                            #             exercise['exercise_id'] = ""
                            #             exercise['exercise_number'] = ""
                            #             exercise['question_types'] = ""
                            #             exercise['tags'] = ""
                            #             exercise['description'] = ""
                            #             exercise['draw_by_skills'] = ""
                            #             exercise['draw_by_tag'] = ""
                            #             exercise['editing_allowed'] = ""
                            #             exercise['help'] = ""
                            #             exercise['instant_feedback'] = ""
                            #             exercise['moving_allowed'] = ""
                            #             exercise['number_to_draw'] = ""
                            #             exercise['passing_criterium'] = ""
                            #             exercise['save_seed'] = ""
                            #             exercise['seed'] = ""
                            #             exercise['shuffled'] = ""
                            #             exercise['text_before_start'] = ""
                            #             exercise['text_after_end'] = ""
                            #             exercise['timed_limit'] = ""
                            #             exercise['timed_type'] = ""
                            #             skills = ""
                            #             exercise['is_repeatable'] = ""

                            # if not course_flag:

                            #     course_flag = True
                            #     course['course_id'] = ""
                            #     course['course_name'] = ""
                            #     course['description'] = ""
                            #     course['difficulty_level'] = ""
                            #     course['requirements'] = ""

                            # if not section_flag:

                            #     course_flag = True
                            #     section['section_id'] = ""
                            #     section['section_name'] = ""
                            #     section['description'] = ""
                            #     section['difficulty_level'] = ""

                            # if not subsection_flag:

                            #     course_flag = True
                            #     subsection['subsection_id'] = ""
                            #     subsection['subsection_name'] = ""
                            #     subsection['description'] = ""
                            #     subsection['difficulty_level'] = ""

        data['location'] = "templates/" + filename
        data['status'] = 'ok'

        # RETURN
        return data

    def check_tutor_course(self, userid, course_id):
        """ CHECK TUTOR COURSE """

        sql_str = "SELECT course_id FROM tutor_courses WHERE"
        sql_str += " course_id='{0}'".format(course_id)
        sql_str += " AND account_id='{0}'".format(userid)

        if not self.postgres.query_fetch_one(sql_str):

            return 0

        return 1

    # def use_course(self, course_id): # check common
    #     """ CHECK IF COURSE IN USE """

    #     sql_str = "SELECT * FROM student_course WHERE"
    #     sql_str += " course_id='{0}'".format(course_id)

    #     if not self.postgres.query_fetch_one(sql_str):

    #         return 1

    #     return 0

    def course_master(self, course_id):
        """ GET EXERCISES """

        sql_str = "SELECT * FROM course_master WHERE"
        sql_str += " course_id='{0}'".format(course_id)

        return self.postgres.query_fetch_all(sql_str)
