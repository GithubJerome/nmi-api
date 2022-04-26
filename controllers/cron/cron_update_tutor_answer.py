# pylint: disable=too-many-public-methods, too-few-public-methods, no-self-use, too-many-arguments
"""Cron Update Answer if Is Correct"""
from library.postgresql_queries import PostgreSQL
from library.common import Common
from library.sha_security import ShaSecurity
from library.progress import Progress
class UpdateTutorAnswer(Common):
    """Class for UpdateAnswer"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateAnswer class"""

        self.postgres = PostgreSQL()
        self.progress = Progress()
        self.sha_security = ShaSecurity()
        super(UpdateTutorAnswer, self).__init__()


    def update_tutor_iscorrect(self):
        """Update Iscorrect Column"""

        sql_str = "SELECT * FROM tutor_exercise WHERE progress IS NOT NULL"
        result = self.postgres.query_fetch_all(sql_str)

        if result:

            for res in result:
                self.update_exercise_questions(res['tutor_exercise_id'])

                # userid = res['account_id']
                # exercise_id = res['exercise_id']

                # # UPDATE PROGRESS
                # self.progress.update_course_progress(userid, exercise_id, "tutor")
                # self.progress.update_section_progress(userid, exercise_id, "tutor")
                # self.progress.update_subsection_progress(userid, exercise_id, "tutor")

        return 1

    def update_exercise_questions(self, tutor_exercise_id):
        """ Update Iscorrect per question """

        sql_str = "SELECT * FROM tutor_exercise_questions"
        sql_str += " WHERE tutor_exercise_id='{0}'".format(tutor_exercise_id)
        result = self.postgres.query_fetch_all(sql_str)

        for res in result:

            if res['answer'] and res['is_correct'] is None:
                message = self.check_answer(res['course_question_id'], res['answer'])

                data = {}
                data['is_correct'] = message['isCorrect']

                conditions = []
                conditions.append({
                    "col": "tutor_exercise_id",
                    "con": "=",
                    "val": res['tutor_exercise_id']
                })

                conditions.append({
                    "col": "course_question_id",
                    "con": "=",
                    "val": res['course_question_id']
                })

                self.postgres.update('tutor_exercise_questions', data, conditions)
