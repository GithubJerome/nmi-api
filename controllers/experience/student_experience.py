# pylint: disable=too-many-function-args
"""Student Experience"""
from datetime import datetime
from flask import  request
from library.common import Common
from library.postgresql_queries import PostgreSQL

class StudentExperience(Common):
    """Class for StudentExperience"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for StudentExperience class"""
        self.postgresql_query = PostgreSQL()
        super(StudentExperience, self).__init__()

    def student_experience(self):
        """
        This API is for Getting Student Experience
        ---
        tags:
          - Experience
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
          - name: format
            in: query
            description: Epoch Format
            required: false
            type: string
          - name: number
            in: query
            description: Number
            required: false
            type: integer
        responses:
          500:
            description: Error
          200:
            description: Student Course
        """
        data = {}

        # GET DATA
        token = request.headers.get('token')
        userid = request.headers.get('userid')
        epoch_format = request.args.get('format')
        number = request.args.get('number')

        # CHECK TOKEN
        token_validation = self.validate_token(token, userid, request)

        if not token_validation:
            data["alert"] = "Invalid Token"
            data['status'] = 'Failed'

            # RETURN ALERT
            return self.return_data(data, userid)

        epoch_range = self.epoch_range(epoch_format, number)

        if epoch_format in ['days', 'day']:
            result = self.get_daily_experience(userid, epoch_range)

        if epoch_format in ['weeks', 'week']:
            result = self.get_weekly_experience(userid, epoch_range)

        if epoch_format in ['months', 'month'] or epoch_format is None:
            result = self.get_monthly_experience(userid, epoch_range)

        if epoch_format in ['years', 'year']:
            result = self.get_yearly_experience(userid, epoch_range)

        data['data'] = result
        data['status'] = 'ok'

        return self.return_data(data, userid)

    def get_student_experience(self, user_id, start, end):
        """ Return Student Experience """

        sql_str = "SELECT * FROM student_exercise WHERE status is True"
        sql_str += " AND progress = '100' AND account_id='{0}'".format(user_id)
        sql_str += " AND end_on BETWEEN '{0}' AND '{1}'".format(start, end)
        results = self.postgres.query_fetch_all(sql_str)

        return results

    def get_previous_experience(self, user_id, start):
        """ Return Previous Student Experience """

        sql_str = "SELECT sum(total_experience) as experience FROM student_exercise WHERE"
        sql_str += " status is True AND progress = '100' AND account_id='{0}'".format(user_id)
        sql_str += " AND end_on < '{0}'".format(start)
        result = self.postgres.query_fetch_one(sql_str)

        total_experience = 0
        if result and result['experience'] is not None:
            total_experience = result['experience']

        return total_experience

    def get_monthly_experience(self, user_id, epoch_range):
        """ Return Monthly Experience """

        data = []
        start = epoch_range[0]
        end = self.month_end(epoch_range[-1])

        # STUDENT EXERCISE DATA
        results = self.get_student_experience(user_id, start, end)

        experience = self.get_previous_experience(user_id, start)
        for month in epoch_range:

            tmp = {}
            month_end = self.month_end(month)

            if results:
                experience += sum(result['total_experience'] for result in results
                                 if result['total_experience'] and result['end_on'] >= month
                                 and result['end_on'] <= month_end)

            tmp['epoch'] = month
            tmp['total_experience'] = experience
            tmp['period'] = self.get_epoch_month(month)
            data.append(tmp)
    
        return data

    def get_daily_experience(self, user_id, epoch_range):
        """ Return Daily Experience """

        data = []
        start = epoch_range[0]
        end = self.day_end(epoch_range[-1])

        # STUDENT EXERCISE DATA
        results = self.get_student_experience(user_id, start, end)
        experience = self.get_previous_experience(user_id, start)

        for day in epoch_range:

            tmp = {}
            day_end = int(self.day_end(day))

            if results:
                experience += sum(result['total_experience'] for result in results
                                 if result['total_experience'] and result['end_on'] >= day
                                 and result['end_on'] <= day_end)

            tmp['epoch'] = day
            tmp['total_experience']= experience
            tmp['period'] = datetime.fromtimestamp(int(day)).strftime('%d.%m.%Y')
            data.append(tmp)

        return data

    def get_weekly_experience(self, user_id, epoch_range):
        """ Return Weekly Experience """

        data = []
        week_start = self.week_start_end(epoch_range[0])
        epoch_range.remove(epoch_range[0])
        epoch_range.append(int(week_start['week_start']))
        epoch_range.sort()

        start = epoch_range[0]
        end = self.week_end_date(epoch_range[-1])

        # STUDENT EXERCISE DATA
        results = self.get_student_experience(user_id, start, end)
        experience = self.get_previous_experience(user_id, start)
        for erange in epoch_range:

            tmp = {}
            week = self.week_start_end(erange)
            week_start = int(week['week_start'])
            week_end = int(week['week_end'])
            # week_number = self.epoch_week_number(erange)

            if results:
                experience += sum(result['total_experience'] for result in results
                                 if result['total_experience'] and result['end_on'] >= week_start
                                 and result['end_on'] <= week_end)

            tmp['epoch'] = erange
            tmp['total_experience'] = experience
            # tmp['period'] = "WN {0}".format(week_number)
            tmp['period'] = datetime.fromtimestamp(int(erange)).strftime('%d.%m.%Y')
            data.append(tmp)

        return data

    def get_yearly_experience(self, user_id, epoch_range):
        """ Return Yearly Experience """

        data = []

        start = epoch_range[0]
        end = self.yearend_month_date(epoch_range[-1])
        end = self.month_end(end)

        # STUDENT EXERCISE DATA
        results = self.get_student_experience(user_id, start, end)

        for year in epoch_range:

            tmp = {}
            year_start = year
            year_end = self.yearend_month_date(year)
            year_end = self.month_end(year_end)

            experience = 0
            if results:
                experience = sum(result['total_experience'] for result in results
                                 if result['total_experience'] and result['end_on'] >= year_start
                                 and result['end_on'] <= year_end)

            tmp['epoch'] = year
            tmp['total_experience'] = experience
            tmp['period'] = self.get_epoch_year(year)
            data.append(tmp)

        return data
