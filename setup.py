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

from library.config_parser import config_section_parser
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity
from library.log import Log

class Setup():
    """Class for Setup"""

    def __init__(self):
        """The constructor for Setup class"""
        self.sha_security = ShaSecurity()
        self.postgres = PostgreSQL()

        # INIT CONFIG
        self.config = ConfigParser()
        # CONFIG FILE
        self.config.read("config/config.cfg")
        self.log = Log()
        self.shuffled = True

    def main(self):
        """Main"""
        # time.sleep(30) # Don't Delete this is for Docker
        self.create_database()
        self.create_tables()
        self.create_default_translation()
        self.create_default_entries(prod_flag=True)
        # self.create_index()
        # self.add_question_skills()
        # self.add_skills() # No need anymore
        # self.add_subskills() # No need anymore
        # self.add_extend_skills()

    def create_database(self):
        """Create Database"""
        self.dbname = config_section_parser(self.config, "POSTGRES")['db_name']
        self.postgres.connection(True)
        self.postgres.create_database(self.dbname)
        self.postgres.close_connection()

    def create_tables(self):
        """Create Tables"""

        # OPEN CONNECTION
        self.postgres.connection()

        # ACCOUNT TABLE
        query_str = "CREATE TABLE account (id VARCHAR (1000) PRIMARY KEY,"
        query_str += " username VARCHAR (50) UNIQUE NOT NULL, password VARCHAR (355) NOT NULL,"
        query_str += " email VARCHAR (355) NOT NULL,"
        query_str += " first_name VARCHAR (1000) ,last_name VARCHAR (1000), is_active BOOLEAN"
        query_str += " DEFAULT true, middle_name VARCHAR (1000), default_value BOOLEAN,"
        query_str += " url VARCHAR (1000), reset_token VARCHAR (355), status BOOLEAN NOT NULL,"
        query_str += " address VARCHAR (1000), zip_code VARCHAR (50),"
        query_str += " city VARCHAR (1000), country VARCHAR (1000),"
        query_str += " language VARCHAR (1000), timezone VARCHAR (1000),"
        query_str += " is_send_email BOOLEAN DEFAULT 't' NOT NULL,"
        query_str += " is_license_renewable BOOLEAN DEFAULT 'f' NOT NULL,"
        query_str += " force_change_password BOOLEAN DEFAULT 't' NOT NULL,"
        query_str += " receive_messages BOOLEAN DEFAULT 't' NOT NULL,"
        query_str += " receive_assignments BOOLEAN DEFAULT 't' NOT NULL,"
        query_str += " receive_progress BOOLEAN DEFAULT 't' NOT NULL,"
        query_str += " receive_updates BOOLEAN DEFAULT 't' NOT NULL,"
        query_str += " receive_reminders BOOLEAN DEFAULT 't' NOT NULL,"
        query_str += " receive_events BOOLEAN DEFAULT 't' NOT NULL,"
        query_str += " receive_discussions BOOLEAN DEFAULT 't' NOT NULL,"
        query_str += " receive_newly_available BOOLEAN DEFAULT 't' NOT NULL,"
        query_str += " receive_certificate_notifications BOOLEAN DEFAULT 't' NOT NULL,"
        query_str += " receive_memo_training BOOLEAN DEFAULT 't' NOT NULL,"
        query_str += " receive_other BOOLEAN DEFAULT 't' NOT NULL,"
        query_str += " email_frequency  VARCHAR (355),"
        query_str += " biography VARCHAR (50000),"
        query_str += " faceboot_url VARCHAR (5000),"
        query_str += " linkedin_url VARCHAR (50000),"
        query_str += " twitter_url VARCHAR (50000),"
        query_str += " skype_username  VARCHAR (50000),"
        query_str += " state BOOLEAN NOT NULL, reset_token_date BIGINT, created_on BIGINT NOT NULL,"
        query_str += " update_on BIGINT, last_login BIGINT)"

        print("Create table: account")
        if self.postgres.exec_query(query_str):
            self.log.info("Account table successfully created!")

        # STUDENT PARENT TABLE
        query_str = "CREATE TABLE student_parent (student_parent_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " student_id VARCHAR (1000) REFERENCES account (id) ON"
        query_str += " UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " perent_id VARCHAR (1000) REFERENCES account (id) ON"
        query_str += " UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: student_parent")
        if self.postgres.exec_query(query_str):
            self.log.info("Student Parent table successfully created!")

        # ACCOUNT OPT OUT TABLE
        query_str = "CREATE TABLE account_opt_out (account_opt_out_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " account_id VARCHAR (1000) REFERENCES account (id) ON"
        query_str += " UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " opt_out_id VARCHAR (1000) REFERENCES account (id) ON"
        query_str += " UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: account_opt_out")
        if self.postgres.exec_query(query_str):
            self.log.info("Student Parent table successfully created!")

        # ACCOUNT TOKEN TABLE
        query_str = "CREATE TABLE account_token ("
        query_str += " account_id VARCHAR (1000) REFERENCES account (id) ON"
        query_str += " UPDATE CASCADE ON DELETE CASCADE, token VARCHAR (1000) NOT NULL,"
        query_str += " token_expire_date BIGINT NOT NULL,"
        query_str += " refresh_token VARCHAR (1000) NOT NULL,"
        query_str += " refresh_token_expire_date BIGINT NOT NULL,"
        query_str += " remote_addr VARCHAR (1000),"
        query_str += " platform VARCHAR (1000),"
        query_str += " browser VARCHAR (1000),"
        query_str += " version VARCHAR (1000),"
        query_str += " language VARCHAR (1000),"
        query_str += " string VARCHAR (1000),"
        query_str += " status BOOLEAN DEFAULT 't',"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL,"
        query_str += " CONSTRAINT account_token_pkey PRIMARY KEY (account_id, token))"

        print("Create table: account_token")
        if self.postgres.exec_query(query_str):
            self.log.info("Account role table successfully created!")

        # ROLE TABLE
        query_str = "CREATE TABLE role (role_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " role_name VARCHAR (355) UNIQUE NOT NULL,"
        query_str += " default_value BOOLEAN,"
        query_str += " role_details VARCHAR (1000),"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: role")
        if self.postgres.exec_query(query_str):
            self.log.info("Role table successfully created!")

        # PERMISSION TABLE
        query_str = "CREATE TABLE permission (permission_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " permission_name VARCHAR (355) UNIQUE NOT NULL,"
        query_str += " permission_details VARCHAR (1000),"
        query_str += " default_value BOOLEAN,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: permission")
        if self.postgres.exec_query(query_str):
            self.log.info("Permission table successfully created!")

        # ROLE PERMISSION TABLE
        query_str = "CREATE TABLE role_permission ("
        query_str += " role_id VARCHAR (1000) REFERENCES role (role_id) ON UPDATE"
        query_str += " CASCADE ON DELETE CASCADE, permission_id VARCHAR (1000) REFERENCES"
        query_str += " permission (permission_id) ON UPDATE CASCADE,"
        query_str += " CONSTRAINT role_permission_pkey PRIMARY KEY (role_id, permission_id))"

        print("Create table: role_permission")
        if self.postgres.exec_query(query_str):
            self.log.info("Role permission table successfully created!")

        # ACCOUNT ROLE TABLE
        query_str = "CREATE TABLE account_role (account_id VARCHAR (1000)"
        query_str += " REFERENCES account (id) ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " role_id VARCHAR (1000) REFERENCES role (role_id) ON UPDATE CASCADE,"
        query_str += " CONSTRAINT account_role_pkey PRIMARY KEY (account_id, role_id))"

        print("Create table: account_role")
        if self.postgres.exec_query(query_str):
            self.log.info("Account role table successfully created!")

        # ACCOUNT LOGIN HISTORY TABLE
        query_str = "CREATE TABLE account_login_history (account_id VARCHAR (1000)"
        query_str += " REFERENCES account (id) ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " login_details jsonb, update_on BIGINT)"

        print("Create table: account_login_history")
        if self.postgres.exec_query(query_str):
            self.log.info("Account login history table successfully created!")

        # COURSE TABLE
        query_str = "CREATE TABLE course (course_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " course_name VARCHAR (355) NOT NULL,"
        query_str += " description VARCHAR (5000),"
        query_str += " requirements VARCHAR (5000),"
        query_str += " difficulty_level INT,"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: course")
        if self.postgres.exec_query(query_str):
            self.log.info("Course table successfully created!")

        # SECTION TABLE
        query_str = "CREATE TABLE section (section_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,"
        query_str += " difficulty_level BIGINT,"
        query_str += " section_name VARCHAR (355) NOT NULL,"
        query_str += " description VARCHAR (5000),"
        query_str += " status BOOLEAN,"
        query_str += " progress VARCHAR (355) NULL,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: section")
        if self.postgres.exec_query(query_str):
            self.log.info("Section table successfully created!")

        # SUBSECTION TABLE
        query_str = "CREATE TABLE subsection (subsection_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " section_id VARCHAR (1000) REFERENCES section (section_id) ON UPDATE CASCADE,"
        query_str += " difficulty_level BIGINT,"
        query_str += " subsection_name VARCHAR (355) NOT NULL,"
        query_str += " description VARCHAR (5000),"
        query_str += " status BOOLEAN,"
        query_str += " progress VARCHAR (355) NULL,"
        query_str += " course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: subsection")
        if self.postgres.exec_query(query_str):
            self.log.info("Subsection table successfully created!")

        # EXERCISE TABLE
        query_str = "CREATE TABLE exercise (exercise_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " subsection_id VARCHAR (1000) REFERENCES subsection"
        query_str += " (subsection_id) ON UPDATE CASCADE, exercise_number VARCHAR (355) NOT NULL,"
        query_str += " course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,"
        query_str += " section_id VARCHAR (1000) REFERENCES section (section_id) ON UPDATE CASCADE,"
        query_str += " description VARCHAR (5000),"
        query_str += " question_type VARCHAR (355),"
        query_str += " status BOOLEAN,"
        query_str += " number_to_draw BIGINT,"
        query_str += " seed BIGINT,"
        query_str += " save_seed BOOLEAN,"
        query_str += " timed_type VARCHAR (355),"
        query_str += " timed_limit BIGINT,"
        query_str += " passing_criterium BIGINT,"
        query_str += " text_before_start VARCHAR (5000),"
        query_str += " text_after_end VARCHAR (5000),"
        query_str += " moving_allowed BOOLEAN,"
        query_str += " instant_feedback BOOLEAN,"
        query_str += " editing_allowed BOOLEAN,"
        query_str += " draw_by_tag BOOLEAN,"
        query_str += " shuffled BOOLEAN,"
        query_str += " help BOOLEAN,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: exercise")
        if self.postgres.exec_query(query_str):
            self.log.info("Exercise table successfully created!")

        # QUESTIONS TABLE
        query_str = "CREATE TABLE questions (question_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " question jsonb,"
        query_str += " question_type VARCHAR (355),"
        query_str += " tags jsonb,"
        query_str += " choices jsonb,"
        query_str += " shuffle_options BOOLEAN,"
        query_str += " shuffle_answers BOOLEAN,"
        query_str += " num_eval BOOLEAN,"
        query_str += " correct_answer jsonb,"
        query_str += " correct VARCHAR (1000),"
        query_str += " incorrect VARCHAR (1000),"
        query_str += " feedback VARCHAR (5000),"
        query_str += " description VARCHAR (5000),"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: questions")
        if self.postgres.exec_query(query_str):
            self.log.info("Questions table successfully created!")

        # COURSE QUESTIONS TABLE
        query_str = "CREATE TABLE course_question (course_question_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,"
        query_str += " section_id VARCHAR (1000) REFERENCES section (section_id) ON UPDATE CASCADE,"
        query_str += " subsection_id VARCHAR (1000) REFERENCES subsection (subsection_id)"
        query_str += " ON UPDATE CASCADE, exercise_id VARCHAR (1000) REFERENCES "
        query_str += " exercise (exercise_id) ON UPDATE CASCADE,"
        query_str += " question_id VARCHAR (1000) REFERENCES"
        query_str += " questions (question_id) ON UPDATE CASCADE,"
        query_str += " question jsonb,"
        query_str += " question_type VARCHAR (355),"
        query_str += " tags jsonb,"
        query_str += " choices jsonb,"
        query_str += " shuffle_options BOOLEAN,"
        query_str += " shuffle_answers BOOLEAN,"
        query_str += " num_eval BOOLEAN,"
        query_str += " correct_answer jsonb,"
        query_str += " correct VARCHAR (1000),"
        query_str += " incorrect VARCHAR (1000),"
        query_str += " feedback VARCHAR (5000),"
        query_str += " description VARCHAR (5000),"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: course_question")
        if self.postgres.exec_query(query_str):
            self.log.info("Course Questions table successfully created!")

        # STUDENT COURSE TABLE
        query_str = "CREATE TABLE student_course (account_id VARCHAR (1000)"
        query_str += " REFERENCES account (id) ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,"
        query_str += " progress VARCHAR (355) NOT NULL,"
        query_str += " expiry_date BIGINT,"
        query_str += " percent_score VARCHAR (355),"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL,"
        query_str += " CONSTRAINT student_course_pkey PRIMARY KEY (account_id, course_id))"

        print("Create table: student_course")
        if self.postgres.exec_query(query_str):
            self.log.info("Student Course table successfully created!")

        # STUDENT EXERCISE TABLE
        query_str = "CREATE TABLE student_exercise (student_exercise_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " exercise_id VARCHAR (1000) REFERENCES exercise (exercise_id) ON UPDATE "
        query_str += " CASCADE ON DELETE CASCADE, account_id VARCHAR (1000) REFERENCES account (id)"
        query_str += "  ON UPDATE CASCADE ON DELETE CASCADE, course_id VARCHAR (1000) REFERENCES"
        query_str += " course (course_id) ON UPDATE CASCADE, exercise_number  BIGINT,"
        query_str += " time_used BIGINT,"
        query_str += " score BIGINT," # <--important--> #
        query_str += " percent_score VARCHAR (355),"
        query_str += " progress VARCHAR (355),"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: student_exercise")
        if self.postgres.exec_query(query_str):
            self.log.info("Student Exercise table successfully created!")

        # STUDENT SECTION TABLE
        query_str = "CREATE TABLE student_section (student_section_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " account_id VARCHAR (1000) REFERENCES account (id)"
        query_str += " ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,"
        query_str += " section_id VARCHAR (1000) REFERENCES section (section_id) ON UPDATE CASCADE,"
        query_str += " progress VARCHAR (355),"
        query_str += " percent_score VARCHAR (355),"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: student_section")
        if self.postgres.exec_query(query_str):
            self.log.info("Student section table successfully created!")

        # STUDENT SUBSECTION TABLE
        query_str = "CREATE TABLE student_subsection"
        query_str += " (student_subsection_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " account_id VARCHAR (1000) REFERENCES account (id)"
        query_str += " ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,"
        query_str += " section_id VARCHAR (1000) REFERENCES section (section_id) ON UPDATE CASCADE,"
        query_str += " subsection_id VARCHAR (1000) REFERENCES"
        query_str += " subsection (subsection_id) ON UPDATE CASCADE,"
        query_str += " progress VARCHAR (355),"
        query_str += " percent_score VARCHAR (355),"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: student_subsection")
        if self.postgres.exec_query(query_str):
            self.log.info("Student subsection table successfully created!")

        # STUDENT EXERCISE QUESTIONS TABLE
        query_str = "CREATE TABLE student_exercise_questions (student_exercise_id VARCHAR (1000)"
        query_str += " REFERENCES student_exercise (student_exercise_id) ON UPDATE CASCADE ON"
        query_str += " DELETE CASCADE, course_question_id VARCHAR (1000) REFERENCES course_question"
        query_str += " (course_question_id) ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " account_id VARCHAR (1000) REFERENCES account (id)"
        query_str += " ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " answer jsonb, time_used BIGINT,"
        query_str += " progress VARCHAR (355),"
        query_str += " started_on BIGINT,"
        query_str += " percent_score VARCHAR (355),"
        query_str += " sequence BIGINT,"
        query_str += " skip_times BIGINT,"
        query_str += " answered_on BIGINT,"
        query_str += " update_on BIGINT,"
        query_str += " CONSTRAINT student_exercise_questions_pkey PRIMARY KEY"
        query_str += " (student_exercise_id, course_question_id))"

        print("Create table: student_exercise_questions")
        if self.postgres.exec_query(query_str):
            self.log.info("Student Exercise Questions table successfully created!")

        # WHAT TO DO TABLE
        query_str = "CREATE TABLE what_to_do (what_to_do_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " what_to_do_name VARCHAR (355),"
        query_str += " page VARCHAR (355) NOT NULL,"
        query_str += " description VARCHAR (500000),"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: what_to_do")
        if self.postgres.exec_query(query_str):
            self.log.info("What to do table successfully created!")

        # HELP TABLE
        query_str = "CREATE TABLE help (help_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " help_name VARCHAR (355),"
        query_str += " skill VARCHAR (355),"
        query_str += " tags VARCHAR (355),"
        query_str += " description VARCHAR (500000),"
        query_str += " url VARCHAR (50000),"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: help")
        if self.postgres.exec_query(query_str):
            self.log.info("Help table successfully created!")

        # VIDEO TABLE
        query_str = "CREATE TABLE videos (video_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " video_name VARCHAR (355),"
        query_str += " description VARCHAR (500000),"
        query_str += " url VARCHAR (50000),"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: videos")
        if self.postgres.exec_query(query_str):
            self.log.info("Videos table successfully created!")

        # ISSUE
        query_str = "CREATE TABLE issue (issue_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " account_id VARCHAR (1000) REFERENCES account (id)"
        query_str += " ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " url VARCHAR (50000),"
        query_str += " description VARCHAR (50000),"
        query_str += " course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,"
        query_str += " section_id VARCHAR (1000) REFERENCES section (section_id) ON UPDATE CASCADE,"
        query_str += " subsection_id VARCHAR (1000)"
        query_str += " REFERENCES subsection (subsection_id) ON UPDATE CASCADE,"
        query_str += " exercise_id VARCHAR (1000)"
        query_str += " REFERENCES exercise (exercise_id) ON UPDATE CASCADE,"
        query_str += " course_question_id VARCHAR (1000) REFERENCES course_question"
        query_str += " (course_question_id) ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: issue")
        if self.postgres.exec_query(query_str):
            self.log.info("Issue table successfully created!")

        # CONVERSATION
        query_str = "CREATE TABLE conversation (conversation_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " conversation_name VARCHAR (50000),"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: conversation")
        if self.postgres.exec_query(query_str):
            self.log.info("CONVERSATION table successfully created!")

        # CONVERSATION USERS
        query_str = "CREATE TABLE conversation_users"
        query_str += " (conversation_users_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " conversation_id VARCHAR (1000) REFERENCES conversation"
        query_str += " (conversation_id) ON UPDATE CASCADE,"
        query_str += " account_id VARCHAR (1000) REFERENCES account (id)"
        query_str += " ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: conversation_users")
        if self.postgres.exec_query(query_str):
            self.log.info("CONVERSATION USERS table successfully created!")

        # CONVERSATION REPLY
        query_str = "CREATE TABLE conversation_reply"
        query_str += " (conversation_reply_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " conversation_id VARCHAR (1000)"
        query_str += " REFERENCES conversation (conversation_id) ON UPDATE CASCADE,"
        query_str += " account_id VARCHAR (1000) REFERENCES account (id)"
        query_str += " ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " reply VARCHAR (50000),"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: conversation_reply")
        if self.postgres.exec_query(query_str):
            self.log.info("CONVERSATION USERS table successfully created!")

        # USER GROUP
        query_str = "CREATE TABLE user_group"
        query_str += " (user_group_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " user_group_name VARCHAR (1000),"
        query_str += " notify_members BOOLEAN,"
        query_str += " notify_managers BOOLEAN,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: user_group")
        if self.postgres.exec_query(query_str):
            self.log.info("USER GROUP table successfully created!")

        # USER GROUP COURSES
        query_str = "CREATE TABLE user_group_courses"
        query_str += " (user_group_courses_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,"
        query_str += " user_group_id VARCHAR (1000)"
        query_str += " REFERENCES user_group (user_group_id) ON UPDATE CASCADE,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: user_group_courses")
        if self.postgres.exec_query(query_str):
            self.log.info("USER GROUP COURSE table successfully created!")

        # USER GROUP STUDENTS
        query_str = "CREATE TABLE user_group_students"
        query_str += " (user_group_students_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " student_id VARCHAR (1000) REFERENCES account (id)"
        query_str += " ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " user_group_id VARCHAR (1000)"
        query_str += " REFERENCES user_group (user_group_id) ON UPDATE CASCADE,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: user_group_students")
        if self.postgres.exec_query(query_str):
            self.log.info("USER GROUP STUDENTS table successfully created!")

        # USER GROUP TUTOR
        query_str = "CREATE TABLE user_group_tutors"
        query_str += " (user_group_tutors_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " tutor_id VARCHAR (1000) REFERENCES account (id)"
        query_str += " ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " user_group_id VARCHAR (1000)"
        query_str += " REFERENCES user_group (user_group_id) ON UPDATE CASCADE,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: user_group_tutors")
        if self.postgres.exec_query(query_str):
            self.log.info("USER GROUP TUTORS table successfully created!")

        # NOTIFICATIONS
        query_str = "CREATE TABLE notifications"
        query_str += " (notification_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " account_id VARCHAR (1000) REFERENCES account (id)"
        query_str += " ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " notification_name VARCHAR (1000),"
        query_str += " notification_type VARCHAR (1000),"
        query_str += " description VARCHAR (50000),"
        query_str += " seen_by_user BOOLEAN,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: notifications")
        if self.postgres.exec_query(query_str):
            self.log.info("NOTIFICATIONS table successfully created!")

        # TUTOR COURSE TABLE
        query_str = "CREATE TABLE tutor_courses (account_id VARCHAR (1000)"
        query_str += " REFERENCES account (id) ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,"
        query_str += " difficulty_level BIGINT,"
        query_str += " percent_score VARCHAR (355),"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL,"
        query_str += " CONSTRAINT tutor_course_pkey PRIMARY KEY (account_id, course_id))"

        print("Create table: tutor_courses")
        if self.postgres.exec_query(query_str):
            self.log.info("Student Course table successfully created!")

        # PARENT STUDENT TABLE
        # query_str = "CREATE TABLE parent_students (account_id VARCHAR (1000)"
        # query_str += " REFERENCES account (id) ON UPDATE CASCADE ON DELETE CASCADE,"
        # query_str += " course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,"
        # query_str += " status BOOLEAN,"
        # query_str += " update_on BIGINT,"
        # query_str += " created_on BIGINT NOT NULL,"
        # query_str += " CONSTRAINT tutor_course_pkey PRIMARY KEY (account_id, course_id))"

        # print("Create table: tutor_courses")
        # if self.postgres.exec_query(query_str):
        #     self.log.info("Student Course table successfully created!")


        # TUTOR EXERCISE TABLE
        query_str = "CREATE TABLE tutor_exercise (tutor_exercise_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " exercise_id VARCHAR (1000) REFERENCES exercise (exercise_id) ON UPDATE "
        query_str += " CASCADE ON DELETE CASCADE, account_id VARCHAR (1000) REFERENCES account (id)"
        query_str += "  ON UPDATE CASCADE ON DELETE CASCADE, course_id VARCHAR (1000) REFERENCES"
        query_str += " course (course_id) ON UPDATE CASCADE, exercise_number  BIGINT,"
        query_str += " time_used BIGINT,"
        query_str += " score BIGINT,"
        query_str += " progress VARCHAR (355),"
        query_str += " percent_score VARCHAR (355),"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: tutor_exercise")
        if self.postgres.exec_query(query_str):
            self.log.info("Tutor Exercise table successfully created!")

        # TUTOR EXERCISE QUESTIONS TABLE
        query_str = "CREATE TABLE tutor_exercise_questions (tutor_exercise_id VARCHAR (1000)"
        query_str += " REFERENCES tutor_exercise (tutor_exercise_id) ON UPDATE CASCADE ON"
        query_str += " DELETE CASCADE, course_question_id VARCHAR (1000) REFERENCES course_question"
        query_str += " (course_question_id) ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " account_id VARCHAR (1000) REFERENCES account (id)"
        query_str += " ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " answer jsonb, time_used BIGINT,"
        query_str += " progress VARCHAR (355),"
        query_str += " percent_score VARCHAR (355),"
        query_str += " started_on BIGINT,"
        query_str += " sequence BIGINT,"
        query_str += " skip_times BIGINT,"
        query_str += " answered_on BIGINT,"
        query_str += " update_on BIGINT,"
        query_str += " CONSTRAINT tutor_exercise_questions_pkey PRIMARY KEY"
        query_str += " (tutor_exercise_id, course_question_id))"

        print("Create table: tutor_exercise_questions")
        if self.postgres.exec_query(query_str):
            self.log.info("Tutor Exercise Questions table successfully created!")

        # TUTOR SECTION TABLE
        query_str = "CREATE TABLE tutor_section (tutor_section_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " account_id VARCHAR (1000) REFERENCES account (id)"
        query_str += " ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,"
        query_str += " section_id VARCHAR (1000) REFERENCES section (section_id) ON UPDATE CASCADE,"
        query_str += " progress VARCHAR (355),"
        query_str += " percent_score VARCHAR (355),"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: tutor_section")
        if self.postgres.exec_query(query_str):
            self.log.info("Tutor section table successfully created!")

        # TUTOR SUBSECTION TABLE
        query_str = "CREATE TABLE tutor_subsection"
        query_str += " (tutor_subsection_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " account_id VARCHAR (1000) REFERENCES account (id)"
        query_str += " ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,"
        query_str += " section_id VARCHAR (1000) REFERENCES section (section_id) ON UPDATE CASCADE,"
        query_str += " subsection_id VARCHAR (1000) REFERENCES"
        query_str += " subsection (subsection_id) ON UPDATE CASCADE,"
        query_str += " progress VARCHAR (355),"
        query_str += " percent_score VARCHAR (355),"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: tutor_subsection")
        if self.postgres.exec_query(query_str):
            self.log.info("Tutor subsection table successfully created!")

        # INSTRUCTION
        query_str = "CREATE TABLE instruction (instruction_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " exercise_id VARCHAR (1000)"
        query_str += " REFERENCES exercise (exercise_id) ON UPDATE CASCADE,"
        query_str += " text TEXT,"
        query_str += " video_url VARCHAR (50000),"
        query_str += " sound_url VARCHAR (50000),"
        # query_str += " image_url VARCHAR (50000),"
        query_str += " image_id VARCHAR (1000),"
        query_str += " page_number BIGINT,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: Instruction")
        if self.postgres.exec_query(query_str):
            self.log.info("Instruction table successfully created!")

        # LANGUAGE TABLE
        query_str = "CREATE TABLE language (language_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " initial VARCHAR (50),"
        query_str += " language_name TEXT,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: words")
        if self.postgres.exec_query(query_str):
            self.log.info("Words table successfully created!")

        # WORDS TABLE
        query_str = "CREATE TABLE words (word_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " type VARCHAR (50),"
        query_str += " name TEXT,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: words")
        if self.postgres.exec_query(query_str):
            self.log.info("Words table successfully created!")

        # TRANSLATION TABLE
        query_str = "CREATE TABLE translations (translation_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " word_id VARCHAR (1000) REFERENCES words (word_id) ON UPDATE CASCADE,"
        query_str += " type VARCHAR (50),"
        query_str += " language_id  VARCHAR (1000) REFERENCES"
        query_str += " language (language_id) ON UPDATE CASCADE,"
        query_str += " translation TEXT,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: translation")
        if self.postgres.exec_query(query_str):
            self.log.info("Translation table successfully created!")

        # INSTRUCTION IMAGE TABLE
        query_str = """CREATE TABLE instruction_image (image_id VARCHAR (1000) PRIMARY KEY,
                        image_name VARCHAR(555),
                        status VARCHAR(10) NOT NULL,
                        created_on BIGINT NOT NULL,
                        update_on BIGINT
                    );"""

        print("Create table: instruction_image")

        if self.postgres.exec_query(query_str):
            self.log.info("Instruction image table successfully created!")

        # ACCOUNT LOGS
        query_str = "CREATE TABLE account_logs (account_id VARCHAR (1000)"
        query_str += " REFERENCES account (id) ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " browser VARCHAR (355),"
        query_str += " version VARCHAR (355),"
        query_str += " platform VARCHAR (355),"
        query_str += " remote_addr VARCHAR (355),"
        query_str += " login BIGINT,"
        query_str += " logout BIGINT,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: account_logs")
        if self.postgres.exec_query(query_str):
            self.log.info("Account logs table successfully created!")

        # ONLINE USER TABLE
        query_str = "CREATE TABLE online_user (online_user_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " account_id VARCHAR (1000) REFERENCES account (id)"
        query_str += " ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " token VARCHAR,"
        query_str += " socket_id VARCHAR (355),"
        query_str += " type VARCHAR (355) NOT NULL,"
        query_str += " status BOOLEAN,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: online_user")
        if self.postgres.exec_query(query_str):
            self.log.info("Online user table successfully created!")

        # # STUDENT EXPERIENCE
        # query_str = """CREATE TABLE student_experience (
        #                 student_experience_id VARCHAR (1000) PRIMARY KEY,
        #                 account_id VARCHAR (1000) REFERENCES account (id)
        #                 ON UPDATE CASCADE ON DELETE CASCADE, student_exercise_id VARCHAR (1000)
        #                 REFERENCES student_exercise (student_exercise_id)
        #                 ON UPDATE CASCADE ON DELETE CASCADE, gain_experience BIGINT,
        #                 finished_date BIGINT, created_on BIGINT
        #             );"""

        # print("Create table: student_experience")
        # if self.postgres.exec_query(query_str):
        #     self.log.info("Student experience table successfully created!")

        # STUDENT INSTRUCTION
        query_str = "CREATE TABLE student_instruction"
        query_str += " (student_instruction_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " instruction_id VARCHAR (1000)"
        query_str += " REFERENCES instruction (instruction_id) ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " account_id VARCHAR (1000) REFERENCES account (id)"
        query_str += " ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " exercise_id VARCHAR (1000)"
        query_str += " REFERENCES exercise (exercise_id) ON UPDATE CASCADE,"
        query_str += " course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,"
        query_str += " is_viewed BOOLEAN, is_unlocked BOOLEAN, unlock_criteria VARCHAR (500),"
        query_str += " unlocked_on BIGINT, update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: Student Instruction")
        if self.postgres.exec_query(query_str):
            self.log.info("Student Instruction table successfully created!")

        # COURSE REQUIREMENTS
        query_str = "CREATE TABLE course_requirements"
        query_str += " (course_requirement_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,"
        query_str += " completion VARCHAR (355),"
        query_str += " grade_locking BOOLEAN,"
        query_str += " on_previous BOOLEAN,"
        query_str += " is_lock BOOLEAN,"
        query_str += " is_visible BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: course_requirements")
        if self.postgres.exec_query(query_str):
            self.log.info("Course requirements table successfully created!")

        # SECTION REQUIREMENTS
        query_str = "CREATE TABLE section_requirements"
        query_str += " (section_requirement_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " section_id VARCHAR (1000) REFERENCES section (section_id) ON UPDATE CASCADE,"
        query_str += " completion VARCHAR (355),"
        query_str += " grade_locking BOOLEAN,"
        query_str += " on_previous BOOLEAN,"
        query_str += " is_lock BOOLEAN,"
        query_str += " is_visible BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: section_requirements")
        if self.postgres.exec_query(query_str):
            self.log.info("Section requirements table successfully created!")

        # SUBSECTION REQUIREMENTS
        query_str = "CREATE TABLE subsection_requirements"
        query_str += " (subsection_requirement_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " subsection_id VARCHAR (1000)"
        query_str += " REFERENCES subsection (subsection_id) ON UPDATE CASCADE,"
        query_str += " completion VARCHAR (355),"
        query_str += " grade_locking BOOLEAN,"
        query_str += " on_previous BOOLEAN,"
        query_str += " is_lock BOOLEAN,"
        query_str += " is_visible BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: subsection_requirements")
        if self.postgres.exec_query(query_str):
            self.log.info("Subsection requirements table successfully created!")

        # EXERCISE REQUIREMENTS
        query_str = "CREATE TABLE exercise_requirements"
        query_str += " (exercise_requirement_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " exercise_id VARCHAR (1000)"
        query_str += " REFERENCES exercise (exercise_id) ON UPDATE CASCADE,"
        query_str += " completion VARCHAR (355),"
        query_str += " grade_locking BOOLEAN,"
        query_str += " on_previous BOOLEAN,"
        query_str += " is_lock BOOLEAN,"
        query_str += " is_visible BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: exercise_requirements")
        if self.postgres.exec_query(query_str):
            self.log.info("Exercise requirements table successfully created!")

        # STUDENT COURSE REQUIREMENTS
        query_str = "CREATE TABLE student_course_requirements"
        query_str += " (student_course_requirement_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,"
        query_str += " completion VARCHAR (355),"
        query_str += " grade_locking BOOLEAN,"
        query_str += " on_previous BOOLEAN,"
        query_str += " is_lock BOOLEAN,"
        query_str += " is_visible BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: student_course_requirements")
        if self.postgres.exec_query(query_str):
            self.log.info("Student Course requirements table successfully created!")

        # STUDENT SECTION REQUIREMENTS
        query_str = "CREATE TABLE student_section_requirements"
        query_str += " (student_section_requirement_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " section_id VARCHAR (1000) REFERENCES section (section_id) ON UPDATE CASCADE,"
        query_str += " completion VARCHAR (355),"
        query_str += " grade_locking BOOLEAN,"
        query_str += " on_previous BOOLEAN,"
        query_str += " is_lock BOOLEAN,"
        query_str += " is_visible BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: student_section_requirements")
        if self.postgres.exec_query(query_str):
            self.log.info("Student Section requirements table successfully created!")

        # STUDENT SUBSECTION REQUIREMENTS
        query_str = "CREATE TABLE student_subsection_requirements"
        query_str += " (student_subsection_requirement_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " subsection_id VARCHAR (1000)"
        query_str += " REFERENCES subsection (subsection_id) ON UPDATE CASCADE,"
        query_str += " completion VARCHAR (355),"
        query_str += " grade_locking BOOLEAN,"
        query_str += " on_previous BOOLEAN,"
        query_str += " is_lock BOOLEAN,"
        query_str += " is_visible BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: student_subsection_requirements")
        if self.postgres.exec_query(query_str):
            self.log.info("Student Subsection requirements table successfully created!")

        # STUDENT EXERCISE REQUIREMENTS
        query_str = "CREATE TABLE student_exercise_requirements"
        query_str += " (student_exercise_requirement_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " exercise_id VARCHAR (1000)"
        query_str += " REFERENCES exercise (exercise_id) ON UPDATE CASCADE,"
        query_str += " completion VARCHAR (355),"
        query_str += " grade_locking BOOLEAN,"
        query_str += " on_previous BOOLEAN,"
        query_str += " is_lock BOOLEAN,"
        query_str += " is_visible BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: student_exercise_requirements")
        if self.postgres.exec_query(query_str):
            self.log.info("Student Exercise requirements table successfully created!")

        # GROUP COURSE REQUIREMENTS
        query_str = "CREATE TABLE group_course_requirements"
        query_str += " (group_course_requirement_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " user_group_id VARCHAR (1000)"
        query_str += " REFERENCES user_group (user_group_id) ON UPDATE CASCADE,"
        query_str += " course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,"
        query_str += " completion VARCHAR (355),"
        query_str += " grade_locking BOOLEAN,"
        query_str += " on_previous BOOLEAN,"
        query_str += " is_lock BOOLEAN,"
        query_str += " is_visible BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: group_course_requirements")
        if self.postgres.exec_query(query_str):
            self.log.info("Student Course requirements table successfully created!")

        # GROUP SECTION REQUIREMENTS
        query_str = "CREATE TABLE group_section_requirements"
        query_str += " (group_section_requirement_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " user_group_id VARCHAR (1000)"
        query_str += " REFERENCES user_group (user_group_id) ON UPDATE CASCADE,"
        query_str += " section_id VARCHAR (1000) REFERENCES section (section_id) ON UPDATE CASCADE,"
        query_str += " completion VARCHAR (355),"
        query_str += " grade_locking BOOLEAN,"
        query_str += " on_previous BOOLEAN,"
        query_str += " is_lock BOOLEAN,"
        query_str += " is_visible BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: group_section_requirements")
        if self.postgres.exec_query(query_str):
            self.log.info("Student Section requirements table successfully created!")

        # GROUP SUBSECTION REQUIREMENTS
        query_str = "CREATE TABLE group_subsection_requirements"
        query_str += " (group_subsection_requirement_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " user_group_id VARCHAR (1000)"
        query_str += " REFERENCES user_group (user_group_id) ON UPDATE CASCADE,"
        query_str += " subsection_id VARCHAR (1000)"
        query_str += " REFERENCES subsection (subsection_id) ON UPDATE CASCADE,"
        query_str += " completion VARCHAR (355),"
        query_str += " grade_locking BOOLEAN,"
        query_str += " on_previous BOOLEAN,"
        query_str += " is_lock BOOLEAN,"
        query_str += " is_visible BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: group_subsection_requirements")
        if self.postgres.exec_query(query_str):
            self.log.info("Student Subsection requirements table successfully created!")

        # GROUP EXERCISE REQUIREMENTS
        query_str = "CREATE TABLE group_exercise_requirements"
        query_str += " (group_exercise_requirement_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " user_group_id VARCHAR (1000)"
        query_str += " REFERENCES user_group (user_group_id) ON UPDATE CASCADE,"
        query_str += " exercise_id VARCHAR (1000)"
        query_str += " REFERENCES exercise (exercise_id) ON UPDATE CASCADE,"
        query_str += " completion VARCHAR (355),"
        query_str += " grade_locking BOOLEAN,"
        query_str += " on_previous BOOLEAN,"
        query_str += " is_lock BOOLEAN,"
        query_str += " is_visible BOOLEAN,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"

        print("Create table: group_exercise_requirements")
        if self.postgres.exec_query(query_str):
            self.log.info("Student Exercise requirements table successfully created!")

        # MASTER SKILL
        query_str = "CREATE TABLE master_skills (master_skill_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " skill VARCHAR (500) UNIQUE NOT NULL,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: master_skills")
        if self.postgres.exec_query(query_str):
            self.log.info("Master Skill table successfully created!")

        # MASTER SUBSKILL
        query_str = "CREATE TABLE master_subskills (master_subskill_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " subskill VARCHAR (500) UNIQUE NOT NULL,"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: master_subskills")
        if self.postgres.exec_query(query_str):
            self.log.info("Master Subskills table successfully created!")

        # MASTER SKILL SUBSKILL
        query_str = "CREATE TABLE master_skill_subskills (master_skill_subskill_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " master_skill_id VARCHAR (1000) REFERENCES master_skills (master_skill_id) ON UPDATE CASCADE,"
        query_str += " master_subskill_id VARCHAR (1000) REFERENCES master_subskills (master_subskill_id) ON UPDATE CASCADE)"

        print("Create table: master_skill_subskills")
        if self.postgres.exec_query(query_str):
            self.log.info("Master Skill Subskills table successfully created!")

        # SKILL
        query_str = "CREATE TABLE skills (skill_id VARCHAR (1000) PRIMARY KEY, skill VARCHAR (500),"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: skills")
        if self.postgres.exec_query(query_str):
            self.log.info("Skills table successfully created!")

        # SUBSKILL
        query_str = "CREATE TABLE subskills (subskill_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " subskill VARCHAR (500),"
        query_str += " update_on BIGINT, created_on BIGINT NOT NULL)"

        print("Create table: subskills")
        if self.postgres.exec_query(query_str):
            self.log.info("Sub Skills table successfully created!")

        # SKILL SUBSKILL
        query_str = "CREATE TABLE skill_subskills (skill_subskill_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " skill_id VARCHAR (1000) REFERENCES skills (skill_id) ON UPDATE CASCADE,"
        query_str += " subskill_id VARCHAR (1000) REFERENCES subskills (subskill_id) ON UPDATE CASCADE)"

        print("Create table: skill_subskills")
        if self.postgres.exec_query(query_str):
            self.log.info("Skill Subskills table successfully created!")

        # QUESTION SKILL
        query_str = "CREATE TABLE question_skills (question_skill_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " question_id VARCHAR (1000) REFERENCES questions (question_id) ON UPDATE CASCADE,"
        query_str += " skill_id VARCHAR (1000) REFERENCES skills (skill_id) ON UPDATE CASCADE)"

        print("Create table: question_skills")
        if self.postgres.exec_query(query_str):
            self.log.info("Question Skills table successfully created!")

        # EXERCISE SKILL
        query_str = "CREATE TABLE exercise_skills (exercise_skill_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " exercise_id VARCHAR (1000) REFERENCES exercise (exercise_id) ON UPDATE CASCADE,"
        query_str += " skill_id VARCHAR (1000) REFERENCES skills (skill_id) ON UPDATE CASCADE)"

        print("Create table: exercise_skills")
        if self.postgres.exec_query(query_str):
            self.log.info("Exercise Skills table successfully created!")

        # STUDENT SKILLS
        query_str = "CREATE TABLE student_skills (student_skill_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " account_id VARCHAR (1000) REFERENCES account (id)"
        query_str += " ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " skill_id VARCHAR (1000) REFERENCES skills (skill_id) ON UPDATE CASCADE,"
        query_str += " progress VARCHAR (355) DEFAULT 0 NOT NULL,"
        query_str += " answered_questions VARCHAR (355) DEFAULT 0 NOT NULL,"
        query_str += " correct VARCHAR (355) DEFAULT 0 NOT NULL,"
        query_str += " time_studied VARCHAR (355) DEFAULT 0 NOT NULL,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"
        print("Create table: student_skills")

        if self.postgres.exec_query(query_str):
            self.log.info("Student Skills table successfully created!")

        # STUDENT ALL SKILLS
        query_str = "CREATE TABLE student_all_skills (student_skill_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " account_id VARCHAR (1000) REFERENCES account (id)"
        query_str += " ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " skill VARCHAR (1000),"
        query_str += " progress VARCHAR (355) DEFAULT 0 NOT NULL,"
        query_str += " answered_questions VARCHAR (355) DEFAULT 0 NOT NULL,"
        query_str += " correct VARCHAR (355) DEFAULT 0 NOT NULL,"
        query_str += " time_studied VARCHAR (355) DEFAULT 0 NOT NULL,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"
        print("Create table: student_all_skills")

        if self.postgres.exec_query(query_str):
            self.log.info("Student All Skills table successfully created!")

        # STUDENT SUBSKILLS
        query_str = "CREATE TABLE student_subskills (student_subskill_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " student_skill_id VARCHAR (1000) REFERENCES student_skills (student_skill_id) ON UPDATE CASCADE,"
        query_str += " account_id VARCHAR (1000) REFERENCES account (id)"
        query_str += " ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " subskill_id VARCHAR (1000) REFERENCES subskills (subskill_id) ON UPDATE CASCADE,"
        query_str += " progress VARCHAR (355) DEFAULT 0 NOT NULL,"
        query_str += " answered_questions VARCHAR (355) DEFAULT 0 NOT NULL,"
        query_str += " correct VARCHAR (355) DEFAULT 0 NOT NULL,"
        query_str += " time_studied VARCHAR (355) DEFAULT 0 NOT NULL,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"
        print("Create table: student_subskills")

        if self.postgres.exec_query(query_str):
            self.log.info("Student Sub skills table successfully created!")

        # STUDENT ALL SUBSKILLS
        query_str = "CREATE TABLE student_all_subskills (student_subskill_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " account_id VARCHAR (1000) REFERENCES account (id)"
        query_str += " ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " subskill_id VARCHAR (1000) REFERENCES subskills (subskill_id) ON UPDATE CASCADE,"
        query_str += " subskill VARCHAR (1000),"
        query_str += " progress VARCHAR (355) DEFAULT 0 NOT NULL,"
        query_str += " answered_questions VARCHAR (355) DEFAULT 0 NOT NULL,"
        query_str += " correct VARCHAR (355) DEFAULT 0 NOT NULL,"
        query_str += " time_studied VARCHAR (355) DEFAULT 0 NOT NULL,"
        query_str += " update_on BIGINT,"
        query_str += " created_on BIGINT NOT NULL)"
        print("Create table: student_all_subskills")

        if self.postgres.exec_query(query_str):
            self.log.info("Student All Subskills table successfully created!")

        # VIDEO SKILL
        query_str = "CREATE TABLE video_skills (video_skill_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " skill_id VARCHAR (1000) REFERENCES skills (skill_id) ON UPDATE CASCADE,"
        query_str += " video_id VARCHAR (1000) REFERENCES videos (video_id) ON UPDATE CASCADE)"

        print("Create table: video_skills")
        if self.postgres.exec_query(query_str):
            self.log.info("Video Skills table successfully created!")

        # VIDEO EXERCISE
        query_str = "CREATE TABLE video_exercise (video_exercise_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " exercise_id VARCHAR (1000) REFERENCES exercise (exercise_id) ON UPDATE CASCADE,"
        query_str += " video_id VARCHAR (1000) REFERENCES videos (video_id) ON UPDATE CASCADE)"

        print("Create table: video_exercise")
        if self.postgres.exec_query(query_str):
            self.log.info("Video Exercise table successfully created!")

        # VIDEO EXERCISE
        query_str = "CREATE TABLE video_subsection (video_subsection_id VARCHAR (1000) PRIMARY KEY,"
        query_str += " subsection_id VARCHAR (1000) REFERENCES subsection (subsection_id) ON UPDATE CASCADE,"
        query_str += " video_id VARCHAR (1000) REFERENCES videos (video_id) ON UPDATE CASCADE)"

        print("Create table: video_subsection")
        if self.postgres.exec_query(query_str):
            self.log.info("Video Subsection table successfully created!")

        # VIDEO EXERCISE
        query_str = """CREATE TABLE student_course_master_data
        (student_course_master_data_id VARCHAR (1000) PRIMARY KEY,
        account_id VARCHAR (1000) REFERENCES account (id)
        ON UPDATE CASCADE ON DELETE CASCADE,
        course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,
        datas jsonb)"""

        print("Create table: student_course_master_data")
        if self.postgres.exec_query(query_str):
            self.log.info("Student Course Master Data table successfully created!")

        # UPLOADED EXERCISE QUESTION
        query_str = "CREATE TABLE uploaded_exercise_question ("
        query_str += "exercise_id VARCHAR (1000) REFERENCES exercise (exercise_id) ON UPDATE CASCADE,"
        query_str += " question_id VARCHAR (1000) REFERENCES questions (question_id) ON UPDATE CASCADE,"
        query_str += " CONSTRAINT uploaded_exercise_question_pkey PRIMARY KEY (exercise_id, question_id))"

        print("Create table: uploaded_exercise_question")
        if self.postgres.exec_query(query_str):
            self.log.info("Uploaded exercise question table successfully created!")

        # STUDEND EXERCISE REPEAT
        query_str = """CREATE TABLE student_exercise_repeat (
            student_exercise_repeat_id VARCHAR (1000) PRIMARY KEY,
            exercise_id VARCHAR (1000) REFERENCES exercise (exercise_id)
            ON UPDATE CASCADE, is_passed BOOLEAN, account_id VARCHAR (1000)
            REFERENCES account (id) ON UPDATE CASCADE ON DELETE CASCADE,
            course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE,
            update_on BIGINT, created_on BIGINT NOT NULL)"""

        print("Create table: student_exercise_repeat")
        if self.postgres.exec_query(query_str):
            self.log.info("Student Exercise Repeat table successfully created!")

        # COURSE SEQUENCE
        query_str = """CREATE TABLE course_sequence
        (course_id VARCHAR (1000) REFERENCES course (course_id) ON UPDATE CASCADE, sequence BIGINT)"""

        print("Create table: course_sequence")
        if self.postgres.exec_query(query_str):
            self.log.info("Course Sequence table successfully created!")

        # ACCOUNT OLD EMAIL
        query_str = "CREATE TABLE account_old_email (account_id VARCHAR (1000)"
        query_str += " REFERENCES account (id) ON UPDATE CASCADE ON DELETE CASCADE,"
        query_str += " email VARCHAR (355) NOT NULL, created_on BIGINT NOT NULL)"
        print("Create table: account_old_email")
        if self.postgres.exec_query(query_str):
            self.log.info("Account Old Email table successfully created!")

        # +++++++++++++++++++++++++++ ALTER +++++++++++++++++++++++++++ #
        # ALTER ACCOUNT
        query_str = "ALTER TABLE uploaded_exercise_question ADD COLUMN sequence BIGINT"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE Uploaded Exercise Question successfully!")

        # ALTER ACCOUNT
        query_str = "ALTER TABLE account ADD COLUMN progress VARCHAR (355) DEFAULT 0 NOT NULL"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE Account Courses successfully!")

        # ALTER SUBSECTION REQUIREMENTS
        query_str = "ALTER TABLE subsection_requirements ADD COLUMN is_repeatable BOOLEAN DEFAULT False NOT NULL"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE Account Courses successfully!")

        # ALTER SECTION REQUIREMENTS
        query_str = "ALTER TABLE section_requirements ADD COLUMN is_repeatable BOOLEAN DEFAULT False NOT NULL"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE Account Courses successfully!")

        # ALTER COURSE REQUIREMENTS
        query_str = "ALTER TABLE course_requirements ADD COLUMN is_repeatable BOOLEAN DEFAULT False NOT NULL"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE course_requirements successfully!")

        # ALTER ACCOUNT
        query_str = "ALTER TABLE account ADD COLUMN is_online BOOLEAN DEFAULT False NOT NULL"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE Account successfully!")

        # ALTER ACCOUNT
        query_str = "ALTER TABLE account ADD COLUMN sidebar BOOLEAN DEFAULT True NOT NULL"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE Account successfully!")

        # ALTER ACCOUNT
        query_str = "ALTER TABLE account_token ADD COLUMN"
        query_str += " role_id VARCHAR (1000) REFERENCES role (role_id) ON UPDATE"
        query_str += " CASCADE ON DELETE CASCADE"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE Account Token successfully!")

        # ALTER USER GROUP
        query_str = "ALTER TABLE user_group"
        query_str += " ADD COLUMN progress VARCHAR (355) DEFAULT 0 NOT NULL,"
        query_str += " ADD COLUMN least_performer VARCHAR (355),"
        query_str += " ADD COLUMN next_class VARCHAR (355)"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE user_group Courses successfully!")

        # ALTER TUTOR COURSES
        query_str = "ALTER TABLE tutor_courses ADD COLUMN progress VARCHAR (355)"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE Tutor Courses successfully!")

        # ALTER EXERCISE
        query_str = "ALTER TABLE exercise ADD COLUMN question_types jsonb"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE exercise successfully!")

        # ALTER EXERCISE
        query_str = "ALTER TABLE exercise ADD COLUMN tags jsonb"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE exercise successfully!")

        # ALTER QUESTIONS
        # query_str = "ALTER TABLE questions ADD COLUMN skill VARCHAR (500)"
        # if self.postgres.exec_query(query_str):
        #     self.log.info("ALTER TABLE questions successfully!")

        # ALTER QUESTION
        query_str = "ALTER TABLE questions ADD COLUMN gain_experience BIGINT"
        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE questions successfully!")

        # ALTER QUESTION
        query_str = "ALTER TABLE questions ADD COLUMN batch VARCHAR (1000)"
        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE questions successfully!")

        # ALTER QUESTION
        query_str = "ALTER TABLE questions ADD COLUMN orig_question jsonb"
        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE questions successfully!")

        # ALTER QUESTION
        query_str = "ALTER TABLE questions ADD COLUMN orig_answer jsonb"
        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE questions successfully!")

        # ALTER QUESTION
        query_str = "ALTER TABLE questions ADD COLUMN orig_choices jsonb"
        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE questions successfully!")

        # ALTER QUESTION
        query_str = "ALTER TABLE questions ADD COLUMN orig_skills jsonb"
        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE questions successfully!")

        # ALTER QUESTION
        query_str = "ALTER TABLE questions ADD COLUMN orig_tags jsonb"
        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE questions successfully!")

        # # ALTER QUESTIONS
        # query_str = "ALTER TABLE questions ADD COLUMN extend_skill jsonb"
        # if self.postgres.exec_query(query_str):
        #     self.log.info("ALTER TABLE questions successfully!")

        # ALTER STUDENT EXERCISE
        query_str = "ALTER TABLE student_exercise ADD COLUMN started_on BIGINT"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE student_exercise successfully!")

        # ALTER STUDENT SECTION
        query_str = "ALTER TABLE student_section ADD COLUMN started_on BIGINT"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE student_section successfully!")

        # ALTER STUDENT SUBSECTION
        query_str = "ALTER TABLE student_subsection ADD COLUMN started_on BIGINT"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE student_subsection successfully!")

        # ALTER STUDENT COURSE
        query_str = "ALTER TABLE student_course ADD COLUMN started_on BIGINT"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE student_course successfully!")

        # ALTER STUDENT EXERCISE QUESTIONS
        query_str = "ALTER TABLE student_exercise_questions ADD COLUMN end_on BIGINT"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE student_exercise successfully!")

        # ALTER STUDENT EXERCISE
        query_str = "ALTER TABLE student_exercise ADD COLUMN end_on BIGINT"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE student_exercise successfully!")

        # ALTER STUDENT SECTION
        query_str = "ALTER TABLE student_section ADD COLUMN end_on BIGINT"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE student_section successfully!")

        # ALTER STUDENT SUBSECTION
        query_str = "ALTER TABLE student_subsection ADD COLUMN end_on BIGINT"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE student_subsection successfully!")

        # ALTER STUDENT COURSE
        query_str = "ALTER TABLE student_course ADD COLUMN end_on BIGINT"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE student_course successfully!")

        # ALTER STUDENT EXERCISE
        query_str = "ALTER TABLE student_exercise ADD COLUMN total_experience BIGINT"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE student_exercise successfully!")

        # ALTER STUDENT EXERCISE QUESTIONS
        query_str = "ALTER TABLE student_exercise_questions ADD COLUMN is_correct BOOLEAN"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE student_exercise_questions successfully!")

        # ALTER TUTOR EXERCISE QUESTIONS
        query_str = "ALTER TABLE tutor_exercise_questions ADD COLUMN is_correct BOOLEAN"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE tutor_exercise_questions successfully!")

        # ALTER STUDENT EXERCISE
        query_str = "ALTER TABLE student_exercise ADD COLUMN is_unlocked BOOLEAN,"
        query_str += " ADD COLUMN unlock_criteria VARCHAR (500), ADD COLUMN unlocked_on BIGINT"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE student_exercise successfully!")

        # ALTER STUDENT SUBSECTION
        query_str = "ALTER TABLE student_subsection ADD COLUMN is_unlocked BOOLEAN,"
        query_str += " ADD COLUMN unlock_criteria VARCHAR (500), ADD COLUMN unlocked_on BIGINT"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE student_subsection successfully!")

        # ALTER STUDENT SECTION
        query_str = "ALTER TABLE student_section ADD COLUMN is_unlocked BOOLEAN,"
        query_str += " ADD COLUMN unlock_criteria VARCHAR (500), ADD COLUMN unlocked_on BIGINT"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE student_section successfully!")

        # ALTER STUDENT COURSE
        query_str = "ALTER TABLE student_course ADD COLUMN is_unlocked BOOLEAN,"
        query_str += " ADD COLUMN unlock_criteria VARCHAR (500), ADD COLUMN unlocked_on BIGINT"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE student_course successfully!")

        # ALTER SECTION
        query_str = "ALTER TABLE section ADD COLUMN requirements VARCHAR (5000)"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE section successfully!")

        # ALTER SUBSECTION
        query_str = "ALTER TABLE subsection ADD COLUMN requirements VARCHAR (5000)"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE subsection successfully!")

        # ALTER EXERCISE
        query_str = "ALTER TABLE exercise ADD COLUMN requirements VARCHAR (5000)"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE exercise successfully!")

        # ALTER SUBSKILL
        query_str = "ALTER TABLE subskills ADD COLUMN max_score BIGINT"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE subskill successfully!")

        # ALTER EXERCISE
        query_str = "ALTER TABLE exercise ADD COLUMN is_repeatable BOOLEAN DEFAULT FALSE"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE exercise successfully!")

        # ALTER COURSE
        query_str = "ALTER TABLE course ADD COLUMN exercise_name VARCHAR (500)"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE course successfully!")

        # ALTER EXERCISE
        query_str = "ALTER TABLE exercise ADD COLUMN draw_by_skills BOOLEAN DEFAULT FALSE"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE exercise successfully!")

        # ALTER COURSE
        query_str = "ALTER TABLE course ADD COLUMN course_title VARCHAR (500)"

        if self.postgres.exec_query(query_str):
            self.log.info("ALTER TABLE course successfully!")
        # +++++++++++++++++++++++++++ VIEWS +++++++++++++++++++++++++++ #
        # USER
        query_str = """CREATE VIEW account_master AS
        SELECT a.id, a.username, a.email, a.password, a.status,
        a.first_name, a.middle_name, a.last_name, a.sidebar, a.last_login,
        a.address, a.zip_code, a.city, a.language, a.timezone,
        (SELECT array_to_json(array_agg(role_perm))
        FROM (SELECT r.role_id, r.role_name, r.role_details, 
        (SELECT array_to_json(array_agg(p)) FROM permission p 
        INNER JOIN role_permission rp ON rp.permission_id = p.permission_id 
        WHERE rp.role_id = r.role_id) AS permissions FROM role r
        INNER JOIN account_role ar ON ar.role_id = r.role_id
        WHERE ar.account_id = a.id) AS role_perm) AS roles, 
        (SELECT array_to_json(array_agg(sgroups))
        FROM (SELECT * FROM user_group WHERE user_group_id IN
        (SELECT user_group_id FROM user_group_students WHERE
        student_id=a.id)) AS sgroups) AS student_groups,
        (SELECT array_to_json(array_agg(tgroups))
        FROM (SELECT * FROM user_group WHERE user_group_id IN
        (SELECT user_group_id FROM user_group_tutors
        WHERE tutor_id=a.id)) AS tgroups) AS tutor_groups,
        a.is_send_email, a.is_license_renewable, a.force_change_password,
        a.receive_messages, a.receive_assignments, a.receive_progress, a.receive_updates,
        a.receive_reminders, a.receive_events, a.receive_discussions, a.receive_newly_available,
        a.receive_certificate_notifications, a.receive_memo_training, a.receive_other, a.email_frequency, 
        a.biography, a.faceboot_url, a.linkedin_url, a.twitter_url, a.skype_username,
        a.created_on FROM account a"""

        print("Create view: account_master")
        if self.postgres.exec_query(query_str):
            self.log.info("Account Master view table successfully created!")

        # USER GROUP
        courses = """, (SELECT array_to_json(array_agg(user_gc)) FROM
        (SELECT c.course_id, c.course_name, c.course_title, c.description, ug.user_group_id 
        FROM course c INNER JOIN user_group_courses ugc
        ON ugc.course_id=c.course_id WHERE ug.user_group_id=ugc.user_group_id)
        AS user_gc ) AS courses"""
        students = """, (SELECT array_to_json(array_agg(user_gs)) FROM
        (SELECT a.id as student_id, a.first_name, a.last_name, a.middle_name,
        CONCAT  (a.first_name, ' ', a.last_name) AS full_name FROM account a
        INNER JOIN user_group_students ugs ON ugs.student_id=a.id
        WHERE ug.user_group_id=ugs.user_group_id) AS user_gs ) AS students"""
        tutors = """, (SELECT array_to_json(array_agg(user_gt)) FROM
        (SELECT ugt.tutor_id, a.first_name, a.last_name, a.middle_name,
        CONCAT  (a.first_name, ' ', a.last_name) AS full_name FROM account a
        INNER JOIN user_group_tutors ugt ON ugt.tutor_id=a.id
        WHERE ug.user_group_id=ugt.user_group_id) AS user_gt ) AS tutors"""
        query_str = "CREATE VIEW user_group_master AS "
        query_str += "SELECT ug.user_group_id, ug.user_group_name, ug.created_on"
        query_str += courses
        query_str += students
        query_str += tutors
        query_str += " FROM user_group ug"

        print("Create view: user_group_master")
        if self.postgres.exec_query(query_str):
            self.log.info("User Group Master view table successfully created!")

        # STUDENT SECTION
        query_str = """CREATE VIEW section_master AS
        SELECT ss.student_section_id AS key, s.course_id, ss.account_id, s.section_id, 
        s.section_name, s.section_name AS name, ss.created_on AS started, ss.status,
        ss.update_on as finished,ss.end_on AS update_on,
        ss.progress, ss.percent_score AS score, s.difficulty_level,
        (SELECT array_to_json(array_agg(sctn)) FROM 
        (SELECT sub.subsection_id, sub.subsection_name, sub.subsection_name AS name, 
        ssub.created_on as started, ssub.end_on AS update_on, ssub.progress, ssub.percent_score AS score, ssub.student_subsection_id AS key,
        (SELECT array_to_json(array_agg(exrcs)) FROM 
        (SELECT ex.exercise_id, ex.exercise_number, se.student_exercise_id, se.created_on as started, se.started_on,
        se.end_on AS update_on, se.progress, se.percent_score AS score, 
        CASE WHEN c.exercise_name is null OR c.exercise_name = '' then
        'Exercise '||ex.exercise_number else CONCAT(c.exercise_name, ' ')||ex.exercise_number end as name,
         se.student_exercise_id AS key, 
        (SELECT array_to_json(array_agg(quest)) FROM (SELECT cq.course_question_id, 
        cq.question_type, seq.is_correct, seq.sequence, seq.started_on AS started, seq.update_on, 
        (SELECT array_to_json(array_agg(row_to_json(t))) AS children
        FROM (  SELECT * FROM (SELECT * FROM (SELECT 'Question' as name, NULL AS is_correct, cq2.question_type, question->'question' AS value, 
        cq2.course_question_id FROM course_question cq2 WHERE  cq2.course_question_id = cq.course_question_id
        UNION SELECT 'Answer' as name, seq1.is_correct, scq.question_type, answer as value, seq1.course_question_id FROM 
        student_exercise_questions seq1 LEFT JOIN course_question scq ON seq1.course_question_id = scq.course_question_id
        WHERE  seq1.course_question_id = cq.course_question_id AND seq1.account_id = seq.account_id AND seq1.student_exercise_id = seq.student_exercise_id
        UNION SELECT 'Correct Answer' as name, NULL AS is_correct, cq1.question_type, CASE WHEN (select case when answer is null OR CAST("answer" AS text) = '""' then true else false end as ans
        FROM student_exercise_questions sqs WHERE sqs.course_question_id = cq.course_question_id AND sqs.account_id = seq.account_id  AND
        sqs.student_exercise_id =  se.student_exercise_id LIMIT 1) is True Then NULL ELSE  correct_answer->'answer' END AS value,    
        cq1.course_question_id FROM course_question cq1 WHERE  cq1.course_question_id = cq.course_question_id) t
        ORDER BY CASE WHEN t.name='Question' THEN 1 WHEN t.name='Answer' THEN 2 WHEN t.name='Correct Answer' THEN 3  ELSE 4 END) t
        ) t) AS children, seq.progress, seq.percent_score AS score, 'Question '||seq.sequence AS name, seq.student_exercise_id||seq.course_question_id AS key
        FROM student_exercise_questions seq INNER JOIN course_question cq 
        ON seq.course_question_id=cq.course_question_id WHERE seq.account_id=ss.account_id 
        AND seq.student_exercise_id=se.student_exercise_id ORDER BY seq.sequence) AS quest) AS children 
        FROM student_exercise se INNER JOIN exercise ex ON se.exercise_id=ex.exercise_id 
        WHERE se.account_id=ss.account_id AND ex.subsection_id=ssub.subsection_id 
        AND se.status=true ORDER BY ex.exercise_number::int) AS exrcs) 
        AS children FROM student_subsection ssub 
        INNER JOIN subsection sub ON ssub.subsection_id=sub.subsection_id 
        WHERE ssub.account_id=ss.account_id AND sub.section_id=s.section_id AND ssub.status=true
        AND sub.status=true ORDER BY sub.difficulty_level) AS sctn) 
        AS children FROM student_section ss INNER 
        JOIN section s ON ss.section_id=s.section_id LEFT JOIN course c ON s.course_id = c.course_id
        """

        print("Create view: section_master")
        if self.postgres.exec_query(query_str):
            self.log.info("Section Master view table successfully created!")

        # COURSE
        query_str = """CREATE VIEW course_master AS
        SELECT * , (SELECT array_to_json(array_agg(sctn)) FROM (
        SELECT s.section_id AS key, s.section_name AS name, * ,
            (SELECT array_to_json(array_agg(sbsctn)) FROM (
        SELECT ss.subsection_id AS key, ss.subsection_name AS name, * ,
            (SELECT array_to_json(array_agg(ex)) FROM (
        SELECT e.exercise_id AS key, CASE WHEN c.exercise_name is null OR c.exercise_name = '' then
        'Exercise '||e.exercise_number else CONCAT(c.exercise_name, ' ')||e.exercise_number end as name, * 
        FROM exercise e WHERE e.subsection_id=ss.subsection_id ORDER BY CAST(e.exercise_number AS INTEGER) ASC)AS ex) 
        AS children FROM subsection ss WHERE ss.section_id=s.section_id 
        AND ss.course_id=c.course_id ORDER BY ss.difficulty_level ASC) AS sbsctn) AS children 
        FROM section s WHERE s.course_id=c.course_id ORDER BY s.difficulty_level ASC) 
        AS sctn) AS children FROM course c ORDER BY c.difficulty_level ASC
        """

        print("Create view: course_master")
        if self.postgres.exec_query(query_str):
            self.log.info("Course Master view table successfully created!")

        # SKILL
        query_str = """CREATE VIEW skill_master AS
        SELECT DISTINCT skill FROM questions"""

        print("Create view: skill_master")
        if self.postgres.exec_query(query_str):
            self.log.info("Skill Master view table successfully created!")

        # TAGS
        query_str = """CREATE VIEW tag_master AS
        SELECT DISTINCT(tags) FROM questions"""

        print("Create view: tag_master")
        if self.postgres.exec_query(query_str):
            self.log.info("Tag Master view table successfully created!")

        # STUDENT COURSE MASTER
        query_str = """CREATE VIEW student_course_master AS
        SELECT sc.account_id, ROUND(cast(sc.progress as numeric),2)
        AS progress, sc.expiry_date, sc.status, sc.update_on, sc.created_on,
        c.course_id, c.course_name, c.course_title, c.description, c.requirements, c.exercise_name,
        c.difficulty_level, (SELECT array_to_json(array_agg(sctn))
        FROM (SELECT s.*, ss.*, (SELECT array_to_json(array_agg(ssctn))
        FROM (SELECT sub.*, ss.*, (SELECT array_to_json(array_agg(exers))
        FROM (SELECT *, CASE WHEN c.exercise_name is null OR c.exercise_name = '' then
        'Exercise '||e.exercise_number else CONCAT(c.exercise_name, ' ')||e.exercise_number end as exercise_num
         FROM exercise e LEFT JOIN student_exercise se ON
        e.exercise_id=se.exercise_id WHERE se.course_id =c.course_id AND
        e.status is True AND se.account_id=sc.account_id AND se.status
        is True AND e.exercise_id IN (SELECT exercise_id FROM exercise
        WHERE subsection_id=sub.subsection_id) ORDER BY e.exercise_number::int)
        AS exers) AS exercises FROM student_subsection ss LEFT JOIN
        subsection sub ON ss.subsection_id = sub.subsection_id WHERE
        ss.section_id=s.section_id AND ss.account_id=sc.account_id AND
        ss.status is True ORDER BY sub.difficulty_level) AS ssctn) AS
        subsection FROM student_section ss LEFT JOIN section s ON
        ss.section_id = s.section_id WHERE ss.course_id=c.course_id AND
        ss.account_id=sc.account_id AND ss.status is True ORDER BY
        s.difficulty_level) AS sctn) AS sections FROM student_course
        sc LEFT JOIN course c ON sc.course_id = c.course_id"""
        # SELECT sc.account_id, ROUND(cast(sc.progress as numeric),2)
        # AS progress, sc.expiry_date, sc.status, sc.update_on, sc.created_on,
        # c.course_id, c.course_name, c.description, c.requirements,
        # c.difficulty_level FROM student_course sc LEFT JOIN course c ON
        # sc.course_id = c.course_id"""

        print("Create view: student_course_master")
        if self.postgres.exec_query(query_str):
            self.log.info("Student Course Master view table successfully created!")

        # CLOSE CONNECTION
        self.postgres.close_connection()

    def create_default_translation(self):
        """Create Default Entries"""

        # +++++++++++++++++++++++++++ LANGUAGE +++++++++++++++++++++++++++ #

        sql_str = "SELECT language_id FROM language WHERE"
        sql_str += " language_name ='dutch'"
        language_id = self.postgres.query_fetch_one(sql_str)

        if not language_id:

            data = {}
            data['language_id'] = self.sha_security.generate_token(False)
            data['language_name'] = "dutch"
            data['initial'] = 'nl-NL'
            data['created_on'] = time.time()
            self.postgres.insert('language', data)

        sql_str = "SELECT language_id FROM language WHERE"
        sql_str += " language_name ='english'"
        language_id = self.postgres.query_fetch_one(sql_str)

        if not language_id:

            data = {}
            data['language_id'] = self.sha_security.generate_token(False)
            data['language_name'] = "english"
            data['initial'] = 'en-US'
            data['created_on'] = time.time()
            self.postgres.insert('language', data)

        # --------------------------- LANGUAGE --------------------------- #

        # +++++++++++++++++++++++++++ WORDS +++++++++++++++++++++++++++ #

        words_path = str(pathlib.Path().absolute())
        words_path += '/sample_datas/words.csv'

        if os.path.isfile(words_path):

            reader = csv.DictReader(open(words_path, encoding='utf-8-sig'))

            for row in reader:

                sql_str = "SELECT word_id FROM words WHERE"
                sql_str += " type ='{0}' AND ".format(row['type'])
                sql_str += " name ='{0}'".format(row['name'])

                word_id = self.postgres.query_fetch_one(sql_str)

                if word_id:

                    continue

                data = {}
                data['word_id'] = self.sha_security.generate_token(False)
                data['type'] = row['type']
                data['name'] = row['name']
                data['created_on'] = time.time()
                self.postgres.insert('words', data)

        # --------------------------- WORDS --------------------------- #

        # +++++++++++++++++++++++++++ TRANSLATION +++++++++++++++++++++++++++ #

        words_path = str(pathlib.Path().absolute())
        words_path += '/sample_datas/translation.csv'

        if os.path.isfile(words_path):

            reader = csv.DictReader(open(words_path, encoding='utf-8-sig'))

            for row in reader:

                sql_str = "SELECT word_id FROM words WHERE"
                sql_str += " name='{0}'".format(row['word'])
                word = self.postgres.query_fetch_one(sql_str)

                if not word:

                    print("row: {0}".format(row['word']))
                    continue

                sql_str = "SELECT language_id FROM language WHERE"
                sql_str += " language_name='{0}'".format(row['language'])
                language = self.postgres.query_fetch_one(sql_str)

                if not language:

                    print("language: {0}".format(row['language']))
                    continue
                sql_str = "SELECT translation_id FROM translations WHERE"
                sql_str += " word_id ='{0}' AND ".format(word['word_id'])
                sql_str += " language_id ='{0}' AND ".format(language['language_id'])
                sql_str += " type ='{0}'".format(row['type'])

                translation_id = self.postgres.query_fetch_one(sql_str)

                if translation_id:

                    continue

                data = {}
                data['translation_id'] = self.sha_security.generate_token(False)
                data['word_id'] = word['word_id']
                data['language_id'] = language['language_id']
                data['type'] = row['type']
                data['translation'] = row['translation']
                data['created_on'] = time.time()
                self.postgres.insert('translations', data)

        # --------------------------- TRANSLATION --------------------------- #


    def create_default_entries(self, prod_flag):
        """Create Default Entries"""

        # +++++++++++++++++++++++++++ PERMISSION +++++++++++++++++++++++++++ #
        data = {}
        data['permission_id'] = self.sha_security.generate_token(False)
        data['permission_name'] = config_section_parser(self.config,
                                                        "PERMISSION")['permission_name']
        data['permission_details'] = config_section_parser(self.config,
                                                           "PERMISSION")['permission_details']
        data['default_value'] = True
        data['created_on'] = time.time()


        print("Create default permission: ", data['permission_name'])
        permission_id = self.postgres.insert('permission', data, 'permission_id')

        if permission_id:

            self.log.info("Default Permission successfully created!")

        else:

            sql_str = "SELECT * FROM permission WHERE"
            sql_str += " permission_name='" + data['permission_name'] + "'"
            res = self.postgres.query_fetch_one(sql_str)
            permission_id = res['permission_id']

        for dta in range(1, 4):

            data1 = {}
            data1['permission_id'] = self.sha_security.generate_token(False)
            data1['permission_name'] = config_section_parser(self.config,
                                                             "PERMISSION")['permission_name'\
                                                             + str(dta)]
            data1['permission_details'] = config_section_parser(self.config,
                                                                "PERMISSION")['permission_details'\
                                                             + str(dta)]
            data1['default_value'] = True
            data1['created_on'] = time.time()

            print("Create default permission: ", data1['permission_name'])
            self.postgres.insert('permission', data1, 'permission_id')

        permission_name1 = config_section_parser(self.config, "PERMISSION")['permission_name1']
        sql_str = "SELECT * FROM permission WHERE permission_name='{0}'".format(permission_name1)
        res = self.postgres.query_fetch_one(sql_str)
        permission_id1 = res['permission_id']

        permission_name2 = config_section_parser(self.config, "PERMISSION")['permission_name2']
        sql_str = "SELECT * FROM permission WHERE permission_name='{0}'".format(permission_name2)
        res = self.postgres.query_fetch_one(sql_str)
        permission_id2 = res['permission_id']

        permission_name3 = config_section_parser(self.config, "PERMISSION")['permission_name3']
        sql_str = "SELECT * FROM permission WHERE permission_name='{0}'".format(permission_name3)
        res = self.postgres.query_fetch_one(sql_str)
        permission_id3 = res['permission_id']

        # --------------------------- PERMISSION --------------------------- #

        # +++++++++++++++++++++++++++ ROLE +++++++++++++++++++++++++++ #
        # MANAGER
        data = {}
        data['role_id'] = self.sha_security.generate_token(False)
        data['role_name'] = config_section_parser(self.config, "ROLE")['role_name']
        data['role_details'] = config_section_parser(self.config, "ROLE")['role_details']
        data['default_value'] = True
        data['created_on'] = time.time()

        # STUDENT
        data1 = {}
        data1['role_id'] = self.sha_security.generate_token(False)
        data1['role_name'] = config_section_parser(self.config, "ROLE")['role_name1']
        data1['role_details'] = config_section_parser(self.config, "ROLE")['role_details1']
        data1['default_value'] = True
        data1['created_on'] = time.time()

        # PARENT
        data2 = {}
        data2['role_id'] = self.sha_security.generate_token(False)
        data2['role_name'] = config_section_parser(self.config, "ROLE")['role_name2']
        data2['role_details'] = config_section_parser(self.config, "ROLE")['role_details2']
        data2['default_value'] = True
        data2['created_on'] = time.time()

        # TUTOR
        data3 = {}
        data3['role_id'] = self.sha_security.generate_token(False)
        data3['role_name'] = config_section_parser(self.config, "ROLE")['role_name3']
        data3['role_details'] = config_section_parser(self.config, "ROLE")['role_details3']
        data3['default_value'] = True
        data3['created_on'] = time.time()

        role_id = self.postgres.insert('role', data, 'role_id')
        student_role_id = self.postgres.insert('role', data1, 'role_id')
        parent_role_id = self.postgres.insert('role', data2, 'role_id')
        tutor_role_id = self.postgres.insert('role', data3, 'role_id')

        # MANAGER
        if role_id:
            print("Default Role successfully created!")
        else:
            self.postgres.connection()

            sql_str = "SELECT * FROM role WHERE role_name='" + data['role_name'] + "'"
            res = self.postgres.query_fetch_one(sql_str)
            role_id = res['role_id']

            self.postgres.close_connection()

        # STUDENT
        if student_role_id:
            print("Default Role successfully created!")
        else:
            self.postgres.connection()

            sql_str = "SELECT * FROM role WHERE role_name='" + data1['role_name'] + "'"
            res = self.postgres.query_fetch_one(sql_str)
            student_role_id = res['role_id']

            self.postgres.close_connection()

        # PARENT
        if parent_role_id:
            print("Default Role successfully created!")
        else:
            self.postgres.connection()

            sql_str = "SELECT * FROM role WHERE role_name='" + data2['role_name'] + "'"
            res = self.postgres.query_fetch_one(sql_str)
            parent_role_id = res['role_id']

            self.postgres.close_connection()

        # TUTOR
        if tutor_role_id:
            print("Default Role successfully created!")
        else:
            self.postgres.connection()

            sql_str = "SELECT * FROM role WHERE role_name='" + data3['role_name'] + "'"
            res = self.postgres.query_fetch_one(sql_str)
            tutor_role_id = res['role_id']

            self.postgres.close_connection()
        # --------------------------- ROLE --------------------------- #

        # +++++++++++++++++++++++++++ MANAGER ACCOUNT +++++++++++++++++++++++++++ #
        data = {}
        data['id'] = self.sha_security.generate_token(False)
        data['username'] = config_section_parser(self.config, "MANAGER1")['username']
        data['password'] = config_section_parser(self.config, "MANAGER1")['password']
        data['email'] = config_section_parser(self.config, "MANAGER1")['email']
        data['first_name'] = config_section_parser(self.config, "MANAGER1")['first_name']
        data['middle_name'] = config_section_parser(self.config, "MANAGER1")['middle_name']
        data['last_name'] = config_section_parser(self.config, "MANAGER1")['last_name']
        data['status'] = bool(config_section_parser(self.config, "MANAGER1")['status'])
        data['state'] = bool(config_section_parser(self.config, "MANAGER1")['state'])
        data['url'] = "default"
        # data['token'] = self.sha_security.generate_token(False)
        data['default_value'] = True
        data['created_on'] = time.time()
        data['update_on'] = time.time()

        print("Create default user: ", data['username'])
        account_id1 = self.postgres.insert('account', data, 'id')
        if account_id1:
            self.log.info("Default user successfully created!")
        else:

            sql_str = "SELECT id FROM account WHERE username='" + data['username'] + "'"
            res = self.postgres.query_fetch_one(sql_str)
            account_id1 = res['id']
        # --------------------------- MANAGER ACCOUNT --------------------------- #

        # +++++++++++++++++++++++++++ STUDENT ACCOUNT +++++++++++++++++++++++++++ #
        # STUDENT 1
        data = {}
        data['id'] = self.sha_security.generate_token(False)
        data['username'] = config_section_parser(self.config, "STUDENT1")['username']
        data['password'] = config_section_parser(self.config, "STUDENT1")['password']
        data['email'] = config_section_parser(self.config, "STUDENT1")['email']
        data['first_name'] = config_section_parser(self.config, "STUDENT1")['first_name']
        data['middle_name'] = config_section_parser(self.config, "STUDENT1")['middle_name']
        data['last_name'] = config_section_parser(self.config, "STUDENT1")['last_name']
        data['status'] = bool(config_section_parser(self.config, "STUDENT1")['status'])
        data['state'] = bool(config_section_parser(self.config, "STUDENT1")['state'])
        data['url'] = "default"
        data['default_value'] = True
        data['created_on'] = time.time()
        data['update_on'] = time.time()

        print("Create default user: ", data['username'])
        student_id1 = self.postgres.insert('account', data, 'id')
        if student_id1:
            self.log.info("Default user successfully created!")
        else:

            sql_str = "SELECT id FROM account WHERE username='" + data['username'] + "'"
            res = self.postgres.query_fetch_one(sql_str)
            student_id1 = res['id']

        # STUDENT 2
        data = {}
        data['id'] = self.sha_security.generate_token(False)
        data['username'] = config_section_parser(self.config, "STUDENT2")['username']
        data['password'] = config_section_parser(self.config, "STUDENT2")['password']
        data['email'] = config_section_parser(self.config, "STUDENT2")['email']
        data['first_name'] = config_section_parser(self.config, "STUDENT2")['first_name']
        data['middle_name'] = config_section_parser(self.config, "STUDENT2")['middle_name']
        data['last_name'] = config_section_parser(self.config, "STUDENT2")['last_name']
        data['status'] = bool(config_section_parser(self.config, "STUDENT2")['status'])
        data['state'] = bool(config_section_parser(self.config, "STUDENT2")['state'])
        data['url'] = "default"
        data['default_value'] = True
        data['created_on'] = time.time()
        data['update_on'] = time.time()

        print("Create default user: ", data['username'])
        student_id2 = self.postgres.insert('account', data, 'id')
        if student_id2:
            self.log.info("Default user successfully created!")
        else:

            sql_str = "SELECT id FROM account WHERE username='" + data['username'] + "'"
            res = self.postgres.query_fetch_one(sql_str)
            student_id2 = res['id']

        # STUDENT 3
        data = {}
        data['id'] = self.sha_security.generate_token(False)
        data['username'] = config_section_parser(self.config, "STUDENT3")['username']
        data['password'] = config_section_parser(self.config, "STUDENT3")['password']
        data['email'] = config_section_parser(self.config, "STUDENT3")['email']
        data['first_name'] = config_section_parser(self.config, "STUDENT3")['first_name']
        data['middle_name'] = config_section_parser(self.config, "STUDENT3")['middle_name']
        data['last_name'] = config_section_parser(self.config, "STUDENT3")['last_name']
        data['status'] = bool(config_section_parser(self.config, "STUDENT3")['status'])
        data['state'] = bool(config_section_parser(self.config, "STUDENT3")['state'])
        data['url'] = "default"
        data['default_value'] = True
        data['created_on'] = time.time()
        data['update_on'] = time.time()

        print("Create default user: ", data['username'])
        student_id3 = self.postgres.insert('account', data, 'id')
        if student_id3:
            self.log.info("Default user successfully created!")
        else:

            sql_str = "SELECT id FROM account WHERE username='" + data['username'] + "'"
            res = self.postgres.query_fetch_one(sql_str)
            student_id3 = res['id']

        # STUDENT 4
        data = {}
        data['id'] = self.sha_security.generate_token(False)
        data['username'] = config_section_parser(self.config, "STUDENT4")['username']
        data['password'] = config_section_parser(self.config, "STUDENT4")['password']
        data['email'] = config_section_parser(self.config, "STUDENT4")['email']
        data['first_name'] = config_section_parser(self.config, "STUDENT4")['first_name']
        data['middle_name'] = config_section_parser(self.config, "STUDENT4")['middle_name']
        data['last_name'] = config_section_parser(self.config, "STUDENT4")['last_name']
        data['status'] = bool(config_section_parser(self.config, "STUDENT4")['status'])
        data['state'] = bool(config_section_parser(self.config, "STUDENT4")['state'])
        data['url'] = "default"
        data['default_value'] = True
        data['created_on'] = time.time()
        data['update_on'] = time.time()

        print("Create default user: ", data['username'])
        student_id4 = self.postgres.insert('account', data, 'id')
        if student_id4:
            self.log.info("Default user successfully created!")
        else:

            sql_str = "SELECT id FROM account WHERE username='" + data['username'] + "'"
            res = self.postgres.query_fetch_one(sql_str)
            student_id4 = res['id']

        # STUDENT 5
        data = {}
        data['id'] = self.sha_security.generate_token(False)
        data['username'] = config_section_parser(self.config, "STUDENT5")['username']
        data['password'] = config_section_parser(self.config, "STUDENT5")['password']
        data['email'] = config_section_parser(self.config, "STUDENT5")['email']
        data['first_name'] = config_section_parser(self.config, "STUDENT5")['first_name']
        data['middle_name'] = config_section_parser(self.config, "STUDENT5")['middle_name']
        data['last_name'] = config_section_parser(self.config, "STUDENT5")['last_name']
        data['status'] = bool(config_section_parser(self.config, "STUDENT5")['status'])
        data['state'] = bool(config_section_parser(self.config, "STUDENT5")['state'])
        data['url'] = "default"
        data['default_value'] = True
        data['created_on'] = time.time()
        data['update_on'] = time.time()

        print("Create default user: ", data['username'])
        student_id5 = self.postgres.insert('account', data, 'id')
        if student_id5:
            self.log.info("Default user successfully created!")
        else:

            sql_str = "SELECT id FROM account WHERE username='" + data['username'] + "'"
            res = self.postgres.query_fetch_one(sql_str)
            student_id5 = res['id']

        # --------------------------- STUDENT ACCOUNT --------------------------- #

        # # +++++++++++++++++++++++++++ PARENT ACCOUNT +++++++++++++++++++++++++++ #
        # # PARENT 1
        # data = {}
        # data['id'] = self.sha_security.generate_token(False)
        # data['username'] = config_section_parser(self.config, "PARENT1")['username']
        # data['password'] = config_section_parser(self.config, "PARENT1")['password']
        # data['email'] = config_section_parser(self.config, "PARENT1")['email']
        # data['first_name'] = config_section_parser(self.config, "PARENT1")['first_name']
        # data['middle_name'] = config_section_parser(self.config, "PARENT1")['middle_name']
        # data['last_name'] = config_section_parser(self.config, "PARENT1")['last_name']
        # data['status'] = bool(config_section_parser(self.config, "PARENT1")['status'])
        # data['state'] = bool(config_section_parser(self.config, "PARENT1")['state'])
        # data['url'] = "default"
        # data['default_value'] = True
        # data['created_on'] = time.time()
        # data['update_on'] = time.time()

        # print("Create default user: ", data['username'])
        # parent_id1 = self.postgres.insert('account', data, 'id')
        # if parent_id1:
        #     self.log.info("Default user successfully created!")
        # else:

        #     sql_str = "SELECT id FROM account WHERE username='" + data['username'] + "'"
        #     res = self.postgres.query_fetch_one(sql_str)
        #     parent_id1 = res['id']

        # # PARENT 2
        # data = {}
        # data['id'] = self.sha_security.generate_token(False)
        # data['username'] = config_section_parser(self.config, "PARENT2")['username']
        # data['password'] = config_section_parser(self.config, "PARENT2")['password']
        # data['email'] = config_section_parser(self.config, "PARENT2")['email']
        # data['first_name'] = config_section_parser(self.config, "PARENT2")['first_name']
        # data['middle_name'] = config_section_parser(self.config, "PARENT2")['middle_name']
        # data['last_name'] = config_section_parser(self.config, "PARENT2")['last_name']
        # data['status'] = bool(config_section_parser(self.config, "PARENT2")['status'])
        # data['state'] = bool(config_section_parser(self.config, "PARENT2")['state'])
        # data['url'] = "default"
        # data['default_value'] = True
        # data['created_on'] = time.time()
        # data['update_on'] = time.time()

        # print("Create default user: ", data['username'])
        # parent_id2 = self.postgres.insert('account', data, 'id')
        # if parent_id2:
        #     self.log.info("Default user successfully created!")
        # else:

        #     sql_str = "SELECT id FROM account WHERE username='" + data['username'] + "'"
        #     res = self.postgres.query_fetch_one(sql_str)
        #     parent_id2 = res['id']

        # # PARENT 3
        # data = {}
        # data['id'] = self.sha_security.generate_token(False)
        # data['username'] = config_section_parser(self.config, "PARENT3")['username']
        # data['password'] = config_section_parser(self.config, "PARENT3")['password']
        # data['email'] = config_section_parser(self.config, "PARENT3")['email']
        # data['first_name'] = config_section_parser(self.config, "PARENT3")['first_name']
        # data['middle_name'] = config_section_parser(self.config, "PARENT3")['middle_name']
        # data['last_name'] = config_section_parser(self.config, "PARENT3")['last_name']
        # data['status'] = bool(config_section_parser(self.config, "PARENT3")['status'])
        # data['state'] = bool(config_section_parser(self.config, "PARENT3")['state'])
        # data['url'] = "default"
        # data['default_value'] = True
        # data['created_on'] = time.time()
        # data['update_on'] = time.time()

        # print("Create default user: ", data['username'])
        # parent_id3 = self.postgres.insert('account', data, 'id')
        # if parent_id3:
        #     self.log.info("Default user successfully created!")
        # else:

        #     sql_str = "SELECT id FROM account WHERE username='" + data['username'] + "'"
        #     res = self.postgres.query_fetch_one(sql_str)
        #     parent_id3 = res['id']

        # # PARENT 4
        # data = {}
        # data['id'] = self.sha_security.generate_token(False)
        # data['username'] = config_section_parser(self.config, "PARENT4")['username']
        # data['password'] = config_section_parser(self.config, "PARENT4")['password']
        # data['email'] = config_section_parser(self.config, "PARENT4")['email']
        # data['first_name'] = config_section_parser(self.config, "PARENT4")['first_name']
        # data['middle_name'] = config_section_parser(self.config, "PARENT4")['middle_name']
        # data['last_name'] = config_section_parser(self.config, "PARENT4")['last_name']
        # data['status'] = bool(config_section_parser(self.config, "PARENT4")['status'])
        # data['state'] = bool(config_section_parser(self.config, "PARENT4")['state'])
        # data['url'] = "default"
        # data['default_value'] = True
        # data['created_on'] = time.time()
        # data['update_on'] = time.time()

        # print("Create default user: ", data['username'])
        # parent_id4 = self.postgres.insert('account', data, 'id')
        # if parent_id4:
        #     self.log.info("Default user successfully created!")
        # else:

        #     sql_str = "SELECT id FROM account WHERE username='" + data['username'] + "'"
        #     res = self.postgres.query_fetch_one(sql_str)
        #     parent_id4 = res['id']

        # # PARENT 5
        # data = {}
        # data['id'] = self.sha_security.generate_token(False)
        # data['username'] = config_section_parser(self.config, "PARENT5")['username']
        # data['password'] = config_section_parser(self.config, "PARENT5")['password']
        # data['email'] = config_section_parser(self.config, "PARENT5")['email']
        # data['first_name'] = config_section_parser(self.config, "PARENT5")['first_name']
        # data['middle_name'] = config_section_parser(self.config, "PARENT5")['middle_name']
        # data['last_name'] = config_section_parser(self.config, "PARENT5")['last_name']
        # data['status'] = bool(config_section_parser(self.config, "PARENT5")['status'])
        # data['state'] = bool(config_section_parser(self.config, "PARENT5")['state'])
        # data['url'] = "default"
        # data['default_value'] = True
        # data['created_on'] = time.time()
        # data['update_on'] = time.time()

        # print("Create default user: ", data['username'])
        # parent_id5 = self.postgres.insert('account', data, 'id')
        # if parent_id5:
        #     self.log.info("Default user successfully created!")
        # else:

        #     sql_str = "SELECT id FROM account WHERE username='" + data['username'] + "'"
        #     res = self.postgres.query_fetch_one(sql_str)
        #     parent_id5 = res['id']

        # # --------------------------- PARENT ACCOUNT --------------------------- #

        # +++++++++++++++++++++++++++ TUTOR ACCOUNT +++++++++++++++++++++++++++ #
        # TUTOR 1
        data = {}
        data['id'] = self.sha_security.generate_token(False)
        data['username'] = config_section_parser(self.config, "TUTOR1")['username']
        data['password'] = config_section_parser(self.config, "TUTOR1")['password']
        data['email'] = config_section_parser(self.config, "TUTOR1")['email']
        data['first_name'] = config_section_parser(self.config, "TUTOR1")['first_name']
        data['middle_name'] = config_section_parser(self.config, "TUTOR1")['middle_name']
        data['last_name'] = config_section_parser(self.config, "TUTOR1")['last_name']
        data['status'] = bool(config_section_parser(self.config, "TUTOR1")['status'])
        data['state'] = bool(config_section_parser(self.config, "TUTOR1")['state'])
        data['url'] = "default"
        data['default_value'] = True
        data['created_on'] = time.time()
        data['update_on'] = time.time()

        print("Create default user: ", data['username'])
        tutor_id1 = self.postgres.insert('account', data, 'id')
        if tutor_id1:
            self.log.info("Default user successfully created!")
        else:

            sql_str = "SELECT id FROM account WHERE username='" + data['username'] + "'"
            res = self.postgres.query_fetch_one(sql_str)
            tutor_id1 = res['id']

        # TUTOR 2
        data = {}
        data['id'] = self.sha_security.generate_token(False)
        data['username'] = config_section_parser(self.config, "TUTOR2")['username']
        data['password'] = config_section_parser(self.config, "TUTOR2")['password']
        data['email'] = config_section_parser(self.config, "TUTOR2")['email']
        data['first_name'] = config_section_parser(self.config, "TUTOR2")['first_name']
        data['middle_name'] = config_section_parser(self.config, "TUTOR2")['middle_name']
        data['last_name'] = config_section_parser(self.config, "TUTOR2")['last_name']
        data['status'] = bool(config_section_parser(self.config, "TUTOR2")['status'])
        data['state'] = bool(config_section_parser(self.config, "TUTOR2")['state'])
        data['url'] = "default"
        data['default_value'] = True
        data['created_on'] = time.time()
        data['update_on'] = time.time()

        print("Create default user: ", data['username'])
        tutor_id2 = self.postgres.insert('account', data, 'id')
        if tutor_id2:
            self.log.info("Default user successfully created!")
        else:

            sql_str = "SELECT id FROM account WHERE username='" + data['username'] + "'"
            res = self.postgres.query_fetch_one(sql_str)
            tutor_id2 = res['id']

        # TUTOR 3
        data = {}
        data['id'] = self.sha_security.generate_token(False)
        data['username'] = config_section_parser(self.config, "TUTOR3")['username']
        data['password'] = config_section_parser(self.config, "TUTOR3")['password']
        data['email'] = config_section_parser(self.config, "TUTOR3")['email']
        data['first_name'] = config_section_parser(self.config, "TUTOR3")['first_name']
        data['middle_name'] = config_section_parser(self.config, "TUTOR3")['middle_name']
        data['last_name'] = config_section_parser(self.config, "TUTOR3")['last_name']
        data['status'] = bool(config_section_parser(self.config, "TUTOR3")['status'])
        data['state'] = bool(config_section_parser(self.config, "TUTOR3")['state'])
        data['url'] = "default"
        data['default_value'] = True
        data['created_on'] = time.time()
        data['update_on'] = time.time()

        print("Create default user: ", data['username'])
        tutor_id3 = self.postgres.insert('account', data, 'id')
        if tutor_id3:
            self.log.info("Default user successfully created!")
        else:

            sql_str = "SELECT id FROM account WHERE username='" + data['username'] + "'"
            res = self.postgres.query_fetch_one(sql_str)
            tutor_id3 = res['id']

        # TUTOR 4
        data = {}
        data['id'] = self.sha_security.generate_token(False)
        data['username'] = config_section_parser(self.config, "TUTOR4")['username']
        data['password'] = config_section_parser(self.config, "TUTOR4")['password']
        data['email'] = config_section_parser(self.config, "TUTOR4")['email']
        data['first_name'] = config_section_parser(self.config, "TUTOR4")['first_name']
        data['middle_name'] = config_section_parser(self.config, "TUTOR4")['middle_name']
        data['last_name'] = config_section_parser(self.config, "TUTOR4")['last_name']
        data['status'] = bool(config_section_parser(self.config, "TUTOR4")['status'])
        data['state'] = bool(config_section_parser(self.config, "TUTOR4")['state'])
        data['url'] = "default"
        data['default_value'] = True
        data['created_on'] = time.time()
        data['update_on'] = time.time()

        print("Create default user: ", data['username'])
        tutor_id4 = self.postgres.insert('account', data, 'id')
        if tutor_id4:
            self.log.info("Default user successfully created!")
        else:

            sql_str = "SELECT id FROM account WHERE username='" + data['username'] + "'"
            res = self.postgres.query_fetch_one(sql_str)
            tutor_id4 = res['id']

        # TUTOR 5
        data = {}
        data['id'] = self.sha_security.generate_token(False)
        data['username'] = config_section_parser(self.config, "TUTOR5")['username']
        data['password'] = config_section_parser(self.config, "TUTOR5")['password']
        data['email'] = config_section_parser(self.config, "TUTOR5")['email']
        data['first_name'] = config_section_parser(self.config, "TUTOR5")['first_name']
        data['middle_name'] = config_section_parser(self.config, "TUTOR5")['middle_name']
        data['last_name'] = config_section_parser(self.config, "TUTOR5")['last_name']
        data['status'] = bool(config_section_parser(self.config, "TUTOR5")['status'])
        data['state'] = bool(config_section_parser(self.config, "TUTOR5")['state'])
        data['url'] = "default"
        data['default_value'] = True
        data['created_on'] = time.time()
        data['update_on'] = time.time()

        print("Create default user: ", data['username'])
        tutor_id5 = self.postgres.insert('account', data, 'id')
        if tutor_id5:
            self.log.info("Default user successfully created!")
        else:

            sql_str = "SELECT id FROM account WHERE username='" + data['username'] + "'"
            res = self.postgres.query_fetch_one(sql_str)
            tutor_id5 = res['id']

        # --------------------------- TUTOR ACCOUNT --------------------------- #

        # +++++++++++++++++++++++++++ ACCOUNT ROLE +++++++++++++++++++++++++++ #
        # MANAGER
        temp = {}
        temp['account_id'] = account_id1
        temp['role_id'] = role_id
        self.postgres.insert('account_role', temp)

        # STUDENT 1
        temp = {}
        temp['account_id'] = student_id1
        temp['role_id'] = student_role_id
        self.postgres.insert('account_role', temp)

        # STUDENT 2
        temp = {}
        temp['account_id'] = student_id2
        temp['role_id'] = student_role_id
        self.postgres.insert('account_role', temp)

        # STUDENT 3
        temp = {}
        temp['account_id'] = student_id3
        temp['role_id'] = student_role_id
        self.postgres.insert('account_role', temp)

        # STUDENT 4
        temp = {}
        temp['account_id'] = student_id4
        temp['role_id'] = student_role_id
        self.postgres.insert('account_role', temp)

        # STUDENT 5
        temp = {}
        temp['account_id'] = student_id5
        temp['role_id'] = student_role_id
        self.postgres.insert('account_role', temp)

        # # PARENT 1
        # temp = {}
        # temp['account_id'] = parent_id1
        # temp['role_id'] = parent_role_id
        # self.postgres.insert('account_role', temp)

        # # PARENT 2
        # temp = {}
        # temp['account_id'] = parent_id2
        # temp['role_id'] = parent_role_id
        # self.postgres.insert('account_role', temp)

        # # PARENT 3
        # temp = {}
        # temp['account_id'] = parent_id3
        # temp['role_id'] = parent_role_id
        # self.postgres.insert('account_role', temp)

        # # PARENT 4
        # temp = {}
        # temp['account_id'] = parent_id4
        # temp['role_id'] = parent_role_id
        # self.postgres.insert('account_role', temp)

        # # PARENT 5
        # temp = {}
        # temp['account_id'] = parent_id5
        # temp['role_id'] = parent_role_id
        # self.postgres.insert('account_role', temp)

        # TUTOR 1
        temp = {}
        temp['account_id'] = tutor_id1
        temp['role_id'] = tutor_role_id
        self.postgres.insert('account_role', temp)

        # TUTOR 2
        temp = {}
        temp['account_id'] = tutor_id2
        temp['role_id'] = tutor_role_id
        self.postgres.insert('account_role', temp)

        # TUTOR 3
        temp = {}
        temp['account_id'] = tutor_id3
        temp['role_id'] = tutor_role_id
        self.postgres.insert('account_role', temp)

        # TUTOR 4
        temp = {}
        temp['account_id'] = tutor_id4
        temp['role_id'] = tutor_role_id
        self.postgres.insert('account_role', temp)

        # TUTOR 5
        temp = {}
        temp['account_id'] = tutor_id5
        temp['role_id'] = tutor_role_id
        self.postgres.insert('account_role', temp)
        # --------------------------- ACCOUNT ROLE --------------------------- #

        # +++++++++++++++++++++++++++ ROLE PERMISSION +++++++++++++++++++++++++++ #
        # MANAGER
        temp = {}
        temp['role_id'] = role_id
        temp['permission_id'] = permission_id
        self.postgres.insert('role_permission', temp)

        # STUDENT
        temp = {}
        temp['role_id'] = student_role_id
        temp['permission_id'] = permission_id1
        self.postgres.insert('role_permission', temp)

        # PARENT
        temp = {}
        temp['role_id'] = parent_role_id
        temp['permission_id'] = permission_id2
        self.postgres.insert('role_permission', temp)

        # TUTOR
        temp = {}
        temp['role_id'] = tutor_role_id
        temp['permission_id'] = permission_id3
        self.postgres.insert('role_permission', temp)
        # --------------------------- ROLE PERMISSION --------------------------- #

        if prod_flag:

            return 1

        # +++++++++++++++++++++++++++ WHAT TO DO +++++++++++++++++++++++++++ #

        sql_str = "SELECT what_to_do_id FROM what_to_do WHERE"
        sql_str += " page ='default'"
        what_to_do_id = self.postgres.query_fetch_one(sql_str)

        if not what_to_do_id:

            data = {}
            data['what_to_do_id'] = self.sha_security.generate_token(False)
            data['what_to_do_name'] = "default"
            data['page'] = "default"

            data['description'] = "Lorem ipsum dolor sit amet, consectetur "
            data['description'] += "adipiscing elit, sed do eiusmod tempor "
            data['description'] += "incididunt ut labore et dolore magna aliqua."

            data['status'] = True
            data['created_on'] = time.time()
            self.postgres.insert('what_to_do', data)

        # --------------------------- WHAT TO DO --------------------------- #

        # +++++++++++++++++++++++++++ HELP +++++++++++++++++++++++++++ #

        sql_str = "SELECT help_id FROM help WHERE"
        sql_str += " page ='default'"
        help_id = self.postgres.query_fetch_one(sql_str)

        if not help_id:

            data = {}
            data['help_id'] = self.sha_security.generate_token(False)
            data['help_name'] = "default"
            data['page'] = "default"
            data['url'] = "default"

            data['description'] = "Lorem ipsum dolor sit amet, consectetur "
            data['description'] += "adipiscing elit, sed do eiusmod tempor "
            data['description'] += "incididunt ut labore et dolore magna aliqua."

            data['status'] = True
            data['created_on'] = time.time()
            self.postgres.insert('help', data)

        # --------------------------- HELP --------------------------- #

        # +++++++++++++++++++++++++++ COURSE +++++++++++++++++++++++++++ #
        course_path = str(pathlib.Path().absolute())
        course_path += '/csv/course.csv'

        if os.path.isfile(course_path):

            reader = csv.DictReader(open(course_path))

            for row in reader:

                sql_str = "SELECT course_id FROM course WHERE"
                sql_str += " course_name ='{0}' AND".format(row['course_name'])
                sql_str += " description ='{0}'".format(row['description'])
                course_id = self.postgres.query_fetch_one(sql_str)

                if course_id:

                    continue

                data = {}
                data['course_id'] = self.sha_security.generate_token(False)
                data['course_name'] = row['course_name']
                data['description'] = row['description']
                data['requirements'] = row['requirements']
                data['difficulty_level'] = row['difficulty_level']
                data['status'] = row['requirements'].upper() == 'TRUE'
                data['created_on'] = time.time()
                self.postgres.insert('course', data)
        # --------------------------- COURSE --------------------------- #

        # +++++++++++++++++++++++++++ NOTIFICATION +++++++++++++++++++++++++++ #

        student_ids = [student_id1, student_id2, student_id3, student_id4, student_id5]
        for student_id in student_ids:

            sql_str = "SELECT account_id FROM notifications WHERE"
            sql_str += " account_id='{0}'".format(student_id)

            notif_types = ['reminders', 'new medals', 'new levels', 'new tasks']

            if not self.postgres.query_fetch_one(sql_str):

                for _ in range(0, random.randrange(3, 9)):

                    notification_type = random.choice(notif_types)

                    data = {}
                    data['notification_id'] = self.sha_security.generate_token(False)
                    data['account_id'] = student_id
                    data['notification_name'] = notification_type
                    data['notification_type'] = notification_type

                    data['description'] = "Lorem ipsum dolor sit amet, consectetur "
                    data['description'] += "adipiscing elit, sed do eiusmod tempor "
                    data['description'] += "incididunt ut labore et dolore magna aliqua."

                    data['seen_by_user'] = False
                    data['created_on'] = time.time()
                    self.postgres.insert('notifications', data)

        # --------------------------- NOTIFICATION --------------------------- #

        # DUMMY QUESTIONS
        self.create_questions('/sample_datas/FITBT.csv', 'FITBT')
        self.create_questions('/sample_datas/FITBT2.csv', 'FITBT')
        self.create_questions('/sample_datas/FITBD.csv', 'FITBD')
        self.create_questions('/sample_datas/MULCH.csv', 'MULCH')
        self.create_questions('/sample_datas/MATCH.csv', 'MATCH')
        self.create_questions('/sample_datas/MULRE.csv', 'MULRE')

        # +++++++++++++++++++++++++++ STUDENT COURSE +++++++++++++++++++++++++++ #
        course_path = str(pathlib.Path().absolute())

        # GET ALL COURSE
        sql_str = "SELECT course_id FROM course"
        sql_str += " WHERE course_name in"
        sql_str += " ('Conceptual Math', 'Contextual Math',"
        sql_str += " 'Algebra', 'Calculus', 'Arithmetic')"
        course_ids = self.postgres.query_fetch_all(sql_str)

        # LOOP ALL COURSE ID
        for course in course_ids:

            # STUDENT 1
            sql_str = "SELECT * FROM student_course WHERE"
            sql_str += " account_id='{0}'".format(student_id1)
            sql_str += " AND course_id='{0}'".format(course['course_id'])
            student_course = self.postgres.query_fetch_all(sql_str)

            if not student_course:
                # BOUND ALL COURSE TO STUDENT
                data = {}
                data['account_id'] = student_id1
                data['course_id'] = course['course_id']
                data['progress'] = 0
                data['expiry_date'] = int(time.time()) + (86400 * 90)
                data['status'] = True
                data['created_on'] = time.time()
                self.postgres.insert('student_course', data)

            # STUDENT 2
            sql_str = "SELECT * FROM student_course WHERE"
            sql_str += " account_id='{0}'".format(student_id2)
            sql_str += " AND course_id='{0}'".format(course['course_id'])
            student_course = self.postgres.query_fetch_all(sql_str)

            if not student_course:
                # BOUND ALL COURSE TO STUDENT
                data = {}
                data['account_id'] = student_id2
                data['course_id'] = course['course_id']
                data['progress'] = 0
                data['expiry_date'] = int(time.time()) + (86400 * 90)
                data['status'] = True
                data['created_on'] = time.time()
                self.postgres.insert('student_course', data)

            # STUDENT 3
            sql_str = "SELECT * FROM student_course WHERE"
            sql_str += " account_id='{0}'".format(student_id3)
            sql_str += " AND course_id='{0}'".format(course['course_id'])
            student_course = self.postgres.query_fetch_all(sql_str)

            if not student_course:
                # BOUND ALL COURSE TO STUDENT
                data = {}
                data['account_id'] = student_id3
                data['course_id'] = course['course_id']
                data['progress'] = 0
                data['expiry_date'] = int(time.time()) + (86400 * 90)
                data['status'] = True
                data['created_on'] = time.time()
                self.postgres.insert('student_course', data)

            # STUDENT 4
            sql_str = "SELECT * FROM student_course WHERE"
            sql_str += " account_id='{0}'".format(student_id4)
            sql_str += " AND course_id='{0}'".format(course['course_id'])
            student_course = self.postgres.query_fetch_all(sql_str)

            if not student_course:
                # BOUND ALL COURSE TO STUDENT
                data = {}
                data['account_id'] = student_id4
                data['course_id'] = course['course_id']
                data['progress'] = 0
                data['expiry_date'] = int(time.time()) + (86400 * 90)
                data['status'] = True
                data['created_on'] = time.time()
                self.postgres.insert('student_course', data)

            # STUDENT 5
            sql_str = "SELECT * FROM student_course WHERE"
            sql_str += " account_id='{0}'".format(student_id5)
            sql_str += " AND course_id='{0}'".format(course['course_id'])
            student_course = self.postgres.query_fetch_all(sql_str)

            if not student_course:
                # BOUND ALL COURSE TO STUDENT
                data = {}
                data['account_id'] = student_id5
                data['course_id'] = course['course_id']
                data['progress'] = 0
                data['expiry_date'] = int(time.time()) + (86400 * 90)
                data['status'] = True
                data['created_on'] = time.time()
                self.postgres.insert('student_course', data)
        # --------------------------- STUDENT COURSE --------------------------- #

        # +++++++++++++++++++++++++++ TUTOR COURSE +++++++++++++++++++++++++++ #
        course_path = str(pathlib.Path().absolute())

        # GET ALL COURSE
        sql_str = "SELECT course_id FROM course"
        sql_str += " WHERE course_name in"
        sql_str += " ('Conceptual Math', 'Contextual Math',"
        sql_str += " 'Algebra', 'Calculus', 'Arithmetic')"
        course_ids = self.postgres.query_fetch_all(sql_str)

        # LOOP ALL COURSE ID
        for course in course_ids:

            # TUTOR 1
            sql_str = "SELECT * FROM tutor_courses WHERE"
            sql_str += " account_id='{0}'".format(tutor_id1)
            sql_str += " AND course_id='{0}'".format(course['course_id'])
            tutor_courses = self.postgres.query_fetch_all(sql_str)

            if not tutor_courses:
                # BOUND ALL COURSE TO TUTOR
                data = {}
                data['account_id'] = tutor_id1
                data['course_id'] = course['course_id']
                data['status'] = True
                data['created_on'] = time.time()
                self.postgres.insert('tutor_courses', data)

            # TUTOR 2
            sql_str = "SELECT * FROM tutor_courses WHERE"
            sql_str += " account_id='{0}'".format(tutor_id2)
            sql_str += " AND course_id='{0}'".format(course['course_id'])
            tutor_courses = self.postgres.query_fetch_all(sql_str)

            if not tutor_courses:
                # BOUND ALL COURSE TO TUTOR
                data = {}
                data['account_id'] = tutor_id2
                data['course_id'] = course['course_id']
                data['status'] = True
                data['created_on'] = time.time()
                self.postgres.insert('tutor_courses', data)

            # TUTOR 3
            sql_str = "SELECT * FROM tutor_courses WHERE"
            sql_str += " account_id='{0}'".format(tutor_id3)
            sql_str += " AND course_id='{0}'".format(course['course_id'])
            tutor_courses = self.postgres.query_fetch_all(sql_str)

            if not tutor_courses:
                # BOUND ALL COURSE TO TUTOR
                data = {}
                data['account_id'] = tutor_id3
                data['course_id'] = course['course_id']
                data['status'] = True
                data['created_on'] = time.time()
                self.postgres.insert('tutor_courses', data)

            # TUTOR 4
            sql_str = "SELECT * FROM tutor_courses WHERE"
            sql_str += " account_id='{0}'".format(tutor_id4)
            sql_str += " AND course_id='{0}'".format(course['course_id'])
            tutor_courses = self.postgres.query_fetch_all(sql_str)

            if not tutor_courses:
                # BOUND ALL COURSE TO TUTOR
                data = {}
                data['account_id'] = tutor_id4
                data['course_id'] = course['course_id']
                data['status'] = True
                data['created_on'] = time.time()
                self.postgres.insert('tutor_courses', data)

            # TUTOR 5
            sql_str = "SELECT * FROM tutor_courses WHERE"
            sql_str += " account_id='{0}'".format(tutor_id5)
            sql_str += " AND course_id='{0}'".format(course['course_id'])
            tutor_courses = self.postgres.query_fetch_all(sql_str)

            if not tutor_courses:
                # BOUND ALL COURSE TO TUTOR
                data = {}
                data['account_id'] = tutor_id5
                data['course_id'] = course['course_id']
                data['status'] = True
                data['created_on'] = time.time()
                self.postgres.insert('tutor_courses', data)
        # --------------------------- TUTOR COURSE --------------------------- #

    def create_questions(self, filename, qtype):
        """ CREATE QUESTIONS """

        course_questions_path = str(pathlib.Path().absolute())
        # course_questions_path += '/csv/course_questions.csv'
        course_questions_path += filename

        if os.path.isfile(course_questions_path):

            reader = csv.DictReader(open(course_questions_path))

            for row in reader:

                sql_str = "SELECT course_id FROM course WHERE"
                sql_str += " course_name ='{0}'".format(row['course_name'])
                course_id = self.postgres.query_fetch_one(sql_str)

                if course_id:

                    section_id = self.get_section_id(course_id, row)
                    subsection_id = self.get_subsection_id(course_id['course_id'], section_id, row)
                    exercise_id = self.get_exercise_id(course_id['course_id'], section_id,
                                                       subsection_id, row)

                    data = {}
                    data['course_question_id'] = self.sha_security.generate_token(False)
                    data['course_id'] = course_id['course_id']
                    data['section_id'] = section_id
                    data['subsection_id'] = subsection_id
                    data['exercise_id'] = exercise_id
                    data['question_type'] = row['questionType']
                    data['tags'] = json.dumps(row['tags'].replace("\"", "")[1:-1].split(", "))
                    data['shuffle_options'] = ""
                    data['shuffle_answers'] = ""
                    data['feedback'] = ""
                    array_choice = []

                    if qtype == 'FITBT':

                        ans = "".join(re.findall(r'[^\{$\}]', row['answerContent']))
                        answer = {}
                        answer['answer'] = row['questionContent'].replace("<ans>", str(ans))

                        quest = {}
                        quest['question'] = row['questionContent']

                        data['correct_answer'] = json.dumps(answer)
                        data['question'] = json.dumps(quest)

                    elif qtype == 'FITBD':

                        answer = {}
                        answer['answer'] = row['questionContent']

                        allans = "".join(re.findall(r'[^\{$\}]', row['answerContent'])).split(", ")

                        for ans in allans:

                            correct_answer = answer['answer'].replace("[blank]", ans, 1)
                            answer['answer'] = correct_answer

                        quest = {}
                        quest['question'] = row['questionContent'].replace("[blank]", "<ans>")

                        data['correct_answer'] = json.dumps(answer)
                        data['question'] = json.dumps(quest)

                    elif qtype == 'MULCH':

                        choices = "".join(re.findall(r'[^\{$\}]', row['optionsContent']))
                        choices = choices.split(", ")

                        for choice in choices:

                            array_choice.append(choice)

                        answer = {}
                        answer['answer'] = row['answerContent']

                        quest = {}
                        quest['question'] = row['questionContent']

                        data['correct_answer'] = json.dumps(answer)
                        data['question'] = json.dumps(quest)

                    elif qtype == 'MATCH':

                        data['shuffle_options'] = row['shuffleOptions']
                        data['shuffle_answers'] = row['shuffleAnswers']

                        allans = "".join(re.findall(r'[^\{$\}]', row['answerContent'])).split(", ")
                        answer = {}
                        answer['answer'] = allans

                        quest_data = row['questionContent'].replace("\"", "")
                        allquest = "".join(re.findall(r'[^\{$\}]', quest_data)).split(", ")
                        quest = {}
                        quest['question'] = allquest

                        array_choice = "".join(re.findall(r'[^\{$\}]', row['optionsContent']))
                        array_choice = array_choice.split(", ")
                        data['correct_answer'] = json.dumps(answer)
                        data['question'] = json.dumps(quest)

                    elif qtype == 'MULRE':

                        data['shuffle_options'] = row['shuffleOptions']
                        data['shuffle_answers'] = row['shuffleAnswers']

                        allans = row['answerContent'].replace("\"", "")
                        allans = "".join(re.findall(r'[^\{$\}]', allans)).split(", ")
                        answer = {}
                        answer['answer'] = allans

                        quest = {}
                        quest['question'] = row['questionContent']

                        array_choice = row['optionsContent'].replace("\"", "")
                        array_choice = "".join(re.findall(r'[^\{$\}]', array_choice))
                        array_choice = array_choice.split(", ")
                        data['correct_answer'] = json.dumps(answer)
                        data['question'] = json.dumps(quest)

                    if row['preQuestionContent']:

                        data['description'] = row['preQuestionContent']

                    else:
                        data['description'] = "Lorem ipsum dolor sit amet, consectetur "
                        data['description'] += "adipiscing elit, sed do eiusmod tempor "
                        data['description'] += "incididunt ut labore et dolore magna aliqua."

                    data['choices'] = json.dumps(array_choice)
                    data['correct'] = row['correctFeedback']
                    data['incorrect'] = row['incorectFeedback']
                    data['status'] = row['status'].upper() == ''
                    data['num_eval'] = row['numEval'].upper() == 'TRUE'
                    data['created_on'] = time.time()

                    sql_str = "SELECT course_question_id FROM course_question WHERE"
                    sql_str += " course_id ='{0}'".format(course_id['course_id'])
                    sql_str += "AND section_id ='{0}'".format(section_id)
                    sql_str += "AND exercise_id ='{0}'".format(exercise_id)
                    sql_str += "AND subsection_id ='{0}'".format(subsection_id)
                    sql_str += "AND question ='{0}'".format(data['question'])
                    sql_str += "AND question_type ='{0}'".format(row['questionType'])
                    course_question_id = self.postgres.query_fetch_one(sql_str)

                    sql_str = "SELECT question_id FROM questions WHERE"
                    sql_str += " question='{0}'".format(data['question'])
                    sql_str += " AND question_type='{0}'".format(row['questionType'])
                    sql_str += " AND tags='{0}'".format(data['tags'])
                    response = self.postgres.query_fetch_one(sql_str)

                    question_id = ""

                    if not response:

                        question_id = self.sha_security.generate_token(False)

                        temp = {}
                        temp['question_id'] = question_id
                        temp['question'] = data['question']
                        temp['question_type'] = data['question_type']
                        temp['tags'] = data['tags']
                        temp['choices'] = data['choices']
                        if data['shuffle_options']:
                            temp['shuffle_options'] = data['shuffle_options']
                            temp['shuffle_answers'] = data['shuffle_answers']
                        temp['num_eval'] = data['num_eval']
                        temp['correct_answer'] = data['correct_answer']
                        temp['correct'] = data['correct']
                        temp['incorrect'] = data['incorrect']
                        if data['feedback']:
                            temp['feedback'] = data['feedback']
                        temp['description'] = data['description']
                        temp['status'] = data['status']
                        temp['created_on'] = data['created_on']
                        self.postgres.insert('questions', temp)

                    else:

                        question_id = response['question_id']

                    if not course_question_id:

                        course_question_id = self.postgres.insert('course_question',
                                                                  data, 'course_question_id')

                    else:

                        course_question_id = course_question_id['course_question_id']

                    cquest = {}
                    cquest['question_id'] = question_id
                    cquest['update_on'] = time.time()

                    conditions = []
                    conditions.append({
                        "col": "course_question_id",
                        "con": "=",
                        "val": course_question_id
                    })

                    self.postgres.update('course_question', cquest, conditions)

    def get_section_id(self, course_id, param):
        """ GET SECTION ID """

        section_id = ""

        sql_str = "SELECT section_id FROM section WHERE"
        sql_str += " course_id='{0}'".format(course_id['course_id'])
        sql_str += " AND section_name='{0}'".format(param['section_name'])
        section = self.postgres.query_fetch_one(sql_str)

        if section:

            section_id = section['section_id']

        else:

            data = {}
            data['section_id'] = self.sha_security.generate_token(False)
            data['course_id'] = course_id['course_id']
            data['difficulty_level'] = param['section_difficulty_level']
            data['section_name'] = param['section_name']
            data['description'] = "Lorem ipsum dolor sit amet, consectetur"
            data['description'] += " adipiscing elit, sed do eiusmod tempor"
            data['description'] += " incididunt ut labore et dolore magna aliqua."
            data['status'] = True
            data['created_on'] = int(time.time())

            section_id = self.postgres.insert('section', data, 'section_id')

        return section_id

    def get_subsection_id(self, course_id, section_id, param):
        """ GET SUBSECTION ID """

        subsection_id = ""

        sql_str = "SELECT subsection_id FROM subsection WHERE"
        sql_str += " course_id='{0}'".format(course_id)
        sql_str += " AND section_id='{0}'".format(section_id)
        sql_str += " AND subsection_name='{0}'".format(param['subsection_name'])
        subsection = self.postgres.query_fetch_one(sql_str)

        if subsection:

            subsection_id = subsection['subsection_id']

        else:

            data = {}
            data['subsection_id'] = self.sha_security.generate_token(False)
            data['course_id'] = course_id
            data['section_id'] = section_id
            data['difficulty_level'] = param['subsection_difficulty_level']
            data['subsection_name'] = param['subsection_name']
            data['description'] = "Lorem ipsum dolor sit amet, consectetur"
            data['description'] += " adipiscing elit, sed do eiusmod tempor"
            data['description'] += " incididunt ut labore et dolore magna aliqua."
            data['status'] = True
            data['created_on'] = int(time.time())

            subsection_id = self.postgres.insert('subsection', data, 'subsection_id')

        return subsection_id

    def get_exercise_id(self, course_id, section_id, subsection_id, param):
        """ GET EXERCISE ID """

        exercise_id = ""

        sql_str = "SELECT exercise_id FROM exercise WHERE"
        sql_str += " course_id='{0}'".format(course_id)
        sql_str += " AND section_id='{0}'".format(section_id)
        sql_str += " AND subsection_id='{0}'".format(subsection_id)
        sql_str += " AND exercise_number='{0}'".format(param['exercise_number'])
        exercise = self.postgres.query_fetch_one(sql_str)

        if exercise:

            exercise_id = exercise['exercise_id']

        else:

            data = {}
            data['exercise_id'] = self.sha_security.generate_token(False)
            data['course_id'] = course_id
            data['section_id'] = section_id
            data['subsection_id'] = subsection_id
            data['timed_type'] = 'per_question'
            data['timed_limit'] = 300
            data['text_before_start'] = "Do your computations on a piece of paper."
            data['text_before_start'] += " Do not use a calculator. Good luck!"
            data['text_after_end'] = 'Congrats you finish the exam!'
            data['moving_allowed'] = True
            data['instant_feedback'] = True
            data['editing_allowed'] = True
            data['draw_by_tag'] = True

            if self.shuffled:

                data['shuffled'] = True
                self.shuffled = False

            else:

                data['shuffled'] = False
                self.shuffled = True

            data['exercise_number'] = param['exercise_number']
            data['description'] = "Lorem ipsum dolor sit amet, consectetur"
            data['description'] += " adipiscing elit, sed do eiusmod tempor"
            data['description'] += " incididunt ut labore et dolore magna aliqua."
            data['number_to_draw'] = 10
            data['seed'] = 10
            data['passing_criterium'] = int(data['seed'] / 2)
            data['save_seed'] = True
            data['status'] = True
            data['help'] = True
            data['created_on'] = int(time.time())

            exercise_id = self.postgres.insert('exercise', data, 'exercise_id')

        return exercise_id

    def create_index(self):
        """ CREATE INDEXING """

        return 1

    # def add_skills(self):
    #     """ ADD SKILLS """
    #     sql_str = "SELECT section_name, subsection_name, question, question_type, tags FROM"
    #     sql_str += " course_question INNER JOIN section ON"
    #     sql_str += " section.section_id=course_question.section_id"
    #     sql_str += " INNER JOIN subsection ON"
    #     sql_str += " subsection.subsection_id=course_question.subsection_id"

    #     all_questions = self.postgres.query_fetch_all(sql_str)

    #     for quest in all_questions:

    #         conditions = []

    #         conditions.append({
    #             "col": "question_type",
    #             "con": "=",
    #             "val": quest['question_type']
    #             })

    #         conditions.append({
    #             "col": "question",
    #             "con": "=",
    #             "val": json.dumps(quest['question'])
    #             })

    #         conditions.append({
    #             "col": "tags",
    #             "con": "=",
    #             "val": json.dumps(quest['tags'])
    #             })

    #         data = {}
    #         data['skill'] = "{0} - {1}".format(quest['section_name'], quest['subsection_name'])

    #         self.postgres.update('questions', data, conditions)

    #     return 1

    def add_skills(self):
        """ ADD SKILLS """
        
        skills_path = str(pathlib.Path().absolute())
        skills_path += '/sample_datas/skill_subskills.csv'

        if os.path.isfile(skills_path):

            reader = csv.DictReader(open(skills_path))

            for row in reader:

                sql_str = "SELECT * FROM skills WHERE skill ='{0}'".format(row['Skills'])
                skill = self.postgres.query_fetch_one(sql_str)

                if not skill:

                    data = {}
                    data['skill_id'] = self.sha_security.generate_token(False)
                    data['skill'] = row['Skills']
                    data['created_on'] = time.time()
                    skill_id = self.postgres.insert('skills', data, 'skill_id')

                else:
                    skill_id = skill['skill_id']

                # ADD SUBSKILLS
                sql_str = "SELECT * FROM subskills WHERE subskill ='{0}'".format(row['Subskills'])
                subskill = self.postgres.query_fetch_one(sql_str)

                if not subskill:

                    data = {}
                    data['subskill_id'] = self.sha_security.generate_token(False)
                    data['subskill'] = row['Subskills']
                    data['created_on'] = time.time()
                    subskill_id = self.postgres.insert('subskills', data, 'subskill_id')

                else:
                    subskill_id = subskill['subskill_id']

                if skill_id and subskill_id:
                    sql_str = "SELECT * FROM skill_subskills WHERE"
                    sql_str += " skill_id ='{0}' AND subskill_id ='{1}'".format(skill_id, subskill_id)
                    result = self.postgres.query_fetch_one(sql_str)

                    if result:
                        continue

                    data = {}
                    data['skill_subskill_id'] = self.sha_security.generate_token(False)
                    data['skill_id'] = skill_id
                    data['subskill_id'] = subskill_id
                    self.postgres.insert('skill_subskills', data)
                
        return 1

    def add_subskills(self):
        """ ADD SKILLS """
        sql_str = "SELECT section_name, subsection_name, question, question_type, tags FROM"
        sql_str += " course_question INNER JOIN section ON"
        sql_str += " section.section_id=course_question.section_id"
        sql_str += " INNER JOIN subsection ON"
        sql_str += " subsection.subsection_id=course_question.subsection_id"

        all_questions = self.postgres.query_fetch_all(sql_str)

        for quest in all_questions:

            conditions = []

            conditions.append({
                "col": "question_type",
                "con": "=",
                "val": quest['question_type']
                })

            conditions.append({
                "col": "question",
                "con": "=",
                "val": json.dumps(quest['question'])
                })

            conditions.append({
                "col": "tags",
                "con": "=",
                "val": json.dumps(quest['tags'])
                })

            subskill = []
            not_subskill = ['x', '+', '/', '-', '<=10', '']

            if quest['tags']:

                for sbskll in quest['tags']:

                    if not sbskll in not_subskill:

                        subskill.append(sbskll)

            data = {}
            data['subskill'] = json.dumps(subskill)

            self.postgres.update('questions', data, conditions)

        return 1

    # def add_extend_skills(self):
    #     """ ADD EXTEND SKILLS """

    #     sql_str = "SELECT section_name, subsection_name, question, question_type, tags FROM"
    #     sql_str += " course_question INNER JOIN section ON"
    #     sql_str += " section.section_id=course_question.section_id"
    #     sql_str += " INNER JOIN subsection ON"
    #     sql_str += " subsection.subsection_id=course_question.subsection_id"

    #     all_questions = self.postgres.query_fetch_all(sql_str)

    #     for quest in all_questions:

    #         conditions = []

    #         conditions.append({
    #             "col": "question_type",
    #             "con": "=",
    #             "val": quest['question_type']
    #             })

    #         conditions.append({
    #             "col": "question",
    #             "con": "=",
    #             "val": json.dumps(quest['question'])
    #             })

    #         conditions.append({
    #             "col": "tags",
    #             "con": "=",
    #             "val": json.dumps(quest['tags'])
    #             })

    #         subskill = []
    #         not_subskill = ['x', '+', '/', '-', '<=10', '']

    #         if quest['tags']:

    #             for sbskll in quest['tags']:

    #                 if not sbskll in not_subskill:

    #                     subskill.append(sbskll)

    #         extend_skill = []
    #         new_skill = {}
    #         new_skill['skill'] = "{0} - {1}".format(quest['section_name'], quest['subsection_name'])
    #         new_skill['subskill'] = subskill
    #         extend_skill.append(new_skill)

    #         data = {}
    #         data['extend_skill'] = json.dumps(extend_skill)

    #         self.postgres.update('questions', data, conditions)



    #     return 1


    def add_question_skills(self):
        """ ADD QUESTIONS SKILLS """

        sql_str = " SELECT question_id, skill FROM questions"
        all_questions = self.postgres.query_fetch_all(sql_str)

        if not all_questions:

            return 1

        for quest in all_questions:

            sql_str = "SELECT skill_id FROM skills WHERE"
            sql_str += " skill='{0}'".format(quest['skill'])
            skill = self.postgres.query_fetch_one(sql_str)

            skill_id = ""

            if not skill:

                skill_id = self.sha_security.generate_token(False)
                data = {}
                data['skill_id'] = skill_id
                data['skill'] = quest['skill']
                data['created_on'] = time.time()
                self.postgres.insert('skills', data)

            else:

                skill_id = skill['skill_id']

            sql_str = "SELECT * FROM question_skills WHERE"
            sql_str += " question_id='{0}'".format(quest['question_id'])
            sql_str += " AND skill_id='{0}'".format(skill_id)

            if not self.postgres.query_fetch_one(sql_str):


                data = {}
                data['question_skill_id'] = self.sha_security.generate_token(False)
                data['skill_id'] = skill_id
                data['question_id'] = quest['question_id']
                self.postgres.insert('question_skills', data)

if __name__ == '__main__':

    # INIT CONFIG
    CONFIG = ConfigParser()
    # CONFIG FILE
    CONFIG.read("config/config.cfg")

    SERVER_TYPE = config_section_parser(CONFIG, "SERVER")['server_type']

    if SERVER_TYPE != 'production':
        SETUP = Setup()
        SETUP.main()

    else:

        print("YOU'RE TRYING TO UPDATE LIVE SERVER!!!")
