
import re
import os
import csv
import time
import json

from library.common import Common

from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.log import Log

# reader = csv.DictReader(open('/Users/penn/Desktop/NMI/FR OLO - Sheet1 (4).csv', encoding='UTF-8'))

class CourseUploader(Common):
    """Class for CourseUploader"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CourseUploader"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()

        super(CourseUploader, self).__init__()

    def main(self):
        """Main"""

        reader = csv.DictReader(open('tempsdata/course1.csv', encoding='UTF-8'))

        headers = []
        Section = []
        Subsection = []
        Exercise = []
        Tags = []
        Question_Type = []


        course_id = ""
        section_id = ""
        subsection_id = ""
        exercise_id = ""

        for row in reader:

            if row['Cursus'] not in headers:

                print("Course: {0}".format(row['Cursus']))
                
                # COURSE
                sql_str = "SELECT course_id FROM course WHERE"
                sql_str += " course_name='{0}'".format(row['Cursus'])
                course = self.postgres.query_fetch_one(sql_str)

                if course:

                    course_id = course['course_id']

                else:

                    course_id = self.sha_security.generate_token(False)
                    data = {}
                    data['course_id'] = course_id
                    data['course_name'] = row['Cursus']
                    data['status'] = True
                    data['difficulty_level'] = 1
                    data['created_on'] = time.time()
                    self.postgres.insert('course', data)

                headers.append(row['Cursus'])



                sql_str = "SELECT account_id FROM account_role WHERE role_id"
                sql_str += " IN (SELECT role_id FROM role WHERE role_name='manager')"
                results = self.postgres.query_fetch_all(sql_str)

                for res in results or []:
                    account_id = res['account_id']
                    data = {}
                    data['account_id'] = account_id
                    data['course_id'] = course_id
                    data['status'] = True
                    data['created_on'] = time.time()
                    self.postgres.insert('tutor_courses', data)


            sections = "{0} : {1}".format(row['Cursus'], row['Section'])
            if sections not in Section:

                print("    Section: {0}".format(sections))

                # SECTION
                sql_str = "SELECT section_id FROM section WHERE"
                sql_str += " section_name='{0}'".format(row['Section'])
                sql_str += " AND course_id='{0}'".format(course_id)
                section = self.postgres.query_fetch_one(sql_str)

                if section:

                    section_id = section['section_id']

                else:

                    section_id = self.sha_security.generate_token(False)
                    updated_data = {}

                    updated_data['difficulty_level'] = self.get_sec_diff(course_id)
                    updated_data['course_id'] = course_id
                    updated_data['section_id'] = section_id
                    updated_data['section_name'] = row['Section']
                    updated_data['status'] = True
                    updated_data['created_on'] = time.time()

                    self.postgres.insert('section', updated_data)

                Section.append(sections)

            subsections = "{0} : {1} : {2}".format(row['Cursus'], row['Section'], row['Subsection'])
            if subsections not in Subsection:

                print("        Subsection: {0}".format(subsections))

                # SUBSECTION
                sql_str = "SELECT subsection_id FROM subsection WHERE"
                sql_str += " subsection_name='{0}'".format(row['Subsection'])
                sql_str += " AND course_id='{0}'".format(course_id)
                sql_str += " AND section_id='{0}'".format(section_id)
                subsection = self.postgres.query_fetch_one(sql_str)

                if subsection:

                    subsection_id = subsection['subsection_id']

                else:

                    subsection_id = self.sha_security.generate_token(False)
                    updated_data = {}

                    updated_data['difficulty_level'] = self.get_subsec_diff(course_id, section_id)

                    updated_data['course_id'] = course_id
                    updated_data['section_id'] = section_id
                    updated_data['subsection_id'] = subsection_id
                    updated_data['subsection_name'] = row['Subsection']
                    updated_data['status'] = True
                    updated_data['created_on'] = time.time()

                    self.postgres.insert('subsection', updated_data)

                Subsection.append(subsections)

            exercises = "{0} : {1} : {2} : {3}".format(row['Cursus'], row['Section'], row['Subsection'], row['Exercise'])

            if exercises not in Exercise:

                print("            Exercise: {0}".format(exercises))

                # EXERCISE
                sql_str = "SELECT exercise_id FROM exercise WHERE"
                sql_str += " exercise_number='{0}'".format(row['Exercise'])
                sql_str += " AND course_id='{0}'".format(course_id)
                sql_str += " AND section_id='{0}'".format(section_id)
                sql_str += " AND subsection_id='{0}'".format(subsection_id)
                exercise = self.postgres.query_fetch_one(sql_str)

                if exercise:

                    exercise_id = exercise['exercise_id']

                else:
                    exercise_id = self.sha_security.generate_token(False)
                    updated_data = {}
                    updated_data['draw_by_tag'] = False
                    updated_data['editing_allowed'] = True
                    updated_data['help'] = True
                    updated_data['instant_feedback'] = True
                    updated_data['moving_allowed'] = True
                    updated_data['number_to_draw'] = 16
                    updated_data['passing_criterium'] = 8
                    updated_data['save_seed'] = True
                    updated_data['seed'] = 10
                    updated_data['shuffled'] = False
                    updated_data['timed_limit'] = 300
                    updated_data['timed_type'] = 'per_question'
                    updated_data['course_id'] = course_id
                    updated_data['section_id'] = section_id
                    updated_data['subsection_id'] = subsection_id
                    updated_data['exercise_id'] = exercise_id
                    updated_data['exercise_number'] = row['Exercise']
                    updated_data['status'] = True
                    updated_data['created_on'] = time.time()

                    self.postgres.insert('exercise', updated_data)

                Exercise.append(exercises)



            # tags = "{0} : {1} : {2} : {3} : {4}".format(row['Cursus'], row['Section'], row['Subsection'], row['Exercise'], row['Tags'])

            # if tags not in Tags:

            # 	print("                Tags: {0}".format(tags))
            # 	Tags.append(tags)


            # question_type = "{0} : {1} : {2} : {3} : {4}".format(row['Cursus'], row['Section'], row['Subsection'], row['Exercise'], row['Question Type'])

            # if question_type not in Question_Type:

            # 	print("                Question_Type: {0}".format(question_type))
            # 	Question_Type.append(question_type)
            # 	print("\n")


    def get_sec_diff(self, course_id):
        """ GET SECTION DIFFICULTY LEVEL """

        sql_str = "SELECT difficulty_level FROM section WHERE"
        sql_str += " course_id = '{0}'".format(course_id)
        sql_str += " ORDER BY difficulty_level DESC LIMIT 1"
        section = self.postgres.query_fetch_one(sql_str)

        if not section:
            return 1
        else:
            return section['difficulty_level'] + 1

    def get_subsec_diff(self, course_id, section_id):
        """ GET SUBSECTION DIFFICULTY LEVEL """

        sql_str = "SELECT difficulty_level FROM subsection WHERE"
        sql_str += " course_id = '{0}'".format(course_id)
        sql_str += " AND section_id = '{0}'".format(section_id)
        sql_str += " ORDER BY difficulty_level DESC LIMIT 1"
        section = self.postgres.query_fetch_one(sql_str)

        if not section:
            return 1
        else:
            return section['difficulty_level'] + 1

TEST = CourseUploader()
TEST.main()
