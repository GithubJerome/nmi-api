# pylint: disable=no-self-use, too-many-arguments, too-many-branches, too-many-public-methods, bare-except, unidiomatic-typecheck, no-member, anomalous-backslash-in-string
"""Common"""
import json
import time
import math
import random
import calendar
from datetime import datetime, timedelta
import re
from typing import Sequence
import simplejson
import dateutil.relativedelta

from flask import jsonify
from library.postgresql_queries import PostgreSQL
from library.log import Log
from socketIO_client import SocketIO, LoggingNamespace

class Common():
    """Class for Common"""

    # INITIALIZE
    def __init__(self):
        """The Constructor for Common class"""
        self.log = Log()
        self.epoch_default = 26763
        # INITIALIZE DATABASE INFO
        self.postgres = PostgreSQL()

    # RETURN DATA
    def return_data(self, data, userid=None):
        """Return Data"""
        if userid:

            data = self.update_translate(data, userid)

        # RETURN
        return jsonify(
            data
        )

    # REMOVE KEY
    def remove_key(self, data, item):
        """Remove Key"""

        # CHECK DATA
        if item in data:

            # REMOVE DATA
            del data[item]

        # RETURN
        return data

    def get_user_info(self, columns, table, user_id, token):
        """Return User Information"""
        # CHECK IF COLUMN EXIST,RETURN 0 IF NOT
        if not columns:
            return 0

        # INITIALIZE
        cols = ''
        count = 1

        # LOOP COLUMNS
        for data in columns:

            # CHECK IF COUNT EQUAL COLUMN LENGHT
            if len(columns) == count:

                # ADD DATA
                cols += data

            else:

                # ADD DATA
                cols += data + ", "

            # INCREASE COUNT
            count += 1

        # CREATE SQL QUERY
        sql_str = "SELECT " + cols + " FROM " + table + " WHERE "
        sql_str += " token = '" + token + "'"
        sql_str += " AND account_id = '" + user_id + "'"
        sql_str += " AND status = 'true'"

        # CALL FUNCTION QUERY ONE
        ret = self.postgres.query_fetch_one(sql_str)

        # RETURN
        return ret

    def get_account_status(self, account_id):
        """ GET ACCOUNT STATUS """

        # CREATE SQL QUERY
        sql_str = "SELECT status FROM account WHERE"
        sql_str += " id='{0}'".format(account_id)

        # CALL FUNCTION QUERY ONE
        res = self.postgres.query_fetch_one(sql_str)

        if res:

            return res['status']

        return 0

    def update_token_data(self, account_id, request_info):
        """ UPDATE TOKEN DATA """

        data = {}
        data['update_on'] = time.time()
        data['status'] = True

        conditions = []

        conditions.append({
            "col": "account_id",
            "con": "=",
            "val": account_id
            })

        conditions.append({
            "col": "remote_addr",
            "con": "=",
            "val": request_info.remote_addr
            })

        conditions.append({
            "col": "platform",
            "con": "=",
            "val": request_info.user_agent.platform
            })

        conditions.append({
            "col": "browser",
            "con": "=",
            "val": request_info.user_agent.browser
            })

        conditions.append({
            "col": "version",
            "con": "=",
            "val": request_info.user_agent.version
            })

        self.postgres.update('account_token', data, conditions)

        return 1

    def validate_token(self, token, user_id, request_info):
        """Validate Token"""

        # CHECK ACCOUNT STATUS
        status = self.get_account_status(user_id)

        if not status:

            return 0

        # SET COLUMN FOR RETURN
        columns = ['account_id', 'update_on']

        # CHECK IF TOKEN EXISTS
        user_data = self.get_user_info(columns, "account_token", user_id, token)

        self.postgres = PostgreSQL()

        # CHECK IF COLUMN EXIST,RETURN 0 IF NOT
        if user_data:

            dt1 = datetime.fromtimestamp(user_data['update_on'])
            dt2 = datetime.fromtimestamp(time.time())
            dateutil.relativedelta.relativedelta(dt2, dt1)

            rd1 = dateutil.relativedelta.relativedelta(dt2, dt1)
            # print(rd1.years, rd1.months, rd1.days, rd1.hours, rd1.minutes, rd1.seconds)

            if rd1.years or rd1.months or rd1.days or rd1.hours:

                return 0

            if rd1.minutes > 30:

                return 0

        else:

            return 0

        self.update_token_data(user_id, request_info)
        # RETURN
        return 1

    # COUNT DATA
    def count_data(self, datas, column, item):
        """Return Data Count"""

        # INITIALIZE
        count = 0

        # LOOP DATAS
        for data in datas:

            # CHECK OF DATA
            if data[column] == item:

                # INCREASE COUNT
                count += 1

        # RETURN
        return count

    def set_return(self, datas):
        """Set Return"""
        ret_data = {}
        ret_data['data'] = []
        for data in datas:
            ret_data['data'].append(data['value'])

        return ret_data

    def check_request_json(self, query_json, important_keys):
        """Check Request Json"""
        query_json = simplejson.loads(simplejson.dumps(query_json))

        for imp_key in important_keys.keys():

            if imp_key not in query_json:
                return 0

            if type(query_json.get(imp_key)):

                if type(query_json[imp_key]) != type(important_keys[imp_key]):

                    return 0

            else:

                return 0

        return 1

    def limits(self, rows, limit, page):
        """Limits"""
        skip = int((page - 1) * limit)

        limit = skip + limit

        return rows[skip:limit]

    def param_filter(self, temp_datas, params, checklist):
        """Parameter Filter"""
        if not params:

            return temp_datas

        param_datas = []
        param_datas = temp_datas

        output = []

        i = 0

        for param in params:
            key = checklist[i]

            i += 1

            for data in param_datas:

                if self.filter_checker(str(param), str(data[key])):

                    output.append(data)

        return output

    def filter_checker(self, pattern, value):
        """Check Filter"""
        if '*' in pattern:
            pattern = pattern.replace('.', r'\.')
            if pattern == "*":
                pattern = "."

            if not pattern[0] == "*" and pattern != ".":
                pattern = "^" + str(pattern)

            if pattern[-1] == "*":
                pattern = pattern[:-1] + '+'

            if not pattern[-1] == "+" and pattern != ".":
                pattern = str(pattern) + '$'

            if pattern[0] == "*":
                pattern = '.?' + pattern[1:]

            pattern = pattern.replace('*', '.+')

            # print("pattern: ", pattern)

            try:

                if not re.findall(pattern, value, re.IGNORECASE):

                    return 0

            except:

                return 0

        else:

            if not value == pattern:

                return 0

        return 1

    def isfloat(self, data):
        """Check if float"""
        try:
            if data == "infinity":
                return False

            float(data)
        except ValueError:
            return False
        else:
            return True

    def isint(self, data):
        """Check if Integer"""
        try:
            if data == "infinity":
                return False

            tmp_data1 = float(data)
            tmp_data2 = int(tmp_data1)
        except ValueError:
            return False
        else:
            return tmp_data1 == tmp_data2

    def file_replace(self, filename):
        """ File Naming """

        file_name = filename.split(".")[0]

        if "_" in file_name:

            suffix = file_name.split("_")[-1]

            if suffix.isdigit():
                new_name = filename.replace(suffix, str(int(suffix) + 1))
            else:
                new_name = filename.replace(suffix, str(suffix+"_1"))
        else:
            new_name = filename.replace(file_name, str(file_name+"_1"))

        return new_name

    def format_filter(self, datas):
        """ Return Filter in Format """

        tmp = []

        for data in datas:

            tmp.append({
                "label": data,
                "value": data
            })

        return tmp

    def data_filter(self, datas, key):
        """Filter Data"""
        temp_data = []

        if datas and key:

            key = "{0}s".format(key)

            data_list = []
            for data in datas[key]:

                data_list.append(data)

            for data in data_list:
                if data in [True, False]:
                    data = "{0}".format(data)

                if key == "statuss":

                    if data == "True":
                        data = "Enabled"

                    if data == "False":
                        data = "Disabled"

                temp_data.append({
                    "label": data,
                    "value": data
                    })


        return  temp_data

    def days_update(self, timestamp, count=0, add=False):
        """Days Update"""
        try:

            named_tuple = time.localtime(int(timestamp))

            # GET YEAR MONTH DAY
            year = int(time.strftime("%Y", named_tuple))
            month = int(time.strftime("%m", named_tuple))
            day = int(time.strftime("%d", named_tuple))

            # Date in tuple
            date_tuple = (year, month, day, 0, 0, 0, 0, 0, 0)

            local_time = time.mktime(date_tuple)
            orig = datetime.fromtimestamp(local_time)

            if add:

                new = orig + timedelta(days=count)

            else:

                new = orig - timedelta(days=count)

            return new.timestamp()

        except:

            return 0

    def check_progress(self, data):
        """ RETURN PROGRESS """

        assert data, "Data is a must."

        answer = [dta['answer'] for dta in data]
        total = len(answer)
        not_answer = [None, '', []]
        total_answer = len([ans for ans in answer if ans not in not_answer])

        average = self.format_progress((total_answer / total) * 100)

        return average

    def format_progress(self, progress, flag=None):
        """ Format Progress """

        if flag:
            progress = progress.replace(",", ".")
            progress = float(progress)

        progress = round(progress, 2)
        if progress.is_integer():
            return int(progress)

        if progress == 100:

            progress = 100

        return progress

    def validate_user(self, userid, user_role):
        """ VALIDATE USER TYPE """

        sql1 = "SELECT role_id FROM account_role WHERE"
        sql1 += " account_id='{0}'".format(userid)

        sql_str = "SELECT role_name FROM role WHERE"
        sql_str += " role_id IN ({0})".format(sql1)

        roles = self.postgres.query_fetch_all(sql_str)

        for role in roles:

            if role['role_name'] == user_role:

                return 1

        return 0

    def check_answer(self, question_id, answer, userid=None, flag=False, swap=False, result=None, translate=True):
        """Return Answer"""

        if not result:

            # DATA
            # sql_str = "SELECT e.*, cq.* FROM course_question cq"
            sql_str = "SELECT e.moving_allowed, cq.* FROM course_question cq"
            sql_str += " LEFT JOIN exercise e ON cq.exercise_id = e.exercise_id"
            sql_str += " WHERE course_question_id = '{0}'".format(question_id)
            result = self.postgres.query_fetch_one(sql_str)

        data = {}
        question = ""

        data['is_mfraction'] = False
        data['mfraction'] = ""

        if flag is True:
            data['correct_answer'] = None

        if result:

            if userid and result['num_eval'] and answer and swap:
                answer = self.swap_decimal_symbol(userid, answer)

            if result['question_type'] == 'FITBT':

                question = result['question']['question'].replace("<ans>", "")

                if question == answer:

                    if result['moving_allowed'] is False:
                        data['message'] = "You cannot skip this question"
                        data['isCorrect'] = False

                    else:
                        data['message'] = "No answer given"
                        data['isCorrect'] = False

                    if userid and translate:
                        data['message'] = self.translate(userid, data['message'])

                    return data

            if result['question_type'] == 'FITBD':

                question = result['question']['question'].replace("<ans>", "")

                if question == answer:
                    data['message'] = "No answer given"
                    data['isCorrect'] = False

                    if userid and translate:
                        data['message'] = self.translate(userid, data['message'])

                    return data

            if answer in [None,'', str( [""]), str([]), str(['']), [], ['']]:
                if result['moving_allowed'] is False:
                    data['message'] = "You cannot skip this question"
                    data['isCorrect'] = False
                else:
                    data['message'] = "No answer given"
                    data['isCorrect'] = False

                if userid and translate:
                    data['message'] = self.translate(userid, data['message'])

                return data

            # FITBD
            if result['question_type'] in ['FITBD']:

                correct_answer = result['correct_answer']['answer']

                if answer in correct_answer:
                    data['message'] = result['correct']
                    data['isCorrect'] = True

                else:
                    data['message'] = result['incorrect']
                    data['isCorrect'] = False

                if flag is True:
                    data['correct_answer'] = correct_answer

                if userid and translate:
                    data['message'] = self.translate(userid, data['message'])

                return data

            if result['question_type'] in ['MULRE', 'MATCH']:

                correct_answer = result['correct_answer']['answer']

                if len(correct_answer) != len(answer):
                    data['message'] = result['incorrect']
                    data['isCorrect'] = False

                    if userid and translate:
                        data['message'] = self.translate(userid, data['message'])

                    if flag is True:
                        data['correct_answer'] = correct_answer

                    return data

                # MATCH
                if result['question_type'] == 'MATCH':
                    if answer == correct_answer:
                        data['message'] = result['correct']
                        data['isCorrect'] = True

                    else:
                        data['message'] = result['incorrect']
                        data['isCorrect'] = False

                    if flag is True:
                        data['correct_answer'] = correct_answer

                    if userid and translate:
                        data['message'] = self.translate(userid, data['message'])

                    return data

                # MULRE
                if result['shuffle_answers'] is False:
                    if answer == correct_answer:
                        data['message'] = result['correct']
                        data['isCorrect'] = True

                    else:
                        data['message'] = result['incorrect']
                        data['isCorrect'] = False

                else:
                    score = 0
                    for ans in answer:
                        if ans in correct_answer:
                            score += 1

                    if score == len(correct_answer):
                        data['message'] = result['correct']
                        data['isCorrect'] = True

                    else:
                        data['message'] = result['incorrect']
                        data['isCorrect'] = False

                if flag is True:
                    data['correct_answer'] = correct_answer

                if userid and translate:
                    data['message'] = self.translate(userid, data['message'])

                return data

            ans = {}
            ans["answer"] = answer

            if result['question_type'] == 'FITBT':

                if type(result['correct_answer']['answer']) is list:

                    if self.is_fraction(result['correct_answer']['answer'][0]):

                        db_answer = result['correct_answer']['answer'][0]
                        # GET ANSWER
                        final_answer = ""

                        try:

                            final_answer = ans["answer"].split(" = ")[1]

                        except:

                            final_answer = ans["answer"].split("=")[1]

                        # REDUCED / MIXED FRACTION
                        if len(result['correct_answer']['answer']) == 3:

                            reduced = result['correct_answer']['answer'][1]
                            reduced = reduced.replace("\"", "")
                            reduced = reduced.replace("\'", "")

                            mfraction = result['correct_answer']['answer'][2]
                            mfraction = mfraction.replace("\"", "")
                            mfraction = mfraction.replace("\'", "")

                            if reduced.upper() == "REDUCED":

                                if str(final_answer) == str(result['correct_answer']['answer'][0]):

                                    data['message'] = result['correct']
                                    data['isCorrect'] = True

                                else:

                                    data['message'] = result['incorrect']
                                    data['isCorrect'] = False

                            else:

                                data['message'] = result['incorrect']
                                data['isCorrect'] = False

                            if flag is True:
                                data['is_mfraction'] = True
                                data['mfraction'] = mfraction.upper()
                                data['correct_answer'] = db_answer

                        # REDUCED
                        elif len(result['correct_answer']['answer']) == 2:

                            reduced = result['correct_answer']['answer'][1]
                            reduced = reduced.replace("\"", "")
                            reduced = reduced.replace("\'", "")

                            if reduced.upper() == "REDUCED":

                                if str(final_answer) == str(result['correct_answer']['answer'][0]):

                                    data['message'] = result['correct']
                                    data['isCorrect'] = True

                                else:

                                    data['message'] = result['incorrect']
                                    data['isCorrect'] = False

                            else:

                                data['message'] = result['incorrect']
                                data['isCorrect'] = False

                            if flag is True:
                                data['correct_answer'] = db_answer

                        # NOT REDUCED
                        else:

                            # VALIDATE ANSWER
                            if self.is_fraction(final_answer):

                                anumerator = final_answer.split('/')[0]
                                adenominator = final_answer.split('/')[1]
                                cnumerator = db_answer.split('/')[0]
                                cdenominator = db_answer.split('/')[1]

                                first = float(anumerator) * float(cdenominator)
                                second = float(adenominator) * float(cnumerator)

                                if first == second:

                                    data['message'] = result['correct']
                                    data['isCorrect'] = True

                                    if flag is True:
                                        data['correct_answer'] = final_answer

                                else:

                                    data['message'] = result['incorrect']
                                    data['isCorrect'] = False

                                    if flag is True:
                                        data['correct_answer'] = db_answer
                            else:

                                data['message'] = result['incorrect']
                                data['isCorrect'] = False

                                if flag is True:
                                    data['correct_answer'] = db_answer
    
                    elif ans['answer'] in result['correct_answer']['answer']:

                        data['message'] = result['correct']
                        data['isCorrect'] = True

                        if flag is True:
                            data['correct_answer'] = result['correct_answer']['answer']

                    elif "remainder" in result['question']['question'] and result['num_eval']:

                        try:
                            user_ans = ans['answer'].split('=')[1]
                            db_ans = result['correct_answer']['answer'][0].split('=')[1]

                            db_ans = '.'.join(ans.strip() for ans in db_ans.split("remainder"))
                            user_ans = '.'.join(ans.strip() for ans in user_ans.split("remainder"))

                            if float(user_ans) == float(db_ans):

                                data['message'] = result['correct']
                                data['isCorrect'] = True

                            else:

                                data['message'] = result['incorrect']
                                data['isCorrect'] = False
                        except:

                                data['message'] = result['incorrect']
                                data['isCorrect'] = False

                        if flag is True:
                            data['correct_answer'] = result['correct_answer']['answer']

                    else:

                        data['message'] = result['incorrect']
                        data['isCorrect'] = False

                        if flag is True:
                            data['correct_answer'] = result['correct_answer']['answer']

                else:

                    if 'Decimal' in result['correct_answer']["answer"] or 'Decimals' in result['correct_answer']["answer"]:

                        ans["answer"] = ans["answer"].replace("Decimaal", "Decimal")
                        ans["answer"] = ans["answer"].replace("Decimalen", "Decimals")

                        # FOR DECIMAL TYPE OF QUESTIONS
                        if str(result['correct_answer']) == str(ans):

                            data['message'] = result['correct']
                            data['isCorrect'] = True
                        
                        else:

                            data['message'] = result['incorrect']
                            data['isCorrect'] = False

                    elif 'decimal' in result['correct_answer']["answer"] or 'decimals' in result['correct_answer']["answer"]:

                        ans["answer"] = ans["answer"].replace("decimaal", "decimal")
                        ans["answer"] = ans["answer"].replace("decimalen", "decimals")

                        # FOR DECIMAL TYPE OF QUESTIONS
                        if str(result['correct_answer']) == str(ans):

                            data['message'] = result['correct']
                            data['isCorrect'] = True
                        
                        else:

                            data['message'] = result['incorrect']
                            data['isCorrect'] = False

                    elif str(result['correct_answer']) == str(ans):
                        data['message'] = result['correct']
                        data['isCorrect'] = True

                    # TIME
                    elif ':' in result['correct_answer']["answer"]:

                        user_answer = ans['answer'].split(' = ')[1]
                        if user_answer[0] == ':' or user_answer[-1] == ':' or '::' in user_answer:

                            data['message'] = result['incorrect']
                            data['isCorrect'] = False

                        else:
                            user_ans = ":".join(str(int(ans)) for ans in ans['answer'].split(' = ')[1].split(':'))
                            db_ans = ":".join(str(int(ans)) for ans in result['correct_answer']['answer'].split(' = ')[1].split(':'))

                            if user_ans == db_ans:
                                data['message'] = result['correct']
                                data['isCorrect'] = True
                            else:
                                data['message'] = result['incorrect']
                                data['isCorrect'] = False

                    else:
                            
                        if result['num_eval']:
 
                            try:

                                eqxn_symbol = ['???', '???' , '=', 'is ???', '~ ???', 'is ']
                                split_symbol = [esymbol for esymbol in eqxn_symbol if esymbol in result['correct_answer']['answer']][-1]

                                user_ans = ans['answer'].split(split_symbol)[1]
                                db_ans = result['correct_answer']['answer'].split(split_symbol)[1]

                                # CHECK ANS POSITION
                                answer = result['question']['question'].split(split_symbol)[1]

                                if "remainder" in db_ans or "rest" in db_ans:

                                    db_ans = '.'.join(ans.strip() for ans in db_ans.split("remainder"))
                                    user_ans = '.'.join(ans.strip() for ans in user_ans.split("remainder"))

                                else:
                                    ans_index = answer.index('<ans>')
                                    ans_label = answer[ans_index:].replace("<ans>","")

                                    if ans_label:
                                        user_ans = user_ans[ans_index:].replace(ans_label,"")
                                        db_ans = db_ans[ans_index:].replace(ans_label,"")

                                if float(user_ans) == float(db_ans):

                                    data['message'] = result['correct']
                                    data['isCorrect'] = True

                                else:

                                    data['message'] = result['incorrect']
                                    data['isCorrect'] = False

                            except:

                                data['message'] = result['incorrect']
                                data['isCorrect'] = False

                        else:

                            data['message'] = result['incorrect']
                            data['isCorrect'] = False

                    if flag is True:
                        data['correct_answer'] = result['correct_answer']['answer']

            else:

                if str(result['correct_answer']) == str(ans):

                    data['message'] = result['correct']
                    data['isCorrect'] = True

                else:

                    data['message'] = result['incorrect']
                    data['isCorrect'] = False

                if flag is True:
                    data['correct_answer'] = result['correct_answer']['answer']

        if userid and translate:

            data['message'] = self.translate(userid, data['message'])

        return data

    def swap_decimal_symbol(self, userid, data, flag=None, language=None):
        """ Format Decimal Symbol By Language """

        if not language:

            sql_str = "SELECT language FROM account WHERE"
            sql_str += " id='{0}'".format(userid)
            language = self.postgres.query_fetch_one(sql_str)

        if language['language'] == 'nl-NL' and data:

            if flag:
                data = str(self.format_progress(data, flag=True))

            if type(data) == list:

                data = [dta.replace(",", "/tmp/").replace(".", ",").replace("/tmp/", ".") for dta in data]
                data = [dta.replace(" ?? ", "/tmp/").replace(" : ", " ?? ").replace("/tmp/", " : ") for dta in data]
                # if "rest" in data[0] or "remainder" in data[0]:
                data = [dta.replace("remainder", "/tmp/").replace("rest", "remainder").replace("/tmp/", "rest") for dta in data]

                for dta in data:

                    if "Decimals" in dta:

                        dta = dta.replace("Decimals", "Decimalen")

                    elif "Decimal" in dta:

                        dta = dta.replace("Decimal", "Decimaal")

                    elif "decimals" in dta:

                        dta = dta.replace("decimals", "decimalen")

                    elif "decimal" in dta:

                        dta = dta.replace("decimal", "decimaal")

            else:

                data = data.replace(",", "/tmp/").replace(".", ",").replace("/tmp/", ".")
                data = data.replace(" ?? ", "/tmp/").replace(" : ", " ?? ").replace("/tmp/", " : ")
                # if "rest" in data or "remainder" in data: 
                data = data.replace("remainder", "/tmp/").replace("rest", "remainder").replace("/tmp/", "rest")

                if "Decimals" in data:

                    data = data.replace("Decimals", "Decimalen")

                elif "Decimal" in data:

                    data = data.replace("Decimal", "Decimaal")

                elif "decimals" in data:

                    data = data.replace("decimals", "decimalen")

                elif "decimal" in data:

                    data = data.replace("decimal", "decimaal")

        return data

    def translate(self, user_id, orig_message, language=None):
        """ Return Translation """

        if not orig_message:

            return orig_message

        if not language:

            sql_str = "SELECT language FROM account WHERE"
            sql_str += " id='{0}'".format(user_id)
            language = self.postgres.query_fetch_one(sql_str)

        if language['language'] != 'en-US':

            message = "".join(re.findall(r'[a-zA-Z0-9\ \.\,\-\(\)\!]', orig_message))

            sql_str = "SELECT translation FROM translations WHERE word_id=("
            sql_str += "SELECT word_id FROM words WHERE"
            sql_str += " name = '{0}') AND ".format(message)
            sql_str += "language_id=(SELECT language_id FROM language WHERE "
            sql_str += "initial='{0}')".format(language['language'])

            translate = self.postgres.query_fetch_one(sql_str)

            if translate:
                orig_message = translate['translation']

        return orig_message

    def translate_course(self, user_id, course_id):
        """ Return Course Translation """

        data = {}
        sql_str = "SELECT * FROM course WHERE course_id = '{0}'".format(course_id)
        result = self.postgres.query_fetch_one(sql_str)

        data['course_name'] = self.translate(user_id, result['course_name'])
        data['description'] = self.translate(user_id, result['description'])

        return data

    def trim_url(self, url):
        """ Return domain url """

        # FORMAT URL
        trim = re.compile(r"https?://(www\.)?")
        return trim.sub('', url).strip().strip('/')

    def can_access_tutorenv(self, user_id):
        """ Check access rights """

        sql_str = "SELECT * FROM account_role ac"
        sql_str += " LEFT JOIN role r ON ac.role_id = r.role_id"
        sql_str += " WHERE account_id = '{0}'".format(user_id)
        roles = self.postgres.query_fetch_all(sql_str)

        for role in roles:

            if role['role_name'].upper() in ['MANAGER', 'TUTOR']:

                return 1

        return 0

    def check_question(self, question_id):
        """ Validate Question ID """

        # DATA
        sql_str = "SELECT * FROM course_question"
        sql_str += " WHERE course_question_id = '{0}'".format(question_id)
        result = self.postgres.query_fetch_one(sql_str)
        if result:
            return 1

        return 0

    def allowed_file_type(self, filename):
        """ Check Allowed File Extension """

        allowed_extensions = set(['csv'])

        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

    def course_header(self):
        """ RETURN COURSE COLUMN """

        return [
            "Course ID",
            "Course Name",
            "Course Description",
            "Course Difficulty Level",
            "Course Requirements",

            "Section ID",
            "Section Name",
            "Section Description",
            "Section Difficulty Level",

            "Subsection ID",
            "Subsection Name",
            "Subsection Description",
            "Subsection Difficulty Level",

            "Exercise ID",
            "Exercise Number",
            "Exercise Question Type",
            "Exercise Tags",
            "Exercise Description",
            "Exercise Draw By Tag",
            "Exercise Editing Allowed",
            "Exercise Help",
            "Exercise Instant Feedback",
            "Exercise Moving Allowed",
            "Exercise Number to Draw",
            "Exercise Passing Criterium",
            "Exercise Save Seed",
            "Exercise Seed",
            "Exercise Shuffled",
            "Exercise Text Before Start",
            "Exercise Text After End",
            "Exercise Timed Limit",
            "Exercise Timed Type",
            "Exercise Skills",

            "Question ID",
            "Question",
            "Question Type",
            "Question Tags",
            "Question Choices",
            "Question Shuffle Options",
            "Question Shuffle Answers",
            "Question Num Eval",
            "Question Correct Answer",
            "Question Correct",
            "Question Incorrect",
            "Question Feedback",
            "Question Description"
        ]

    def fetch_course_details(self, userid, course_id):
        """ Return Course Details """

        sql_str = "SELECT language FROM account WHERE"
        sql_str += " id='{0}'".format(userid)
        language = self.postgres.query_fetch_one(sql_str)

        sql_str = "SELECT * FROM course_master WHERE"
        sql_str += " course_id='{0}'".format(course_id)
        result = self.postgres.query_fetch_all(sql_str)

        for res in result:
            res['course_name'] = self.translate(userid, res['course_name'])
            res['description'] = self.translate(userid, res['description'])

            if language['language'] == 'en-US':

                continue

            if 'children' in res.keys():

                if not res['children']:

                    continue

                res['children'] = self.section_master_translation(res['children'], userid)

        return result

    def check_headers(self, csv_data, headers):
        """ CHECK COLUMN """

        # for key in self.course_header():

        for key in self.course_temp_headers():

            if not key in headers:

                return 0

        return 1

    def run_course_update(self, csv_data, old_course_id=None):
        """ CONVERT CSV TO JSON """

        json_data = {}
        json_data['status'] = 'ok'
        json_data['course_name'] = ""

        course_id = ""
        course_json = {}
        section_id = ""
        subsection_id = ""
        exercise_id = ""

        batch = self.sha_security.generate_token(False)

        # for row in csv_data:

        #     # COURSE
        #     if row['Course ID'] or row['Course Name']:

        #         if row['Course Name'] in course_json.keys():

        #             course_id = course_json[row['Course Name']]['course_id']

        #         else:

        #             course_id = self.iu_course(row)
        #             course_json[row['Course Name']] = {}
        #             course_json[row['Course Name']]['course_id'] = course_id
        #             course_json[row['Course Name']]['Sections'] = {}

        #             if not course_id:

        #                 json_data["alert"] = "Course already exist!"
        #                 json_data['status'] = 'Failed'

        #                 return json_data

        #             # CHECK IF COURSE IS ALREADY IN USE
        #             if not self.use_course(course_id):

        #                 json_data["alert"] = "Course is in use!"
        #                 json_data['status'] = 'Failed'

        #                 return json_data

        #     # SECTION
        #     if row['Section ID'] or row['Section Name']:

        #         if row['Section Name'] in course_json[row['Course Name']]['Sections'].keys():

        #             section_id = course_json[row['Course Name']]['Sections'][row['Section Name']]['section_id']

        #         else:

        #             section_id = self.iu_section(row, course_id)
        #             course_json[row['Course Name']]['Sections'][row['Section Name']] = {}
        #             course_json[row['Course Name']]['Sections'][row['Section Name']]['section_id'] = section_id
        #             course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'] = {}

        #             if not section_id:

        #                 json_data["alert"] = "Section {0} already exist!".format(row['Section Name'])
        #                 json_data['status'] = 'Failed'

        #                 return json_data

        #     # SUBSECTION
        #     if row['Subsection ID'] or row['Subsection Name']:

        #         if row['Subsection Name'] in course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'].keys():

        #             subsection_id = course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'][row['Subsection Name']]['subsection_id']

        #         else:

        #             subsection_id = self.iu_subsection(row, course_id, section_id)
        #             course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'][row['Subsection Name']] = {}
        #             course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'][row['Subsection Name']]['subsection_id'] = subsection_id
        #             course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'][row['Subsection Name']]['Exercises'] = {}

        #             if not subsection_id:

        #                 json_data["alert"] = "Subsection {0} already exist!".format(row['Subsection Name'])
        #                 json_data['status'] = 'Failed'

        #                 return json_data

        #     # EXERCISE
        #     if row['Exercise ID'] or row['Exercise Number']:
        #         if row['Exercise Number'] in course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'][row['Subsection Name']]['Exercises'].keys():

        #             exercise_id = course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'][row['Subsection Name']]['Exercises'][row['Exercise Number']]['exercise_id']

        #         else:

        #             exercise_id = self.iu_exercise(row, course_id, section_id, subsection_id)
        #             course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'][row['Subsection Name']]['Exercises'][row['Exercise Number']] = {}
        #             course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'][row['Subsection Name']]['Exercises'][row['Exercise Number']]['exercise_id'] = exercise_id

        #             if not exercise_id:

        #                 json_data["alert"] = "Exercise {0} already exist!".format(row['Exercise Number'])
        #                 json_data['status'] = 'Failed'

        #                 return json_data

        #     # QUESTION
        #     if row['Question ID'] or row['Question']:

        #         # UPDATE
        #         if row['Question'] and row['Question ID']:

        #             self.update_question(row, course_id=course_id,
        #                                  section_id=section_id,
        #                                  subsection_id=subsection_id,
        #                                  exercise_id=exercise_id)

        #         # INSERT
        #         elif row['Question'] and not row['Question ID']:

        #             self.insert_question(row, batch,
        #                                  course_id=course_id,
        #                                  section_id=section_id,
        #                                  subsection_id=subsection_id,
        #                                  exercise_id=exercise_id,
        #                                  )

        #         # DELETE
        #         elif row['Question ID'] and not row['Question']:

        #             self.delete_question(row, exercise_id, course_id)

        try:

            for row in csv_data:

                # COURSE
                if row['Course Name']:

                    if row['Course Name'] in course_json.keys():

                        course_id = course_json[row['Course Name']]['course_id']

                    else:

                        course_id = self.iu_course(row, old_course_id=old_course_id)
                        course_json[row['Course Name']] = {}
                        course_json[row['Course Name']]['course_id'] = course_id
                        course_json[row['Course Name']]['Sections'] = {}
                        json_data['course_name'] = row['Course Name']

                        if not course_id:

                            json_data["alert"] = "Course already exist!"
                            json_data['status'] = 'Failed'

                            return json_data

                        course_ids = [course_id]
                        # CHECK IF COURSE IS ALREADY IN USE
                        if not self.use_course(course_ids):

                            json_data["alert"] = "Course is in use!"
                            json_data['status'] = 'Failed'

                            return json_data

                # SECTION
                if row['Section Name']:

                    if row['Section Name'] in course_json[row['Course Name']]['Sections'].keys():

                        section_id = course_json[row['Course Name']]['Sections'][row['Section Name']]['section_id']

                    else:

                        section_id = self.iu_section(row, course_id)
                        course_json[row['Course Name']]['Sections'][row['Section Name']] = {}
                        course_json[row['Course Name']]['Sections'][row['Section Name']]['section_id'] = section_id
                        course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'] = {}

                        if not section_id:

                            json_data["alert"] = "Section {0} already exist!".format(row['Section Name'])
                            json_data['status'] = 'Failed'

                            return json_data

                # SUBSECTION
                if row['Subsection Name']:

                    if row['Subsection Name'] in course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'].keys():

                        subsection_id = course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'][row['Subsection Name']]['subsection_id']

                    else:

                        subsection_id = self.iu_subsection(row, course_id, section_id)
                        course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'][row['Subsection Name']] = {}
                        course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'][row['Subsection Name']]['subsection_id'] = subsection_id
                        course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'][row['Subsection Name']]['Exercises'] = {}

                        if not subsection_id:

                            json_data["alert"] = "Subsection {0} already exist!".format(row['Subsection Name'])
                            json_data['status'] = 'Failed'

                            return json_data

                # EXERCISE
                if row['Exercise Number']:
                    if row['Exercise Number'] in course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'][row['Subsection Name']]['Exercises'].keys():

                        exercise_id = course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'][row['Subsection Name']]['Exercises'][row['Exercise Number']]['exercise_id']

                    else:

                        exercise_id = self.iu_exercise(row, course_id, section_id, subsection_id)
                        course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'][row['Subsection Name']]['Exercises'][row['Exercise Number']] = {}
                        course_json[row['Course Name']]['Sections'][row['Section Name']]['Subsections'][row['Subsection Name']]['Exercises'][row['Exercise Number']]['exercise_id'] = exercise_id

                        if not exercise_id:

                            json_data["alert"] = "Exercise {0} already exist!".format(row['Exercise Number'])
                            json_data['status'] = 'Failed'

                            return json_data

                # QUESTION
                if row['Question']:

                    # # UPDATE
                    # if row['Question'] and row['Question ID']:

                    #     self.update_question(row, course_id=course_id,
                    #                          section_id=section_id,
                    #                          subsection_id=subsection_id,
                    #                          exercise_id=exercise_id)

                    # INSERT
                    self.insert_question(row, batch,
                                        course_id=course_id,
                                        section_id=section_id,
                                        subsection_id=subsection_id,
                                        exercise_id=exercise_id,
                                            )

                    # # DELETE
                    # elif row['Question ID'] and not row['Question']:

                    #     self.delete_question(row, exercise_id, course_id)

            # ENABLE COURSE
            for new_cs in course_json.keys():

                new_course = course_json[new_cs]['course_id']
                updated_data = {}
                updated_data['status'] = True

                conditions = []
                conditions.append({
                    "col": "course_id",
                    "con": "=",
                    "val": new_course
                    })

                self.postgres.update('course', updated_data, conditions)

        except:
            json_data["alert"] = "File error, Please contact Admin!"
            json_data['status'] = 'Failed'

        return json_data

    def iu_course(self, data, old_course_id=None):
        """ UPDATE COURSE """

        # if data['Course ID']:

        #     return self.update_course(data)

        if data['Course Name']:

            sql_str = "SELECT * FROM course WHERE"
            sql_str += " course_name ='{0}'".format(data['Course Name'])

            cdata = self.postgres.query_fetch_one(sql_str)

            if cdata:

                return 0

            updated_data = {}

            data['difficulty_level'] = 1

            if old_course_id:

                updated_data['course_id'] = old_course_id

            else:

                updated_data['course_id'] = self.sha_security.generate_token(False)

            updated_data['course_name'] = data['Course Name']
            updated_data['course_title'] = data['Course Title']
            if data['Course Description']:
                updated_data['description'] = data['Course Description']
            if data['Course Difficulty Level']:
                updated_data['difficulty_level'] = data['Course Difficulty Level']
            if data['Course Requirements']:
                updated_data['requirements'] = data['Course Requirements']
            updated_data['status'] = False
            updated_data['created_on'] = time.time()

            course_id = self.postgres.insert('course', updated_data, 'course_id')

            if not course_id:

                return 0

            # INSERT SEQUENCE
            temp_sequence = 1
            sql_str = "SELECT sequence FROM course_sequence ORDER BY sequence DESC LIMIT 1"
            course_sequence = self.postgres.query_fetch_one(sql_str)

            if course_sequence:

                temp_sequence = course_sequence['sequence'] + 1

                course_seq = {}
                course_seq['course_id'] = course_id
                course_seq['sequence'] = temp_sequence

                self.postgres.insert('course_sequence', course_seq)

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

            return course_id

    def iu_section(self, data, course_id):
        """ UPDATE SECTION """

        # if not data['Section Name'] and data['Section ID']:

        #     conditions = []

        #     conditions.append({
        #         "col": "section_id",
        #         "con": "=",
        #         "val": data['Section ID']
        #         })

        #     self.postgres.delete('section', conditions)

        # if data['Section ID']:

        #     updated_data = {}

        #     # updated_data['difficulty_level'] = 1
        #     updated_data['difficulty_level'] = self.get_sec_diff(course_id)

        #     updated_data['section_name'] = data['Section Name']
        #     if data['Section Description']:
        #         updated_data['description'] = data['Section Description']
        #     if data['Section Difficulty Level']:
        #         updated_data['difficulty_level'] = data['Section Difficulty Level']

        #     # INIT CONDITION
        #     conditions = []

        #     # CONDITION FOR QUERY
        #     conditions.append({
        #         "col": "course_id",
        #         "con": "=",
        #         "val": course_id
        #         })

        #     conditions.append({
        #         "col": "section_id",
        #         "con": "=",
        #         "val": data['Section ID']
        #         })

        #     self.postgres.update('section', updated_data, conditions)

        #     return data['Section ID']

        if data['Section Name']:

            sql_str = "SELECT * FROM section WHERE"
            sql_str += " section_name ='{0}' AND".format(data['Section Name'])
            sql_str += " course_id ='{0}'".format(course_id)

            sdata = self.postgres.query_fetch_one(sql_str)

            if sdata:

                return 0

            updated_data = {}

            # updated_data['difficulty_level'] = 1
            updated_data['difficulty_level'] = self.get_sec_diff(course_id)

            updated_data['course_id'] = course_id
            updated_data['section_id'] = self.sha_security.generate_token(False)
            updated_data['section_name'] = data['Section Name']

            if data['Section Description']:

                updated_data['description'] = data['Section Description']

            if data['Section Difficulty Level']:

                if int(data['Section Difficulty Level']) > updated_data['difficulty_level']:

                    updated_data['difficulty_level'] = data['Section Difficulty Level']

            updated_data['status'] = True
            updated_data['created_on'] = time.time()

            section_id = self.postgres.insert('section', updated_data, 'section_id')

        return section_id

    def iu_subsection(self, data, course_id, section_id):
        """ UPDATE SUBSECTION """

        # if not data['Subsection Name'] and data['Subsection ID']:

        #     conditions = []

        #     conditions.append({
        #         "col": "subsection_id",
        #         "con": "=",
        #         "val": data['Subsection ID']
        #         })

        #     self.postgres.delete('subsection', conditions)

        # if data['Subsection ID']:

        #     updated_data = {}

        #     updated_data['difficulty_level'] = 1

        #     sql_str = "SELECT difficulty_level FROM subsection WHERE"
        #     sql_str += " course_id='{0}'".format(course_id)
        #     sql_str += " ORDER BY difficulty_level DESC"
        #     dlevel = self.postgres.query_fetch_one(sql_str)

        #     if dlevel:

        #         updated_data['difficulty_level'] = int(dlevel['difficulty_level']) + 1

        #     updated_data['subsection_name'] = data['Subsection Name']
        #     if data['Subsection Description']:
        #         updated_data['description'] = data['Subsection Description']
        #     if data['Subsection Difficulty Level']:
        #         updated_data['difficulty_level'] = data['Subsection Difficulty Level']

        #     # INIT CONDITION
        #     conditions = []

        #     # CONDITION FOR QUERY
        #     conditions.append({
        #         "col": "course_id",
        #         "con": "=",
        #         "val": course_id
        #         })

        #     conditions.append({
        #         "col": "section_id",
        #         "con": "=",
        #         "val": section_id
        #         })

        #     conditions.append({
        #         "col": "subsection_id",
        #         "con": "=",
        #         "val": data['Subsection ID']
        #         })

        #     self.postgres.update('subsection', updated_data, conditions)

        #     return data['Subsection ID']

        if data['Subsection Name']:

            sql_str = "SELECT * FROM subsection WHERE"
            sql_str += " subsection_name ='{0}' AND".format(data['Subsection Name'])
            sql_str += " section_id ='{0}' AND".format(section_id)
            sql_str += " course_id ='{0}'".format(course_id)

            ssdata = self.postgres.query_fetch_one(sql_str)

            if ssdata:

                return 0

            updated_data = {}

            updated_data['difficulty_level'] = self.get_subsec_diff(course_id, section_id)

            updated_data['course_id'] = course_id
            updated_data['section_id'] = section_id
            updated_data['subsection_id'] = self.sha_security.generate_token(False)
            updated_data['subsection_name'] = data['Subsection Name']
            if data['Subsection Description']:
                updated_data['description'] = data['Subsection Description']
            if data['Subsection Difficulty Level']:
                if int(data['Subsection Difficulty Level']) > updated_data['difficulty_level']:
                    updated_data['difficulty_level'] = data['Subsection Difficulty Level']
            updated_data['status'] = True
            updated_data['created_on'] = time.time()

            subsection_id = self.postgres.insert('subsection', updated_data, 'subsection_id')

            return subsection_id

    def iu_exercise(self, data, course_id, section_id, subsection_id):
        """ UPDATE COURSE """

        # if not data['Exercise Number'] and data['Exercise ID']:

        #     conditions = []

        #     conditions.append({
        #         "col": "exercise_id",
        #         "con": "=",
        #         "val": data['Exercise ID']
        #         })

        #     self.postgres.delete('course_question', conditions)

        #     data_update = {}
        #     data_update['exercise_id'] = ""

        #     self.postgres.update('instruction', data_update, conditions)
        #     self.postgres.delete('exercise_requirements', conditions)
        #     self.postgres.delete('uploaded_exercise_question', conditions)
        #     self.postgres.delete('video_exercise', conditions)
        #     self.postgres.delete('group_exercise_requirements', conditions)
        #     self.postgres.delete('exercise_skills', conditions)
        #     self.postgres.delete('exercise', conditions)

        #     return data['Exercise ID']

        # if data['Exercise ID']:

        #     updated_data = {}
        #     updated_data['exercise_number'] = data['Exercise Number']

        #     # CODE FOR QUESTIONS

        #     if data['Exercise Question Type']:
        #         updated_data['question_types'] = json.dumps(data['Exercise Question Type'].replace("\'", "").replace("\"", "")[1:-1].split(", "))
        #     if data['Exercise Tags']:
        #         updated_data['tags'] = json.dumps(data['Exercise Tags'].replace("\'", "").replace("\"", "")[1:-1].split(", "))
        #     if data['Exercise Description']:
        #         updated_data['description'] = data['Exercise Description']
        #     if data['Exercise Draw By Tag']:
        #         updated_data['draw_by_tag'] = data['Exercise Draw By Tag'].upper() == 'TRUE'
        #     if data['Exercise Editing Allowed']:
        #         updated_data['editing_allowed'] = data['Exercise Editing Allowed'].upper() == 'TRUE'
        #     if data['Exercise Help']:
        #         updated_data['help'] = data['Exercise Help'].upper() == 'TRUE'
        #     if data['Exercise Instant Feedback']:
        #         updated_data['instant_feedback'] = data['Exercise Instant Feedback'].upper() == 'TRUE'
        #     if data['Exercise Moving Allowed']:
        #         updated_data['moving_allowed'] = data['Exercise Moving Allowed'].upper() == 'TRUE'
        #     if data['Exercise Number to Draw']:
        #         updated_data['number_to_draw'] = data['Exercise Number to Draw']
        #     if data['Exercise Passing Criterium']:
        #         updated_data['passing_criterium'] = data['Exercise Passing Criterium']
        #     if data['Exercise Save Seed']:
        #         updated_data['save_seed'] = data['Exercise Save Seed'].upper() == 'TRUE'
        #     if data['Exercise Seed']:
        #         updated_data['seed'] = data['Exercise Seed']
        #     if data['Exercise Shuffled']:
        #         updated_data['shuffled'] = data['Exercise Shuffled'].upper() == 'TRUE'
        #     if data['Exercise Text Before Start']:
        #         updated_data['text_before_start'] = data['Exercise Text Before Start']
        #     if data['Exercise Text After End']:
        #         updated_data['text_after_end'] = data['Exercise Text After End']
        #     if data['Exercise Timed Limit']:
        #         updated_data['timed_limit'] = data['Exercise Timed Limit']
        #     if data['Exercise Timed Type']:
        #         updated_data['timed_type'] = data['Exercise Timed Type']


        #     # INIT CONDITION
        #     conditions = []

        #     # CONDITION FOR QUERY
        #     conditions.append({
        #         "col": "course_id",
        #         "con": "=",
        #         "val": course_id
        #         })

        #     conditions.append({
        #         "col": "section_id",
        #         "con": "=",
        #         "val": section_id
        #         })

        #     conditions.append({
        #         "col": "subsection_id",
        #         "con": "=",
        #         "val": subsection_id
        #         })

        #     conditions.append({
        #         "col": "exercise_id",
        #         "con": "=",
        #         "val": data['Exercise ID']
        #         })

        #     self.postgres.update('exercise', updated_data, conditions)

        #     # UPDATE SKILLS
        #     if data['Exercise Skills']:

        #         conditions = []

        #         conditions.append({
        #             "col": "exercise_id",
        #             "con": "=",
        #             "val": data['Exercise ID']
        #             })

        #         self.postgres.delete('exercise_skills', conditions)

        #         skills = json.loads(data['Exercise Skills'])

        #         if skills:
        #             self.insert_exe_skills(data['Exercise ID'], skills)

        #     else:

        #         conditions = []

        #         conditions.append({
        #             "col": "exercise_id",
        #             "con": "=",
        #             "val": data['Exercise ID']
        #             })

        #         self.postgres.delete('exercise_skills', conditions)

        #     # ADD QUESTION to COURSE QUESTION
        #     self.add_course_question(data['Exercise ID'])

        #     return data['Exercise ID']

        # INSERT
        updated_data = {}
        updated_data['draw_by_tag'] = False
        updated_data['editing_allowed'] = True
        updated_data['help'] = True
        updated_data['instant_feedback'] = True
        updated_data['moving_allowed'] = True
        updated_data['number_to_draw'] = 10
        updated_data['passing_criterium'] = 5
        updated_data['save_seed'] = True
        updated_data['seed'] = 10
        updated_data['shuffled'] = False
        updated_data['timed_limit'] = 300
        updated_data['timed_type'] = 'per_question'

        updated_data['course_id'] = course_id
        updated_data['section_id'] = section_id
        updated_data['subsection_id'] = subsection_id
        updated_data['exercise_id'] = self.sha_security.generate_token(False)
        updated_data['exercise_number'] = data['Exercise Number']
        if data['Exercise Question Type']:
            updated_data['question_types'] = json.dumps(data['Exercise Question Type'].replace("\'", "").replace("\"", "")[1:-1].split(", "))
        if data['Exercise Tags']:
            updated_data['tags'] = json.dumps(data['Exercise Tags'].replace("\'", "").replace("\"", "")[1:-1].split(", "))
        if data['Exercise Description']:
            updated_data['description'] = data['Exercise Description']
        if data['Exercise Draw By Tag']:
            updated_data['draw_by_tag'] = data['Exercise Draw By Tag'].upper() == 'TRUE'
        if data['Exercise Description']:
            updated_data['editing_allowed'] = data['Exercise Editing Allowed'].upper() == 'TRUE'
        if data['Exercise Help']:
            updated_data['help'] = data['Exercise Help'].upper() == 'TRUE'
        if data['Exercise Instant Feedback']:
            updated_data['instant_feedback'] = data['Exercise Instant Feedback'].upper() == 'TRUE'
        if data['Exercise Moving Allowed']:
            updated_data['moving_allowed'] = data['Exercise Moving Allowed'].upper() == 'TRUE'
        if data['Exercise Number to Draw']:
            updated_data['number_to_draw'] = data['Exercise Number to Draw']
        if data['Exercise Passing Criterium']:
            updated_data['passing_criterium'] = data['Exercise Passing Criterium']
        if data['Exercise Save Seed']:
            updated_data['save_seed'] = data['Exercise Save Seed'].upper() == 'TRUE'
        if data['Exercise Seed']:
            updated_data['seed'] = data['Exercise Seed']
        if data['Exercise Shuffled']:
            updated_data['shuffled'] = data['Exercise Shuffled'].upper() == 'TRUE'
        if data['Exercise Text Before Start']:
            updated_data['text_before_start'] = data['Exercise Text Before Start']
        if data['Exercise Text After End']:
            updated_data['text_after_end'] = data['Exercise Text After End']
        if data['Exercise Timed Limit']:
            updated_data['timed_limit'] = data['Exercise Timed Limit']
        if data['Exercise Timed Type']:
            updated_data['timed_type'] = data['Exercise Timed Type']
        if data['Exercise Repeatable']:
            updated_data['is_repeatable'] = data['Exercise Repeatable'].upper() == 'TRUE'
        updated_data['status'] = True
        updated_data['created_on'] = time.time()

        exercise_id = self.postgres.insert('exercise', updated_data, 'exercise_id')

        if data['Exercise Skills']:

            skills = json.loads(data['Exercise Skills'])

            if skills:

                self.insert_exe_skills(exercise_id, skills)

        # ADD QUESTION to COURSE QUESTION
        self.add_course_question(exercise_id)

        return exercise_id

    def insert_exe_skills(self, exercise_id, skills):
        """ EXERCISE SKILLS """

        for item in skills:

            skill = ""
            skill_id = ""
            subskills = []
            if 'skill' in item.keys():

                skill = item['skill']

            if 'subskills' in item.keys():

                subskills = item['subskills']

            if skill:

                sql_str = "SELECT skill_id FROM skills WHERE"
                sql_str += " skill='{0}'".format(skill)
                response = self.postgres.query_fetch_all(sql_str)

                if response:

                    db_subskills = []

                    flag = False
                    for res in response:

                        skill_id = res['skill_id']

                        # VALIDATE SUBSKILL
                        sql_str = "SELECT subskill FROM subskills WHERE subskill_id IN"
                        sql_str += " (SELECT subskill_id FROM skill_subskills WHERE"
                        sql_str += " skill_id='{0}')".format(skill_id)
                        db_res = self.postgres.query_fetch_all(sql_str)

                        if db_res:

                            db_subskills = [res['subskill'] for res in db_res]

                        db_subskills.sort()
                        subskills.sort()

                        if db_subskills == subskills:

                            flag = True
                            temp = {}
                            temp['exercise_skill_id'] = self.sha_security.generate_token(False)
                            temp['skill_id'] = skill_id
                            temp['exercise_id'] = exercise_id
                            self.postgres.insert('exercise_skills', temp, 'exercise_skill_id')

                            break

                    if not flag:

                        self.new_exercise_skill(exercise_id, skill, subskills)

                else:

                    self.new_exercise_skill(exercise_id, skill, subskills)

    def new_exercise_skill(self, exercise_id, skill, subskills):
        """ CREATE SKILL """

        skill_id = self.sha_security.generate_token(False)
        temp = {}
        temp['skill_id'] = skill_id
        temp['skill'] = skill
        temp['created_on'] = time.time()
        self.postgres.insert('skills', temp, 'skill_id')

        # GET SUBSKILL IDs
        if subskills:

            for subskill in subskills:

                subskill_id = ""
                sql_str = "SELECT subskill_id FROM subskills WHERE"
                sql_str += " subskill='{0}'".format(subskill)
                response = self.postgres.query_fetch_one(sql_str)

                if response:

                    subskill_id = response['subskill_id']

                else:

                    subskill_id = self.sha_security.generate_token(False)
                    temp = {}
                    temp['subskill_id'] = subskill_id
                    temp['subskill'] = subskill
                    temp['created_on'] = time.time()
                    self.postgres.insert('subskills', temp, 'subskill_id')

                # LINK SUBSKILL TO SKILL
                temp = {}
                temp['skill_subskill_id'] = self.sha_security.generate_token(False)
                temp['skill_id'] = skill_id
                temp['subskill_id'] = subskill_id
                self.postgres.insert('skill_subskills', temp, 'skill_subskill_id')

        # LINK QUESTION TO SKILL
        temp = {}
        temp['exercise_skill_id'] = self.sha_security.generate_token(False)
        temp['skill_id'] = skill_id
        temp['exercise_id'] = exercise_id
        self.postgres.insert('exercise_skills', temp, 'exercise_skill_id')

        return 1

    # def iu_question(self, data, course_id, section_id, subsection_id, exercise_id):
    #     """ UPDATE QUESTION """

    #     question_id = self.get_question_id(data)

    #     sql_str = "SELECT question_id FROM course_question WHERE"
    #     sql_str += " course_id='{0}'".format(course_id)
    #     sql_str += " AND section_id='{0}'".format(section_id)
    #     sql_str += " AND subsection_id='{0}'".format(subsection_id)
    #     sql_str += " AND exercise_id='{0}'".format(exercise_id)
    #     sql_str += " AND question_id='{0}'".format(question_id)

    #     if not self.postgres.query_fetch_one(sql_str):

    #         qtype = data['Question Type']

    #         temp = {}
    #         temp['question_id'] = question_id
    #         temp['course_question_id'] = self.sha_security.generate_token(False)
    #         temp['course_id'] = course_id
    #         temp['section_id'] = section_id
    #         temp['subsection_id'] = subsection_id
    #         temp['exercise_id'] = exercise_id
    #         temp['question_type'] = data['Question Type']
    #         temp['tags'] = json.dumps(data['Question Tags'].replace("\'", "").replace("\"", "")[1:-1].split(", "))
    #         temp['shuffle_options'] = ""
    #         temp['shuffle_answers'] = ""
    #         temp['feedback'] = ""
    #         array_choice = []

    #         if qtype == 'FITBT':

    #             ans = "".join(re.findall(r'[^\{$\}]', data['Question Correct Answer']))
    #             answer = {}
    #             answer['answer'] = data['Question'].replace("<ans>", str(ans))

    #             quest = {}
    #             quest['question'] = data['Question']

    #             temp['correct_answer'] = json.dumps(answer)
    #             temp['question'] = json.dumps(quest)

    #         elif qtype == 'FITBD':

    #             answer = {}
    #             answer['answer'] = data['Question']

    #             allans = "".join(re.findall(r'[^\{$\}]', data['Question Correct Answer'])).split(", ")

    #             for ans in allans:

    #                 correct_answer = answer['answer'].replace("[blank]", ans, 1)
    #                 answer['answer'] = correct_answer

    #             quest = {}
    #             quest['question'] = data['Question'].replace("[blank]", "<ans>")

    #             temp['correct_answer'] = json.dumps(answer)
    #             temp['question'] = json.dumps(quest)

    #         elif qtype == 'MULCH':

    #             choices = "".join(re.findall(r'[^\{$\}]', data['Question Choices']))
    #             choices = choices.split(", ")

    #             for choice in choices:

    #                 array_choice.append(choice)

    #             answer = {}
    #             answer['answer'] = data['Question Correct Answer']

    #             quest = {}
    #             quest['question'] = data['Question']

    #             temp['correct_answer'] = json.dumps(answer)
    #             temp['question'] = json.dumps(quest)

    #         elif qtype == 'MATCH':

    #             temp['shuffle_options'] = data['Question Shuffle Options']
    #             temp['shuffle_answers'] = data['Question Shuffle Answers']

    #             allans = "".join(re.findall(r'[^\{$\}]', data['Question Correct Answer'])).split(", ")
    #             answer = {}
    #             answer['answer'] = allans

    #             quest_data = data['Question'].replace("\"", "")
    #             allquest = "".join(re.findall(r'[^\{$\}]', quest_data)).split(", ")
    #             quest = {}
    #             quest['question'] = allquest

    #             array_choice = "".join(re.findall(r'[^\{$\}]', data['Question Choices']))
    #             array_choice = array_choice.split(", ")
    #             temp['correct_answer'] = json.dumps(answer)
    #             temp['question'] = json.dumps(quest)

    #         elif qtype == 'MULRE':

    #             temp['shuffle_options'] = data['Question Shuffle Options']
    #             temp['shuffle_answers'] = data['Question Shuffle Answers']

    #             allans = data['Question Correct Answer'].replace("\"", "")
    #             allans = "".join(re.findall(r'[^\{$\}]', allans)).split(", ")
    #             answer = {}
    #             answer['answer'] = allans

    #             quest = {}
    #             quest['question'] = data['Question']

    #             array_choice = data['Question Choices'].replace("\"", "")
    #             array_choice = "".join(re.findall(r'[^\{$\}]', array_choice))
    #             array_choice = array_choice.split(", ")
    #             temp['correct_answer'] = json.dumps(answer)
    #             temp['question'] = json.dumps(quest)

    #         if data['Question Description']:

    #             temp['description'] = data['Question Description']

    #         else:
    #             temp['description'] = "Lorem ipsum dolor sit amet, consectetur "
    #             temp['description'] += "adipiscing elit, sed do eiusmod tempor "
    #             temp['description'] += "incididunt ut labore et dolore magna aliqua."

    #         temp['choices'] = json.dumps(array_choice)
    #         temp['correct'] = data['Question Correct']
    #         temp['incorrect'] = data['Question Incorrect']
    #         temp['status'] = True
    #         temp['num_eval'] = data['Question Num Eval'].upper() == 'TRUE'
    #         temp['created_on'] = time.time()

    #         self.postgres.insert('course_question', temp, 'course_question_id')

    #     return question_id

    def add_course_question(self, exercise_id):
        """ Add Question for Exercise """

        sql_str = "SELECT * FROM exercise WHERE exercise_id='{0}'".format(exercise_id)
        result = self.postgres.query_fetch_one(sql_str)

        if result:

            questions = []
            if result['draw_by_tag'] is True:

                # SELECT QUESTION BY QUESTION TYPE AND TAGS
                # tags = []
                # if result['draw_by_tag'] is True:
                tags = result['tags']

                qtypes = result['question_types']
                number_to_draw = result['number_to_draw']
                questions = self.generate_random_questions(qtypes, int(number_to_draw), tags)
                # questionnaires = self.get_questions_by_condition(qtypes, tags)
                # questions = self.select_random_questions(questionnaires, number_to_draw, qtypes)

            # INSERT TO COURSE QUESTION TABLE
            for question_id in questions:
                course_id = result['course_id']
                section_id = result['section_id']
                subsection_id = result['subsection_id']
                exercise_id = exercise_id

                self.insert_course_question(course_id, section_id, subsection_id, exercise_id, question_id)
                # qdata = self.get_question_by_id(question_id)

                # if qdata:

                #     tmp = {}
                #     tmp['course_question_id'] = self.sha_security.generate_token(False)
                #     tmp['course_id'] = result['course_id']
                #     tmp['section_id'] = result['section_id']
                #     tmp['subsection_id'] = result['subsection_id']
                #     tmp['exercise_id'] = exercise_id
                #     tmp['question_id'] = question_id
                #     tmp['question'] = json.dumps(qdata['question'])
                #     tmp['question_type'] = qdata['question_type']
                #     tmp['tags'] = json.dumps(qdata['tags'])
                #     tmp['choices'] = json.dumps(qdata['choices'])
                #     tmp['num_eval'] = qdata['num_eval']
                #     tmp['correct_answer'] = json.dumps(qdata['correct_answer'])
                #     tmp['correct'] = qdata['correct']
                #     tmp['incorrect'] = qdata['incorrect']

                #     if qdata['feedback']:
                #         tmp['feedback'] = qdata['feedback']

                #     if qdata['shuffle_options']:
                #         tmp['shuffle_options'] = qdata['shuffle_options']

                #     if qdata['shuffle_answers']:
                #         tmp['shuffle_answers'] = qdata['shuffle_answers']

                #     tmp['description'] = qdata['description']
                #     tmp['status'] = qdata['status']
                #     tmp['created_on'] = time.time()

                #     self.postgres.insert('course_question', tmp, 'course_question_id')

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

    def get_questions_by_condition(self, question_types, tags):
        """ Return Question by type and tags """

        qtype = ','.join("'{0}'".format(qtype) for qtype in question_types)
        tag = '"tags"'

        sql_str = "SELECT * FROM questions WHERE question_type IN ({0})".format(qtype)
        if tags:
            tags = ', '.join('"{0}"'.format(tag) for tag in tags)
            sql_str += " AND CAST({0} AS text) = '[{1}]'".format(tag, tags)

        results = self.postgres.query_fetch_all(sql_str)

        return results

    def select_random_questions(self, questions, number_to_draw, question_type):
        """ Return Questions by type """

        questionnaires = []

        number_to_draw = int(number_to_draw)
        if not number_to_draw:
            number_to_draw = 10

        limit = math.floor(number_to_draw / len(question_type))

        for qtype in question_type:
            qlist = [question['question_id'] for question in questions \
                     if question['question_type'] == qtype]

            # SHUFFLE QUESTIONS
            random.shuffle(qlist)

            qlist = qlist[:limit]
            questionnaires += qlist

        if len(questionnaires) != number_to_draw:

            draw_again = number_to_draw - len(questionnaires)
            qlist = [question['question_id'] for question in questions \
                     if question['question_type'] in question_type \
                     and question['question_id'] not in questionnaires]

            # SHUFFLE QUESTIONS
            random.shuffle(qlist)

            qlist = qlist[:draw_again]
            questionnaires += qlist

        return questionnaires

    def get_question_by_id(self, question_id):
        """ Return Question Data by ID """

        sql_str = "SELECT * FROM questions WHERE question_id = '{0}'".format(question_id)
        result = self.postgres.query_fetch_one(sql_str)

        return result

    def use_course(self, course_ids, token=None, userid=None):
        """ CHECK IF COURSE IN USE """

        for course_id in course_ids:

            sql_str = "SELECT course_id FROM user_group_courses WHERE"
            sql_str += " course_id='{0}'".format(course_id)
            if not self.postgres.query_fetch_one(sql_str):

                sql_str = "SELECT * FROM student_course WHERE"
                sql_str += " course_id='{0}'".format(course_id)

                student_course = self.postgres.query_fetch_all(sql_str)

                if student_course:

                    # CREATE GROUP
                    ng_data = {}
                    ng_data['user_group_name'] = self.generate_group_name()
                    ng_data['course_ids'] = [course_id]
                    ng_data['student_ids'] = [sc['account_id'] for sc in student_course or []]
                    ng_data['tutor_ids'] = []
                    ng_data['notify_members'] = False
                    ng_data['notify_managers'] = False

                    self.create_new_group(ng_data, token=token, userid=userid)

                    return 0
            else:
                return 0
        return 1

        # sql_str = "SELECT * FROM student_course WHERE"
        # sql_str += " course_id='{0}'".format(course_id)

        # if not self.postgres.query_fetch_one(sql_str):

        #     return 1

        # return 0

    def update_course(self, data, course_id=None):
        """ UPDATE COURSE """

        updated_data = {}
        updated_data['course_name'] = data['Course Name']
        updated_data['description'] = data['Course Description']
        updated_data['difficulty_level'] = data['Course Difficulty Level']
        updated_data['requirements'] = data['Course Requirements']

        # INIT CONDITION
        conditions = []

        # CONDITION FOR QUERY
        conditions.append({
            "col": "course_id",
            "con": "=",
            "val": data['Course ID']
            })

        self.postgres.update('course', updated_data, conditions)

        return data['Course ID']

    # def get_question_id(self, row):
    #     """ RETURN QUESTION ID """

    #     if row['Question'] and row['Question ID']:

    #         return row['Question ID']

    #     sql_str = "SELECT question_id FROM questions WHERE"
    #     sql_str += " question='{0}'".format(row['Question'])
    #     sql_str += " AND question_type='{0}'".format(row['Question Type'])
    #     sql_str += " AND tags='{0}'".format(row['Question Tags'])
    #     response = self.postgres.query_fetch_one(sql_str)

    #     question_id = ""

    #     if not response:

    #         qtype = row['Question Type']

    #         question_id = self.sha_security.generate_token(False)

    #         temp = {}
    #         temp['question_id'] = question_id
    #         temp['question_type'] = row['Question Type']
    #         temp['tags'] = json.dumps(row['Question Tags'].replace("\'", "").replace("\"", "")[1:-1].split(", "))
    #         temp['shuffle_options'] = ""
    #         temp['shuffle_answers'] = ""
    #         temp['feedback'] = ""
    #         array_choice = []

    #         if qtype == 'FITBT':

    #             ans = "".join(re.findall(r'[^\{$\}]', row['Question Correct Answer']))
    #             answer = {}
    #             answer['answer'] = row['Question'].replace("<ans>", str(ans))

    #             quest = {}
    #             quest['question'] = row['Question']

    #             temp['correct_answer'] = json.dumps(answer)
    #             temp['question'] = json.dumps(quest)

    #         elif qtype == 'FITBD':

    #             answer = {}
    #             answer['answer'] = row['Question']

    #             allans = "".join(re.findall(r'[^\{$\}]', row['Question Correct Answer'])).split(", ")

    #             for ans in allans:

    #                 correct_answer = answer['answer'].replace("[blank]", ans, 1)
    #                 answer['answer'] = correct_answer

    #             quest = {}
    #             quest['question'] = row['Question'].replace("[blank]", "<ans>")

    #             temp['correct_answer'] = json.dumps(answer)
    #             temp['question'] = json.dumps(quest)

    #         elif qtype == 'MULCH':

    #             choices = "".join(re.findall(r'[^\{$\}]', row['Question Choices']))
    #             choices = choices.split(", ")

    #             for choice in choices:

    #                 array_choice.append(choice)

    #             answer = {}
    #             answer['answer'] = row['Question Correct Answer']

    #             quest = {}
    #             quest['question'] = row['Question']

    #             temp['correct_answer'] = json.dumps(answer)
    #             temp['question'] = json.dumps(quest)

    #         elif qtype == 'MATCH':

    #             temp['shuffle_options'] = row['Question Shuffle Options']
    #             temp['shuffle_answers'] = row['Question Shuffle Answers']

    #             allans = "".join(re.findall(r'[^\{$\}]', row['Question Correct Answer'])).split(", ")
    #             answer = {}
    #             answer['answer'] = allans

    #             quest_data = row['Question'].replace("\"", "")
    #             allquest = "".join(re.findall(r'[^\{$\}]', quest_data)).split(", ")
    #             quest = {}
    #             quest['question'] = allquest

    #             array_choice = "".join(re.findall(r'[^\{$\}]', row['Question Choices']))
    #             array_choice = array_choice.split(", ")
    #             temp['correct_answer'] = json.dumps(answer)
    #             temp['question'] = json.dumps(quest)

    #         elif qtype == 'MULRE':

    #             temp['shuffle_options'] = row['Question Shuffle Options']
    #             temp['shuffle_answers'] = row['Question Shuffle Answers']

    #             allans = row['Question Correct Answer'].replace("\"", "")
    #             allans = "".join(re.findall(r'[^\{$\}]', allans)).split(", ")
    #             answer = {}
    #             answer['answer'] = allans

    #             quest = {}
    #             quest['question'] = row['Question']

    #             array_choice = row['Question Choices'].replace("\"", "")
    #             array_choice = "".join(re.findall(r'[^\{$\}]', array_choice))
    #             array_choice = array_choice.split(", ")
    #             temp['correct_answer'] = json.dumps(answer)
    #             temp['question'] = json.dumps(quest)

    #         if row['Question Description']:

    #             temp['description'] = row['Question Description']

    #         else:
    #             temp['description'] = "Lorem ipsum dolor sit amet, consectetur "
    #             temp['description'] += "adipiscing elit, sed do eiusmod tempor "
    #             temp['description'] += "incididunt ut labore et dolore magna aliqua."

    #         temp['choices'] = json.dumps(array_choice)
    #         temp['correct'] = row['Question Correct']
    #         temp['incorrect'] = row['Question Incorrect']
    #         temp['num_eval'] = row['Question Num Eval'].upper() == 'TRUE'

    #         if row['Question Feedback']:
    #             temp['feedback'] = row['Question Feedback']
    #         temp['status'] = True
    #         temp['created_on'] = time.time()
    #         self.postgres.insert('questions', temp)

    #     else:

    #         question_id = response['question_id']

    #     return question_id


    def get_period(self, epoch_range, format_range):
        """ Return Start and End Time """

        start = epoch_range[0]
        end = epoch_range[-1]

        year = datetime.fromtimestamp(int(end)).strftime('%Y')
        month = datetime.fromtimestamp(int(end)).strftime('%m')
        day = datetime.fromtimestamp(int(end)).strftime('%d')

        if format_range in ['day', 'days']:
            end = datetime(int(year), int(month), int(day), 23, 59, 59).timestamp()

        elif format_range in ['weeks', 'week']:
            end = self.week_end_date(end)

        elif format_range in ['year', 'years']:
            month_end = calendar.monthrange(int(year), int(month))[1]
            end = datetime(int(year), 12, int(month_end), 23, 59, 59).timestamp()

        else:
            month_end = calendar.monthrange(int(year), int(month))[1]
            end = datetime(int(year), int(month), int(month_end), 23, 59, 59).timestamp()

        tmp = {}
        tmp['start'] = int(start)
        tmp['end'] = int(end)

        return tmp

    def epoch_range(self, epoch_format, number):
        """ Return Epoch Timestamp Coverage """

        if epoch_format in ['years', 'year']:
            epoch_format = "years"

        if epoch_format in ['months', 'month']:
            epoch_format = "months"

        if epoch_format in ['weeks', 'week']:
            epoch_format = "weeks"

        if epoch_format in ['days', 'day']:
            epoch_format = "days"

        year = datetime.now().strftime("%Y")
        month = datetime.now().strftime("%m")
        day = datetime.now().strftime("%d")

        is_default = False
        if not epoch_format and not number:
            start = datetime(int(year), 1, 1, 0, 0)
            end = datetime(int(year), int(month), 1, 0, 0)
            number = dateutil.relativedelta.relativedelta(end, start).months
            epoch_format = "months"
            is_default = True

        epoch = []

        if epoch_format == "months":
            day = 1

        if epoch_format == "years":
            day = 1
            month = 1

        base_start = datetime(int(year), int(month), int(day), 0, 0)

        if number and int(number):
            for num in range(int(number)):
                kwargs = {}
                kwargs[epoch_format] = int(num + 1)

                start = base_start - dateutil.relativedelta.relativedelta(**kwargs)
                epoch_start = round(start.timestamp())
                epoch.append(epoch_start)

            if is_default:
                epoch.append(round(base_start.timestamp()))
            else:
                epoch.append(round(base_start.timestamp()))
                epoch.sort()
                epoch.remove(epoch[0])

            epoch.sort()

        return epoch

    def week_end_date(self, epoch):
        """ Return end of week date """

        timestamp = epoch
        one_day = 86400
        end_week_date = (timestamp + (one_day * 7)) - 1
        return end_week_date

    def week_start_end(self, epoch):
        """ Return week start and end """

        date = datetime.fromtimestamp(int(epoch)).strftime('%Y-%m-%d')

        date = datetime.strptime(date, '%Y-%m-%d')

        week_start = date - timedelta(days=date.weekday())  # Monday
        week_end = week_start + timedelta(days=6)  # Sunday

        data = {}
        data['week_start'] = week_start.timestamp()
        data['week_end'] = week_end.timestamp()
        return data

    def epoch_week_number(self, epoch):
        """ Return Week Number """

        return datetime.fromtimestamp(int(epoch)).strftime("%V")

    def yearend_month_date(self, epoch_date):
        """ Return Month Year End Date in Epoch"""

        year = datetime.fromtimestamp(int(epoch_date)).strftime('%Y')
        epoch_year = datetime(int(year), 12, 1, 0, 0).strftime('%s')
        return epoch_year

    def month_end(self, epoch_date):
        """ Return Month End """

        year = datetime.fromtimestamp(int(epoch_date)).strftime('%Y')
        month = datetime.fromtimestamp(int(epoch_date)).strftime('%m')
        day = calendar.monthrange(int(year), int(month))[1]

        month_end = int(datetime(int(year), int(month), int(day), 0, 0).timestamp())
        return month_end

    def get_epoch_weekday(self, epoch_date):
        """ Return day of epoch date """

        return datetime.fromtimestamp(epoch_date).strftime("%A")

    def get_epoch_month(self, epoch_date):
        """ Return Epoch Date Month """

        return datetime.fromtimestamp(int(epoch_date)).strftime('%b')

    def get_epoch_year(self, epoch_date):
        """ Return Epoch Year """

        return datetime.fromtimestamp(int(epoch_date)).strftime('%Y')

    def day_end(self, epoch_date):
        """ Return Day End"""

        # END
        year = datetime.fromtimestamp(int(epoch_date)).strftime("%Y")
        month = datetime.fromtimestamp(int(epoch_date)).strftime("%m")
        day = datetime.fromtimestamp(int(epoch_date)).strftime("%d")
        end = int(datetime(int(year), int(month), int(day), 23, 59, 59).timestamp())
        return end

    def generate_random_questions(self, question_types, number_to_draw, tags):
        """ Generate Random Question """

        questions = []
        limit = math.floor(number_to_draw / len(question_types))
        for qtype in question_types:

            questions += self.get_random_questions(qtype, limit, tags)

        if len(questions) != number_to_draw:

            draw_again = number_to_draw - len(questions)
            question_type = random.choice(question_types)
            questions += self.get_random_questions(question_type, draw_again, tags)

        return questions
        
    def get_random_questions(self, question_type, number_to_draw, tags):
        """ Return Question by Type and Tags """

        if question_type.upper() == "MATCH":
            # GENERATE FITBT MATCHING TYPE QUESTIONS
            questions = self.create_match_question(tags, number_to_draw)

        else:
            questionnaires = self.get_questions(question_type, tags, number_to_draw)
            questions = [question['question_id'] for question in questionnaires]

        return questions

    def get_questions(self, question_type, tags, limit):
        """ Return Questions """

        tag = '"tags"'

        sql_str = "SELECT * FROM questions WHERE question_type='{0}'".format(question_type)
        if tags:
            tags = ', '.join('"{0}"'.format(tag) for tag in tags)
            sql_str += " AND CAST({0} AS text) = '[{1}]'".format(tag, tags)

        results = self.postgres.query_fetch_all(sql_str)

        if results:
            # questions = [result['question_id'] for result in results]
            random.shuffle(results)
            results = results[:limit]
        return results

    def create_match_question(self, tags, number_to_draw):
        """ Create Matching Type Questions """

        data = []
        match_qlimit = 5
        for _ in range(number_to_draw):
            questions = self.get_questions("FITBT", tags, match_qlimit)

            if questions:
                match_questions = []
                correct_answer = []
                for question in questions:

                    quest = question['question']['question'].replace("<ans>", "")
                    if "rest" in question['question']['question']:
                        quest = question['question']['question'].replace("<ans> rest <ans>", "")

                    answer = question['correct_answer']['answer'].replace(quest, "")
                    if "rest" in answer:
                        answer = answer.replace("rest", "/")
                        answer = answer.replace(" ", "")

                    match_questions.append(quest.rstrip())
                    correct_answer.append(answer)

                choices = correct_answer
                random.shuffle(choices)

                tmp_question = {}
                tmp_question['question'] = match_questions

                tmp_correct_answer = {}
                tmp_correct_answer['answer'] = correct_answer

                temp = {}
                temp['question_id'] = self.sha_security.generate_token(False)
                temp['question'] = json.dumps(tmp_question)
                temp['question_type'] = "MATCH"
                temp['tags'] = json.dumps(tags)
                temp['choices'] = json.dumps(choices)
                temp['shuffle_options'] = True
                temp['shuffle_answers'] = False
                temp['num_eval'] = True
                temp['correct_answer'] = json.dumps(tmp_correct_answer)
                temp['correct'] = questions[0]['correct']
                temp['incorrect'] = questions[0]['incorrect']
                temp['feedback'] = questions[0]['feedback']
                temp['description'] = questions[0]['description']
                temp['status'] = True
                temp['created_on'] = time.time()

                question_id = self.postgres.insert('questions', temp, 'question_id')
                data.append(question_id)

        return data

    def get_translation(self, message, language):
        """ Return Translation """

        sql_str = "SELECT translation FROM translations WHERE word_id=("
        sql_str += "SELECT word_id FROM words WHERE"
        sql_str += " name = '{0}') AND ".format(message)
        sql_str += "language_id=(SELECT language_id FROM language WHERE "
        sql_str += "initial='{0}')".format(language)

        return self.postgres.query_fetch_one(sql_str)

    def update_translate(self, data, userid):
        """ Update Translation """

        sql_str = "SELECT language FROM account WHERE"
        sql_str += " id='{0}'".format(userid)
        language = self.postgres.query_fetch_one(sql_str)

        if not language:

            return data

        if language['language'] != 'en-US':
            keys = ['rows', 'data', 'course', 'question_type', 'alert', 'message']
            for key in keys:

                if key in data.keys():

                    if key in ['alert', 'message']:

                        data[key] = self.translate_key(language, data[key])

                        continue

                    # print("PUmasok din dito")

                    # if key == 'question_type':

                    #     print("*"*100)
                    #     print("pumasok dito")
                    #     print(data[key])
                    #     print("*"*100)
                    #     if type(data[key]) == list:
                    #         new_question_type = []

                    #         for qt in data[key]:

                    #             new_question_type.append(self.translate_key(language,qt))

                    #         data[key] = new_question_type

                    #         continue

                    if type(data[key]) == list:

                        for row in data[key]:

                            # COURSE NAME
                            if 'course_name' in row.keys():
                                row['course_name'] = self.translate_key(language,
                                                                        row['course_name'])

                            # DESCRIPTION
                            if 'description' in row.keys() and row['description']:
                                row['description'] = self.translate_key(language,
                                                                        row['description'])

                            if 'notification_name' in row.keys():
                                row['notification_name'] = self.translate_key(language,
                                                                              row['notification_name'])

                            if 'progress' in row.keys() and row['progress'] not in [None, 0]:
                                row['progress'] = self.swap_decimal_symbol(userid, str(row['progress']), flag=True)

                            if 'round_progress' in row.keys() and row['round_progress'] not in [None, 0]:
                                row['round_progress'] = self.swap_decimal_symbol(userid, str(row['round_progress']), flag=True)

                            if 'correct' in row.keys() and row['correct'] not in [None, 0]:
                                if 'CORRECT' not in row['correct'].upper():
                                    row['correct'] = self.swap_decimal_symbol(userid, str(row['correct']), flag=False)

                            if 'score' in row.keys() and row['score'] not in [None, 0]:
                                row['score'] = self.swap_decimal_symbol(userid, str(row['score']), flag=True)

                            if 'subskills' in row.keys():
                                subskills = row['subskills']
                                if subskills:
                                    for sub in subskills:
                                        if sub['progress'] not in [None, 0]:
                                            sub['progress'] = self.swap_decimal_symbol(userid, str(sub['progress']), flag=True)

                                        if sub['correct'] not in [None, 0]:
                                            sub['correct'] = self.swap_decimal_symbol(userid, str(sub['correct']), flag=True)

                            if 'sections' in row.keys() and row['sections']:
                                    self.handle_subsection_progress(userid, row['sections'], language)

                            if 'subsection' in row.keys() and row['subsection']:
                                    self.handle_exercise_progress(userid, row['subsection'], language)

                            if 'exercise' in row.keys() and row['exercise']:
                                for exercise in row['exercise']:
                                    if exercise['progress'] not in [None, 0]:
                                        exercise['progress'] = self.swap_decimal_symbol(userid, str(exercise['progress']), flag=True)

                                    if exercise['percent_score'] not in [None, 0]:
                                        exercise['percent_score'] = self.swap_decimal_symbol(userid,
                                                                                            str(exercise['percent_score']),
                                                                                            flag=True)

                            # # QUESTION
                            # if 'question' in row.keys() and row['question'] not in [None, 0]:
                            #     row['question'] = self.swap_decimal_symbol(userid, str(row['question']))

                            # if 'choices' in row.keys() and row['choices'] not in [None, 0]:
                            #     row['choices'] = self.swap_decimal_symbol(userid, str(row['choices']))

                            # if 'correct_answer' in row.keys() and row['correct_answer'] not in [None, 0]:
                            #     row['correct_answer'] = self.swap_decimal_symbol(userid, str(row['correct_answer']))

                    else:

                        if not data[key]:

                            continue

                        if 'course_name' in data[key].keys():
                            if type(data[key]['course_name']) == str:

                                data[key]['course_name'] = self.translate_key(language,
                                                                              data[key]['course_name'])


                        if 'description' in data[key].keys():
                            if type(data[key]['description']) == str:

                                data[key]['description'] = self.translate_key(language,
                                                                              data[key]['description'])


                        if 'question_type' in data[key].keys():

                            if type(data[key]['question_type']) == list:

                                new_question_type = []

                                for qt in data[key]['question_type']:

                                    new_question_type.append(self.translate_key(language,qt))

                                data[key]['question_type'] = new_question_type

                        if 'help' in data[key].keys():

                            if type(data[key]['help']) == bool:

                                if data[key]['help']:

                                    data[key]['help'] = self.translate_key(language,'true')

                                else:

                                    data[key]['help'] = self.translate_key(language,'false')

                        if 'estimate_time' in data[key].keys():

                            estimate_time = data[key]['estimate_time'].split(" ")

                            if estimate_time[1] == 'minutes':

                                est = estimate_time[0] + ' ' + self.translate_key(language,'minutes')

                                data[key]['estimate_time'] = est

                        if 'progress' in data[key].keys() and data[key]['progress'] not in [None, 0]:
                            data[key]['progress'] = self.swap_decimal_symbol(userid, str(data[key]['progress']), flag=True)

                        if 'percent_score' in data[key].keys() and data[key]['percent_score'] not in [None, 0]:
                            data[key]['percent_score'] = self.swap_decimal_symbol(userid, str(data[key]['percent_score']))

                        if 'sections' in data[key].keys() and data[key]['sections']:
                            self.handle_subsection_progress(userid, data[key]['sections'], language)

        return data

    def handle_exercise_progress(self, userid, data, language):
        """ Handle Decimal Swap of Exercise """

        for dta in data:
            if dta['exercises']:
                for exercise in dta['exercises']:
                    if exercise['progress'] not in [None, 0]:
                        exercise['progress'] = self.swap_decimal_symbol(userid, str(exercise['progress']), flag=True, language=language)

                    if exercise['percent_score'] not in [None, 0]:
                        exercise['percent_score'] = self.swap_decimal_symbol(userid, str(exercise['percent_score']), flag=True, language=language)

    def handle_subsection_progress(self, userid, data, language):
        """ Handle Decimal Swap of Subsection """

        for dta in data:
            if not 'subsection' in dta.keys():
                continue
            if dta['subsection']:
                self.handle_exercise_progress(userid, dta['subsection'], language)


    def translate_key(self, language, original):
        """ Translate Key """

        message = "".join(re.findall(r'[a-zA-Z0-9\ \.\,\-\(\)\!]', original))
        translate = self.get_translation(message, language['language'])

        if translate:
            return translate['translation']

        return original

    def get_account_details(self, user_id):
        """ Return Account Details """

        sql_str = "SELECT * FROM account WHERE id='{0}'".format(user_id)
        result = self.postgres.query_fetch_one(sql_str)
        return result

    def section_master_translation(self, rows, userid, language=None, exercise_name=None, question_name=None):
        """ SECTION MASTER TRANSLATION """

        if not language:

            sql_str = "SELECT language FROM account WHERE"
            sql_str += " id='{0}'".format(userid)
            language = self.postgres.query_fetch_one(sql_str)

        tras_answer = self.translate_key(language, 'Answer')
        trans_cor_ans = self.translate_key(language, 'Correct Answer')

        if not question_name:

            question_name = self.translate_key(language, 'Question')

        if language['language'] == 'en-US':

            return rows

        if not rows:

            return []

        for row in rows:

            if 'children' in row.keys():

                if not row['children']:

                    continue

                for subsection in row['children']:

                    if 'children' in subsection.keys():

                        if not subsection['children']:

                            continue

                        for exercise in subsection['children']:
    
                            if not exercise_name:

                                exercise_name = self.translate_key(language, 'Exercise')
                                ename = exercise['name'].split(" ")[0]
                                if ename == "Exercise":
                                    exercise['name'] = exercise_name + " " + exercise['name'].split('Exercise ')[1]

                            else:

                                exercise_name = exercise['name'].split(" ")[0]
                                if exercise_name == "Exercise":
                                    exercise_name = self.translate_key(language, 'Exercise')
                                    exercise['name'] = exercise_name + " " + exercise['name'].split('Exercise ')[1]
                    
                            if 'children' in exercise.keys() and exercise['children']:

                                exercise['children'] = self.question_translate(exercise['children'], language, question_name, tras_answer, trans_cor_ans)

        return rows

    def question_translate(self, rows, language, question_name, tras_answer, trans_cor_ans):
        """ TRANSLATION OF QUESTIONS KEYS """

        for row in rows:

            row['name'] = question_name + " " + row['name'].split('Question ')[1]

            if 'children' in row.keys():

                if not row['children']:

                    continue

                for child in row['children']:

                    if child['name'] == 'Question':
                        child['name'] = question_name
                    elif child['name'] == 'Answer':
                        child['name'] = tras_answer
                    elif child['name'] == 'Correct Answer':
                        child['name'] = trans_cor_ans
                    else:
                        child['name'] = self.translate_key(language, child['name'])

        return rows

    def insert_student_skills(self, account_id):
        """ UPDATE STUDENT SKILLS """

        sql_str = "SELECT DISTINCT(skill) FROM skills WHERE"
        sql_str += " skill NOT IN (SELECT skill FROM student_all_skills WHERE"
        sql_str += " account_id='{0}')".format(account_id)
        skills = self.postgres.query_fetch_all(sql_str)


        # INSERT MISSING SKILL
        for skill in skills or []:

            student_skills = {}
            student_skills['student_skill_id'] = self.sha_security.generate_token(False)
            student_skills['account_id'] = account_id
            student_skills['skill'] = skill['skill']
            student_skills['progress'] = 0
            student_skills['answered_questions'] = 0
            student_skills['correct'] = 0
            student_skills['time_studied'] = '0 day'
            student_skills['created_on'] = int(time.time())

            self.postgres.insert('student_all_skills', student_skills)

        # -- OLD PROCESS -- #
        # # GET ALL SKILLS NOT EXIST IN student_skills TABLE
        # sql_str = "SELECT skill_id FROM skills WHERE skill_id IN ("
        # sql_str += "SELECT skill_id FROM question_skills WHERE question_id IN ("
        # sql_str += "SELECT question_id FROM course_question WHERE exercise_id IN ("
        # sql_str += "SELECT exercise_id FROM student_exercise WHERE"
        # sql_str += " account_id='{0}'".format(account_id)
        # sql_str += " AND status=True))) AND skill_id NOT IN ("
        # sql_str += "SELECT skill_id FROM student_skills WHERE "
        # sql_str += "account_id ='{0}')".format(account_id)
        # skills = self.postgres.query_fetch_all(sql_str)

        # if skills:

        #     # INSERT MISSING SKILL
        #     for skill in skills:

        #         student_skills = {}
        #         student_skills['student_skill_id'] = self.sha_security.generate_token(False)
        #         student_skills['account_id'] = account_id
        #         student_skills['skill_id'] = skill['skill_id']
        #         student_skills['progress'] = 0
        #         student_skills['answered_questions'] = 0
        #         student_skills['correct'] = 0
        #         student_skills['time_studied'] = '0 day'
        #         student_skills['created_on'] = int(time.time())

        #         self.postgres.insert('student_skills', student_skills)

        return 1

    def insert_student_subskills(self, account_id):
        """ INSERT STUDENT SUBSKILLS """

        sql_str = "SELECT subskill_id, subskill FROM subskills WHERE"
        sql_str += " subskill_id IN (SELECT DISTINCT(subskill_id) FROM"
        sql_str += " subskills WHERE subskill_id NOT IN (SELECT subskill_id"
        sql_str += " FROM student_all_subskills WHERE"
        sql_str += " account_id='{0}'))".format(account_id)
        subskills = self.postgres.query_fetch_all(sql_str)

        for subskill in subskills or []:

            student_subskills = {}
            student_subskills['student_subskill_id'] = self.sha_security.generate_token(False)
            student_subskills['account_id'] = account_id
            student_subskills['subskill_id'] = subskill['subskill_id']
            student_subskills['subskill'] = subskill['subskill']
            student_subskills['progress'] = 0
            student_subskills['answered_questions'] = 0
            student_subskills['correct'] = 0
            student_subskills['time_studied'] = '0 day'
            student_subskills['created_on'] = int(time.time())

            self.postgres.insert('student_all_subskills', student_subskills)

        # -- OLD PROCESS -- #
        # sql_str = "SELECT * FROM ("
        # sql_str += "SELECT * FROM subskills WHERE subskill_id IN ("
        # sql_str += "SELECT subskill_id FROM skill_subskills WHERE skill_id in ("
        # sql_str += "SELECT skill_id FROM student_skills WHERE"
        # sql_str += " account_id='{0}'".format(account_id)
        # sql_str += "))) AS subskills WHERE subskill_id NOT IN ("
        # sql_str += "SELECT subskill_id FROM student_subskills WHERE"
        # sql_str += " account_id = '{0}')".format(account_id)
        # subskills = self.postgres.query_fetch_all(sql_str)

        # if subskills:

        #     for subskill in subskills:

        #         student_subskills = {}
        #         student_subskills['student_subskill_id'] = self.sha_security.generate_token(False)
        #         student_subskills['account_id'] = account_id
        #         student_subskills['subskill_id'] = subskill['subskill_id']
        #         student_subskills['progress'] = 0
        #         student_subskills['answered_questions'] = 0
        #         student_subskills['correct'] = 0
        #         student_subskills['time_studied'] = '0 day'
        #         student_subskills['created_on'] = int(time.time())

        #         self.postgres.insert('student_subskills', student_subskills)

        return 1

    def update_skill_subskills(self, account_id, master_skill_ids):
        """" UPDATE STUDENT SUBSKILLS """

        selected = ','.join("'{0}'".format(selected) for selected in master_skill_ids)

        # GET ALL STUDENT SKILLS
        # sql_str = "SELECT skill_id FROM student_skills WHERE"
        # sql_str += " account_id='{0}'".format(account_id)
        # student_skills = self.postgres.query_fetch_all(sql_str)
        sql_str = "SELECT skill FROM master_skills"
        sql_str += " WHERE master_skill_id IN ({0})".format(selected)
        student_skills = self.postgres.query_fetch_all(sql_str)

        # EACH ALL SKILLS
        skills = {}
        skill_ttl_quest = {}
        skill_correct = {}
        skill_answered = {}

        for student_skill in student_skills:

            skills[student_skill['skill']] = 0
            skill_ttl_quest[student_skill['skill']] = 0
            skill_correct[student_skill['skill']] = 0
            skill_answered[student_skill['skill']] = 0

        # GET ALL SUBSKILLS
        # sql_str = "SELECT subskill_id FROM student_subskills WHERE"
        # sql_str += " account_id='{0}'".format(account_id)
        # student_subskills = self.postgres.query_fetch_all(sql_str)
        sql_str = "SELECT subskill FROM master_subskills"
        student_subskills = self.postgres.query_fetch_all(sql_str)

        # EACH ALL SUBSKILLS
        sskills = {}
        ttl_quest = {}
        correct = {}
        answered = {}

        for student_subskill in student_subskills:

            sskills[student_subskill['subskill']] = 0
            ttl_quest[student_subskill['subskill']] = 0
            correct[student_subskill['subskill']] = 0
            answered[student_subskill['subskill']] = 0

        # GET QUESTIONS WITH SUBSKILL
        # sql_str = "SELECT seq.is_correct, seq.course_question_id, seq.answer, cquest.question_id, ("
        # sql_str += "SELECT array_to_json(array_agg(sklls)) FROM (SELECT *, ("
        # sql_str += "SELECT array_to_json(array_agg(sbsklls)) FROM ("
        # sql_str += "SELECT * FROM skill_subskills skll_sskll WHERE"
        # sql_str += " skll_sskll.skill_id=qs.skill_id) AS sbsklls)"
        # sql_str += " AS subskills FROM question_skills qs WHERE"
        # sql_str += " qs.question_id=cquest.question_id) AS sklls) AS skills FROM ("
        # sql_str += "SELECT is_correct, course_question_id, answer FROM student_exercise_questions"
        # sql_str += " WHERE student_exercise_id IN (SELECT student_exercise_id FROM"
        # sql_str += " student_exercise WHERE status is True AND"
        # sql_str += " account_id='{0}'".format(account_id)
        # sql_str += " AND status is True) AND "
        # sql_str += " account_id='{0}'".format(account_id)
        # sql_str += ") AS seq INNER JOIN course_question cquest ON"
        # sql_str += " seq.course_question_id=cquest.course_question_id "
        # questions = self.postgres.query_fetch_all(sql_str)
        sql_str = """SELECT seq.is_correct, seq.course_question_id, seq.answer,
        cquest.question_id, (SELECT array_to_json(array_agg(sklls)) FROM
        (SELECT qs.question_id, qs.skill_id, sk.skill,
        (SELECT array_to_json(array_agg(sbsklls)) FROM (SELECT skll_sskll.skill_id,
        skll_sskll.subskill_id, ssubs.subskill FROM skill_subskills skll_sskll
        INNER JOIN subskills ssubs ON ssubs.subskill_id=skll_sskll.subskill_id
        WHERE skll_sskll.skill_id=qs.skill_id) AS sbsklls) AS subskills FROM
        question_skills qs INNER JOIN skills AS sk ON sk.skill_id=qs.skill_id
        WHERE qs.question_id=cquest.question_id) AS sklls) AS skills FROM
        (SELECT is_correct, course_question_id, answer FROM
        student_exercise_questions WHERE student_exercise_id IN (SELECT
        student_exercise_id FROM student_exercise WHERE status is True AND
        account_id='{0}'""".format(account_id)
        sql_str += """ AND status is True) AND"""
        sql_str += """ account_id='{0}')""".format(account_id)
        sql_str += """ AS seq INNER JOIN course_question cquest ON
        seq.course_question_id=cquest.course_question_id"""
        questions = self.postgres.query_fetch_all(sql_str)

        # EACH QUESTIONS
        for question in questions or []:

            if not question['skills']:

                continue

            for skill in question['skills']:

                # ========= SKILLS ========= #
                if skill['skill'] in skills.keys():

                    skill_ttl_quest[skill['skill']] = skill_ttl_quest[skill['skill']] + 1
                    
                    if not question['answer'] in [None, '', str([""]), str([]), str(['']), [], ['']]:

                        skill_answered[skill['skill']] = skill_answered[skill['skill']] + 1

                    if question['is_correct']:

                        skill_correct[skill['skill']] = skill_correct[skill['skill']] + 1

                # ========= SUBSKILLS ========= #
                if not skill['subskills']:

                    continue

                for subskills in skill['subskills']:

                    if not subskills['subskill'] in sskills.keys():

                        continue

                    ttl_quest[subskills['subskill']] = ttl_quest[subskills['subskill']] + 1

                    if not question['answer'] in [None, '', str([""]), str([]), str(['']), [], ['']]:

                        answered[subskills['subskill']] = answered[subskills['subskill']] + 1

                    if question['is_correct']:

                        correct[subskills['subskill']] = correct[subskills['subskill']] + 1

        # UPDATE student_subskills
        for sskill in sskills.keys():

            # INIT CONDITION
            conditions = []

            # CONDITION FOR QUERY
            conditions.append({
                "col": "account_id",
                "con": "=",
                "val": account_id
                })
            conditions.append({
                "col": "subskill",
                "con": "=",
                "val": sskill
                })

            fsscorrect = 0

            if correct[sskill] and answered[sskill]:

                fsscorrect = self.format_progress((correct[sskill] / answered[sskill]) * 100)

            updated_data = {}
            updated_data['progress'] = self.subskill_progress(sskill, correct[sskill])
            updated_data['answered_questions'] = answered[sskill]
            updated_data['correct'] = fsscorrect
            updated_data['update_on'] = int(time.time())

            # -- OLD PROCESS -- #
            # self.postgres.update('student_subskills', updated_data, conditions)

            self.postgres.update('student_all_subskills', updated_data, conditions)

        # UPDATE student_skills
        for skill in skills.keys():

            # INIT CONDITION
            conditions = []

            # CONDITION FOR QUERY
            conditions.append({
                "col": "account_id",
                "con": "=",
                "val": account_id
                })
            conditions.append({
                "col": "skill",
                "con": "=",
                "val": skill
                })


            progress, qanswered, qcorrect = self.skill_progress(account_id, skill)

            updated_data = {}
            updated_data['progress'] = progress
            updated_data['answered_questions'] = qanswered
            updated_data['correct'] = qcorrect

            # fscorrect = 0

            # if skill_correct[skill] and skill_answered[skill]:

            #     fscorrect = self.format_progress((skill_correct[skill] / skill_answered[skill]) * 100)

            # updated_data['answered_questions'] = skill_answered[skill]
            # updated_data['correct'] = fscorrect
            updated_data['update_on'] = int(time.time())

            # self.postgres.update('student_skills', updated_data, conditions)
            self.postgres.update('student_all_skills', updated_data, conditions)

        return 1

    def skill_progress(self, account_id, skill):
        """ SKILL PROGRESS """

        # sql_str = "SELECT progress, answered_questions, correct FROM student_subskills WHERE"
        # sql_str += " account_id='{0}'".format(account_id)
        # sql_str += " AND subskill_id IN (SELECT subskill_id FROM skill_subskills WHERE"
        # sql_str += " skill='{0}')".format(skill)

        sql_str = """SELECT progress, answered_questions, correct FROM
        student_all_subskills WHERE"""
        sql_str += """ account_id='{0}'""".format(account_id)
        sql_str += """ AND subskill IN (SELECT subskill FROM master_subskills
        WHERE master_subskill_id IN (SELECT master_subskill_id
        FROM master_skill_subskills WHERE master_skill_id IN
        (SELECT master_skill_id FROM master_skills WHERE"""
        sql_str += """ skill='{0}')))""".format(skill)

        result = self.postgres.query_fetch_all(sql_str)

        if result:

            total_progress = 0
            total_answered = 0
            total_correct = 0

            for row in result:

                total_progress = total_progress + float(row['progress'])
                total_answered = total_answered + int(row['answered_questions'])
                total_correct = total_correct + float(row['correct'])

            progress = self.format_progress(total_progress / len(result))
            correct = self.format_progress((total_correct/(len(result)*100)) * 100)

            return [progress, total_answered, correct]

        return [0, 0, 0]

    def subskill_progress(self, subskill_id, correct_answer):
        """ SUBSKILL PROGRESS """

        sql_str = "SELECT max_score FROM subskills WHERE"
        sql_str += " subskill='{0}'".format(subskill_id)
        result = self.postgres.query_fetch_one(sql_str)

        if not result['max_score']:

            max_score = 80
        else:

            max_score = int(result['max_score'])

        if correct_answer > max_score:

            return 100

        else:

            return self.format_progress((correct_answer / max_score) * 100)

    # def update_student_skills(self, account_id):
    #     """" UPDATE STUDENT SUBSKILLS """

    #     # GET ALL STUDENT SKILLS
    #     sql_str = "SELECT skill_id FROM student_skills WHERE"
    #     sql_str += " account_id='{0}'".format(account_id)
    #     student_skills = self.postgres.query_fetch_all(sql_str)

    #     # EACH ALL SKILLS
    #     skills = {}
    #     # ttl_quest = {}
    #     # correct = {}
    #     # answered = {}

    #     for student_skill in student_skills:

    #         skills[student_skill['skill_id']] = 0

    #     # GET QUESTION SKILLS
    #     # COMPUTE SUBSKILLS
    #     # UPDATE SUBSKILLS

    #     return 0

    def get_exercise_hierarchy(self, course_id):
        """Return All Exercise By Sequence """

        sql_str = "SELECT * FROM course_master WHERE course_id ='{0}'".format(course_id)
        result = self.postgres.query_fetch_one(sql_str)

        if not result:
            return 0

        data = []
        # section = [res['section_id'] for res in result['children']]
        # subsection = [sec['subsection_id'] for res in result['children'] for sec in res['children']]
        
        if result['children']:
            seccount = 1
            for res in result['children']:
                subcount = 1
                for sub in res['children']:
                    data += self.get_exercises(sub, res['section_name'], seccount, subcount)
                    subcount += 1
                seccount += 1

        return data

    def get_exercises(self, subsection, section_name, sec_num, sub_num):
        """ Return Exercise in Sequence"""

        data = []
        subsection_name = subsection['subsection_name']
        exercise =  subsection['children']

        if exercise:
            for res in exercise:
                tmp = {}
                tmp['exercise_id'] = res['exercise_id']
                tmp['exercise_number'] = res['exercise_number']
                tmp['subsection_name'] = subsection_name
                tmp['section_name'] = section_name
                tmp['exercise'] = "{0}.{1}.{2}".format(sec_num, sub_num, res['exercise_number'])

                data.append(tmp)

        return data
        
    def get_exercise_requirements(self, user_id, exercise_id):
        """ Return Requirements  """

        sql_str = "SELECT * FROM exercise e INNER JOIN exercise_requirements er ON"
        sql_str += " e.exercise_id=er.exercise_id INNER JOIN student_exercise se ON"
        sql_str += " e.exercise_id=se.exercise_id WHERE"
        sql_str += " e.exercise_id='{0}'".format(exercise_id)
        sql_str += " AND se.account_id='{0}'".format(user_id)
        sql_str += " AND se.status is True"
        result = self.postgres.query_fetch_one(sql_str)

        requirements = []
        if result:

            # exercise_name = result['exercise_name']

            sql_str = "SELECT course_id FROM exercise WHERE"
            sql_str += " exercise_id='{0}'".format(exercise_id)
            course = self.postgres.query_fetch_one(sql_str)
            course_id = course['course_id']

            in_group = self.student_in_group(user_id, course_id)

            if not in_group:

                result['is_lock'] = False

            if result['is_lock']:

                requirements.append({"status": False,
                                     "description": "This is lock by the Tutor!"})

            if result['grade_locking'] is True and result['is_unlocked'] is False:

            # CHECK ON PREVIOUS AS PREREQUISITE
                requirements.append({"status": True,
                                     "description": "Available after you have been granted explicit access"})


                # sql_str = "SELECT e.exercise_id, e.exercise_number, ss.difficulty_level,"
                # sql_str += " ss.subsection_name, s.difficulty_level AS section_diff FROM"
                # sql_str += " exercise e INNER JOIN subsection ss ON"
                # sql_str += " e.subsection_id=ss.subsection_id INNER JOIN section s ON"
                # sql_str += " e.section_id=s.section_id WHERE"
                # sql_str += " e.course_id ='{0}'".format(course_id)
                # sql_str += " ORDER BY s.difficulty_level ASC, ss.difficulty_level ASC"
                # sql_str += " e.exercise_number ASC"
                # all_exercise = self.postgres.query_fetch_all(sql_str)
                all_exercise = self.get_exercise_hierarchy(course_id)
                if all_exercise:

                    previous_ex = ""
                    flag = False
                    for item in all_exercise:

                        if item['exercise_id'] == exercise_id:

                            flag = True
                            break

                        else:

                            previous_ex = item
                            flag = False

                    if flag and previous_ex:

                        subsection_name = previous_ex['subsection_name']
                        exercise_number = previous_ex['exercise_number']

                        exercise_name = self.get_exercise_name(course_id)
                        previous = "{0} -> {1} {2}".format(subsection_name, exercise_name, exercise_number)

                        req = {}
                        req['status'] = False
                        req['description'] = "Available after {0} is finished".format(previous)

                        requirements.append(req)

        return requirements

    def get_exercise_name(self, course_id):
        """ Return Exercise name"""

        sql_str = "SELECT * FROM course WHERE course_id = '{0}'".format(course_id)
        result = self.postgres.query_fetch_one(sql_str)

        exercise_name = "Exercise"
        if result and result['exercise_name']:
            exercise_name = result['exercise_name']

        # if exercise_name == "Exercise":
        #     exercise_name = self.translate_key(language, 'Exercise')

        return exercise_name

    def get_subsection_requirements(self, user_id, subsection_id):
        """ Return Requirements  """

        sql_str = "SELECT * FROM subsection s INNER JOIN subsection_requirements sr ON"
        sql_str += " s.subsection_id=sr.subsection_id INNER JOIN student_subsection ss ON"
        sql_str += " s.subsection_id=ss.subsection_id WHERE"
        sql_str += " s.subsection_id='{0}'".format(subsection_id)
        sql_str += " AND ss.account_id='{0}'".format(user_id)
        sql_str += " AND ss.status is True"
        result = self.postgres.query_fetch_one(sql_str)

        requirements = []
        if result:

            if result['is_lock']:

                requirements.append({"status": False,
                                     "description": "This is lock by the Tutor!"})

            if result['grade_locking'] is True and result['is_unlocked'] is False:

            # CHECK ON PREVIOUS AS PREREQUISITE
                requirements.append({"status": True,
                                     "description": "Available after you have been granted explicit access"})
            
                level = result['difficulty_level'] - 1

                sql_str = "SELECT * FROM subsection WHERE difficulty_level = '{0}'".format(level)
                sql_str += " AND section_id = '{0}'".format(result['section_id'])
                prev = self.postgres.query_fetch_one(sql_str)

                prev_sub = "previous"
                if prev:
                    prev_sub = prev['subsection_name']

                    requirements.append({"status": False,
                                         "description": "Available after {0} meets the completion level".format(prev_sub)})

        return requirements

    def get_section_requirements(self, user_id, section_id):
        """ Return Requirements  """

        sql_str = "SELECT * FROM section s INNER JOIN section_requirements sr ON"
        sql_str += " s.section_id=sr.section_id INNER JOIN student_section ss ON"
        sql_str += " s.section_id=ss.section_id WHERE"
        sql_str += " s.section_id='{0}' AND ss.status is True".format(section_id)
        result = self.postgres.query_fetch_one(sql_str)

        requirements = []
        if result:

            if result['is_lock']:

                requirements.append({"status": False,
                                     "description": "This is lock by the Tutor!"})

            if result['grade_locking'] is True and result['is_unlocked'] is False:

            # CHECK ON PREVIOUS AS PREREQUISITE
                requirements.append({"status": True,
                                     "description": "Available after you have been granted explicit access"})
                
                level = result['difficulty_level'] - 1

                sql_str = "SELECT * FROM section WHERE difficulty_level = '{0}'".format(level)
                sql_str += " AND course_id = '{0}'".format(result['course_id'])
                prev = self.postgres.query_fetch_one(sql_str)

                prev_sub = "previous"
                if prev:
                    prev_sub = prev['section_name']

                    requirements.append({"status": False,
                                         "description": "Available after {0} meets the completion level".format(prev_sub)})

        return requirements

    def send_notif(self, userid, token, account_id, description, notif_type, notif_name):
        """ SEND NOTIFICATION """

        # NOTIFICATION
        notification_id = self.sha_security.generate_token(False)
        # notif_type = "New Task"
        notif = {}
        notif['notification_id'] = notification_id
        notif['account_id'] = account_id
        # notif['notification_name'] = "New Task"
        notif['notification_name'] = notif_name
        notif['notification_type'] = notif_type
        # notif['description'] = "You have new Course: {0}".format(query_json['course_name'])
        notif['description'] = description
        notif['seen_by_user'] = False
        notif['created_on'] = time.time()
        self.postgres.insert('notifications', notif)

        # TRIGGER SOCKETIO NOTIFICATION
        message = {}
        message['token'] = token
        message['userid'] = userid
        message['type'] = 'notification'
        message['data'] = notif
        message['notification_id'] = notification_id
        message['notification_type'] = notif_type

        socketio = SocketIO('0.0.0.0', 5000, LoggingNamespace)
        socketio.emit('notification', message)
        socketio.disconnect()

        return 1

    def validate_course_requirements(self, course_id):
        """ VALIDATE COURSE REQUIREMENTS """

        # GET COURSE STRUCTURE
        sql_str = "SELECT e.exercise_id, e.exercise_number, ss.difficulty_level,"
        sql_str += " ss.subsection_name, s.difficulty_level AS section_diff,"
        sql_str += " s.section_id, ss.subsection_id"
        sql_str += " FROM exercise e INNER JOIN subsection ss ON"
        sql_str += " e.subsection_id=ss.subsection_id"
        sql_str += " INNER JOIN section s ON e.section_id=s.section_id WHERE"
        sql_str += " e.course_id ='{0}'".format(course_id)
        sql_str += " ORDER BY s.difficulty_level ASC, ss.difficulty_level ASC,"
        sql_str += " e.exercise_number ASC"
        all_exercise = self.postgres.query_fetch_all(sql_str)

        fsection_id = ""
        fsubsection_id = ""
        fexercise_id = ""
        if all_exercise:

            fsection_id = all_exercise[0]['section_id']
            fsubsection_id = all_exercise[0]['subsection_id']
            fexercise_id = all_exercise[0]['exercise_id']

        # VALIDATE COURSE TABLE
        sql_str = "SELECT * FROM course_requirements WHERE"
        sql_str += " course_id='{0}'".format(course_id)

        # VALIDATE COURSE TABLE
        if not self.postgres.query_fetch_one(sql_str):

            # INSERT REQUIREMENTS (COURSE TABLE)
            temp = {}
            temp['course_requirement_id'] =  self.sha_security.generate_token(False)
            temp['course_id'] = course_id
            temp['completion'] = 80
            temp['grade_locking'] = False
            temp['on_previous'] = False
            temp['is_lock'] = False
            temp['is_visible'] = True
            temp['created_on'] = time.time()
            self.postgres.insert('course_requirements', temp)

        # CHECK SECTION TABLE
        sql_str = "SELECT * FROM section WHERE"
        sql_str += " course_id='{0}'".format(course_id)
        sections = self.postgres.query_fetch_all(sql_str)
        
        # EACH SECTION
        for section in sections:

            # VALIDATE SECTION TABLE
            sql_str = "SELECT * FROM section_requirements WHERE"
            sql_str += " section_id='{0}'".format(section['section_id'])

            if not self.postgres.query_fetch_one(sql_str):

                # INSERT REQUIREMENTS (SECTION TABLE)
                temp = {}
                temp['section_requirement_id'] =  self.sha_security.generate_token(False)
                temp['section_id'] = section['section_id']
                temp['completion'] = 80
                temp['grade_locking'] = True
                temp['on_previous'] = False
                temp['is_lock'] = False
                temp['is_visible'] = True
                temp['created_on'] = time.time()

                if fsection_id == section['section_id']:

                    temp['grade_locking'] = False
                    
                self.postgres.insert('section_requirements', temp)

        # CHECK SUBSECTION TABLE
        sql_str = "SELECT * FROM subsection WHERE"
        sql_str += " course_id='{0}'".format(course_id)
        subsections = self.postgres.query_fetch_all(sql_str)
        
        # EACH SUBSECTION
        for subsection in subsections:

            # VALIDATE SUBSECTION TABLE
            sql_str = "SELECT * FROM subsection_requirements WHERE"
            sql_str += " subsection_id='{0}'".format(subsection['subsection_id'])

            if not self.postgres.query_fetch_one(sql_str):

                # INSERT REQUIREMENTS (SUBSECTION TABLE)
                temp = {}
                temp['subsection_requirement_id'] =  self.sha_security.generate_token(False)
                temp['subsection_id'] = subsection['subsection_id']
                temp['completion'] = 80
                temp['grade_locking'] = True
                temp['on_previous'] = False
                temp['is_lock'] = False
                temp['is_visible'] = True
                temp['created_on'] = time.time()

                if fsubsection_id == subsection['subsection_id']:

                    temp['grade_locking'] = False

                self.postgres.insert('subsection_requirements', temp)

        # CHECK EXERCISE TABLE
        sql_str = "SELECT * FROM exercise WHERE"
        sql_str += " course_id='{0}'".format(course_id)
        exercises = self.postgres.query_fetch_all(sql_str)
        
        # EACH EXERCISE
        for exercise in exercises:

            # VALIDATE EXERCISE TABLE
            sql_str = "SELECT * FROM exercise_requirements WHERE"
            sql_str += " exercise_id='{0}'".format(exercise['exercise_id'])

            if not self.postgres.query_fetch_one(sql_str):

                # INSERT REQUIREMENTS (EXERCISE TABLE)
                temp = {}
                temp['exercise_requirement_id'] =  self.sha_security.generate_token(False)
                temp['exercise_id'] = exercise['exercise_id']
                temp['completion'] = 80

                temp['grade_locking'] = True
                if self.is_min_exercise(exercise['exercise_id']):
                    temp['grade_locking'] = False

                temp['on_previous'] = False
                temp['is_lock'] = False
                temp['is_visible'] = True
                temp['created_on'] = time.time()

                if fexercise_id == exercise['exercise_id']:

                    temp['grade_locking'] = False

                self.postgres.insert('exercise_requirements', temp)

        return 1

    def is_fraction(self, data):
        """ VALIDATE IF FRACTION """

        # REMOVE SPACE
        data = data.replace(" ", "")
        values = data.split('/')
        return len(values) == 2 and all(i.isdigit() for i in values)

    def is_min_exercise(self, exercise_id):
        """ RETURN IF FIRST EXERCISE """

        sql_str = "SELECT e.exercise_number, s.difficulty_level FROM exercise e"
        sql_str += " LEFT JOIN subsection s ON e.subsection_id = s.subsection_id"
        sql_str += " WHERE e.exercise_id = '{0}'".format(exercise_id)
        exercise = self.postgres.query_fetch_one(sql_str)

        if not exercise:
            return 0

        exercise_number = exercise['exercise_number']
        # subsection_level = exercise['difficulty_level']

        # CHECK SECTION FIRST EXERCISE
        sql_str = "SELECT (SELECT MIN(difficulty_level) FROM subsection WHERE section_id"
        sql_str += " IN( SELECT section_id FROM exercise WHERE"
        sql_str += " exercise_id='{0}')) as subdiff,(SELECT MIN(exercise_number)".format(exercise_id)
        sql_str += " FROM exercise WHERE subsection_id IN( SELECT subsection_id FROM exercise"
        sql_str += " WHERE exercise_id='{0}')) as exercise_number".format(exercise_id)
        result = self.postgres.query_fetch_one(sql_str)
        if result:
            # if result['subdiff'] == subsection_level and \
            if result['exercise_number'] == exercise_number:
                return 1

        return 0

    def update_master_skills(self, skill, subskills):
        """ UPDATE MASTER SKILLS """

        sql_str = "SELECT master_skill_id FROM master_skills WHERE"
        sql_str += " skill='{0}'".format(skill)
        result = self.postgres.query_fetch_one(sql_str)

        master_skill_id = ""
        if not result:

            master_skill_id = self.sha_security.generate_token(False)
            temp = {}
            temp['master_skill_id'] = master_skill_id
            temp['skill'] = skill
            temp['created_on'] = time.time()
            self.postgres.insert('master_skills', temp, 'master_skill_id')

        else:

            master_skill_id = result['master_skill_id']

        for subskill in subskills or []:

            sql_str = "SELECT master_subskill_id FROM master_subskills WHERE"
            sql_str += " subskill='{0}'".format(subskill)
            response = self.postgres.query_fetch_one(sql_str)

            master_subskill_id = ""
            if not response:

                master_subskill_id = self.sha_security.generate_token(False)
                temp = {}
                temp['master_subskill_id'] = master_subskill_id
                temp['subskill'] = subskill
                temp['created_on'] = time.time()
                self.postgres.insert('master_subskills', temp, 'master_subskill_id')

            else:

                master_subskill_id = response['master_subskill_id']

            # MASTER SKILL SUBSKILL
            sql_str = "SELECT master_skill_subskill_id FROM master_skill_subskills WHERE"
            sql_str += " master_skill_id='{0}' AND".format(master_skill_id)
            sql_str += " master_subskill_id='{0}'".format(master_subskill_id)
            response = self.postgres.query_fetch_one(sql_str)

            if not response:

                master_skill_subskill_id = self.sha_security.generate_token(False)
                temp = {}
                temp['master_skill_subskill_id'] = master_skill_subskill_id
                temp['master_skill_id'] = master_skill_id
                temp['master_subskill_id'] = master_subskill_id
                self.postgres.insert('master_skill_subskills', temp, 'master_skill_subskill_id')

        return master_skill_id

    def student_in_group(self, userid, course_id):
        """ CHECK IF STUDENT IN GROUP """

        in_group = True

        sql_str = "SELECT student_id FROM user_group_students"
        sql_str += " WHERE user_group_id IN (SELECT user_group_id"
        sql_str += " FROM user_group_courses WHERE"
        sql_str += " course_id='{0}'".format(course_id)
        sql_str += ") AND student_id='{0}'".format(userid)
        student_id = self.postgres.query_fetch_one(sql_str)

        if not student_id:

            in_group = False

        return in_group

    def time_studied(self, userid, start, end, language):
        """ DATE DIFFERENCE """

        try:
            dt1 = datetime.fromtimestamp(start)
            dt2 = datetime.fromtimestamp(end)
            rd = dateutil.relativedelta.relativedelta (dt2, dt1)

            days = ""
            hours = ""
            minutes = ""
            seconds = ""

            if rd.days:

                unit = "day"
                if rd.days > 1:
                    unit = "days"

                unit = self.translate(userid, unit, language=language)
                days = "{0} {1} ".format(rd.days, unit)

            if rd.hours:

                unit = "hour"
                if rd.hours > 1:
                    unit = "hours"

                unit = self.translate(userid, unit, language=language)
                hours = "{0} {1} ".format(rd.hours, unit)

            if rd.minutes:

                unit = "minute"
                if rd.minutes > 1:
                    unit = "minutes"

                unit = self.translate(userid, unit, language=language)
                minutes = "{0} {1} ".format(rd.minutes, unit)

            if rd.seconds:

                unit = self.translate(userid, "seconds", language=language)
                seconds = "{0} {1}".format(rd.seconds, unit)

            date_diff = "{0}{1}{2}{3}".format(days, hours, minutes, seconds)

            return date_diff

        except:

            return 0

    def course_temp_headers(self):
        """ RETURN ALL COURSE TEMPLATE HEADERS """

        return [
            "Course ID",
            "Course Name",
            "Course Title",
            "Course Description",
            "Course Difficulty Level",
            "Course Requirements",

            # "Section ID",
            "Section Name",
            "Section Description",
            "Section Difficulty Level",

            # "Subsection ID",
            "Subsection Name",
            "Subsection Description",
            "Subsection Difficulty Level",

            # "Exercise ID",
            "Exercise Number",
            "Exercise Question Type",
            "Exercise Tags",
            "Exercise Description",
            "Exercise Draw By Skills",
            "Exercise Draw By Tag",
            "Exercise Editing Allowed",
            "Exercise Help",
            "Exercise Instant Feedback",
            "Exercise Moving Allowed",
            "Exercise Number to Draw",
            "Exercise Passing Criterium",
            "Exercise Save Seed",
            "Exercise Seed",
            "Exercise Shuffled",
            "Exercise Text Before Start",
            "Exercise Text After End",
            "Exercise Timed Limit",
            "Exercise Timed Type",
            "Exercise Skills",
            "Exercise Repeatable",

            # "Question ID",
            "Question",
            "Question Type",
            "Question Tags",
            "Question Choices",
            "Question Shuffle Options",
            "Question Shuffle Answers",
            "Question Num Eval",
            "Question Correct Answer",
            "Question Correct",
            "Question Incorrect",
            "Question Feedback",
            "Question Skills",
            "Question Description"
        ]

    def check_course_headers(self, headers):
        """ CHECK COURSE HEADERS """

        for key in self.course_temp_headers():

            if not key in headers:

                return 0

        return 1

    def insert_questions(self, rows):
        """ INSERT QUESTIONS """

        batch = self.sha_security.generate_token(False)

        for row in rows:
    
            if not self.insert_question(row, batch):

                return 0

        return 1

    def insert_question(self, row, batch, course_id=None, section_id=None, subsection_id=None, exercise_id=None):
        """ INSERT QUESTION """

        correct_answer = {}
        question = {}
        array_choice = []

        correct_answer, question, array_choice, tags = self.arrange_question(row)

        # cst_tag = 'CAST("tags" AS text)'
        # sql_str = "SELECT * FROM questions WHERE"
        # sql_str += " question->>'question' = '{0}' AND".format(row['Question'])
        # sql_str += " question_type ='{0}' AND".format(row['Question Type'])
        # sql_str += " {0} = '{1}'".format(cst_tag, json.dumps(tags))

        sql_str = "SELECT question_id, orig_question, orig_answer,"
        sql_str += " orig_choices, orig_skills, orig_tags FROM questions WHERE"
        sql_str += " question='{0}'".format(json.dumps(question))
        sql_str += " AND question_type='{0}'".format(row['Question Type'])
        sql_str += " AND tags='{0}'".format(json.dumps(tags))
        sql_str += " AND correct_answer='{0}'".format(json.dumps(correct_answer))

        questions = self.postgres.query_fetch_one(sql_str)

        if questions:

            question_id = questions['question_id']
            orig_question = questions['orig_question']
            orig_answer = questions['orig_answer']
            orig_choices = questions['orig_choices']
            orig_tags = questions['orig_tags']
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

                conditions = []

                # CONDITION FOR QUERY
                conditions.append({
                    "col": "question_id",
                    "con": "=",
                    "val": question_id
                    })

                self.postgres.update('questions', updated_data, conditions)

            if not orig_tags and row['Question Tags']:

                orig_tags = {}
                orig_tags['tags'] = row['Question Tags']

                updated_data = {}
                updated_data['orig_tags'] = json.dumps(orig_tags)

                conditions = []

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

            if exercise_id:

                sequence_num = 1

                sql_str = "SELECT sequence FROM uploaded_exercise_question WHERE"
                sql_str += " exercise_id='{0}'".format(exercise_id)
                sql_str += " AND NOT sequence IS NULL ORDER BY sequence DESC LIMIT 1"
                qsec = self.postgres.query_fetch_one(sql_str)

                if qsec:

                    sequence_num = qsec['sequence'] + 1

                ins_data = {}
                ins_data['exercise_id'] = exercise_id
                ins_data['question_id'] = question_id
                ins_data['sequence'] = sequence_num
                self.postgres.insert('uploaded_exercise_question', ins_data)

            if course_id and section_id and subsection_id and exercise_id and question_id:

                self.insert_course_question(course_id, section_id, subsection_id, exercise_id, question_id)

            return 1

        question_id = self.sha_security.generate_token(False)
        temp = {}
        temp['question_id'] = question_id
        temp['question'] = json.dumps(question)
        temp['question_type'] = row['Question Type']
        temp['tags'] = json.dumps(tags)

        temp['choices'] = json.dumps(array_choice)

        temp['shuffle_options'] = False
        if row['Question Shuffle Options']:
            temp['shuffle_options'] = row['Question Shuffle Options'].upper() == 'TRUE'

        temp['shuffle_answers'] = False
        if row['Question Shuffle Answers']:
            temp['shuffle_answers'] = row['Question Shuffle Answers'].upper() == 'TRUE'

        temp['num_eval'] = False
        if row['Question Num Eval']:
            temp['num_eval'] = row['Question Num Eval'].upper() == 'TRUE'

        temp['correct_answer'] = json.dumps(correct_answer)
        temp['correct'] = row['Question Correct']
        temp['incorrect'] = row['Question Incorrect']
        temp['feedback'] = row['Question Feedback']
        temp['description'] = row['Question Description']
        temp['batch'] = batch

        orig_question = {}
        orig_question['question'] = row['Question']

        orig_answer = {}
        orig_answer['answer'] = row['Question Correct Answer']

        orig_choices = {}
        orig_choices['choices'] = row['Question Choices']

        orig_tags = {}
        orig_tags['tags'] = row['Question Tags']

        orig_skills = {}
        orig_skills['skills'] = row['Question Skills']

        temp['orig_question'] = json.dumps(orig_question)
        temp['orig_answer'] = json.dumps(orig_answer)
        temp['orig_choices'] = json.dumps(orig_choices)
        temp['orig_tags'] = json.dumps(orig_tags)
        temp['orig_skills'] = json.dumps(orig_skills)

        temp['status'] = True
        # if row['Status']:
        #     temp['status'] = row['Status'].upper() == 'TRUE'

        temp['created_on'] = time.time()

        if not self.postgres.insert('questions', temp, 'question_id'):

            # An error occured while uploading the file!
            return 0

        if course_id and section_id and subsection_id and exercise_id and question_id:

            self.insert_course_question(course_id, section_id, subsection_id, exercise_id, question_id)

        # GET SKILL IDs
        if row['Question Skills']:

            skills = []

            try:

                skills = json.loads(row['Question Skills'])

            except:

                row['Question Skills'] = row['Question Skills'].replace("}\", \"{", "}, {")

                try:

                    skills = json.loads(row['Question Skills'])

                except:

                    print("Invalid skills: {0}".format(row['Question Skills']))

            for item in skills:

                skill = ""
                skill_id = ""
                subskills = []
                if 'skill' in item.keys():

                    skill = item['skill']

                if 'subskills' in item.keys():

                    subskills = item['subskills']

                if skill:

                    sql_str = "SELECT skill_id FROM skills WHERE"
                    sql_str += " skill='{0}'".format(skill)
                    response = self.postgres.query_fetch_all(sql_str)

                    if response:

                        db_subskills = []

                        flag = False
                        for res in response:

                            skill_id = res['skill_id']

                            # VALIDATE SUBSKILL
                            sql_str = "SELECT subskill FROM subskills WHERE subskill_id IN"
                            sql_str += " (SELECT subskill_id FROM skill_subskills WHERE"
                            sql_str += " skill_id='{0}')".format(skill_id)
                            db_res = self.postgres.query_fetch_all(sql_str)

                            if db_res:

                                db_subskills = [res['subskill'] for res in db_res]

                            db_subskills.sort()
                            subskills.sort()

                            if db_subskills == subskills:

                                flag = True
                                temp = {}
                                temp['question_skill_id'] = self.sha_security.generate_token(False)
                                temp['skill_id'] = skill_id
                                temp['question_id'] = question_id
                                self.postgres.insert('question_skills', temp, 'question_skill_id')

                                break

                        if not flag:

                            self.create_skill(question_id, skill, subskills)

                    else:

                        self.create_skill(question_id, skill, subskills)

        if exercise_id:

            sequence_num = 1

            sql_str = "SELECT sequence FROM uploaded_exercise_question WHERE"
            sql_str += " exercise_id='{0}'".format(exercise_id)
            sql_str += " AND NOT sequence IS NULL ORDER BY sequence DESC LIMIT 1"
            qsec = self.postgres.query_fetch_one(sql_str)

            if qsec:

                sequence_num = qsec['sequence'] + 1

            ins_data = {}
            ins_data['exercise_id'] = exercise_id
            ins_data['question_id'] = question_id
            ins_data['sequence'] = sequence_num
            self.postgres.insert('uploaded_exercise_question', ins_data)

        return 1

    def create_skill(self, question_id, skill, subskills):
        """ CREATE SKILL """

        # UPDATE MASTER SKILLS
        self.update_master_skills(skill, subskills)

        skill_id = self.sha_security.generate_token(False)
        temp = {}
        temp['skill_id'] = skill_id
        temp['skill'] = skill
        temp['created_on'] = time.time()
        self.postgres.insert('skills', temp, 'skill_id')

        # GET SUBSKILL IDs
        if subskills:

            for subskill in subskills:

                subskill_id = ""
                sql_str = "SELECT subskill_id FROM subskills WHERE"
                sql_str += " subskill='{0}'".format(subskill)
                response = self.postgres.query_fetch_one(sql_str)

                if response:

                    subskill_id = response['subskill_id']

                else:

                    subskill_id = self.sha_security.generate_token(False)
                    temp = {}
                    temp['subskill_id'] = subskill_id
                    temp['subskill'] = subskill
                    temp['created_on'] = time.time()
                    self.postgres.insert('subskills', temp, 'subskill_id')

                # LINK SUBSKILL TO SKILL
                temp = {}
                temp['skill_subskill_id'] = self.sha_security.generate_token(False)
                temp['skill_id'] = skill_id
                temp['subskill_id'] = subskill_id
                self.postgres.insert('skill_subskills', temp, 'skill_subskill_id')

        # LINK QUESTION TO SKILL
        temp = {}
        temp['question_skill_id'] = self.sha_security.generate_token(False)
        temp['skill_id'] = skill_id
        temp['question_id'] = question_id
        self.postgres.insert('question_skills', temp, 'question_skill_id')

        return 1

    def run_sequence(self):
        """ Run Sequence """

        sql_str = "SELECT * FROM course_sequence"
        results = self.postgres.query_fetch_all(sql_str)

        if not results:

            sql_str = "SELECT course_id FROM course ORDER BY difficulty_level"
            result = self.postgres.query_fetch_all(sql_str)

            count = 1
            for res in result:
                temp = {}
                temp['course_id'] = res['course_id']
                temp['sequence'] = count

                self.postgres.insert('course_sequence', temp)
                count += 1

        sql_str = "SELECT course_id FROM course"
        sql_str += " WHERE course_id NOT IN (SELECT course_id FROM course_sequence) ORDER BY difficulty_level"
        results = self.postgres.query_fetch_all(sql_str)

        if results:
            prev_sequence = "SELECT MAX(sequence) AS sequence FROM course_sequence"
            result = self.postgres.query_fetch_one(sql_str)

            sequence = 10
            if not result:
                sequence = result['sequence']

            for res in results:
                temp = {}
                temp['course_id'] = res['course_id']
                temp['sequence'] = sequence

                self.postgres.insert('course_sequence', temp)
                sequence += 1

        return 1

    # UNUSED - PLEASE CHECK CHANGE ON TABLE (uploaded_exercise_question) IF PLAN TO USE THIS AGAIN
    def update_question(self, row, course_id=None, section_id=None, subsection_id=None, exercise_id=None):
        """ UPDATE QUESTIONS """

        question_id = row['Question ID']

        correct_answer = {}
        question = {}
        array_choice = []

        correct_answer, question, array_choice, tags = self.arrange_question(row)

        temp = {}
        temp['question'] = json.dumps(question)
        temp['question_type'] = row['Question Type']
        temp['tags'] = json.dumps(tags)

        temp['choices'] = json.dumps(array_choice)

        temp['shuffle_options'] = False
        if row['Question Shuffle Options']:
            temp['shuffle_options'] = row['Question Shuffle Options'].upper() == 'TRUE'

        temp['shuffle_answers'] = False
        if row['Question Shuffle Answers']:
            temp['shuffle_answers'] = row['Question Shuffle Answers'].upper() == 'TRUE'

        temp['num_eval'] = False
        if row['Question Num Eval']:
            temp['num_eval'] = row['Question Num Eval'].upper() == 'TRUE'

        temp['correct_answer'] = json.dumps(correct_answer)
        temp['correct'] = row['Question Correct']
        temp['incorrect'] = row['Question Incorrect']
        temp['feedback'] = row['Question Feedback']
        temp['description'] = row['Question Description']

        orig_question = {}
        orig_question['question'] = row['Question']

        orig_answer = {}
        orig_answer['answer'] = row['Question Correct Answer']

        orig_choices = {}
        orig_choices['choices'] = row['Question Choices']

        orig_tags = {}
        orig_tags['tags'] = row['Question Tags']

        orig_skills = {}
        orig_skills['skills'] = row['Question Skills']

        temp['orig_question'] = json.dumps(orig_question)
        temp['orig_answer'] = json.dumps(orig_answer)
        temp['orig_choices'] = json.dumps(orig_choices)
        temp['orig_tags'] = json.dumps(orig_tags)
        temp['orig_skills'] = json.dumps(orig_skills)

        temp['status'] = True
        # if row['Status']:
        #     temp['status'] = row['Status'].upper() == 'TRUE'

        temp['created_on'] = time.time()

        conditions = []
        conditions.append({
            "col": "question_id",
            "con": "=",
            "val": question_id
        })

        if course_id:

            sql_str = "SELECT question_id FROM course_question WHERE"
            sql_str += " course_id !='{0}' LIMIT 1".format(course_id)
            course_question = self.postgres.query_fetch_one(sql_str)

            if course_question:

                print("Not Possible to Update question_id: {0}".format(question_id))

                return 1

        if not self.postgres.update('questions', temp, conditions):

            # An error occured while uploading the file!
            return 0

        if course_id and section_id and subsection_id and exercise_id and question_id:

            conditions = []
            conditions.append({
                "col": "question_id",
                "con": "=",
                "val": question_id
            })

            self.postgres.update('course_question', temp, conditions)

        # GET SKILL IDs
        if row['Question Skills']:

            skills = []

            try:

                skills = json.loads(row['Question Skills'])

            except:

                row['Question Skills'] = row['Question Skills'].replace("}\", \"{", "}, {")

                try:

                    skills = json.loads(row['Question Skills'])

                except:

                    print("Invalid skills: {0}".format(row['Question Skills']))

            for item in skills:

                skill = ""
                skill_id = ""
                subskills = []
                if 'skill' in item.keys():

                    skill = item['skill']

                if 'subskills' in item.keys():

                    subskills = item['subskills']

                if skill:

                    sql_str = "SELECT skill_id FROM skills WHERE"
                    sql_str += " skill='{0}'".format(skill)
                    response = self.postgres.query_fetch_all(sql_str)

                    if response:

                        db_subskills = []

                        flag = False
                        for res in response:

                            skill_id = res['skill_id']

                            # VALIDATE SUBSKILL
                            sql_str = "SELECT subskill FROM subskills WHERE subskill_id IN"
                            sql_str += " (SELECT subskill_id FROM skill_subskills WHERE"
                            sql_str += " skill_id='{0}')".format(skill_id)
                            db_res = self.postgres.query_fetch_all(sql_str)

                            if db_res:

                                db_subskills = [res['subskill'] for res in db_res]

                            db_subskills.sort()
                            subskills.sort()

                            if db_subskills == subskills:

                                conditions = []

                                conditions.append({
                                    "col": "question_id",
                                    "con": "=",
                                    "val": question_id
                                    })

                                conditions.append({
                                    "col": "skill_id",
                                    "con": "=",
                                    "val": skill_id
                                    })

                                self.postgres.delete('question_skills', conditions)

                                flag = True
                                temp = {}
                                temp['question_skill_id'] = self.sha_security.generate_token(False)
                                temp['skill_id'] = skill_id
                                temp['question_id'] = question_id
                                self.postgres.insert('question_skills', temp, 'question_skill_id')

                                break

                        if not flag:

                            self.create_skill(question_id, skill, subskills)

                    else:

                        self.create_skill(question_id, skill, subskills)

        if exercise_id:

            ins_data = {}
            ins_data['exercise_id'] = exercise_id
            ins_data['question_id'] = question_id
            self.postgres.insert('uploaded_exercise_question', ins_data)

        return 1

    def arrange_question(self, row):
        """ ARRANGE QUESTION """

        correct_answer = {}
        question = {}
        array_choice = []

        tags = row['Question Tags'].replace("\"", "")
        tags = "".join(re.findall(r'[^\{$\}]', tags)).split(", ")

        if row['Question Type'] == 'FITBT':

            if row['Question Correct Answer'][0] == '{' and row['Question Correct Answer'][-1] == '}':

                allans = "".join(re.findall(r'[^\{$\}]', row['Question Correct Answer'])).split(", ")
                correct_answer['answer'] = allans

            elif '<ans> remainder <ans>' in row['Question']:

                # correct_answer['answer'] = row['Correct Answer']
                correct_answer['answer'] = row['Question'].replace("<ans> remainder <ans>", row['Question Correct Answer'])

            elif '<ans>/<ans>' in row['Question']:

                temp_quest = row['Question'].split('<ans>/<ans>')[0] + row['Question Correct Answer']

                correct_answer['answer'] = temp_quest

            elif '<ans>:<ans>:<ans>' in row['Question']:

                temp_quest = row['Question'].split('<ans>:<ans>:<ans>')[0] + row['Question Correct Answer']

                correct_answer['answer'] = temp_quest

            elif '<ans>:<ans>' in row['Question']:

                ans_count = row['Question'].split(" = ")[1].count('<ans>')
                ans_num = ':'.join("<ans>" for _ in range(ans_count))
                temp_quest = row['Question'].split(ans_num)[0] + row['Question Correct Answer']

                correct_answer['answer'] = temp_quest

            else:

                ans = "".join(re.findall(r'[^\{$\}]', row['Question Correct Answer']))
                correct_answer['answer'] = row['Question'].replace("<ans>", str(ans))

            question['question'] = row['Question']

        elif row['Question Type'] == 'MULCH':

            # choices = [choice for choice in row['Question choices'].split(",")]
            choices = "".join(re.findall(r'[^\{$\}]', row['Question Choices']))
            choices = choices.split(", ")

            if len(choices) == 1:
                choices = choices[0].split(",")

            for choice in choices:
                array_choice.append(choice)

            correct_answer['answer'] = row['Question Correct Answer']
            question['question'] = row['Question']

        elif row['Question Type'] == 'MATCH':

            allans = "".join(re.findall(r'[^\{$\}]', row['Question Correct Answer'])).split(", ")
            correct_answer['answer'] = allans

            quest_data = row['Question'].replace("\"", "")
            allquest = "".join(re.findall(r'[^\{$\}]', quest_data)).split(", ")
            question['question'] = allquest
            row['Question'] = json.dumps(allquest)

            array_choice = "".join(re.findall(r'[^\{$\}]', row['Question Choices']))
            array_choice = array_choice.split(", ")

        elif row['Question Type'] == 'MULRE':

            allans = row['Question Correct Answer'].replace("\"", "")
            allans = "".join(re.findall(r'[^\{$\}]', allans)).split(", ")

            correct_answer['answer'] = allans
            question['question'] = row['Question']

            array_choice = row['Question Choices'].replace("\"", "")
            array_choice = "".join(re.findall(r'[^\{$\}]', array_choice))
            array_choice = array_choice.split(", ")

        elif row['Question Type'] == 'FITBD':

            choices = "".join(re.findall(r'[^\{$\}]', row['Question Choices']))
            choices = choices.split(", ")

            if len(choices) == 1:
                choices = choices[0].split(",")

            for choice in choices:
                array_choice.append(choice)

            ans = row['Question Correct Answer'].replace("\"", "")
            ans = "".join(re.findall(r'[^\{$\}]', ans))
            ans = ans.split(", ")

            if len(ans) == 1:
                ans = ans[0].split(",")

            correct_answer['answer'] = ans
            question['question'] = row['Question']

        else:
            correct_answer['answer'] = row['Question Correct Answer']
            question['question'] = row['Question']

        return [correct_answer, question, array_choice, tags]

    def delete_question(self, row, exercise_id, course_id):
        """ DELETE QUESTION """

        question_id = row['Question ID']

        conditions = []

        conditions.append({
            "col": "question_id",
            "con": "=",
            "val": question_id
            })

        conditions.append({
            "col": "exercise_id",
            "con": "=",
            "val": exercise_id
            })

        self.postgres.delete('uploaded_exercise_question', conditions)

        sql_str = "SELECT question_id FROM course_question WHERE"
        sql_str += " NOT course_id !='{0}'".format(course_id)
        sql_str += " AND  question_id='{0}'".format(question_id)

        course_question = self.postgres.query_fetch_all(sql_str)

        if not course_question:

            # DELETE
            conditions = []

            conditions.append({
                "col": "question_id",
                "con": "=",
                "val": question_id
                })

            self.postgres.delete('course_question', conditions)
            self.postgres.delete('question_skills', conditions)
            self.postgres.delete('questions', conditions)

    def insert_course_question(self, course_id, section_id, subsection_id, exercise_id, question_id):
        """ INSERT COURSE QUESTION """

        qdata = self.get_question_by_id(question_id)

        if qdata:

            tmp = {}
            tmp['course_question_id'] = self.sha_security.generate_token(False)
            tmp['course_id'] = course_id
            tmp['section_id'] = section_id
            tmp['subsection_id'] = subsection_id
            tmp['exercise_id'] = exercise_id
            tmp['question_id'] = question_id
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

        return 1

    def delete_courses(self, course_ids, delete_questions):
        """Delete Courses"""

        for course_id in course_ids:

            sql_str = "SELECT * FROM section WHERE"
            sql_str += " course_id='{0}'".format(course_id)

            sections = self.postgres.query_fetch_all(sql_str)

            for section in sections:

                section_id = section['section_id']
                sql_str = "SELECT * FROM subsection WHERE"
                sql_str += " section_id='{0}'".format(section_id)

                subsections = self.postgres.query_fetch_all(sql_str)

                for subsection in subsections:

                    subsection_id = subsection['subsection_id']
                    sql_str = "SELECT * FROM exercise WHERE"
                    sql_str += " subsection_id='{0}'".format(subsection_id)

                    exercises = self.postgres.query_fetch_all(sql_str)


                    for exercise in exercises:

                        self.delete_exercise(exercise['exercise_id'])

                    self.delete_subsection(subsection['subsection_id'])

                self.delete_section(section['section_id'])

            # DELETE REQUIREMENTS
            # GET COURSE STRUCTURE
            sql_str = "SELECT e.exercise_id, e.exercise_number, ss.difficulty_level,"
            sql_str += " ss.subsection_name, s.difficulty_level AS section_diff,"
            sql_str += " s.section_id, ss.subsection_id"
            sql_str += " FROM exercise e INNER JOIN subsection ss ON"
            sql_str += " e.subsection_id=ss.subsection_id"
            sql_str += " INNER JOIN section s ON e.section_id=s.section_id WHERE"
            sql_str += " e.course_id ='{0}'".format(course_id)
            sql_str += " ORDER BY s.difficulty_level ASC, ss.difficulty_level ASC,"
            sql_str += " e.exercise_number ASC"
            all_exercise = self.postgres.query_fetch_all(sql_str)

            # EXERCISE
            if all_exercise:

                array_ids = [exer['exercise_id'] for exer in all_exercise]

                conditions = []

                conditions.append({
                    "col": "exercise_id",
                    "con": "in",
                    "val": array_ids
                    })

                self.postgres.delete('exercise_requirements', conditions)

                conditions = []

                conditions.append({
                    "col": "exercise_id",
                    "con": "in",
                    "val": array_ids
                    })

                self.postgres.delete('exercise_skills', conditions)

                del_question_ids = []
                if delete_questions:

                    str_ids = ','.join("'{0}'".format(ex_id) for ex_id in array_ids)

                    # DELETE QUESTIONS
                    sql_str = "SELECT question_id FROM uploaded_exercise_question WHERE"
                    sql_str += " exercise_id IN ({0})".format(str_ids)
                    sql_str += " AND NOT question_id IN (SELECT DISTINCT(question_id)"
                    sql_str += " FROM course_question WHERE NOT"
                    sql_str += " course_id='{0}')".format(course_id)
                    del_question_ids = self.postgres.query_fetch_all(sql_str)

                conditions = []

                conditions.append({
                    "col": "exercise_id",
                    "con": "in",
                    "val": array_ids
                    })

                self.postgres.delete('uploaded_exercise_question', conditions)


                conditions = []

                conditions.append({
                    "col": "exercise_id",
                    "con": "in",
                    "val": array_ids
                    })

                self.postgres.delete('course_question', conditions)

                # DO NOT MOVE THIS LINE ON TOP CHECK uploaded_exercise_question
                if del_question_ids:

                    question_ids = [del_quest['question_id'] for del_quest in del_question_ids]

                    conditions = []

                    conditions.append({
                        "col": "question_id",
                        "con": "in",
                        "val": question_ids
                        })

                    self.postgres.delete('question_skills', conditions)
                    self.postgres.delete('questions', conditions)

                conditions = []

                conditions.append({
                    "col": "exercise_id",
                    "con": "in",
                    "val": array_ids
                    })

                self.postgres.delete('video_exercise', conditions)

                conditions = []

                conditions.append({
                    "col": "exercise_id",
                    "con": "in",
                    "val": array_ids
                    })

                self.postgres.delete('student_exercise_repeat', conditions)

                conditions = []

                conditions.append({
                    "col": "exercise_id",
                    "con": "in",
                    "val": array_ids
                    })

                # self.postgres.delete('instruction', conditions)
                data_update = {}
                data_update['exercise_id'] = ""

                self.postgres.update('instruction', data_update, conditions)

                conditions = []

                conditions.append({
                    "col": "exercise_id",
                    "con": "in",
                    "val": array_ids
                    })

                self.postgres.delete('group_exercise_requirements', conditions)

            # SUBSECTION
            sql_str = "SELECT ss.difficulty_level, ss.subsection_name,"
            sql_str += " s.difficulty_level AS section_diff, ss.subsection_id FROM"
            sql_str += " subsection ss INNER JOIN section s ON ss.section_id=s.section_id WHERE"
            sql_str += " ss.course_id ='{0}'".format(course_id)
            sql_str += " ORDER BY s.difficulty_level ASC, ss.difficulty_level ASC"
            all_subsection = self.postgres.query_fetch_all(sql_str)

            if all_subsection:

                array_ids = [exer['subsection_id'] for exer in all_subsection]

                conditions = []

                conditions.append({
                    "col": "subsection_id",
                    "con": "in",
                    "val": array_ids
                    })

                self.postgres.delete('subsection_requirements', conditions)

                conditions = []

                conditions.append({
                    "col": "subsection_id",
                    "con": "in",
                    "val": array_ids
                    })

                self.postgres.delete('student_subsection', conditions)

                conditions = []

                conditions.append({
                    "col": "subsection_id",
                    "con": "in",
                    "val": array_ids
                    })

                self.postgres.delete('video_subsection', conditions)


                conditions = []

                conditions.append({
                    "col": "subsection_id",
                    "con": "in",
                    "val": array_ids
                    })

                self.postgres.delete('group_subsection_requirements', conditions)

            # SECTION
            sql_str = "SELECT s.difficulty_level AS section_diff,"
            sql_str += " s.section_id FROM section s WHERE"
            sql_str += " s.course_id ='{0}'".format(course_id)
            sql_str += " ORDER BY s.difficulty_level ASC"
            all_section = self.postgres.query_fetch_all(sql_str)

            if all_section:

                array_ids = [exer['section_id'] for exer in all_section]

                conditions = []

                conditions.append({
                    "col": "section_id",
                    "con": "in",
                    "val": array_ids
                    })

                self.postgres.delete('section_requirements', conditions)

                conditions = []

                conditions.append({
                    "col": "section_id",
                    "con": "in",
                    "val": array_ids
                    })

                self.postgres.delete('student_section', conditions)


                conditions = []

                conditions.append({
                    "col": "section_id",
                    "con": "in",
                    "val": array_ids
                    })

                self.postgres.delete('group_section_requirements', conditions)

            # COURSE
            conditions = []

            conditions.append({
                "col": "course_id",
                "con": "=",
                "val": course_id
                })

            self.postgres.delete('course_requirements', conditions)

            # DELETE COURSE
            conditions = []

            conditions.append({
                "col": "course_id",
                "con": "=",
                "val": course_id
                })

            self.postgres.delete('tutor_courses', conditions)
            self.postgres.delete('course_question', conditions)
            self.postgres.delete('student_exercise_repeat', conditions)
            self.postgres.delete('exercise', conditions)
            self.postgres.delete('subsection', conditions)
            self.postgres.delete('section', conditions)
            self.postgres.delete('user_group_courses', conditions)
            self.postgres.delete('group_course_requirements', conditions)
            self.postgres.delete('course_sequence', conditions)
            if not self.postgres.delete('course', conditions):

                return 0

        return 1

    def delete_section(self, section_id):
        """Delete Section"""

        conditions = []

        conditions.append({
            "col": "section_id",
            "con": "=",
            "val": section_id
            })

        self.postgres.delete('tutor_section', conditions)
        if not self.postgres.delete('section', conditions):

            return 0

        return 1

    def delete_subsection(self, subsection_id):
        """Delete Subsection"""

        conditions = []

        conditions.append({
            "col": "subsection_id",
            "con": "=",
            "val": subsection_id
            })

        self.postgres.delete('tutor_subsection', conditions)
        if not self.postgres.delete('subsection', conditions):

            return 0

        return 1

    def delete_exercise(self, exercise_id):
        """Delete Exercise"""

        conditions = []

        conditions.append({
            "col": "exercise_id",
            "con": "=",
            "val": exercise_id
            })

        if not self.postgres.delete('exercise', conditions):

            return 0

        return 1

    def create_new_group(self, query_json, token=None, userid=None):
        """ CREATE USER GROUP """
    
        user_group_id = self.sha_security.generate_token(False)

        # CREATE USER GROUP
        user_group = {}
        user_group['user_group_id'] = user_group_id
        user_group['user_group_name'] = query_json['user_group_name']
        user_group['notify_members'] = query_json['notify_members']
        user_group['notify_managers'] = query_json['notify_managers']
        user_group['created_on'] = time.time()

        self.postgres.insert('user_group', user_group, 'user_group_id')

        # CREATE USER GROUP COURSES
        if 'course_ids' in query_json.keys():

            for course_id in query_json['course_ids']:
                user_group_courses = {}
                user_group_courses['user_group_courses_id'] = self.sha_security.generate_token(False)
                user_group_courses['course_id'] = course_id
                user_group_courses['user_group_id'] = user_group_id
                user_group_courses['created_on'] = time.time()

                self.postgres.insert('user_group_courses', user_group_courses)

        # CREATE USER GROUP STUDENTS
        if 'student_ids' in query_json.keys():

            for student_id in query_json['student_ids']:

                user_group_students = {}
                user_group_students['user_group_students_id'] = self.sha_security.generate_token(False)
                user_group_students['student_id'] = student_id
                user_group_students['user_group_id'] = user_group_id
                user_group_students['created_on'] = time.time()

                self.postgres.insert('user_group_students', user_group_students)

                if token and userid:

                    notif_type = "New Group"
                    notif_name = "New Group"
                    description = "You have new Group: {0}".format(query_json['user_group_name'])
                    self.send_notif(userid, token, student_id, description, notif_type, notif_name)

        # CREATE USER GROUP TUTORS
        if 'tutor_ids' in query_json.keys():

            for tutor_id in query_json['tutor_ids']:

                user_group_tutors = {}
                user_group_tutors['user_group_tutors_id'] = self.sha_security.generate_token(False)
                user_group_tutors['tutor_id'] = tutor_id
                user_group_tutors['user_group_id'] = user_group_id
                user_group_tutors['created_on'] = time.time()

                self.postgres.insert('user_group_tutors', user_group_tutors)

                if token and userid:

                    notif_type = "New Group"
                    notif_name = "New Group"
                    description = "You have new Group: {0}".format(query_json['user_group_name'])
                    self.send_notif(userid, token, tutor_id, description, notif_type, notif_name)

        # CREATE COURSE STUDENT
        if 'student_ids' in query_json.keys():

            for student_id in query_json['student_ids']:

                for course_id in query_json['course_ids']:

                    # VALIDATE
                    sql_str = "SELECT * FROM student_course WHERE"
                    sql_str += " account_id='{0}'".format(student_id)
                    sql_str += " AND course_id='{0}'".format(course_id)
                    res = self.postgres.query_fetch_one(sql_str)

                    if res:

                        continue

                    # ADD STUDENT TO A COURSE
                    temp = {}
                    temp['account_id'] = student_id
                    temp['course_id'] = course_id
                    temp['progress'] = 0
                    temp['expiry_date'] = int(time.time()) + (86400 * 90)
                    temp['status'] = True
                    temp['created_on'] = time.time()

                    self.postgres.insert('student_course', temp)

                    # GET COURSE NAME
                    sql_str = "SELECT course_name FROM course WHERE"
                    sql_str += " course_id='{0}'".format(course_id)
                    course = self.postgres.query_fetch_one(sql_str)

                    if token and userid:

                        notif_type = "New Course"
                        notif_name = "New Course"
                        description = "You have new course: {0}".format(course['course_name'])
                        self.send_notif(userid, token, student_id, description, notif_type, notif_name)

        # CREATE COURSE tutor
        if 'tutor_ids' in query_json.keys():

            for tutor_id in query_json['tutor_ids']:

                for course_id in query_json['course_ids']:

                    # VALIDATE
                    sql_str = "SELECT * FROM tutor_courses WHERE"
                    sql_str += " account_id='{0}'".format(tutor_id)
                    sql_str += " AND course_id='{0}'".format(course_id)
                    res = self.postgres.query_fetch_one(sql_str)

                    if res:

                        continue

                    data = {}
                    data['account_id'] = tutor_id
                    data['course_id'] = course_id
                    data['status'] = True
                    data['created_on'] = time.time()

                    self.postgres.insert('tutor_courses', data)

                    # GET COURSE NAME
                    sql_str = "SELECT course_name FROM course WHERE"
                    sql_str += " course_id='{0}'".format(course_id)
                    course = self.postgres.query_fetch_one(sql_str)

                    if token and userid:

                        notif_type = "New Course"
                        notif_name = "New Course"
                        description = "You have new course: {0}".format(course['course_name'])
                        self.send_notif(userid, token, tutor_id, description, notif_type, notif_name)

    def generate_group_name(self):
        """ GENERATE GROUP NAME """

        user_group_name = "GROUP 1"

        sql_str = "SELECT user_group_name FROM user_group WHERE user_group_name LIKE 'GROUP %'"
        user_group = self.postgres.query_fetch_all(sql_str)

        if not user_group:

            return user_group_name

        gnames = [gn['user_group_name'] for gn in user_group or []]

        for ctr in range(2, 1000):

            user_group_name = 'GROUP {0}'.format(ctr)
            if not user_group_name in gnames:

                return user_group_name

        return "No name"
