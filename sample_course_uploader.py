import re
import os
import csv
import time
import json

from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity

# reader = csv.DictReader(open('sample_course_uploader/sample2.csv', encoding='UTF-8'))
reader = csv.DictReader(open('tempsdata/course1.csv', encoding='UTF-8'))

headers = []
Section = []
Subsection = []
Exercise = []
Tags = []
Question_Type = []
PROGRESS = PostgreSQL()
SHA_SECURITY = ShaSecurity()
ctr = 0

for row in reader:
    ctr += 1

    tags = row['Tags'].replace("\"", "")
    tags = "".join(re.findall(r'[^\{$\}]', tags)).split(", ")

    # COURSE
    sql_str = "SELECT course_id FROM course WHERE"
    sql_str += " course_name='{0}'".format(row['Cursus'])
    course = PROGRESS.query_fetch_one(sql_str)
    course_id = course['course_id']

    # SECTION
    sql_str = "SELECT section_id FROM section WHERE"
    sql_str += " section_name='{0}'".format(row['Section'])
    sql_str += " AND course_id='{0}'".format(course_id)
    section = PROGRESS.query_fetch_one(sql_str)
    section_id = section['section_id']

    # SUBSECTION
    sql_str = "SELECT subsection_id FROM subsection WHERE"
    sql_str += " subsection_name='{0}'".format(row['Subsection'])
    sql_str += " AND course_id='{0}'".format(course_id)
    sql_str += " AND section_id='{0}'".format(section_id)
    subsection = PROGRESS.query_fetch_one(sql_str)
    subsection_id = subsection['subsection_id']

    # EXERCISE
    sql_str = "SELECT exercise_id FROM exercise WHERE"
    sql_str += " exercise_number='{0}'".format(row['Exercise'])
    sql_str += " AND course_id='{0}'".format(course_id)
    sql_str += " AND section_id='{0}'".format(section_id)
    sql_str += " AND subsection_id='{0}'".format(subsection_id)
    exercise = PROGRESS.query_fetch_one(sql_str)
    exercise_id = exercise['exercise_id']

    # print("course_id: {0}".format(course_id))
    # print("section_id: {0}".format(section_id))
    # print("subsection_id: {0}".format(subsection_id))
    # print("exercise_id: {0}".format(exercise_id))


    # CHECK IF QUESTION EXIST
    correct_answer = {}
    question = {}
    array_choice = []

    tags = row['Tags'].replace("\"", "")
    tags = "".join(re.findall(r'[^\{$\}]', tags)).split(", ")

    if row['Question Type'] == 'FITBT':

        if row['Correct Answer'][0] == '{' and row['Correct Answer'][-1] == '}':

            allans = "".join(re.findall(r'[^\{$\}]', row['Correct Answer'])).split(", ")
            correct_answer['answer'] = allans

        elif '<ans> remainder <ans>' in row['Question']:

            # correct_answer['answer'] = row['Correct Answer']
            correct_answer['answer'] = row['Question'].replace("<ans> remainder <ans>", row['Correct Answer'])

        elif '<ans>/<ans>' in row['Question']:

            temp_quest = row['Question'].split('<ans>/<ans>')[0] + row['Correct Answer']

            correct_answer['answer'] = temp_quest

        elif '<ans>:<ans>:<ans>' in row['Question']:

            temp_quest = row['Question'].split('<ans>:<ans>:<ans>')[0] + row['Correct Answer']

            correct_answer['answer'] = temp_quest

        elif '<ans>:<ans>' in row['Question']:

            ans_count = row['Question'].split(" = ")[1].count('<ans>')
            ans_num = ':'.join("<ans>" for _ in range(ans_count))
            temp_quest = row['Question'].split(ans_num)[0] + row['Correct Answer']

            correct_answer['answer'] = temp_quest

        else:

            ans = "".join(re.findall(r'[^\{$\}]', row['Correct Answer']))
            correct_answer['answer'] = row['Question'].replace("<ans>", str(ans))

        question['question'] = row['Question']

    elif row['Question Type'] == 'MULCH':

        # choices = [choice for choice in row['choices'].split(",")]
        choices = "".join(re.findall(r'[^\{$\}]', row['Choices']))
        choices = choices.split(", ")

        if len(choices) == 1:
            choices = choices[0].split(",")

        for choice in choices:
            array_choice.append(choice)

        correct_answer['answer'] = row['Correct Answer']
        question['question'] = row['Question']

    elif row['Question Type'] == 'MATCH':

        allans = "".join(re.findall(r'[^\{$\}]', row['Correct Answer'])).split(", ")
        correct_answer['answer'] = allans

        quest_data = row['Question'].replace("\"", "")
        allquest = "".join(re.findall(r'[^\{$\}]', quest_data)).split(", ")
        question['question'] = allquest
        row['Question'] = json.dumps(allquest)

        array_choice = "".join(re.findall(r'[^\{$\}]', row['Choices']))
        array_choice = array_choice.split(", ")

    elif row['Question Type'] == 'MULRE':

        allans = row['Correct Answer'].replace("\"", "")
        allans = "".join(re.findall(r'[^\{$\}]', allans)).split(", ")

        correct_answer['answer'] = allans
        question['question'] = row['Question']

        array_choice = row['Choices'].replace("\"", "")
        array_choice = "".join(re.findall(r'[^\{$\}]', array_choice))
        array_choice = array_choice.split(", ")

    elif row['Question Type'] == 'FITBD':

        choices = "".join(re.findall(r'[^\{$\}]', row['Choices']))
        choices = choices.split(", ")

        if len(choices) == 1:
            choices = choices[0].split(",")

        for choice in choices:
            array_choice.append(choice)

        ans = row['Correct Answer'].replace("\"", "")
        ans = "".join(re.findall(r'[^\{$\}]', ans))
        ans = ans.split(", ")

        if len(ans) == 1:
            ans = ans[0].split(",")

        correct_answer['answer'] = ans
        question['question'] = row['Question']

    else:
        correct_answer['answer'] = row['Correct Answer']
        question['question'] = row['Question']

    # QUESTION
    sql_str = "SELECT question_id FROM questions WHERE"
    sql_str += " question='{0}'".format(json.dumps(question))
    sql_str += " AND question_type='{0}'".format(row['Question Type'])
    sql_str += " AND tags='{0}'".format(json.dumps(tags))
    sql_str += " AND correct_answer='{0}'".format(json.dumps(correct_answer))

    # print(sql_str)
    response = PROGRESS.query_fetch_one(sql_str)

    if not response:

        print("Not OK -> {0}".format(row['Question']))
        print(sql_str)

        continue

    else:

        question_id = response['question_id']
        # print("question_id: {0}".format(question_id))
        # continue
        # print("{0}. OK".format(ctr))

        sql_str = "SELECT course_question_id FROM course_question WHERE"
        sql_str += " question='{0}'".format(json.dumps(question))
        sql_str += " AND question_type='{0}'".format(row['Question Type'])
        sql_str += " AND tags='{0}'".format(json.dumps(tags))
        sql_str += " AND correct_answer='{0}'".format(json.dumps(correct_answer))
        sql_str += " AND course_id='{0}'".format(course_id)
        sql_str += " AND section_id='{0}'".format(section_id)
        sql_str += " AND subsection_id='{0}'".format(subsection_id)
        sql_str += " AND exercise_id='{0}'".format(exercise_id)
        sql_str += " AND question_id='{0}'".format(question_id)
        course_question_id = PROGRESS.query_fetch_one(sql_str)

        if not course_question_id:

            print("INSERT!")
            # INSERT IN course_question
            tmp = {}
            tmp['course_question_id'] = SHA_SECURITY.generate_token(False)
            tmp['course_id'] = course_id
            tmp['section_id'] = section_id
            tmp['subsection_id'] = subsection_id
            tmp['exercise_id'] = exercise_id
            tmp['question_id'] = question_id
            tmp['question'] = json.dumps(question)
            tmp['question_type'] = row['Question Type']
            tmp['tags'] = json.dumps(tags)
            tmp['choices'] = json.dumps(array_choice)
            tmp['num_eval'] = False
            if row['Num Eval']:
                tmp['num_eval'] = row['Num Eval'].upper() == 'TRUE'
            tmp['correct_answer'] = json.dumps(correct_answer)
            tmp['correct'] = row['Correct']
            tmp['incorrect'] = row['Incorrect']

            if row['Feedback']:
                tmp['feedback'] = row['Feedback']

            tmp['shuffle_options'] = False
            if row['Shuffle Options']:
                tmp['shuffle_options'] = row['Shuffle Options'].upper() == 'TRUE'

            tmp['shuffle_answers'] = False
            if row['Shuffle Answers']:
                tmp['shuffle_answers'] = row['Shuffle Answers'].upper() == 'TRUE'

            tmp['description'] = row['Description']
            tmp['status'] = False
            if row['Status']:
                tmp['status'] = row['Status'].upper() == 'TRUE'
            tmp['created_on'] = time.time()

            # print("tmp: {0}".format(tmp))
            PROGRESS.insert('course_question', tmp, 'course_question_id')

        else:

            print("Exist!")