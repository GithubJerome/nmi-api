# pylint: disable=too-many-statements, too-many-locals
"""Upload Exercise"""
import re
import csv
import time
import json

from configparser import ConfigParser
from flask import request
from library.config_parser import config_section_parser
from library.common import Common
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.questions import Questions

class UploadExercise(Common):
    """Class for UploadExerciseTemplate"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UploadExercise class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()
        self.config = ConfigParser()
        self.config.read("config/config.cfg")
        self.questions = Questions()

        super(UploadExercise, self).__init__()

    def upload_exercise(self):
        """
        This API is for Upload Exercise
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
          - name: courseid
            in: header
            description: Course ID
            required: true
            type: string
          - name: sectionid
            in: header
            description: Section ID
            required: true
            type: string
          - name: subsectionid
            in: header
            description: Subsection ID
            required: true
            type: string
          - name: upfile
            in: formData
            description: File temp
            required: true
            type: file
        consumes:
          - multipart/form-data
        responses:
          500:
            description: Error
          200:
            description: Upload Exercise
        """
        data = {}

        # GET HEADER
        token = request.headers.get('token')
        userid = request.headers.get('userid')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        ext = ""
        try:

            filename = request.files['upfile'].filename
            ext = filename.split(".")[-1]

            if not self.allowed_file_type(filename):

                data["alert"] = "File Type Not Allowed!"
                data['status'] = 'Failed'
                return self.return_data(data, userid)

        except ImportError:

            data["alert"] = "No File!"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        uploads = config_section_parser(self.config, "APPDIR")['dir']

        # SOURCE:
        # https://riptutorial.com/flask/example/19418/save-uploads-on-the-server

        file = request.files['upfile']
        filename = '/course_' + str(int(time.time())) + "." + ext
        # filename = secure_filename(filename)
        # file.save(os.path.join(uploads, filename))

        file_dir = uploads + filename
        file.save(file_dir)
        # reader = csv.DictReader(open(file_dir))

        # headers = next(csv.reader(open(file_dir)))

        reader = csv.DictReader(open(file_dir, encoding='unicode_escape'))

        headers = next(csv.reader(open(file_dir, encoding='unicode_escape')))

        if not self.check_headers(reader, headers):

            data["alert"] = "Invalid File!"
            data['status'] = 'Failed'
            return self.return_data(data, userid)

        updates = self.run_course_update(reader)

        if updates['status'] == "Failed":

            # RETURN ALERT
            return self.return_data(updates)

        data['message'] = "Course successfully updated!"
        data['status'] = "ok"

        return self.return_data(data, userid)

    #     course_id = request.headers.get('courseid')
    #     section_id = request.headers.get('sectionid')
    #     subsection_id = request.headers.get('subsectionid')

    #     # CHECK TOKEN
    #     token_validation = self.validate_token(token, userid, request)

    #     if not token_validation:
    #         data["alert"] = "Invalid Token"
    #         data['status'] = 'Failed'

    #         # RETURN ALERT
    #         return self.return_data(data, userid)

    #     # CHECK IF COURSE IS ALREADY IN USE
    #     if not self.use_course(course_id):

    #         data["alert"] = "Course is in use!"
    #         data['status'] = 'Failed'

    #         return data

    #     ext = ""
    #     try:

    #         filename = request.files['upfile'].filename
    #         ext = filename.split(".")[-1]

    #         if not self.allowed_file_type(filename):

    #             data["alert"] = "File Type Not Allowed!"
    #             data['status'] = 'Failed'
    #             return self.return_data(data, userid)

    #     except ImportError:

    #         data["alert"] = "No File!"
    #         data['status'] = 'Failed'

    #         # RETURN ALERT
    #         return self.return_data(data, userid)

    #     uploads = config_section_parser(self.config, "APPDIR")['dir']

    #     # SOURCE:
    #     # https://riptutorial.com/flask/example/19418/save-uploads-on-the-server

    #     file = request.files['upfile']
    #     filename = '/question_' + str(int(time.time())) + "." + ext
    #     # filename = secure_filename(filename)
    #     # file.save(os.path.join(uploads, filename))

    #     file_dir = uploads + filename
    #     file.save(file_dir)
    #     reader = csv.DictReader(open(file_dir))

    #     for row in reader:

    #         if row['Sample'].upper() == 'TRUE':

    #             continue

    #         tags = row['Tags'].replace("\"", "")
    #         row['tags'] = "".join(re.findall(r'[^\{$\}]', tags)).split(", ")

    #         qtypes = row['Question Types'].replace("\"", "")
    #         row['question_types'] = "".join(re.findall(r'[^\{$\}]', qtypes)).split(", ")

    #         temp = {}
    #         temp['exercise_id'] = self.sha_security.generate_token(False)
    #         temp['course_id'] = course_id
    #         temp['section_id'] = section_id
    #         temp['subsection_id'] = subsection_id
    #         temp['exercise_number'] = row['Exercise Number']
    #         temp['description'] = row['Description']
    #         temp['question_types'] = json.dumps(row['question_types'])
    #         temp['tags'] = json.dumps(row['tags'])
    #         temp['status'] = row['Status'].upper() == 'TRUE'
    #         temp['number_to_draw'] = row['Number to Draw']
    #         temp['seed'] = row['Seed']
    #         temp['save_seed'] = row['Save Seed'].upper() == 'TRUE'
    #         temp['timed_type'] = row['Timed Type']
    #         temp['timed_limit'] = row['Timed Limit']
    #         temp['passing_criterium'] = row['Passing Criterium']
    #         temp['text_before_start'] = row['Text Before Start']
    #         temp['text_after_end'] = row['Text After End']
    #         temp['moving_allowed'] = row['Moving Allowed'].upper() == 'TRUE'
    #         temp['instant_feedback'] = row['Instant Feedback'].upper() == 'TRUE'
    #         temp['editing_allowed'] = row['Editing Allowed'].upper() == 'TRUE'
    #         temp['draw_by_tag'] = row['Draw by Tag'].upper() == 'TRUE'
    #         temp['shuffled'] = row['Shuffled'].upper() == 'TRUE'
    #         temp['help'] = row['Help'].upper() == 'TRUE'
    #         temp['created_on'] = time.time()

    #         exercise_id = self.postgres.insert('exercise', temp, 'exercise_id')
    #         if not exercise_id:
    #             data['alert'] = "An error occured while uploading the file!"
    #             data['status'] = "failed"
    #             return self.return_data(data, userid)

    #         # RANDOMLY PICK QUESTIONS
    #         self.add_random_questions(row, exercise_id, course_id, section_id, subsection_id)

    #     data['message'] = "Exercise successfully uploaded!"
    #     data['status'] = "ok"

    #     return self.return_data(data, userid)

    # def add_random_questions(self, row, exercise_id, course_id, section_id, subsection_id):
    #     """ Insert Random Questions """

    #     # if row['Shuffled'] in [True, 'T', 't', 1]:
    #     if row['Shuffled'].upper() == 'TRUE':

    #         # SELECT QUESTION BY QUESTION TYPE AND TAGS
    #         question_types = ['FITBT'] # DEFAULT
    #         if row['question_types']:
    #             question_types = row['question_types']

    #         tags = []
    #         # if row['Draw by Tag'] in [True, 'T', 't', 1]:
    #         if row['Draw by Tag'].upper() == 'TRUE':
    #             tags = row['tags']

    #         questionnaires = self.questions.get_questions_byCondition(question_types, tags)
    #         questions = self.questions.select_random_questions(questionnaires,
    #                                                            row['Number to Draw'],
    #                                                            question_types)

    #         # INSERT TO COURSE QUESTION TABLE
    #         for question in questions:

    #             qdata = self.questions.get_question_byID(question)

    #             if qdata:

    #                 tmp = {}
    #                 tmp['course_question_id'] = self.sha_security.generate_token(False)
    #                 tmp['course_id'] = course_id
    #                 tmp['section_id'] = section_id
    #                 tmp['subsection_id'] = subsection_id
    #                 tmp['exercise_id'] = exercise_id
    #                 tmp['question_id'] = question
    #                 tmp['question'] = json.dumps(qdata['question'])
    #                 tmp['question_type'] = qdata['question_type']
    #                 tmp['tags'] = json.dumps(qdata['tags'])
    #                 tmp['choices'] = json.dumps(qdata['choices'])
    #                 tmp['num_eval'] = qdata['num_eval']
    #                 tmp['correct_answer'] = json.dumps(qdata['correct_answer'])
    #                 tmp['correct'] = qdata['correct']
    #                 tmp['incorrect'] = qdata['incorrect']

    #                 if qdata['feedback']:
    #                     tmp['feedback'] = qdata['feedback']

    #                 if qdata['shuffle_options']:
    #                     tmp['shuffle_options'] = qdata['shuffle_options']

    #                 if qdata['shuffle_answers']:
    #                     tmp['shuffle_answers'] = qdata['shuffle_answers']

    #                 tmp['description'] = qdata['description']
    #                 tmp['status'] = qdata['status']
    #                 tmp['created_on'] = time.time()

    #                 self.postgres.insert('course_question', tmp, 'course_question_id')

    # def use_course(self, course_id):
    #     """ CHECK IF COURSE IN USE """

    #     sql_str = "SELECT * FROM student_course WHERE"
    #     sql_str += " course_id='{0}'".format(course_id)

    #     if not self.postgres.query_fetch_one(sql_str):

    #         return 1

    #     return 0
