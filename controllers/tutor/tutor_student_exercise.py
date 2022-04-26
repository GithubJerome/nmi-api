"""Tutor Student Exercise"""
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class TutorStudentExercise(Common):
    """Class for TutorStudentExercise"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for TutorStudentExercise class"""
        self.postgresql_query = PostgreSQL()
        super(TutorStudentExercise, self).__init__()

    def tutor_student_exercise(self):
        """
        This API is for Getting All Exercise Tries
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
          - name: student_id
            in: query
            description: Student ID
            required: true
            type: string
          - name: exercise_id
            in: query
            description: Exercise ID
            required: true
            type: string

        responses:
          500:
            description: Error
          200:
            description: Student Exercise
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        exercise_id = request.args.get('exercise_id')
        student_id = request.args.get('student_id')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        datas = self.get_exercise(userid, exercise_id, student_id)
        datas['student_details'] = self.get_account_details(student_id)
        datas['status'] = 'ok'

        return self.return_data(datas, userid)

    def get_exercise(self, userid, exercise_id, student_id):
        """ RETURN ALL EXERCISE """

        data = {}

        # SUBSECTION DETAILS
        sql_str = "SELECT c.course_name, c.course_title, * FROM subsection s"
        sql_str += " LEFT JOIN student_subsection ss ON s.subsection_id = ss.subsection_id"
        sql_str += " LEFT JOIN course c ON s.course_id = c.course_id"
        sql_str += " WHERE ss.account_id = '{0}'".format(student_id)
        sql_str += " AND ss.subsection_id IN (SELECT subsection_id FROM exercise"
        sql_str += " WHERE exercise_id = '{0}') AND ss.status is True".format(exercise_id)
        subsection = self.postgres.query_fetch_one(sql_str)

        data['subsection'] = subsection

        sql_str = """SELECT se.*, se.student_exercise_id as key, c.exercise_name, se.percent_score AS score,
                    CASE WHEN c.exercise_name is null OR c.exercise_name = '' then
                    'Exercise '||se.exercise_number else CONCAT(c.exercise_name, ' ')||se.exercise_number end as name,
                    (SELECT array_to_json(array_agg(quest)) FROM
                    (SELECT cq.course_question_id, cq.question_type, seq.is_correct, seq.sequence, seq.started_on,
                    seq.update_on, (SELECT array_to_json(array_agg(row_to_json(t))) AS children FROM (  SELECT * FROM (SELECT * FROM
                    (SELECT 'Question' as name, NULL AS is_correct, cq2.question_type, question->'question' AS value, 
                    cq2.course_question_id FROM course_question cq2 WHERE  cq2.course_question_id = cq.course_question_id
                    UNION SELECT 'Answer' as name, seq1.is_correct, scq.question_type, answer as value,
                    seq1.course_question_id FROM student_exercise_questions seq1 
                    LEFT JOIN course_question scq ON seq1.course_question_id = scq.course_question_id 
                    WHERE  seq1.course_question_id = cq.course_question_id AND
                    seq1.account_id = seq.account_id AND seq1.student_exercise_id = seq.student_exercise_id
                    UNION SELECT 'Correct Answer' as name, NULL AS is_correct,
                    cq1.question_type, CASE WHEN (select case when answer is null OR
                    CAST("answer" AS text) = '""' then true else false end as ans
                    FROM student_exercise_questions sqs WHERE sqs.course_question_id = cq.course_question_id
                    AND sqs.account_id = seq.account_id  AND sqs.student_exercise_id =  se.student_exercise_id LIMIT 1) is True
                    Then NULL ELSE  correct_answer->'answer' END AS value, cq1.course_question_id FROM course_question cq1
                    WHERE  cq1.course_question_id = cq.course_question_id) t
                    ORDER BY CASE WHEN t.name='Question' THEN 1 WHEN t.name='Answer' THEN 2
                    WHEN t.name='Correct Answer' THEN 3  ELSE 4 END) t
                    ) t) AS children, seq.progress, seq.percent_score AS score,
                    'Question '||seq.sequence AS name, seq.student_exercise_id||seq.course_question_id AS key
                    FROM student_exercise_questions seq INNER JOIN course_question cq ON
                    seq.course_question_id=cq.course_question_id WHERE seq.account_id=se.account_id 
                    AND seq.student_exercise_id=se.student_exercise_id ORDER BY seq.sequence) AS quest) AS children"""

        sql_str += " FROM student_exercise se LEFT JOIN course c ON se.course_id = c.course_id"
        sql_str += " WHERE exercise_id='{0}'".format(exercise_id)
        sql_str += " AND account_id='{0}' ORDER BY created_on".format(student_id)
        results = self.postgres.query_fetch_all(sql_str)

        if results:

            sql_str = "SELECT language FROM account WHERE"
            sql_str += " id='{0}'".format(userid)
            language = self.postgres.query_fetch_one(sql_str)

            self.get_correct_answer(userid, results, language=language)

        data['data'] = results
        return data


    def get_correct_answer(self, user_id, exercises, language):
        """ Return Correct Answer """

        for exercise in exercises:

            exercise['time_studied'] = self.time_studied(user_id, exercise['started_on'], exercise['update_on'], language)

            if exercise['children']:

                question_name = self.translate_key(language, 'Question')

                for question in exercise['children']:

                    question['name'] = question_name  + " " + question['name'].split('Question ')[1]
                    if question['children']:

                        # CORRECT ANSWER
                        answer = question['children'][1]['value']
                        question_id = question['children'][1]['course_question_id']

                        if answer not in [None, ""]:

                            correct_answer = self.check_answer(question_id, answer, flag=True)

                            # UPDATE CORRECT ANSWER
                            question['children'][2]['value'] = self.swap_decimal_symbol(user_id, correct_answer['correct_answer'], language=language)
                            question['children'][2]['name'] = self.translate_key(language, question['children'][2]['name'])

                        # QUESTION
                        question['children'][0]['value'] = self.swap_decimal_symbol(user_id, question['children'][0]['value'], language=language)
                        question['children'][0]['name'] = self.translate_key(language, question['children'][0]['name'])

                        # ANSWER
                        question['children'][1]['value'] = self.swap_decimal_symbol(user_id, question['children'][1]['value'], language=language)
                        question['children'][1]['name'] = self.translate_key(language, question['children'][1]['name'])
