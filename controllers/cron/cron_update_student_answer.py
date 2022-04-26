# pylint: disable=too-many-public-methods, too-few-public-methods, no-self-use, too-many-arguments
"""Cron Update Answer if Is Correct"""
from library.postgresql_queries import PostgreSQL
from library.common import Common
from library.sha_security import ShaSecurity
from library.progress import Progress
class UpdateStudentAnswer(Common):
    """Class for UpdateAnswer"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateAnswer class"""

        self.postgres = PostgreSQL()
        self.progress = Progress()
        self.sha_security = ShaSecurity()
        super(UpdateStudentAnswer, self).__init__()


    def update_student_iscorrect(self):
        """Update Iscorrect Column"""

        sql_str = "SELECT * FROM student_exercise WHERE progress IS NOT NULL"
        result = self.postgres.query_fetch_all(sql_str)

        if result:

            for res in result:
                self.update_exercise_questions(res['student_exercise_id'])

                # userid = res['account_id']
                # exercise_id = res['exercise_id']

                # # UPDATE PROGRESS
                # self.progress.update_course_progress(userid, exercise_id, "student")
                # self.progress.update_section_progress(userid, exercise_id, "student")
                # self.progress.update_subsection_progress(userid, exercise_id, "student")

        return 1

    def update_exercise_questions(self, student_exercise_id):
        """ Update Iscorrect per question """

        sql_str = "SELECT * FROM student_exercise_questions"
        sql_str += " WHERE student_exercise_id='{0}'".format(student_exercise_id)
        result = self.postgres.query_fetch_all(sql_str)

        for res in result:

            if res['answer'] and res['is_correct'] is None:
                message = self.check_answer(res['course_question_id'], res['answer'])

                data = {}
                data['is_correct'] = message['isCorrect']

                conditions = []
                conditions.append({
                    "col": "student_exercise_id",
                    "con": "=",
                    "val": res['student_exercise_id']
                })

                conditions.append({
                    "col": "course_question_id",
                    "con": "=",
                    "val": res['course_question_id']
                })

                self.postgres.update('student_exercise_questions', data, conditions)
