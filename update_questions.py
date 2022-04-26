# pylint: disable=too-many-locals, unused-import, too-many-nested-blocks, unnecessary-pass,  too-many-statements, too-many-function-args, too-many-branches, too-many-instance-attributes, attribute-defined-outside-init
"""Set Up"""
from __future__ import print_function
import re
import os
import json
import csv
import time
import pathlib
import random
from configparser import ConfigParser
from library.common import Common

from library.config_parser import config_section_parser
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.log import Log

class UpdateAnswers(Common):
    """Class for UpdateAnswers"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateAnswers class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()

        super(UpdateAnswers, self).__init__()

    def main(self):
        """Main"""
        reader = csv.DictReader(open('tempsdata/tempsdata2.csv', encoding='UTF-8'))

        ctr = 0
        for row in reader:
            continue

            ctr += 1

            temp_question = {}
            temp_question['question'] = row['Question'].replace(",", ".")
            question = json.dumps(temp_question)

            sql_str = "SELECT question_id, question ,correct_answer FROM questions WHERE"
            sql_str += " question='{0}'".format(question)
            sql_str += " AND question_type='{0}'".format(row['Question Type'])
            response = self.postgres.query_fetch_one(sql_str)
            # print("sql_str: {0}".format((sql_str)))
            # print("response: {0}".format((response)))

            if response:
                question_id = response['question_id']

                old_correct_answer = response['correct_answer']

                correct_answer = {}
                # new_correct_answer = row['Question'].split('<ans>:<ans>:<ans>')[0] + row['Correct Answer']
                new_correct_answer = [temp_question['question'].replace("<ans>", row['Correct Answer'])]
                # new_correct_answer = [str(row['Correct Answer'])]
                correct_answer['answer'] = new_correct_answer

                print(ctr,
                      ". ",
                      question_id,
                      " : ",
                      json.dumps(old_correct_answer),
                      " -> ",
                      json.dumps(correct_answer))

                # # QUESTION UPDATE

                qupdate = {}
                qupdate['correct_answer'] = json.dumps(correct_answer)

                conditions = []
                conditions.append({
                    "col": "question_id",
                    "con": "=",
                    "val": question_id
                })

                self.postgres.update('questions', qupdate, conditions)


                sql_str = "SELECT course_question_id, correct_answer FROM"
                sql_str += " course_question WHERE"
                sql_str += " question_id='{0}'".format(question_id)
                course_questions = self.postgres.query_fetch_all(sql_str)

                for cq1 in course_questions or []:

                    course_question_id = cq1['course_question_id']
                    old_correct_answer = cq1['correct_answer']
                    print(ctr,
                          ". ",
                          course_question_id,
                          " : ",
                          json.dumps(old_correct_answer),
                          " -> ",
                          json.dumps(correct_answer))

                    # # UPDATE COURSE QUESTION
                    cqupdate = {}
                    cqupdate['correct_answer'] = json.dumps(correct_answer)

                    conditions = []
                    conditions.append({
                        "col": "course_question_id",
                        "con": "=",
                        "val": course_question_id
                    })

                    self.postgres.update('course_question', cqupdate, conditions)

            else:

                continue
                temp_question = {}
                temp_question['question'] = row['Question'].replace(",", ".")
                temp_question['question'] = temp_question['question'].replace(" : ", " ÷ ")
                question = json.dumps(temp_question)

                sql_str = "SELECT question_id, question ,correct_answer FROM questions WHERE"
                sql_str += " question='{0}'".format(question)
                sql_str += " AND question_type='{0}'".format(row['Question Type'])
                response = self.postgres.query_fetch_one(sql_str)

                if response:
                    question_id = response['question_id']
                    old_correct_answer = response['correct_answer']

                    correct_answer = {}
                    # new_correct_answer = row['Question'].split('<ans>:<ans>:<ans>')[0] + row['Correct Answer']
                    new_correct_answer = [temp_question['question'].replace("<ans>", row['Correct Answer'])]
                    # new_correct_answer = [str(row['Correct Answer'])]
                    correct_answer['answer'] = new_correct_answer

                    print(ctr,
                        ". ",
                        question_id,
                        " : ",
                        json.dumps(old_correct_answer),
                        " -> ",
                        json.dumps(correct_answer))

                    # # QUESTION UPDATE

                    qupdate = {}
                    qupdate['correct_answer'] = json.dumps(correct_answer)

                    conditions = []
                    conditions.append({
                        "col": "question_id",
                        "con": "=",
                        "val": question_id
                    })

                    self.postgres.update('questions', qupdate, conditions)


                    sql_str = "SELECT course_question_id, correct_answer FROM"
                    sql_str += " course_question WHERE"
                    sql_str += " question_id='{0}'".format(question_id)
                    course_questions = self.postgres.query_fetch_all(sql_str)

                    for cq1 in course_questions or []:

                        course_question_id = cq1['course_question_id']
                        old_correct_answer = cq1['correct_answer']
                        print(ctr,
                            ". ",
                            course_question_id,
                            " : ",
                            json.dumps(old_correct_answer),
                            " -> ",
                            json.dumps(correct_answer))

                        # # UPDATE COURSE QUESTION
                        cqupdate = {}
                        cqupdate['correct_answer'] = json.dumps(correct_answer)

                        conditions = []
                        conditions.append({
                            "col": "course_question_id",
                            "con": "=",
                            "val": course_question_id
                        })

                        self.postgres.update('course_question', cqupdate, conditions)

                else:
                    print("*"*100)
                    print("sql_str: {0}".format(sql_str))
                    print("*"*100)

    def update_decimal(self):
        """ UPDATE DECIMAL """

        sql_str = "SELECT question_id, question, correct_answer FROM questions"
        questions = self.postgres.query_fetch_all(sql_str)

        for quest in questions or []:

            if "," in quest['question']['question'] or "," in quest['correct_answer']['answer']:

                print(quest['question_id'], " : ", quest['question']['question'], " : ", quest['correct_answer']['answer'])

                try:

                    new_quest = quest['question']['question'].replace(",", ".")

                except:

                    new_quest = quest['question']['question']

                try:

                    new_ans = quest['correct_answer']['answer'].replace(",", ".")

                except:

                    new_ans = quest['correct_answer']['answer']

                print(quest['question_id'], " : ", new_quest, " : ", new_ans)


                correct_answer = {}
                correct_answer['answer'] = new_ans
            
                new_question = {}
                new_question['question'] = new_quest

                # UPDATE COURSE QUESTION
                cqupdate = {}
                cqupdate['correct_answer'] = json.dumps(correct_answer)
                cqupdate['question'] = json.dumps(new_question)

                conditions = []
                conditions.append({
                    "col": "question_id",
                    "con": "=",
                    "val": quest['question_id']
                })

                self.postgres.update('questions', cqupdate, conditions)
                self.postgres.update('course_question', cqupdate, conditions)


        return 1

class UpdateSkills(Common):
    """Class for UpdateSkills"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateSkills class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()

        super(UpdateSkills, self).__init__()

    def main(self):
        """Main"""
        sql_str = """SELECT s.skill, (SELECT array_to_json(array_agg(subs))
                    FROM (SELECT sub.subskill FROM skill_subskills sksub INNER
                    JOIN subskills sub ON sksub.subskill_id=sub.subskill_id AND
                    s.skill_id=sksub.skill_id) AS subs) AS subskills FROM skills s"""

        skills = self.postgres.query_fetch_all(sql_str)

        for skill in skills or []:

            new_skill = skill['skill']
            new_subskill = [subs['subskill'] for subs in skill['subskills'] or []]
            self.update_master_skills(new_skill, new_subskill)

class UpdateChoices(Common):
    """ UPDATE CHOICES """

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateChoices class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()

        super(UpdateChoices, self).__init__()


    def main(self):
        """Main"""
        reader = csv.DictReader(open('tempsdata/tempsdata.csv', encoding='UTF-8'))

        ctr = 0
        for row in reader:

            ctr += 1

            temp_question = {}
            temp_question['question'] = row['Question'].replace(",", ".")
            question = json.dumps(temp_question)

            sql_str = "SELECT question_id, correct_answer, choices FROM questions WHERE"
            sql_str += " question='{0}'".format(question)
            sql_str += " AND question_type='{0}'".format(row['Question Type'])
            response = self.postgres.query_fetch_one(sql_str)

            if response:

                question_id = response['question_id']
                old_choices = response['choices']
                new_choices = "".join(re.findall(r'[^\{$\}]', row['Choices']))
                new_choices = new_choices.split(", ")

                if len(new_choices) == 1:
                    new_choices = new_choices[0].split(",")

                print(ctr,
                      ". ",
                      question_id,
                      " : ",
                      json.dumps(old_choices),
                      " -> ",
                      json.dumps(new_choices))

                # # QUESTION UPDATE
                continue

                qupdate = {}
                qupdate['choices'] = json.dumps(new_choices)

                conditions = []
                conditions.append({
                    "col": "question_id",
                    "con": "=",
                    "val": question_id
                })

                self.postgres.update('questions', qupdate, conditions)

                sql_str = "SELECT course_question_id, correct_answer, choices  FROM"
                sql_str += " course_question WHERE"
                sql_str += " question_id='{0}'".format(question_id)
                course_questions = self.postgres.query_fetch_all(sql_str)

                for cq1 in course_questions or []:

                    course_question_id = cq1['course_question_id']
                    old_choices = cq1['choices']
                    print(ctr,
                          ". ",
                          course_question_id,
                          " : ",
                          json.dumps(old_choices),
                          " -> ",
                          json.dumps(new_choices))

                    # # UPDATE COURSE QUESTION
                    cqupdate = {}
                    cqupdate['choices'] = json.dumps(new_choices)

                    conditions = []
                    conditions.append({
                        "col": "course_question_id",
                        "con": "=",
                        "val": course_question_id
                    })

                    self.postgres.update('course_question', cqupdate, conditions)

class UpdateQuestions(Common):
    """Class for UpdateQuestions"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateQuestions class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()

        super(UpdateQuestions, self).__init__()

    def main(self):
        """Main"""
        reader = csv.DictReader(open('tempsdata/tempsdata1.csv', encoding='UTF-8'))

        ctr = 0
        for row in reader:

            ctr += 1

            temp_question = {}
            temp_question['question'] = row['Question'].replace(",", ".")
            question = json.dumps(temp_question)

            sql_str = "SELECT question_id, question FROM questions WHERE"
            sql_str += " question='{0}'".format(question)
            sql_str += " AND question_type='{0}'".format(row['Question Type'])
            response = self.postgres.query_fetch_one(sql_str)
            # print("sql_str: {0}".format((sql_str)))
            # print("response: {0}".format((response)))

            if response:

                question_id = response['question_id']
                old_question = response['question']

                new_question = {}
                # new_question = row['Question'].split('<ans>:<ans>:<ans>')[0] + row['Correct Answer']
                question1 = str(row['Question']).replace(",", ".")
                new_question['question'] = question1 + "/<ans>"

                print(ctr,
                      ". ",
                      question_id,
                      " : ",
                      json.dumps(old_question),
                      " -> ",
                      json.dumps(new_question))

                # # QUESTION UPDATE
                continue

                qupdate = {}
                qupdate['question'] = json.dumps(new_question)

                conditions = []
                conditions.append({
                    "col": "question_id",
                    "con": "=",
                    "val": question_id
                })

                self.postgres.update('questions', qupdate, conditions)


                sql_str = "SELECT course_question_id, question FROM"
                sql_str += " course_question WHERE"
                sql_str += " question_id='{0}'".format(question_id)
                course_questions = self.postgres.query_fetch_all(sql_str)

                for cq1 in course_questions or []:

                    course_question_id = cq1['course_question_id']
                    old_question = cq1['question']
                    print(ctr,
                          ". ",
                          course_question_id,
                          " : ",
                          json.dumps(old_question),
                          " -> ",
                          json.dumps(new_question))

                    # # UPDATE COURSE QUESTION
                    cqupdate = {}
                    cqupdate['question'] = json.dumps(new_question)

                    conditions = []
                    conditions.append({
                        "col": "course_question_id",
                        "con": "=",
                        "val": course_question_id
                    })

                    self.postgres.update('course_question', cqupdate, conditions)


class UpdateQuestionsDB(Common):
    """Class for UpdateQuestionsDB"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateQuestionsDB class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()

        super(UpdateQuestionsDB, self).__init__()

    def main(self):
        """Main"""
        sql_str = "SELECT * FROM questions"
        questions = self.postgres.query_fetch_all(sql_str)

        ctr = 0
        for row in questions:

            if ' / ' in row['question']['question']:
            # if 'rest' in row['question']['question']:

                question_id = row['question_id']
                ctr += 1

                new_question = {}
                new_question['question'] = str(row['question']['question'].replace(" / ", " ÷ "))
                # new_question['question'] = str(row['question']['question'].replace("rest", "remainder"))

                print(ctr,
                      ". ",
                      question_id,
                      " : ",
                      json.dumps(row['question']),
                      " -> ",
                      json.dumps(new_question))

                # QUESTION UPDATE
                qupdate = {}
                qupdate['question'] = json.dumps(new_question)

                conditions = []
                conditions.append({
                    "col": "question_id",
                    "con": "=",
                    "val": question_id
                })

                self.postgres.update('questions', qupdate, conditions)


                sql_str = "SELECT course_question_id, question FROM"
                sql_str += " course_question WHERE"
                sql_str += " question_id='{0}'".format(question_id)
                course_questions = self.postgres.query_fetch_all(sql_str)

                for cq1 in course_questions or []:

                    course_question_id = cq1['course_question_id']
                    old_question = cq1['question']
                    print(ctr,
                          ". ",
                          course_question_id,
                          " : ",
                          json.dumps(old_question),
                          " -> ",
                          json.dumps(new_question))

                    # # UPDATE COURSE QUESTION
                    cqupdate = {}
                    cqupdate['question'] = json.dumps(new_question)

                    conditions = []
                    conditions.append({
                        "col": "course_question_id",
                        "con": "=",
                        "val": course_question_id
                    })

                    self.postgres.update('course_question', cqupdate, conditions)


class UpdateAnswerDB(Common):
    """Class for UpdateAnswerDB"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateAnswerDB class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()

        super(UpdateAnswerDB, self).__init__()

    def main(self):
        """Main"""
        sql_str = "SELECT * FROM questions"
        questions = self.postgres.query_fetch_all(sql_str)

        ctr = 0
        for row in questions:

            if ' / ' in row['correct_answer']['answer']:
            # if 'rest' in row['correct_answer']['answer']:

                question_id = row['question_id']
                ctr += 1

                new_answer = {}
                new_answer['answer'] = str(row['correct_answer']['answer'].replace(" / ", " ÷ "))
                # new_answer['answer'] = str(row['correct_answer']['answer'].replace("rest", "remainder"))

                print(ctr,
                      ". ",
                      question_id,
                      " : ",
                      json.dumps(row['correct_answer']),
                      " -> ",
                      json.dumps(new_answer))

                # QUESTION UPDATE
                qupdate = {}
                qupdate['correct_answer'] = json.dumps(new_answer)

                conditions = []
                conditions.append({
                    "col": "question_id",
                    "con": "=",
                    "val": question_id
                })

                self.postgres.update('questions', qupdate, conditions)

                sql_str = "SELECT course_question_id, correct_answer FROM"
                sql_str += " course_question WHERE"
                sql_str += " question_id='{0}'".format(question_id)
                course_questions = self.postgres.query_fetch_all(sql_str)

                for cq1 in course_questions or []:

                    course_question_id = cq1['course_question_id']
                    old_answer = cq1['correct_answer']
                    print(ctr,
                          ". ",
                          course_question_id,
                          " : ",
                          json.dumps(old_answer),
                          " -> ",
                          json.dumps(new_answer))

                    # # UPDATE COURSE QUESTION
                    cqupdate = {}
                    cqupdate['correct_answer'] = json.dumps(new_answer)

                    conditions = []
                    conditions.append({
                        "col": "course_question_id",
                        "con": "=",
                        "val": course_question_id
                    })

                    self.postgres.update('course_question', cqupdate, conditions)


class UpdateQuestionsRest(Common):
    """Class for UpdateQuestionsRest"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateQuestionsRest class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()

        super(UpdateQuestionsRest, self).__init__()

    def main(self):
        """Main"""
        sql_str = "SELECT * FROM questions"
        questions = self.postgres.query_fetch_all(sql_str)

        ctr = 0
        for row in questions:

            # if ' = <ans>%' in row['question']['question']:
            if '3/5 = <ans>%' in row['question']['question']:

                question_id = row['question_id']
                ctr += 1

                new_answer = {}
                new_question = {}
                # new_question['question'] = str(row['question']['question'].replace("Decimaal", "Decimal"))
                # new_question['question'] = new_question['question'].replace("Decimalen", "Decimals")

                # new_answer['answer'] = str(row['correct_answer']['answer'].replace("Decimaal", "Decimal"))
                # new_answer['answer'] = new_answer['answer'].replace("Decimalen", "Decimals")

                print(ctr,
                      ". ",
                      question_id,
                      " : ",
                      row['question'],
                      " -> ",
                      new_question)
                print(ctr,
                      ". ",
                      question_id,
                      " : ",
                      row['correct_answer'],
                      " -> ",
                      new_answer)

                continue
                # QUESTION UPDATE
                qupdate = {}
                qupdate['question'] = json.dumps(new_question)
                qupdate['correct_answer'] = json.dumps(new_answer)

                conditions = []
                conditions.append({
                    "col": "question_id",
                    "con": "=",
                    "val": question_id
                })

                self.postgres.update('questions', qupdate, conditions)


                sql_str = "SELECT course_question_id, correct_answer, question FROM"
                sql_str += " course_question WHERE"
                sql_str += " question_id='{0}'".format(question_id)
                course_questions = self.postgres.query_fetch_all(sql_str)

                for cq1 in course_questions or []:

                    course_question_id = cq1['course_question_id']
                    old_question = cq1['question']
                    old_answer = cq1['correct_answer']
                    print(ctr,
                          ". ",
                          course_question_id,
                          " : ",
                          json.dumps(old_question),
                          " -> ",
                          json.dumps(new_question))
                    print(ctr,
                          ". ",
                          course_question_id,
                          " : ",
                          json.dumps(old_answer),
                          " -> ",
                          json.dumps(new_answer))


                    # # UPDATE COURSE QUESTION
                    cqupdate = {}
                    cqupdate['question'] = json.dumps(new_question)
                    cqupdate['correct_answer'] = json.dumps(new_answer)

                    conditions = []
                    conditions.append({
                        "col": "course_question_id",
                        "con": "=",
                        "val": course_question_id
                    })

                    self.postgres.update('course_question', cqupdate, conditions)

class CheckQuestions(Common):
    """Class for CheckQuestions"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CheckQuestions class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()

        super(CheckQuestions, self).__init__()

    def main(self):
        """Main"""
        reader = csv.DictReader(open('tempsdata/tempsdata3.csv', encoding='UTF-8'))

        ctr = 0
        for row in reader:

            ctr += 1

            temp_question = {}
            temp_question['question'] = row['Question'].replace(",", ".")
            question = json.dumps(temp_question)

            sql_str = "SELECT question_id, question, correct_answer FROM questions WHERE"
            sql_str += " question='{0}'".format(question)
            sql_str += " AND question_type='{0}'".format(row['Question Type'])
            response = self.postgres.query_fetch_one(sql_str)
            # print("sql_str: {0}".format((sql_str)))
            # print("response: {0}".format((response)))

            if response:

                question_id = response['question_id']
                old_correct_answer = response['correct_answer']
                new_correct_answer = {}
                new_correct_answer['answer'] = temp_question['question'].replace("<ans>", row['Correct Answer'])

                if new_correct_answer == old_correct_answer:

                    continue

                print(ctr,
                      ". ",
                      question_id,
                      " : ",
                      old_correct_answer,
                      " -> ",
                      new_correct_answer)

                # # QUESTION UPDATE
                # continue

                qupdate = {}
                qupdate['correct_answer'] = json.dumps(new_correct_answer)

                conditions = []
                conditions.append({
                    "col": "question_id",
                    "con": "=",
                    "val": question_id
                })

                # self.postgres.update('questions', qupdate, conditions)


                sql_str = "SELECT course_question_id, question, correct_answer FROM"
                sql_str += " course_question WHERE"
                sql_str += " question_id='{0}'".format(question_id)
                course_questions = self.postgres.query_fetch_all(sql_str)

                for cq1 in course_questions or []:

                    course_question_id = cq1['course_question_id']
                    old_correct_answer = response['correct_answer']
                    print(ctr,
                          ". ",
                          course_question_id,
                          " : ",
                          json.dumps(old_correct_answer),
                          " -> ",
                          json.dumps(new_correct_answer))

                    # # UPDATE COURSE QUESTION
                    cqupdate = {}
                    cqupdate['correct_answer'] = json.dumps(new_correct_answer)

                    conditions = []
                    conditions.append({
                        "col": "course_question_id",
                        "con": "=",
                        "val": course_question_id
                    })

                    # self.postgres.update('course_question', cqupdate, conditions)

class ValidateQuestions(Common):
    """Class for ValidateQuestions"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for ValidateQuestions class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()

        super(ValidateQuestions, self).__init__()

    def main(self):
        """Main"""
        # sql_str = "SELECT * FROM questions"
        sql_str = "SELECT * FROM course_question"
        questions = self.postgres.query_fetch_all(sql_str)

        ctr = 0
        for row in questions:

            ctr += 1

            question_id = row['question_id']
            old_question = row['question']

            sql_str = "SELECT question FROM questions"
            sql_str += " WHERE question='{0}'".format(json.dumps(old_question))
            res = self.postgres.query_fetch_one(sql_str)

            if not res:

                sql_str = "SELECT * FROM questions"
                sql_str += " WHERE question_id='{0}'".format(question_id)
                final_question = self.postgres.query_fetch_one(sql_str)
                new_question = final_question['question']

                print(ctr,
                        ". ",
                        question_id,
                        " : ",
                        old_question,
                        " -> ",
                        new_question)


                # # UPDATE COURSE QUESTION
                cqupdate = {}
                cqupdate['question'] = json.dumps(new_question)

                conditions = []
                conditions.append({
                    "col": "question_id",
                    "con": "=",
                    "val": question_id
                })

                self.postgres.update('course_question', cqupdate, conditions)

class ValidateAnswers(Common):
    """Class for ValidateAnswers"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for ValidateAnswers class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()

        super(ValidateAnswers, self).__init__()

    def main(self):
        """Main"""
        # sql_str = "SELECT * FROM questions"
        sql_str = "SELECT * FROM course_question"
        questions = self.postgres.query_fetch_all(sql_str)

        ctr = 0
        for row in questions:

            ctr += 1

            question_id = row['question_id']
            old_correct_answer = row['correct_answer']

            sql_str = "SELECT question FROM questions"
            sql_str += " WHERE correct_answer='{0}'".format(json.dumps(old_correct_answer))
            res = self.postgres.query_fetch_one(sql_str)

            if not res:

                sql_str = "SELECT * FROM questions"
                sql_str += " WHERE question_id='{0}'".format(question_id)
                final_question = self.postgres.query_fetch_one(sql_str)
                new_correct_answer = final_question['correct_answer']

                print(ctr,
                        ". ",
                        question_id,
                        " : ",
                        old_correct_answer,
                        " -> ",
                        new_correct_answer)


                # # UPDATE COURSE QUESTION
                cqupdate = {}
                cqupdate['correct_answer'] = json.dumps(new_correct_answer)

                conditions = []
                conditions.append({
                    "col": "question_id",
                    "con": "=",
                    "val": question_id
                })

                # self.postgres.update('course_question', cqupdate, conditions


class UpdateOriginal(Common):
    """Class for UpdateOriginal"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateOriginal class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()

        super(UpdateOriginal, self).__init__()

    def main(self):
        """Main"""
        # reader = csv.DictReader(open('tempsdata/tempsdata3.csv', encoding='UTF-8'))
        # reader = csv.DictReader(open('tempsdata/recepten.csv', encoding='UTF-8'))
        reader = csv.DictReader(open('tempsdata/added.csv', encoding='UTF-8'))

        ctr = 0
        for row in reader:

            row['Question Tags'] = row['Tags']
            row['Question Choices'] = row['Choices']
            row['Question Shuffle Options'] = row['Shuffle Options']
            row['Question Shuffle Answers'] = row['Shuffle Answers']
            row['Question Num Eval'] = row['Num Eval']
            row['Question Correct Answer'] = row['Correct Answer']
            row['Question Correct'] = row['Correct']
            row['Question Incorrect'] = row['Incorrect']
            row['Question Feedback'] = row['Feedback']
            row['Question Description'] = row['Description']
            row['Question Skills'] = row['skills']

            row['Question'] = row['Question'].replace(" : ", " ÷ ")
            row['Question Correct Answer'] = row['Question Correct Answer'].replace(" : ", " ÷ ")

            row['Question'] = row['Question'].replace(" / ", " ÷ ")
            row['Question Correct Answer'] = row['Question Correct Answer'].replace(" / ", " ÷ ")

            row['Question'] = row['Question'].replace("rest", "remainder")
            row['Question Correct Answer'] = row['Question Correct Answer'].replace("rest", "remainder")

            row['Question'] = row['Question'].replace(",", ".")
            if not 'reduced' in row['Question Correct Answer']:
                row['Question Correct Answer'] = row['Question Correct Answer'].replace(",", ".")

            correct_answer, question, array_choice, tags = self.arrange_question(row)

            if correct_answer['answer'][0] in [" =", " >", " <"] and array_choice == ["<", "=", ">"]:

                new_cor = correct_answer['answer'][0].replace(" ", "")
                row['Question Correct Answer'] = row['Question'].replace("<ans>", new_cor)
                correct_answer, question, array_choice, tags = self.arrange_question(row)

            # if ' ~ € ' in row['Question']:

            #     row['Question Correct Answer'] = str(row['Question Correct Answer']) + '.00'
            #     correct_answer, question, array_choice, tags = self.arrange_question(row)

            sql_str = "SELECT question_id, orig_question, orig_answer,"
            sql_str += " orig_choices, orig_skills, orig_tags FROM questions WHERE"
            sql_str += " question='{0}'".format(json.dumps(question))
            sql_str += " AND question_type='{0}'".format(row['Question Type'])
            sql_str += " AND choices='{0}'".format(json.dumps(array_choice))
            sql_str += " AND tags='{0}'".format(json.dumps(tags))
            sql_str += " AND correct_answer='{0}'".format(json.dumps(correct_answer))

            questions = self.postgres.query_fetch_one(sql_str)

            if not questions:


                correct_answer['answer'] = [correct_answer['answer']]
                sql_str = "SELECT question_id, orig_question, orig_answer,"
                sql_str += " orig_choices, orig_skills, orig_tags FROM questions WHERE"
                sql_str += " question='{0}'".format(json.dumps(question))
                sql_str += " AND question_type='{0}'".format(row['Question Type'])
                sql_str += " AND choices='{0}'".format(json.dumps(array_choice))
                sql_str += " AND tags='{0}'".format(json.dumps(tags))
                sql_str += " AND correct_answer='{0}'".format(json.dumps(correct_answer))

                questions = self.postgres.query_fetch_one(sql_str)

                if not questions:
                    
                    ctr += 1
                    print("{0}. row['Question']: {1}".format(ctr, row['Question']))
                    print("sql: {0}".format(sql_str))

            # continue

            if questions:

                print("Question ID: {0}".format(questions))


                question_id = questions['question_id']
                orig_question = questions['orig_question']
                orig_answer = questions['orig_answer']
                orig_choices = questions['orig_choices']
                orig_skills = questions['orig_skills']

                if not orig_question:

                    # UPDATE QUESTION
                    orig_question = {}
                    orig_question['question'] = row['Question']

                    updated_data = {}
                    updated_data['orig_question'] = json.dumps(orig_question)

                    conditions = []

                    # CONDITION FOR QUERY
                    conditions.append({
                        "col": "question_id",
                        "con": "=",
                        "val": question_id
                        })

                    self.postgres.update('questions', updated_data, conditions)

                if not orig_answer:

                    orig_answer = {}
                    orig_answer['answer'] = row['Question Correct Answer']

                    updated_data = {}
                    updated_data['orig_answer'] = json.dumps(orig_answer)

                    conditions = []

                    # CONDITION FOR QUERY
                    conditions.append({
                        "col": "question_id",
                        "con": "=",
                        "val": question_id
                        })

                    self.postgres.update('questions', updated_data, conditions)

                if not orig_skills and row['Question Skills']:

                    orig_skills = {}
                    orig_skills['skills'] = row['Question Skills']

                    updated_data = {}
                    updated_data['orig_skills'] = json.dumps(orig_skills)

                    # CONDITION FOR QUERY
                    conditions.append({
                        "col": "question_id",
                        "con": "=",
                        "val": question_id
                        })

                    self.postgres.update('questions', updated_data, conditions)

                if not orig_choices and row['Question Choices']:

                    orig_choices = {}
                    orig_choices['choices'] = row['Question Choices']

                    updated_data = {}
                    updated_data['orig_choices'] = json.dumps(orig_choices)

                    conditions = []

                    # CONDITION FOR QUERY
                    conditions.append({
                        "col": "question_id",
                        "con": "=",
                        "val": question_id
                        })

                    self.postgres.update('questions', updated_data, conditions)



class UpdateCSVBound(Common):
    """Class for UpdateCSVBound"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateCSVBound class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()

        super(UpdateCSVBound, self).__init__()

    def main(self):
        """Main"""

        sql_str = "SELECT exercise_id, question_id FROM course_question WHERE"
        # sql_str += " course_id='42414ae56bc446418251b43412f4871b'"
        # sql_str += " course_id='4b405c3a319f4c7fa89e2944fab0cf45'"
        sql_str += " course_id='7439833ebb01457e9cc8b94453bc84bb'"

        exercise_questions = self.postgres.query_fetch_all(sql_str)

        for exq in exercise_questions or []:
            print("{0}".format(exq))
            ins_data = {}
            ins_data['exercise_id'] = exq['exercise_id']
            ins_data['question_id'] = exq['question_id']
            self.postgres.insert('uploaded_exercise_question', ins_data)


class CheckDuplicate(Common):
    """Class for CheckDuplicate"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for CheckDuplicate class"""
        self.postgres = PostgreSQL()
        self.sha_security = ShaSecurity()

        super(CheckDuplicate, self).__init__()

    def main(self):
        """Main"""

        reader = csv.DictReader(open('tempsdata/tempsdata4.csv', encoding='UTF-8'))

        line_count = 1

        headers = []
        Section = []
        Subsection = []
        Exercise = []
        Tags = []
        Question_Type = []

        Questions_Datas = {}

        course_id = ""
        section_id = ""
        subsection_id = ""
        exercise_id = ""

        for row in reader:
            row['Cursus'] = row['Course Name']
            row['Section'] = row['Section Name']
            row['Subsection'] = row['Subsection Name']
            row['Exercise'] = row['Exercise Number']

            line_count += 1
            if row['Cursus'] not in headers:

                print("Course: {0}".format(row['Cursus']))
                
                headers.append(row['Cursus'])


            sections = "{0} : {1}".format(row['Cursus'], row['Section'])
            if sections not in Section:

                print("    Section: {0}".format(sections))

                Section.append(sections)

            subsections = "{0} : {1} : {2}".format(row['Cursus'], row['Section'], row['Subsection'])
            if subsections not in Subsection:

                print("        Subsection: {0}".format(subsections))

                Subsection.append(subsections)

            exercises = "{0} : {1} : {2} : {3}".format(row['Cursus'], row['Section'], row['Subsection'], row['Exercise'])
            if exercises not in Exercise:

                print("            Exercise: {0}".format(exercises))

                Exercise.append(exercises)

            # QUESTIONS
            question_data = "{0} : {1} : {2} : {3} : {4}".format(row['Cursus'], row['Section'], row['Subsection'], row['Exercise'], row['Question'])
            if question_data not in Questions_Datas.keys():

                Questions_Datas[question_data] = line_count
            else:
                print("{1} to {0} : {2}".format(line_count, Questions_Datas[question_data], row['Question']))

# TEST = ValidateQuestions()
# TEST.main()

# TEST = ValidateAnswers()
# TEST.main()


# TEST = UpdateAnswers()
# # TEST.update_decimal()
# TEST.main()

# TEST = UpdateSkills()
# TEST.main()

# TEST = UpdateChoices()

# TEST = UpdateQuestions()
# TEST.main()

# TEST = UpdateQuestionsDB()
# TEST.main()

# TEST = UpdateAnswerDB()
# TEST.main()

# TEST = UpdateQuestionsRest()
# TEST.main()

# TEST = CheckQuestions()
# TEST.main()

# TEST = UpdateOriginal()
# TEST.main()

# TEST = UpdateCSVBound()
# TEST.main()

TEST = CheckDuplicate()
TEST.main()