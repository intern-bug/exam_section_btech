from django.http import Http404
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q 
from BTsuperintendent.user_access_test import faculty_subject_assignment_access, faculty_assignment_status_access
from BTExamStaffDB.models import BTFacultyInfo
from BTsuperintendent.constants import DEPT_DICT, ROMAN_TO_INT
from BTco_ordinator.forms import FacultySubjectAssignmentForm, FacultyAssignmentStatusForm
from BTco_ordinator.models import BTFacultyAssignment, BTStudentRegistrations, BTSubjects, BTRollLists
from BThod.models import BTCoordinator
from ADUGDB.models import BTRegistrationStatus
from BTsuperintendent.models import BTHOD, BTCycleCoordinator


@login_required(login_url="/login/")
@user_passes_test(faculty_subject_assignment_access)
def faculty_subject_assignment(request):
    user = request.user
    groups = user.groups.all().values_list('name', flat=True)
    regIDs = None
    if 'Co-ordinator' in groups:
        current_user = BTCoordinator.objects.filter(User=user, RevokeDate__isnull=True).first()
        valid_subjects = BTSubjects.objects.filter(OfferedBy=current_user.Dept, RegEventId__BYear=current_user.BYear)
        regular_regIDs = valid_subjects.filter(RegEventId__Status=1).values_list('RegEventId_id', flat=True)
        active_regIDs = BTRegistrationStatus.objects.filter(Status=1, BYear=current_user.BYear).exclude(Mode='R')
        other_regIDs = BTStudentRegistrations.objects.filter(RegEventId__in=active_regIDs.values_list('id', flat=True), sub_id__in=valid_subjects.values_list('id', flat=True)).values_list('RegEventId', flat=True)
        regIDs = BTRegistrationStatus.objects.filter(Q(id__in=regular_regIDs)|Q(id__in=other_regIDs))
    elif 'HOD' in groups:
        current_user = BTHOD.objects.filter(User=user, RevokeDate__isnull=True).first()
        valid_subjects = BTSubjects.objects.filter(OfferedBy=current_user.Dept, RegEventId__BYear=1)
        regular_regIDs = valid_subjects.filter(RegEventId__Status=1).values_list('RegEventId_id', flat=True)
        active_regIDs = BTRegistrationStatus.objects.filter(Status=1, BYear=1).exclude(Mode='R')
        other_regIDs = BTStudentRegistrations.objects.filter(RegEventId__in=active_regIDs.values_list('id', flat=True), sub_id__in=valid_subjects.values_list('id', flat=True)).values_list('RegEventId', flat=True)
        regIDs = BTRegistrationStatus.objects.filter(Q(id__in=regular_regIDs)|Q(id__in=other_regIDs))
    if(request.method =='POST'):
        form = FacultySubjectAssignmentForm(regIDs, request.POST)
        if(form.is_valid()):
            regEvent=form.cleaned_data['regID']
            event_string = regEvent.split(':')
            dept = DEPT_DICT[event_string[0]]
            ayear = int(event_string[3])
            asem = int(event_string[4])
            byear = ROMAN_TO_INT[event_string[1]]
            bsem = ROMAN_TO_INT[event_string[2]]
            regulation = int(event_string[5])
            mode = event_string[6]
            regEventId = BTRegistrationStatus.objects.filter(AYear=ayear,ASem=asem,BYear=byear,BSem=bsem,\
                    Dept=dept,Mode=mode,Regulation=regulation).first()
            if mode == 'R':
                subjects = BTSubjects.objects.filter(RegEventId_id=regEventId.id, OfferedBy=current_user.Dept)
            else:
                student_Registrations = BTStudentRegistrations.objects.filter(RegEventId=regEventId.id).values_list('sub_id', flat=True)
                subjects = BTSubjects.objects.filter(OfferedBy=current_user.Dept, id__in=student_Registrations.values_list('sub_id', flat=True))
            request.session['currentRegEvent']=regEventId.id
            return render(request, 'BTco_ordinator/FacultyAssignment.html', {'form': form, 'subjects':subjects})
    else:
        form = FacultySubjectAssignmentForm(regIDs)
    return render(request, 'BTco_ordinator/FacultyAssignment.html',{'form':form})

@login_required(login_url="/login/")
@user_passes_test(faculty_subject_assignment_access)
def faculty_subject_assignment_detail(request, pk):
    user = request.user
    groups = user.groups.all().values_list('name', flat=True)
    if 'Co-ordinator' in groups:
        current_user = BTCoordinator.objects.filter(User=user, RevokeDate__isnull=True).first()
    elif 'HOD' in groups:
        current_user = BTHOD.objects.filter(User=user, RevokeDate__isnull=True).first()
    subject = BTSubjects.objects.get(id=pk)
    faculty = BTFacultyInfo.objects.filter(Dept=current_user.Dept, Working=True)
    sections = BTRollLists.objects.filter(RegEventId_id=request.session.get('currentRegEvent')).values_list('Section', flat=True).distinct().order_by('Section')
    faculty_assigned = BTFacultyAssignment.objects.filter(Subject=subject, RegEventId_id=request.session.get('currentRegEvent'))
    co_ordinator=''
    if faculty_assigned:
        co_ordinator = faculty_assigned[0].Coordinator_id
    for fac in faculty:
        if faculty_assigned.filter(Faculty=fac).exists():
            fac.Section = []
            for fac_assign in faculty_assigned.filter(Faculty=fac):
                fac.Section.append(fac_assign.Section)
    
    if request.method == 'POST':
        for sec in sections:
            if request.POST.get('faculty-'+str(sec)):
                if faculty_assigned and faculty_assigned.get(Section=sec):
                    faculty_row = faculty_assigned.get(Section=sec)
                    faculty_row.co_ordinator_id = request.POST.get('course-coordinator') or 0
                    faculty_row.faculty_id = request.POST.get('faculty-'+str(sec))
                    faculty_row.save()
                else:
                    faculty_row = BTFacultyAssignment(Subject=subject, Coordinator_id=request.POST.get('course-coordinator'),\
                        Faculty_id=request.POST.get('faculty-'+str(sec)), Section=sec, RegEventId_id=request.session['currentRegEvent'])
                    faculty_row.save()
        return redirect('BTFacultySubjectAssignment')
    return render(request, 'BTco_ordinator/FacultyAssignmentDetail.html', {'subject':subject, 'faculty':faculty,\
        'section':sections, 'co_ordinator':co_ordinator, 'faculty_section':faculty_assigned})

@login_required(login_url="/login/")
@user_passes_test(faculty_assignment_status_access)
def faculty_assignment_status(request):
    user = request.user
    groups = user.groups.all().values_list('name', flat=True)
    if 'Co-ordinator' in groups:
        current_user = BTCoordinator.objects.filter(User=user, RevokeDate__isnull=True).first()
        current_user.group = 'Co-ordinator'  
        valid_subjects = BTSubjects.objects.filter(OfferedBy=current_user.Dept, RegEventId__BYear=current_user.BYear)
        regular_regIDs = valid_subjects.filter(RegEventId__Status=1).values_list('RegEventId_id', flat=True)
        active_regIDs = BTRegistrationStatus.objects.filter(Status=1, BYear=current_user.BYear).exclude(Mode='R')
        other_regIDs = BTStudentRegistrations.objects.filter(RegEventId__in=active_regIDs.values_list('id', flat=True), sub_id__in=valid_subjects.values_list('id', flat=True)).values_list('RegEventId', flat=True)
        regIDs = BTRegistrationStatus.objects.filter(Q(id__in=regular_regIDs)|Q(id__in=other_regIDs))
    elif 'HOD' in groups:
        current_user = BTHOD.objects.filter(User=user, RevokeDate__isnull=True).first()
        current_user.group = 'HOD'
        valid_subjects = BTSubjects.objects.filter(OfferedBy=current_user.Dept)
        regular_regIDs = valid_subjects.filter(RegEventId__Status=1).values_list('RegEventId_id', flat=True)
        active_regIDs = BTRegistrationStatus.objects.filter(Status=1, BYear=1).exclude(Mode='R')
        other_regIDs = BTStudentRegistrations.objects.filter(RegEventId__in=active_regIDs.values_list('id', flat=True), sub_id__in=valid_subjects.values_list('id', flat=True)).values_list('RegEventId', flat=True)
        regIDs = BTRegistrationStatus.objects.filter(Q(id__in=regular_regIDs)|Q(id__in=other_regIDs))
    elif 'Superintendent' in groups:
        current_user = user
        current_user.group = 'Superintendent'
        regIDs = BTRegistrationStatus.objects.filter(Status=1)
    elif 'Associate-Dean' in groups:
        current_user = user
        current_user.group = 'Associate-Dean'
        regIDs = BTRegistrationStatus.objects.filter(Status=1)
    elif 'Cycle-Co-ordinator' in groups:
        current_user = BTCycleCoordinator.objects.filter(User=user, RevokeDate__isnull=True).first()
        current_user.group = 'Cycle-Co-ordinator'
        regIDs = BTRegistrationStatus.objects.filter(Status=1, BYear=1, Dept=current_user.Cycle)
    else:
        raise Http404("You are not authorized to view this page")
    if(request.method =='POST'):
        form = FacultyAssignmentStatusForm(regIDs, request.POST)
        if(form.is_valid()):
            regeventid=form.cleaned_data['regID']
            regEvent = BTRegistrationStatus.objects.filter(id=regeventid).first()
            if current_user.group == 'Superintendent' or current_user.group == 'Associate-Dean':
                faculty = BTFacultyAssignment.objects.filter(RegEventId__id=regeventid).order_by('Section')
            elif current_user.group == 'Co-ordinator' or current_user.group == 'HOD':
                if regEvent.Dept==current_user.Dept:
                    faculty = BTFacultyAssignment.objects.filter(RegEventId__id=regeventid).order_by('Section')
                else:
                    faculty = BTFacultyAssignment.objects.filter(RegEventId__id=regeventid, Subject__OfferedBy=current_user.Dept).order_by('Section')
            elif current_user.group == 'Cycle-Co-ordinator':
                faculty = BTFacultyAssignment.objects.filter(RegEventId__id=regeventid).order_by('Section')
            return render(request, 'BTco_ordinator/FacultyAssignmentStatus.html',{'form':form, 'faculty':faculty})
    else:
        form = FacultyAssignmentStatusForm(regIDs)
    return render(request, 'BTco_ordinator/FacultyAssignmentStatus.html',{'form':form})


def faculty_assignment(**kwargs):
    '''
    Dept can be given in the form of list consisting of departments.
    All the remaining arguments are not lists
    '''
    print(kwargs)
    if not (kwargs.get('Mode') or kwargs.get('AYear') or kwargs.get('BYear') or kwargs.get('BSem') or kwargs.get('ASem') or kwargs.get('Regulation')):
        return "Provide the required arguments!!!!"
    if kwargs.get('Mode') == 'R':
        regEvents = BTRegistrationStatus.objects.filter(AYear=kwargs.get('AYear'), ASem=kwargs.get('ASem'), BYear=kwargs.get('BYear'), BSem=kwargs.get('BSem'), \
            Regulation=kwargs.get('Regulation'), Mode=kwargs.get('Mode'))
        if not regEvents:
            return "No Events!!!!"
        depts = kwargs.get('Dept')
        if not kwargs.get('Dept') and kwargs.get('BYear')!=1:
            depts = [1,2,3,4,5,6,7,8]
        elif not kwargs.get('Dept') and kwargs.get('BYear')==1:
            depts = [9,10]
        for dept in depts:
            print(regEvents.filter(Dept=dept).first().__dict__)
            regEventId = regEvents.filter(Dept=dept).first().id
            dept_sub = BTSubjects.objects.filter(RegEventId_id=regEventId)
            for sub in dept_sub:
                print(sub.__dict__)
                offering_dept = sub.OfferedBy
                if offering_dept > 10: offering_dept -= 2
                print(offering_dept)
                fac_name = 'fac'+str(offering_dept)
                print(fac_name)
                fac_id = BTFacultyInfo.objects.filter(Name=fac_name).first()
                if not BTFacultyAssignment.objects.filter(Subject_id=sub.id, RegEventId_id=regEventId, Faculty_id=fac_id.id, Coordinator_id=fac_id.id).exists():
                    fac_assign_obj = BTFacultyAssignment(Subject_id=sub.id, RegEventId_id=regEventId, Faculty_id=fac_id.id, Coordinator_id=fac_id.id)
                    fac_assign_obj.save()
    elif kwargs.get('Mode') == 'M' or kwargs.get('Mode') == 'B':
        regEvents = BTRegistrationStatus.objects.filter(AYear=kwargs.get('AYear'), ASem=kwargs.get('ASem'), BYear=kwargs.get('BYear'), BSem=kwargs.get('BSem'), \
            Regulation=kwargs.get('Regulation'), Mode=kwargs.get('Mode'))
        if not regEvents:
            return "No Events!!!!"
        depts = kwargs.get('Dept')
        if not kwargs.get('Dept') and kwargs.get('BYear')!=1:
            depts = [1,2,3,4,5,6,7,8]
        elif not kwargs.get('Dept') and kwargs.get('BYear')==1:
            depts = [9,10]
        for dept in depts:
            print(regEvents.filter(Dept=dept).first().__dict__)
            regEventId = regEvents.filter(Dept=dept).first().id
            student_regs = BTStudentRegistrations.objects.filter(RegEventId_id=regEventId).distinct('sub_id_id')
            subjects = BTSubjects.objects.filter(id__in=student_regs.values_list('sub_id_id', flat=True))
            for sub in subjects:
                print(sub.__dict__)
                offering_dept = sub.OfferedBy
                if offering_dept > 10: offering_dept -= 2
                print(offering_dept)
                fac_name = 'fac'+str(offering_dept)
                print(fac_name)
                fac_id = BTFacultyInfo.objects.filter(Name=fac_name).first()
                if not BTFacultyAssignment.objects.filter(Subject_id=sub.id, RegEventId_id=regEventId, Faculty_id=fac_id.id, Coordinator_id=fac_id.id).exists():
                    fac_assign_obj = BTFacultyAssignment(Subject_id=sub.id, RegEventId_id=regEventId, Faculty_id=fac_id.id, Coordinator_id=fac_id.id)
                    fac_assign_obj.save()
    return "Completed!!!!"

