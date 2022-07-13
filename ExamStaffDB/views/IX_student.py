from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import Http404
from django.shortcuts import render
from superintendent.user_access_test import is_ExamStaff, ix_grade_student_status_access
from co_ordinator.models import StudentRegistrations
from superintendent.models import RegistrationStatus, HOD
from hod.models import Coordinator
from ExamStaffDB.forms import IXGradeStudentsAddition, IXGradeStudentsStatus
from ExamStaffDB.models import IXGradeStudents

@login_required(login_url="/login/")
@user_passes_test(is_ExamStaff)
def ix_student_assignment(request):
    if request.method == 'POST':
        form = IXGradeStudentsAddition(request.POST)
        if form.is_valid():
            if form.cleaned_data.get('submit-form'):
                regEvent = form.cleaned_data.get('regId')
                subject = form.cleaned_data.get('subject')
                regd_no = form.cleaned_data.get('regd_no')
                grade = form.cleaned_data.get('grade')
                student_registration = StudentRegistrations.objects.filter(RegEventId=regEvent, sub_id=subject, RegNo=regd_no).first()
                ix_row = IXGradeStudents(Registration=student_registration, Grade=grade)
                ix_row.save()
                msg = 'Student Grade Added Successfully.'
                return render(request, 'ExamStaffDB/IXStudentAddition.html', {'form':form, 'msg':msg})
    else:
        form = IXGradeStudentsAddition()
    return render(request, 'ExamStaffDB/IXStudentAddition.html', {'form':form})

@login_required(login_url="/login/")
@user_passes_test(ix_grade_student_status_access)
def ix_student_status(request):
    msg = ''
    user = request.user
    groups = user.groups.all().values_list('name', flat=True)
    regIDs = None
    students = None
    if 'Superintendent' in groups or 'ExamStaff' in groups:
        regIDs = RegistrationStatus.objects.filter(Status=1)
    elif 'HOD' in groups:
        hod = HOD.objects.filter(User=user, RevokeDate__isnull=True)
        regIDs = RegistrationStatus.objects.filter(Status=1, Dept=hod.Dept)
    elif 'Co-ordinator' in groups:
        co_ordinator = Coordinator.objects.filter(User=user, RevokeDate__isnull=True).first()
        regIDs = RegistrationStatus.objects.filter(Status=1, Dept=co_ordinator.Dept)
    if request.method == 'POST':
        form = IXGradeStudentsStatus(regIDs, request.POST)
        if request.POST.get('submit'):
            regEvent = request.POST.get('regId')
            students = IXGradeStudents.objects.filter(Registration__RegEventId=regEvent)
        elif request.POST.get('delete'):
            if 'ExamStaff' in groups:
                IXGradeStudents.objects.filter(id=request.POST.get('delete')).delete()
                regEvent = request.POST.get('regId')
                students = IXGradeStudents.objects.filter(Registration__RegEventId=regEvent)
                msg = 'Record Deleted Successfully.'
            else:
                raise Http404('You are not authorized to view this page')
    else:
        form = IXGradeStudentsStatus(regIDs)
    return render(request, 'ExamStaffDB/IXGradeStudentsStatus.html', {'form':form, 'students':students, 'msg':msg})

