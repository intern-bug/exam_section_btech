from django.contrib.auth.decorators import login_required, user_passes_test
from MTsuperintendent.user_access_test import is_Associate_Dean, grade_challenge_status_access
from django.shortcuts import render
from MTco_ordinator.models import MTFacultyAssignment, MTRollLists 
from ADPGDB.models import MTGradeChallenge
from MThod.models import MTCoordinator
from MTfaculty.models import MTMarks_Staging, MTAttendance_Shortage, MTStudentGrades_Staging
from ADPGDB.forms import GradeChallengeForm, GradeChallengeStatusForm
from MTExamStaffDB.models import MTIXGradeStudents
from MTfaculty.models import MTGradesThreshold


@login_required(login_url="/login/")
@user_passes_test(is_Associate_Dean)
def grade_challenge(request):
    user = request.user
    co_ordinator = MTCoordinator.objects.filter(User=user, RevokeDate__isnull=True)
    if request.method == 'POST':
        form = GradeChallengeForm(co_ordinator, request.POST)
        if request.POST.get('submit'):
            if request.POST.get('regID') and request.POST.get('subject') and request.POST.get('regd_no')\
                and request.POST.get('exam-type') and request.POST.get('mark'):
                required_marks_obj = MTMarks_Staging.objects.filter(Registration__RegNo=request.POST.get('regd_no'), Registration__RegEventId=request.POST.get('regID'),\
                    Registration__sub_id=request.POST.get('subject')).first()
                required_grade_obj = MTStudentGrades_Staging.objects.filter(Registration=required_marks_obj.Registration).first()
                exam_outer_index = request.POST.get('exam-type').split(',')[0]
                exam_inner_index = request.POST.get('exam-type').split(',')[1]
                grade_challenge_obj = MTGradeChallenge.objects.filter(Registration=required_marks_obj.Registration)
                if grade_challenge_obj:
                    grade_challenge_obj = grade_challenge_obj.first()
                else:
                    grade_challenge_obj = MTGradeChallenge(Registration=required_marks_obj.Registration, prev_marks=required_marks_obj.Marks, \
                        prev_grade=required_grade_obj.Grade)
                marks_string = required_marks_obj.Marks.split(',')
                marks = [mark.split('+') for mark in marks_string]
                marks[exam_outer_index][exam_inner_index] = str(request.POST.get('mark'))
                marks = ['+'.join(mark) for mark in marks]
                marks_string = ','.join(marks)
                required_marks_obj.Marks = marks_string
                required_marks_obj.TotalMarks = required_marks_obj.get_total_marks()
                grade_challenge_obj.updated_marks = required_marks_obj.Marks
                required_marks_obj.save()

                attendance_shortage = MTAttendance_Shortage.objects.filter(Registration=required_marks_obj.Registration)

                ix_grades = MTIXGradeStudents.objects.filter(Registration=required_marks_obj.Registration)


                if attendance_shortage:
                    grade_challenge_obj.updated_grade = 'R'
                    required_grade_obj.Grade = 'R'
                    required_grade_obj.AttGrade = 'X'
                    required_grade_obj.save()
                
                elif ix_grades:
                    grade_challenge_obj.updated_grade = ix_grades.Grade
                    required_grade_obj.Grade = ix_grades.Grade
                    required_grade_obj.save()
                
                else:
                    if MTGradesThreshold.objects.filter(Subject_id=request.POST.get('subject'), RegEventId_id=request.POST.get('regEvent'), uniform_grading=True).exists():
                        thresholds = MTGradesThreshold.objects.filter(Subject_id=request.POST.get('subject'), RegEventId_id=request.POST.get('regEvent'), uniform_grading=True).order_by('-ThresholdMark')
                    else:
                        roll_list_obj = MTRollLists.objects.filter(Student__RegNo=request.POST.get('regd_no'), RegEventId_id=request.POST.get('regID'))
                        thresholds = MTGradesThreshold.objects.filter(Subject_id=request.POST.get('subject'), RegEventId_id=request.POST.get('regEvent'), unifrom_grading=False, Section=roll_list_obj.Section).order_by('-ThresholdMark')

                    for threshold in thresholds:
                        if required_marks_obj.TotalMarks >= threshold.ThresholdMark:
                            required_grade_obj.Grade = threshold.Grade
                            grade_challenge_obj.Grade = threshold.Grade
                            required_grade_obj.save()
                
                grade_challenge_obj.save()

                msg = 'Grade Challenge result for {} is updated successfully'.format(request.POST.get('regd_no'))

                return render(request, 'ADPGDB/GradeChallenge.html', {'form':form, 'msg':msg})
                
        elif request.POST.get('regID') and request.POST.get('subject') and request.POST.get('regd_no'):
            mark_obj = MTMarks_Staging.objects.filter(Registration__RegEventId=request.POST.get('regID'), Registration__subject=request.POST.get('subject'))
            return render(request, 'ADPGDB/GradeChallenge.html', {'form':form, 'mark':mark_obj})
    else:
        form = GradeChallengeForm(co_ordinator=co_ordinator)
    return render(request, 'ADPGDB/GradeChallenge.html', {'form':form})

@login_required(login_url="/login/")
@user_passes_test(grade_challenge_status_access)
def grade_challenge_status(request):
    user = request.user
    co_ordinator = MTCoordinator.objects.filter(User=user, RevokeDate__isnull=True)
    subjects = MTFacultyAssignment.objects.filter(Faculty__Dept=co_ordinator.Dept, RegEventId__MYear=co_ordinator.MYear, RegEventId__Status=1)
    if request.method == 'POST':
        form = GradeChallengeStatusForm(subjects, request.POST)
        if form.is_valid():
            msg = ''
            subject = form.cleaned_data.get('subject').split(':')[0]
            regEvent = form.cleaned_data.get('subject').split(':')[1]
            if request.POST.get('submit'):
                grade_challenge_objs = MTGradeChallenge.objects.filter(Registration__sub_id=subject, Registration__RegEventId=regEvent)
            elif request.POST.get('delete'):
                grade_challenge_id = request.POST.get('delete').split('-')[1]
                MTGradeChallenge.objects.filter(id=grade_challenge_id).delete()
                grade_challenge_objs = MTGradeChallenge.objects.filter(Registration__sub_id=subject, Registration__RegEventId=regEvent)
                msg = 'Grade Challenge object is deleted successfully.'
            return render(request, 'ADPGDB/GradeChallengeStatus.html', {'form':form, 'grade_challenge':grade_challenge_objs, 'msg':msg})
    else:
        form = GradeChallengeStatusForm(subjects=subjects)
    return render(request, 'ADPGDB/GradeChallengeStatus.html', {'form':form})
