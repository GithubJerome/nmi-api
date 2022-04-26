# pylint: disable=too-many-public-methods, too-few-public-methods, no-self-use, too-many-arguments
"""Cron Update Progress"""
from library.postgresql_queries import PostgreSQL
from library.common import Common
from library.sha_security import ShaSecurity
from library.progress import Progress
class UpdateProgress(Common):
    """Class for UpdateProgress"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for UpdateProgress class"""

        self.postgres = PostgreSQL()
        self.progress = Progress()
        self.sha_security = ShaSecurity()
        super(UpdateProgress, self).__init__()


    def update_student_progress(self):
        """Update Progress"""

        sql_str = "SELECT * FROM student_course sc"
        sql_str += " LEFT JOIN student_exercise se ON sc.course_id = se.course_id"
        sql_str += " WHERE sc.percent_score is NULL AND se.progress = '100'"
        sql_str += " AND se.status is True AND se.account_id = sc.account_id"
        result = self.postgres.query_fetch_all(sql_str)
        
        if result:

            for res in result:
                userid = res['account_id']
                exercise_id = res['exercise_id']

                # UPDATE PROGRESS
                self.progress.update_course_progress(userid, exercise_id, "student")
                self.progress.update_section_progress(userid, exercise_id, "student")
                self.progress.update_subsection_progress(userid, exercise_id, "student")

        return 1
