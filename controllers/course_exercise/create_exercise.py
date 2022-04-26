# pylint: disable=too-many-statements
"""Create Exercise"""
# import re
import math
import time
import json
# import unicodedata

from flask import request
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.questions import Questions

class CreateExercise(Common):
    """Class for CreateExercise"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CreateExercise class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        self.questions = Questions()

        super(CreateExercise, self).__init__()

    def create_exercise(self):
        """
        This API is for Creating Instruction
        ---
        tags:
          - Exercise
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
          - name: section_id
            in: query
            description: Section ID
            required: true
            type: string
          - name: subsection_id
            in: query
            description: Subsection ID
            required: true
            type: string
          - name: query
            in: body
            description: Create Exercise
            required: true
            schema:
              id: Create Exercise
              properties:
                description:
                    type: string
                question_types:
                    type: array
                    example: []
                status:
                    type: boolean
                number_to_draw:
                    type: integer
                seed:
                    type: integer
                save_seed:
                    type: boolean
                timed_type:
                    type: string
                timed_limit:
                    type: integer
                passing_criterium:
                    type: integer
                text_before_start:
                    type: string
                text_after_end:
                    type: string
                moving_allowed:
                    type: boolean
                instant_feedback:
                    type: boolean
                editing_allowed:
                    type: boolean
                draw_by_tag:
                    type: boolean
                shuffled:
                    type: boolean
                help:
                    type: boolean
                questions:
                    type: array
                    example: []
                tags:
                    type: array
                    example: []
                is_repeatable:
                    type: boolean
        responses:
          500:
            description: Error
          200:
            description: Create Exercise
        """
        data = {}

        # GET JSON REQUEST
        query_json = request.get_json(force=True)

        # GET HEADER
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        course_id = request.args.get('course_id')
        section_id = request.args.get('section_id')
        subsection_id = request.args.get('subsection_id')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # CHECK IF COURSE IS ALREADY IN USE
        course_ids = [course_id]
        if not self.use_course(course_ids):

            data["alert"] = "Course is in use!"
            data['status'] = 'Failed'

            return self.return_data(data, userid)

        if not 'question_types' in query_json.keys():

            query_json['question_types'] = []

        if not 'shuffled' in query_json.keys():

            query_json['shuffled'] = False

        if not 'tags' in query_json.keys():

            query_json['tags'] = []

        if query_json['draw_by_tag'] is True and not query_json['question_types']:

            data["alert"] = "Question Type is required"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        if query_json['draw_by_tag'] is False:

            if not len(query_json['questions']) >= int(query_json['number_to_draw']):

                data["alert"] = "Questions are not enough!"
                data['status'] = 'Failed'
                return self.return_data(data, userid)

        if not self.insert_exercise(course_id, section_id, subsection_id, query_json, userid):

            data["alert"] = "Please check your query!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        # SEND EMAIL TO TUTOR

        data['message'] = "Exercise successfully created!"
        data['status'] = "ok"

        return self.return_data(data, userid)

    def insert_exercise(self, course_id, section_id, subsection_id, query_json, userid):
        """Insert Exercise"""

        # if not query_json['exercise_number']:

        #     query_json['exercise_number'] = 1

        #     sql_str = "SELECT exercise_number FROM exercise WHERE"
        #     sql_str += " subsection_id='{0}'".format(subsection_id)
        #     sql_str += " ORDER BY exercise_number DESC"

        #     exer = self.postgres.query_fetch_one(sql_str)

        #     if exer:

        #         query_json['exercise_number'] = int(exer['exercise_number']) + 1

        exercise_number = self.check_next_exercise(subsection_id)
        data = {}
        data['exercise_id'] = self.sha_security.generate_token(False)
        data['subsection_id'] = subsection_id
        data['exercise_number'] = exercise_number
        data['course_id'] = course_id
        data['section_id'] = section_id
        data['description'] = query_json['description']
        data['question_types'] = json.dumps(query_json['question_types'])

        # CHECK VALID TAGS
        # self.check_valid_tags(json.dumps(query_json['tags']))

        data['tags'] = json.dumps(query_json['tags'])
        data['status'] = query_json['status']

        if query_json['number_to_draw']:
            data['number_to_draw'] = query_json['number_to_draw']
        data['seed'] = query_json['seed']

        data['save_seed'] = False
        if query_json['save_seed']:
            data['save_seed'] = query_json['save_seed']

        data['timed_type'] = query_json['timed_type']
        data['timed_limit'] = query_json['timed_limit']

        total_questions = query_json['number_to_draw']
        if query_json['questions']:
            total_questions = len(query_json['questions'])

        data['passing_criterium'] = math.ceil(int(total_questions)/2)
        if query_json['passing_criterium']:
            data['passing_criterium'] = query_json['passing_criterium']

        data['text_before_start'] = query_json['text_before_start']
        data['text_after_end'] = query_json['text_after_end']

        data['moving_allowed'] = False
        if query_json['moving_allowed']:
            data['moving_allowed'] = query_json['moving_allowed']

        data['instant_feedback'] = False
        if query_json['instant_feedback']:
            data['instant_feedback'] = query_json['instant_feedback']

        data['editing_allowed'] = False
        if query_json['editing_allowed']:
            data['editing_allowed'] = query_json['editing_allowed']

        data['draw_by_tag'] = False
        if query_json['draw_by_tag']:
            data['draw_by_tag'] = query_json['draw_by_tag']

        data['shuffled'] = False
        if query_json['shuffled']:
            data['shuffled'] = query_json['shuffled']

        data['help'] = False
        if query_json['help']:
            data['help'] = query_json['help']

        data['is_repeatable'] = False
        if query_json['is_repeatable']:
            data['is_repeatable'] = query_json['is_repeatable']

        data['created_on'] = time.time()

        # INSERT TO EXERCISE TABLE
        exercise_id = self.postgres.insert('exercise', data, 'exercise_id')

        if query_json['draw_by_tag'] is True:

            # SELECT QUESTION BY QUESTION TYPE AND TAGS
            # tags = []
            # if query_json['draw_by_tag'] is True:
            tags = query_json['tags']

            questions = self.generate_random_questions(query_json['question_types'],
                                                        int(query_json['number_to_draw']), tags)

        else:
            questions = query_json['questions']

            if questions and exercise_id:

                sequence_num = 0
                for question_id in questions:

                    sequence_num += 1
                    up_ex_quest = {}
                    up_ex_quest['question_id'] = question_id
                    up_ex_quest['exercise_id'] = exercise_id
                    up_ex_quest['sequence'] = sequence_num

                    self.postgres.insert('uploaded_exercise_question', up_ex_quest)

        if exercise_id:

            # INSERT TO COURSE QUESTION TABLE
            for question in questions:

                qdata = self.questions.get_question_by_id(question)

                if qdata:

                    tmp = {}
                    tmp['course_question_id'] = self.sha_security.generate_token(False)
                    tmp['course_id'] = course_id
                    tmp['section_id'] = section_id
                    tmp['subsection_id'] = subsection_id
                    tmp['exercise_id'] = exercise_id
                    tmp['question_id'] = question
                    tmp['question'] = json.dumps(qdata['question'])
                    tmp['question_type'] = qdata['question_type']
                    tmp['tags'] = json.dumps(qdata['tags'])
                    tmp['choices'] = json.dumps(qdata['choices'])
                    tmp['num_eval'] = qdata['num_eval']
                    tmp['correct_answer'] = json.dumps(qdata['correct_answer'])
                    tmp['correct'] = qdata['correct']
                    tmp['incorrect'] = qdata['incorrect']

                    if qdata['feedback']:
                        tmp['feedback'] = qdata['feedback']

                    if qdata['shuffle_options']:
                        tmp['shuffle_options'] = qdata['shuffle_options']

                    if qdata['shuffle_answers']:
                        tmp['shuffle_answers'] = qdata['shuffle_answers']

                    tmp['description'] = qdata['description']
                    tmp['status'] = qdata['status']
                    tmp['created_on'] = time.time()

                    self.postgres.insert('course_question', tmp, 'course_question_id')

            sql_str = "SELECT * FROM tutor_courses"
            sql_str += " WHERE course_id = '{0}'".format(course_id)
            sql_str += " AND account_id='{0}'".format(userid)
            result = self.postgres.query_fetch_one(sql_str)

            if result:

                sql_str = "SELECT * FROM exercise WHERE "
                sql_str += "exercise_id='{0}'".format(exercise_id)
                exercise = self.postgres.query_fetch_one(sql_str)

                if exercise:

                    sql_str = "SELECT * FROM tutor_section WHERE"
                    sql_str += " section_id='{0}'".format(exercise['section_id'])
                    sql_str += " AND account_id='{0}'".format(userid)
                    section = self.postgres.query_fetch_one(sql_str)

                    if not section:

                        temp = {}
                        temp['tutor_section_id'] = self.sha_security.generate_token(False)
                        temp['account_id'] = userid
                        temp['course_id'] = course_id
                        temp['section_id'] = exercise['section_id']
                        temp['progress'] = 0
                        temp['percent_score'] = 0
                        temp['status'] = True
                        temp['created_on'] = time.time() 
                        self.postgres.insert('tutor_section', temp, 'tutor_section_id')

                    sql_str = "SELECT * FROM tutor_subsection WHERE"
                    sql_str += " subsection_id='{0}'".format(exercise['subsection_id'])
                    sql_str += " AND account_id='{0}'".format(userid)
                    subsection = self.postgres.query_fetch_one(sql_str)

                    if not subsection:

                        temp = {}
                        temp['tutor_subsection_id'] = self.sha_security.generate_token(False)
                        temp['account_id'] = userid
                        temp['course_id'] = course_id
                        temp['section_id'] = exercise['section_id']
                        temp['subsection_id'] = exercise['subsection_id']
                        temp['progress'] = 0
                        temp['percent_score'] = 0
                        temp['status'] = True
                        temp['created_on'] = time.time()
                        self.postgres.insert('tutor_subsection', temp, 'tutor_subsection_id')

                    # tmp = {}
                    # tmp['tutor_exercise_id'] = self.sha_security.generate_token(False)
                    # tmp['exercise_id'] = exercise_id
                    # tmp['account_id'] = userid
                    # tmp['course_id'] = course_id
                    # tmp['exercise_number'] = exercise['exercise_number']
                    # tmp['time_used'] = 0
                    # tmp['score'] = 0
                    # tmp['progress'] = 0
                    # tmp['percent_score'] = 0
                    # tmp['status'] = True
                    # tmp['created_on'] = time.time()
                    # self.postgres.insert('tutor_exercise', tmp, 'tutor_exercise_id')
                    self.questions.generate_questions(userid, course_id, exercise_id, "tutor")
            
            return 1

        return 0

    # def use_course(self, course_id): # CHECK IN COMMON
    #     """ CHECK IF COURSE IN USE """

    #     sql_str = "SELECT * FROM student_course WHERE"
    #     sql_str += " course_id='{0}'".format(course_id)

    #     if not self.postgres.query_fetch_one(sql_str):

    #         return 1

    #     return 0

    def check_valid_tags(self, tags):
        """ CHECK VALID TAGS """

        sql_str = "SELECT * FROM tag_master WHERE"
        sql_str += " tags='{0}'".format(tags)


        if self.postgres.query_fetch_one(sql_str):

            return 1

        # new_tags = "".join(re.findall(r'[^\[\"$\"\]]', tags)).split(",")
        # unicodedata.normalize('NFKD', new_tags[2]).encode('ascii', 'ignore')
        # print("*"*100)
        # print(new_tags)
        # print("*"*100)
        # # if len(tags) == 1:

        # #     new_tags = tags[0]
        # #     unicodedata.normalize('NFKD', new_tags).encode('ascii', 'ignore')
        # #     new_tags = new_tags.split(",")

        # #     sql_str = "SELECT * FROM tag_master WHERE"
        # #     sql_str += " tags='{0}'".format(new_tags)

        # #     print(sql_str)

        return 0

    def check_next_exercise(self, subsection_id):
        """ Return Next Exercise Number """

        sql_str = "SELECT MAX(exercise_number::int) as exercise_number FROM exercise"
        sql_str += " WHERE subsection_id = '{0}' AND status is True".format(subsection_id)
        result = self.postgres.query_fetch_one(sql_str)

        exercise_number = 1

        if result and result['exercise_number']:
            exercise_number = int(result['exercise_number']) + 1

        return exercise_number
