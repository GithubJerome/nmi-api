"""APP"""
import atexit
from flask import Flask
from flasgger import Swagger
from flask_cors import CORS
from library.log import Log
# from apscheduler.schedulers.background import BackgroundScheduler

# USER CONTROLLER
from controllers.user import login
from controllers.user import logout
from controllers.user import reset_password
from controllers.user import authentication_key
from controllers.user import new_token
from controllers.user import create_user
from controllers.user import user
from controllers.user import user_profile
from controllers.user import update_user
from controllers.user import force_change_password
from controllers.user import delete_user
from controllers.user import set_language
from controllers.user import set_role
from controllers.user import user_by_ids

# SIDEBAR
from controllers.sidebar import sidebar
from controllers.sidebar import update_sidebar

# ROLE
from controllers.role import role

# COURSE CONTROLLER
from controllers.course import course
from controllers.course import create_course
from controllers.course import course_details
from controllers.course import update_course
from controllers.course import delete_course
from controllers.course import course_by_ids
from controllers.course import update_course_sequence

# COURSE STUDENT CONTROLLER
# from controllers.course_student import course_student
# from controllers.course_student import add_course_student
# from controllers.course_student import remove_course_student

# TUTOR CONTROLLER
from controllers.tutor import tutors
from controllers.tutor import tutor_groups
from controllers.tutor import tutor_group_table
from controllers.tutor import tutor_group_students
from controllers.tutor import tutor_course
from controllers.tutor import tutor_course_set
from controllers.tutor import tutor_section
from controllers.tutor import tutor_subsection
from controllers.tutor import tutor_exercise
from controllers.tutor import tutor_summary
from controllers.tutor import tutor_students
from controllers.tutor import tutor_student_exercise
from controllers.tutor import tutor_student_progress
from controllers.tutor import tutor_student_course_progress
from controllers.tutor import tutor_course_requirements
from controllers.tutor import tutor_group_course
from controllers.tutor import tutor_group_course_progress
from controllers.tutor import update_tutor_course_requirements

# STUDENT COURSE CONTROLLER
from controllers.student_course import student_course
from controllers.student_course import course_section
from controllers.student_course import course_subsection
from controllers.student_course import student_exercise
from controllers.student_course import student_course_exercise
from controllers.student_course import update_student_course

# EXERCISE
from controllers.exercise import exercise_question
from controllers.exercise import exercise_answer
from controllers.exercise import exercise_summary
from controllers.exercise import reset_exercise
from controllers.exercise import exercise_overview
from controllers.exercise import reset_student_exercise

from controllers.course_exercise import create_exercise
from controllers.course_exercise import exercise_skill
from controllers.course_exercise import exercise
from controllers.course_exercise import upload as upload_exercise

# TUTOR EXERCISE
from controllers.tutor_exercise import tutor_exercise_answer
from controllers.tutor_exercise import reset_tutor_exercise
from controllers.tutor_exercise import tutor_overview
from controllers.tutor_exercise import tutor_reset_course

# INSTRUCTION
from controllers.instruction import instruction
from controllers.instruction import create_instruction
from controllers.instruction.image import upload as instruction_upload
from controllers.instruction.image import images as instruction_images
from controllers.instruction.image import delete as instruction_delete
from controllers.instruction import view_instruction

# PROGRESS
from controllers.progress import student_skills
from controllers.progress import student_course_progress
from controllers.progress import quick_start
from controllers.progress import course_progress
from controllers.progress import results_overview

# WHAT TO DO
from controllers.what_to_do import what_to_do

# ISSUE
from controllers.issue import create_issue

# NOTIFICATION
from controllers.notification import notification
from controllers.notification import create_notification
from controllers.notification import seen_notification

# QUESTION
from controllers.question import question
from controllers.question import upload as upload_question
from controllers.question import download as download_question_template

# USER CONTROLLER
from controllers.user_group import create_user_group
from controllers.user_group import user_group
from controllers.user_group import delete_user_group
from controllers.user_group import update_user_group
from controllers.user_group import course_requirements
from controllers.user_group import update_course_requirements
from controllers.user_group import set_course_requirements
from controllers.user_group import group_by_ids

# DOWNLOAD
from controllers.download import course_template
from controllers.download import exercise_template
from controllers.download import course_update

# UPLOAD
from controllers.upload import course_template as upload_course_template
from controllers.upload import course_update as upload_course_update
from controllers.upload import io_course_uploader

from controllers.help import create_help
from controllers.help import update_help
from controllers.help import delete_help
from controllers.help import helper

# SKILL
from controllers.skill import skill
from controllers.skill import skills

# TAGS
from controllers.tag import tag

# EXPERIENCE
from controllers.experience import student_experience
from controllers.experience import student_level

# VIDEOS
from controllers.videos import add_video
from controllers.videos import videos
from controllers.videos import delete_videos
from controllers.videos import create_skill_video
from controllers.videos import create_exercise_video
from controllers.videos import create_subsection_video
from controllers.videos import course_videos

# --------------------------------------------------------------
# CRON
# --------------------------------------------------------------
# from controllers.cron import cron_update_student_answer
# from controllers.cron import cron_update_tutor_answer
# from controllers.cron import cron_update_progress

# --------------------------------------------------------------
# IO
# --------------------------------------------------------------
from controllers.io import skill_update

LOG = Log()

APP = Flask(__name__)

CORS(APP)
Swagger(APP)

# --------------------------------------------------------------
# USER
# --------------------------------------------------------------
LOGIN = login.Login()
LOGOUT = logout.Logout()
RESET_PASSWORD = reset_password.ResetPassword()
AUTHENTICATION_KEY = authentication_key.AuthenticationKey()
NEW_TOKEN = new_token.NewToken()
CREATE_USER = create_user.CreateUser()
DELETE_USER = delete_user.DeleteUser()
USER = user.User()
USER_PROFILE = user_profile.UserProfile()
UPDATE_USER = update_user.UpdateUser()
FORCE_CHANGE_PASSWORD = force_change_password.ForceChangePassword()
SET_LANGUAGE = set_language.SetLanguage()
USER_BY_IDs = user_by_ids.UserByIDs()
SET_ROLE = set_role.SetRole()

# USER ROUTE
APP.route('/user/login', methods=['POST'])(LOGIN.login)
APP.route('/user/logout', methods=['POST'])(LOGOUT.logout)
APP.route('/user/reset/password', methods=['PUT'])(RESET_PASSWORD.reset_password)
APP.route('/user/authentication-key', methods=['PUT'])(AUTHENTICATION_KEY.authentication_key)
APP.route('/user/new-token', methods=['PUT'])(NEW_TOKEN.new_token)
APP.route('/user/create', methods=['POST'])(CREATE_USER.create_user)
APP.route('/user/delete', methods=['DELETE'])(DELETE_USER.delete_user)
APP.route('/user/index', methods=['GET'])(USER.user)
APP.route('/user/profile', methods=['GET'])(USER_PROFILE.user_profile)
APP.route('/user/update', methods=['PUT'])(UPDATE_USER.update_user)
APP.route('/user/force/change-password', methods=['PUT'])(FORCE_CHANGE_PASSWORD.force_change_password)
APP.route('/user/set-language', methods=['PUT'])(SET_LANGUAGE.set_language)
APP.route('/user/by-ids', methods=['GET'])(USER_BY_IDs.user_by_ids)
APP.route('/user/set-role', methods=['PUT'])(SET_ROLE.set_role)

# --------------------------------------------------------------
# SIDEBAR
# --------------------------------------------------------------
SIDEBAR = sidebar.Sidebar()
UPDATE_SIDEBAR = update_sidebar.UpdateSidebar()

# ROLE ROUTE
APP.route('/sidebar', methods=['GET'])(SIDEBAR.sidebar)
APP.route('/sidebar/update', methods=['PUT'])(UPDATE_SIDEBAR.update_sidebar)

# --------------------------------------------------------------
# ROLE
# --------------------------------------------------------------
ROLE = role.Role()

# ROLE ROUTE
APP.route('/role/index', methods=['GET'])(ROLE.role)

# --------------------------------------------------------------
# COURSE
# --------------------------------------------------------------
COURSE = course.Course()
CREATE_COURSE = create_course.CreateCourse()
COURSE_DETAILS = course_details.CourseDetails()
UPDATE_COURSE = update_course.UpdateCourse()
DELETE_COURSE = delete_course.DeleteCourse()
COURSE_BY_IDs = course_by_ids.CourseByIDs()
UPDATE_COURSE_SEQUENCE = update_course_sequence.UpdateCourseSequence()

# COURSE ROUTE
APP.route('/course/index', methods=['GET'])(COURSE.course)
APP.route('/course/create', methods=['POST'])(CREATE_COURSE.create_course)
APP.route('/course/details', methods=['GET'])(COURSE_DETAILS.course_details)
APP.route('/course/update', methods=['PUT'])(UPDATE_COURSE.update_course)
APP.route('/course/delete', methods=['DELETE'])(DELETE_COURSE.delete_course)
APP.route('/course/by-ids', methods=['GET'])(COURSE_BY_IDs.course_by_ids)
APP.route('/course/sequence', methods=['PUT'])(UPDATE_COURSE_SEQUENCE.update_course_sequence)

# # --------------------------------------------------------------
# # COURSE
# # --------------------------------------------------------------
# COURSE_STUDENT = course_student.CourseStudent()
# ADD_COURSE_STUDENT = add_course_student.AddCourseStudent()
# REMOVE_COURSE_STUDENT = remove_course_student.RemoveCourseStudent()

# # COURSE ROUTE
# APP.route('/course-student', methods=['GET'])(COURSE_STUDENT.course_student)
# APP.route('/course-student/add', methods=['POST'])(ADD_COURSE_STUDENT.add_course_student)
# APP.route('/course-student/remove', methods=['DELETE'])(REMOVE_COURSE_STUDENT.remove_course_student)

# --------------------------------------------------------------
# STUDENT COURSE
# --------------------------------------------------------------
STUDENT_COURSE = student_course.StudentCourse()
COURSE_SECTION = course_section.CourseSection()
COURSE_SUBSECTION = course_subsection.CourseSubsection()
STUDENT_EXERCISE = student_exercise.StudentExercise()
STUDENT_COURSE_EXERCISE = student_course_exercise.StudentCourseExercise()
UPDATE_STUDENT_COURSE = update_student_course.UpdateStudentCourse()

APP.route('/student/course', methods=['GET'])(STUDENT_COURSE.student_course)
APP.route('/student/course/section', methods=['GET'])(COURSE_SECTION.course_section)
APP.route('/student/course/subsection', methods=['GET'])(COURSE_SUBSECTION.subsection)
APP.route('/student/course/exercise', methods=['GET'])(STUDENT_EXERCISE.student_exercise)
APP.route('/student/course/set', methods=['GET'])(STUDENT_COURSE_EXERCISE.course_exercise)
APP.route('/student/course/update', methods=['GET'])(UPDATE_STUDENT_COURSE.update_course_exercise)

# --------------------------------------------------------------
# TUTOR COURSE
# --------------------------------------------------------------
TUTORS = tutors.Tutors()
TUTOR_GROUPS = tutor_groups.TutorGroups()
TUTOR_GROUP_STUDENTS = tutor_group_students.TutorGroupStudents()
TUTOR_COURSE = tutor_course.TutorCourse()
TUTOR_COURSE_SET = tutor_course_set.TutorCourseSet()
TUTOR_SECTION = tutor_section.TutorSection()
TUTOR_SUBSECTION = tutor_subsection.TutorSubsection()
TUTOR_EXERCISE = tutor_exercise.TutorExercise()
TUTOR_GROUP_TABLE = tutor_group_table.TutorGroupTable()
TUTOR_GROUP_COURSE_PROG = tutor_group_course_progress.TutorGroupCourseProgress()

APP.route('/tutor', methods=['GET'])(TUTORS.tutors)
APP.route('/tutor/groups', methods=['GET'])(TUTOR_GROUPS.tutor_groups)
APP.route('/tutor/group-students', methods=['GET'])(TUTOR_GROUP_STUDENTS.tutor_group_students)
APP.route('/tutor/course', methods=['GET'])(TUTOR_COURSE.tutor_course)
APP.route('/tutor/course/set', methods=['GET'])(TUTOR_COURSE_SET.tutor_course_set)
APP.route('/tutor/course/section', methods=['GET'])(TUTOR_SECTION.tutor_section)
APP.route('/tutor/course/subsection', methods=['GET'])(TUTOR_SUBSECTION.tutor_subsection)
APP.route('/tutor/course/exercise', methods=['GET'])(TUTOR_EXERCISE.tutor_exercise)
APP.route('/tutor/group-table', methods=['GET'])(TUTOR_GROUP_TABLE.tutor_group_table)
APP.route('/tutor/group/progress', methods=['GET'])(TUTOR_GROUP_COURSE_PROG.tutor_group_course_progress)

# --------------------------------------------------------------
# MANAGER COURSE
# --------------------------------------------------------------
APP.route('/manager/course/set', methods=['GET'])(TUTOR_COURSE_SET.tutor_course_set)
APP.route('/manager/course/section', methods=['GET'])(TUTOR_SECTION.tutor_section)
APP.route('/manager/course/subsection', methods=['GET'])(TUTOR_SUBSECTION.tutor_subsection)
APP.route('/manager/course/exercise', methods=['GET'])(TUTOR_EXERCISE.tutor_exercise)

# --------------------------------------------------------------
# COURSE EXERCISE
# --------------------------------------------------------------
CREATE_EXERCISE = create_exercise.CreateExercise()
EXERCISE_SKILL = exercise_skill.ExerciseSkill()
EXERCISE = exercise.Exercise()
UPLOAD_EXERCISE = upload_exercise.UploadExercise()

APP.route('/exercise/create', methods=['POST'])(CREATE_EXERCISE.create_exercise)
APP.route('/exercise/skill', methods=['GET'])(EXERCISE_SKILL.exercise_skill)
APP.route('/exercise', methods=['GET'])(EXERCISE.exercise)
APP.route('/upload/exercise', methods=['POST'])(UPLOAD_EXERCISE.upload_exercise)

# --------------------------------------------------------------
# EXERCISE
# --------------------------------------------------------------
EXERCISE_QUESTION = exercise_question.ExerciseQuestionnaire()
EXERCISE_ANSWER = exercise_answer.ExerciseAnswer()
EXERCISE_SUMMARY = exercise_summary.ExerciseSummary()
RESET_EXERCISE = reset_exercise.ResetExercise()
EXERCISE_OVERVIEW = exercise_overview.ExerciseOverview()
RESET_STUDENT_EXERCISE = reset_student_exercise.ResetStudentExercise()

APP.route('/exercise/question', methods=['GET'])(EXERCISE_QUESTION.exercise_question)
APP.route('/exercise/answer', methods=['POST'])(EXERCISE_ANSWER.exercise_answer)
APP.route('/exercise/overview', methods=['GET'])(EXERCISE_OVERVIEW.exercise_overview)
APP.route('/exercise/summary', methods=['GET'])(EXERCISE_SUMMARY.summary)
APP.route('/exercise/reset', methods=['GET'])(RESET_EXERCISE.reset_exercise)
APP.route('/reset/student/exercise', methods=['GET'])(RESET_STUDENT_EXERCISE.reset_student_exercise)


# --------------------------------------------------------------
# TUTOR EXERCISE
# --------------------------------------------------------------
TUTOR_ANSWER = tutor_exercise_answer.TutorAnswer()
RESET_TUTOR_EXERCISE = reset_tutor_exercise.ResetTutorExercise()
TUTOR_OVERVIEW = tutor_overview.TutorResultsOverview()
TUTOR_RESET_COURSE = tutor_reset_course.TutorResetCourse()
TUTOR_SUMMARY = tutor_summary.TutorSummary()
TUTOR_STUDENTS = tutor_students.TutorStudents()
TUTOR_STUDENT_PROGRESS = tutor_student_progress.TutorStudentProgress()
TUTOR_STUDENT_COURSE_PROG = tutor_student_course_progress.TutorStudentCourseProgress()
TUTORCR = tutor_course_requirements.TutorCourseRequirements()
TUTOR_GROUP_COURSE = tutor_group_course.TutorGroupCourse()
UTUTORCR = update_tutor_course_requirements.UpdateTutorCourseRequirements()
TUTOR_STUDENT_EXERCISE = tutor_student_exercise.TutorStudentExercise()

APP.route('/tutor/exercise/answer', methods=['POST'])(TUTOR_ANSWER.tutor_answer)
APP.route('/tutor/exercise/reset', methods=['GET'])(RESET_TUTOR_EXERCISE.reset_tutor_exercise)
APP.route('/tutor/exercise/overview', methods=['GET'])(TUTOR_OVERVIEW.tutor_results_overview)
APP.route('/reset/tutor/course', methods=['GET'])(TUTOR_RESET_COURSE.reset_tutor_course)
APP.route('/tutor/summary', methods=['GET'])(TUTOR_SUMMARY.tutor_summary)
APP.route('/tutor/students', methods=['GET'])(TUTOR_STUDENTS.tutor_students)
APP.route('/tutor/student-progress', methods=['GET'])(TUTOR_STUDENT_PROGRESS.tutor_student_progress)
APP.route('/tutor/student-course-progress', methods=['GET'])(TUTOR_STUDENT_COURSE_PROG.tutor_student_course_progress)
APP.route('/tutor/course-requirements', methods=['GET'])(TUTORCR.tutor_course_requirements)
APP.route('/tutor/group/course', methods=['GET'])(TUTOR_GROUP_COURSE.tutor_group_course)
APP.route('/tutor/course-requirements-update', methods=['PUT'])(UTUTORCR.update_tutor_course_requirements)
APP.route('/tutor/student/exercise', methods=['GET'])(TUTOR_STUDENT_EXERCISE.tutor_student_exercise)
# --------------------------------------------------------------
# MANAGER EXERCISE
# --------------------------------------------------------------
APP.route('/manager/summary', methods=['GET'])(TUTOR_SUMMARY.tutor_summary)
APP.route('/manager/exercise/reset', methods=['GET'])(RESET_TUTOR_EXERCISE.reset_tutor_exercise)
APP.route('/manager/exercise/answer', methods=['POST'])(TUTOR_ANSWER.tutor_answer)
APP.route('/manager/course-requirements', methods=['GET'])(TUTORCR.tutor_course_requirements)
APP.route('/manager/course-requirements-update', methods=['PUT'])(UTUTORCR.update_tutor_course_requirements)

# --------------------------------------------------------------
# EXPERIENCE
# --------------------------------------------------------------
STUDENT_EXPERIENCE = student_experience.StudentExperience()
STUDENT_LEVEL = student_level.StudentLevel()

APP.route('/student-experience', methods=['GET'])(STUDENT_EXPERIENCE.student_experience)
APP.route('/student-level', methods=['GET'])(STUDENT_LEVEL.student_level)

# --------------------------------------------------------------
# INSTRUCTION
# --------------------------------------------------------------
INSTRUCTION = instruction.Instruction()
CREATE_INSTRUCTION = create_instruction.CreateInstruction()
INSTRUCTION_UPLOAD = instruction_upload.Upload()
INSTRUCTION_IMAGES = instruction_images.InstructionImages()
INSTRUCTION_DELETE = instruction_delete.DeleteInstructionImage()
VIEW_INSTRUCTION = view_instruction.ViewInstruction()

APP.route('/instruction', methods=['GET'])(INSTRUCTION.instruction)
APP.route('/instruction/create-instruction', methods=['POST'])(CREATE_INSTRUCTION.create_instruction)
APP.route('/instruction/image/upload', methods=['POST'])(INSTRUCTION_UPLOAD.instruction_upload)
APP.route('/instruction/image/list', methods=['GET'])(INSTRUCTION_IMAGES.get_images)
APP.route('/instruction/image/delete', methods=['DELETE'])(INSTRUCTION_DELETE.delete_instruction_image)
APP.route('/instruction/view', methods=['POST'])(VIEW_INSTRUCTION.view_instruction)

# --------------------------------------------------------------
# PROGRESS
# --------------------------------------------------------------
STUDENT_SKILLS = student_skills.StudentSkills()
STUDENT_COURSE_PROGRESS = student_course_progress.StudentCourseProgress()
QUICK_START = quick_start.QuickStart()
COURSE_PROGRESS = course_progress.CourseProgress()
RESULTS_OVERVIEW = results_overview.ResultsOverview()

# PROGRESS ROUTE
APP.route('/progress/student/skills', methods=['GET'])(STUDENT_SKILLS.student_skills)
APP.route('/progress/student/course', methods=['GET'])(STUDENT_COURSE_PROGRESS.student_course_progress)
APP.route('/quick-start', methods=['GET'])(QUICK_START.quick_start)
APP.route('/course/progress', methods=['GET'])(COURSE_PROGRESS.course_progress)
APP.route('/results/overview', methods=['GET'])(RESULTS_OVERVIEW.results_overview)

# --------------------------------------------------------------
# USER GROUP
# --------------------------------------------------------------
CREATE_USER_GROUP = create_user_group.CreateUserGroup()
USER_GROUP = user_group.UserGroup()
DELETE_USER_GROUP = delete_user_group.DeleteUserGroup()
UPDATE_USER_GROUP = update_user_group.UpdateUserGroup()
COURSE_REQUIREMENTS = course_requirements.CourseRequirements()
UPDATE_COURSE_REQUIREMENTS = update_course_requirements.UpdateCourseRequirements()
SET_COURSE_REQUIREMENTS = set_course_requirements.SetCourseRequirements()
GROUP_BY_IDS = group_by_ids.GroupByIDs()

# USER GROUP ROUTE
APP.route('/user-group/create-user-group', methods=['POST'])(CREATE_USER_GROUP.create_user_group)
APP.route('/user-group', methods=['GET'])(USER_GROUP.user_group)
APP.route('/user-group/delete', methods=['DELETE'])(DELETE_USER_GROUP.delete_user_group)
APP.route('/user-group/update', methods=['PUT'])(UPDATE_USER_GROUP.update_user_group)
APP.route('/user-group/course-requirements', methods=['GET'])(COURSE_REQUIREMENTS.course_requirements)
APP.route('/user-group/course-requirements-update', methods=['PUT'])(UPDATE_COURSE_REQUIREMENTS.update_course_requirements)
APP.route('/user-group/set-requirements', methods=['GET'])(SET_COURSE_REQUIREMENTS.set_course_requirements)
APP.route('/user-group/by-ids', methods=['GET'])(GROUP_BY_IDS.group_by_ids)

# --------------------------------------------------------------
# WHAT TO DO
# --------------------------------------------------------------
WHAT_TO_DO = what_to_do.WhatToDo()

APP.route('/what-to-do', methods=['GET'])(WHAT_TO_DO.what_to_do)

# --------------------------------------------------------------
# ISSUE
# --------------------------------------------------------------
CREATE_ISSUE = create_issue.CreateIssue()

APP.route('/issue/create', methods=['POST'])(CREATE_ISSUE.create_issue)

# --------------------------------------------------------------
# NOTIFICATION
# --------------------------------------------------------------
NOTIFICATION = notification.Notification()
CREATE_NOTIFICATION = create_notification.CreateNotification()
SEEN_NOTIFICATION = seen_notification.UpdateNotification()

APP.route('/notification', methods=['GET'])(NOTIFICATION.notification)
APP.route('/notification/create', methods=['POST'])(CREATE_NOTIFICATION.create_notification)
APP.route('/notification/seen', methods=['PUT'])(SEEN_NOTIFICATION.update_notification)

# --------------------------------------------------------------
# QUESTION
# --------------------------------------------------------------
QUESTION = question.Question()
UPLOAD_QUESTION = upload_question.UploadQuestions()
QUESTION_TEMPLATE = download_question_template.QuestionTemplate()

APP.route('/questions', methods=['GET'])(QUESTION.question)
APP.route('/upload/questions', methods=['POST'])(UPLOAD_QUESTION.upload_questions)
APP.route('/download/question-template', methods=['GET'])(QUESTION_TEMPLATE.question_template)

# --------------------------------------------------------------
# DOWNLOAD
# --------------------------------------------------------------
COURSE_TEMPLATE = course_template.CourseTemplate()
EXERCISE_TEMPLATE = exercise_template.ExerciseTemplate()
COURSE_UPDATE = course_update.CourseUpdate()

# DOWNLOAD ROUTE
APP.route('/download/course-template', methods=['GET'])(COURSE_TEMPLATE.course_template)
APP.route('/download/exercise-template', methods=['GET'])(EXERCISE_TEMPLATE.exercise_template)
APP.route('/download/course-update', methods=['GET'])(COURSE_UPDATE.course_update)

# --------------------------------------------------------------
# UPLOAD
# --------------------------------------------------------------
UPLOAD_COURSE_TEMPLATE = upload_course_template.UploadCourseTemplate()
UPLOAD_COURSE_UPDATE = upload_course_update.UploadCourseUpdate()
IO_COURSE_UPLOADER = io_course_uploader.IOCourseUploader()

# UPLOAD ROUTE
APP.route('/upload/course-template', methods=['POST'])(UPLOAD_COURSE_TEMPLATE.upload_course_template)
APP.route('/upload/course-update', methods=['POST'])(UPLOAD_COURSE_UPDATE.upload_course_update)
APP.route('/upload/io-course-uploader', methods=['POST'])(IO_COURSE_UPLOADER.io_course_uploader)

# --------------------------------------------------------------
# HELP
# --------------------------------------------------------------
HELPER = helper.Help()
CREATE_HELP = create_help.CreateHelp()
UPDATE_HELP = update_help.UpdateHep()
DELETE_HELP = delete_help.DeleteHelp()

# HELP ROUTE
APP.route('/help/create', methods=['POST'])(CREATE_HELP.create_help)
APP.route('/help/update', methods=['PUT'])(UPDATE_HELP.update_help)
APP.route('/help', methods=['GET'])(HELPER.help)
APP.route('/help/delete', methods=['DELETE'])(DELETE_HELP.delete_help)

# --------------------------------------------------------------
# SKILL
# --------------------------------------------------------------
SKILL = skill.Skill()
SKILLS = skills.Skills()

# UPLOAD ROUTE
APP.route('/skill', methods=['GET'])(SKILL.skill)
APP.route('/skills', methods=['GET'])(SKILLS.skills)

# --------------------------------------------------------------
# TAG
# --------------------------------------------------------------
TAG = tag.Tag()

# UPLOAD ROUTE
APP.route('/tags', methods=['GET'])(TAG.tag)

# --------------------------------------------------------------
# VIDEOS
# --------------------------------------------------------------
ADD_VIDEO = add_video.AddVideo()
VIDEOS = videos.Videos()
DELETE_VIDEOS = delete_videos.DeleteVideos()

# UPLOAD ROUTE
APP.route('/videos', methods=['GET'])(VIDEOS.videos)
APP.route('/videos/add', methods=['POST'])(ADD_VIDEO.add_video)
APP.route('/videos/delete', methods=['DELETE'])(DELETE_VIDEOS.delete_videos)

# --------------------------------------------------------------
# LINK VIDEOS
# --------------------------------------------------------------

COURSE_VIDEOS = course_videos.CourseVideos()
CREATE_SKILL_VIDEO = create_skill_video.CreateSkillVideos()
CREATE_EXERCISE_VIDEO = create_exercise_video.CreateExerciseVideo()
CREATE_SUBSECTION_VIDEO = create_subsection_video.CreateSubsectionVideo()

APP.route('/video/course', methods=['GET'])(COURSE_VIDEOS.course_videos)
APP.route('/video/skill/create', methods=['POST'])(CREATE_SKILL_VIDEO.create_skill_videos)
APP.route('/video/exercise/create', methods=['POST'])(CREATE_EXERCISE_VIDEO.create_exercise_video)
APP.route('/video/subsection/create', methods=['POST'])(CREATE_SUBSECTION_VIDEO.create_subsection_video)

# --------------------------------------------------------------
# IO
# --------------------------------------------------------------
SKILL_UPDATES = skill_update.SkillUpdates()

# UPLOAD ROUTE
APP.route('/io/skill-updates', methods=['GET'])(SKILL_UPDATES.skill_updates)

# --------------------------------------------------------------
# CRON
# --------------------------------------------------------------
# LOG.info("Cron will start in a while!")
# CRON = BackgroundScheduler()

# def goodbye():

#     """Exit Cron"""
#     CRON.shutdown()

# REPORTS = reports.Reports()
# CRON_STUDENT_ANSWER = cron_update_student_answer.UpdateStudentAnswer()
# CRON_TUTOR_ANSWER = cron_update_tutor_answer.UpdateTutorAnswer()
# CRON_UPDATE_PROGRESS = cron_update_progress.UpdateProgress()

# CRON.add_job(func=CRON_STUDENT_ANSWER.update_student_iscorrect, trigger="interval", minutes=5)
# CRON.add_job(func=CRON_TUTOR_ANSWER.update_tutor_iscorrect, trigger="interval", minutes=5)
# CRON.add_job(func=CRON_UPDATE_PROGRESS.update_student_progress, trigger="interval", minutes=5)

# CRON.start()
# atexit.register(goodbye)

if __name__ == '__main__':

    APP.run(host='0.0.0.0', port=8080)
