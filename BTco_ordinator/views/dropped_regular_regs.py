from django.contrib.auth.decorators import login_required, user_passes_test 
from django.shortcuts import render
from BTsuperintendent.user_access_test import registration_access
from BTco_ordinator.forms import DroppedRegularRegistrationsForm
from BTco_ordinator.models import BTSubjects, BTDroppedRegularCourses, BTStudentRegistrations_Staging
from ADUGDB.models import BTRegistrationStatus
from BTsuperintendent.models import BTCycleCoordinator
from BTExamStaffDB.models import BTStudentInfo
from BThod.models import BTCoordinator

@login_required(login_url="/login/")
@user_passes_test(registration_access)
def dropped_regular_registrations(request):
    user = request.user
    groups = user.groups.all().values_list('name', flat=True)
    regIDs =None
    if 'Co-ordinator' in groups:
        coordinator = BTCoordinator.objects.filter(User=user, RevokeDate__isnull=True).first()
        regIDs = BTRegistrationStatus.objects.filter(Status=1, RegistrationStatus=1, Dept=coordinator.Dept, BYear=coordinator.BYear, Mode='D')
    elif 'Cycle-Co-ordinator' in groups:
        cycle_cord = BTCycleCoordinator.objects.filter(User=user, RevokeDate__isnull=True).first()
        regIDs = BTRegistrationStatus.objects.filter(Status=1, RegistrationStatus=1, Dept=cycle_cord.Cycle, BYear=1, Mode='D')
    if regIDs:
        regIDs = [(row.AYear, row.ASem, row.BYear, row.BSem, row.Dept, row.Mode, row.Regulation) for row in regIDs]
    studentInfo = []
    if(request.method == 'POST'):
        regId = request.POST['RegEvent']
        strs = regId.split(':')
        depts = ['BTE','CHE','CE','CSE','EEE','ECE','ME','MME','CHEMISTRY','PHYSICS']
        years = {1:'I',2:'II',3:'III',4:'IV'}
        deptDict = {dept:ind+1 for ind, dept  in enumerate(depts)}
        rom2int = {'I':1,'II':2,'III':3,'IV':4}
        strs = regId.split(':')
        dept = deptDict[strs[0]]
        ayear = int(strs[3])
        asem = int(strs[4])
        byear = rom2int[strs[1]]
        bsem = rom2int[strs[2]]
        regulation = int(strs[5])
        mode = strs[6]
        currentRegEventId = BTRegistrationStatus.objects.filter(AYear=ayear,ASem=asem,BYear=byear,BSem=bsem,\
                    Dept=dept,Mode=mode,Regulation=regulation)
        currentRegEventId = currentRegEventId[0].id
        con = {key:request.POST[key] for key in request.POST.keys()} 
        if('RegNo' in request.POST.keys()):
            droppedCourses = BTDroppedRegularCourses.objects.filter(RegNo=request.POST['RegNo'])
            reg_status = BTRegistrationStatus.objects.filter(AYear=ayear,ASem=asem, Regulation=regulation)
            studentRegistrations=[]
            for regevent in reg_status:
                studentRegistrations += list(BTStudentRegistrations_Staging.objects.filter(student__student__RegNo=request.POST['RegNo'],RegEventId=regevent.id))
            studentRegularRegistrations = []
            for regn in studentRegistrations:
                regEvent = BTRegistrationStatus.objects.get(id=regn.RegEventId)
                if (regEvent.Mode == 'R' or regEvent.Mode == 'D'):
                    studentRegularRegistrations.append(regn)
            for row in droppedCourses:
                for entry in studentRegistrations:
                    if row.sub_id == entry. sub_id:
                        con[str('RadioMode'+row.sub_id)] = list(str(entry.Mode))

        form = DroppedRegularRegistrationsForm(regIDs,con)
        if not 'RegNo' in request.POST.keys():
            pass 
        elif 'RegEvent' in request.POST and 'RegNo' in request.POST and not 'Submit' in request.POST:
            regEvents = BTRegistrationStatus.objects.filter(AYear=ayear, ASem=asem, Regulation=regulation)
            studentRegistrations = BTStudentRegistrations_Staging.objects.filter(student__student__RegNo=request.POST.get('RegNo'), RegEventId__in=regEvents.values_list('id', flat=True))
            mode_selection = {'RadioMode'+str(reg.sub_id): reg.Mode for reg in studentRegistrations}
            student_obj = BTStudentInfo.objects.get(RegNo=request.POST.get('RegNo'))
            context = {'form':form, 'msg':0}
            context['RollNo'] = student_obj.RollNo
            context['Name'] = student_obj.Name  
            from json import dumps
            context['modes'] = dumps(mode_selection)
            return render(request, 'BTco_ordinator/DroppedRegularReg.html',context)
        elif('RegEvent' in request.POST and 'RegNo' in request.POST and 'Submit' in request.POST and form.is_valid()):
            regNo = request.POST['RegNo']
            event = (request.POST['RegEvent'])
            studentInfo = BTStudentInfo.objects.filter(RegNo=regNo) 
            studyModeCredits = 0
            examModeCredits = 0
            for sub in form.myFields:
                if(form.cleaned_data['Check'+str(sub[9])]):
                    if(form.cleaned_data['RadioMode'+str(sub[9])]!=''):
                        if (form.cleaned_data['RadioMode'+str(sub[9])]=='1'):
                            studyModeCredits += sub[2]
                        else:
                            examModeCredits += sub[2]
                    else:
                        form = DroppedRegularRegistrationsForm(regIDs,request.POST)
                        context = {'form':form, 'msg': 2}  
                        if(len(studentInfo)!=0):
                            context['RollNo'] = studentInfo[0].RollNo
                            context['Name'] = studentInfo[0].Name  
                        return render(request, 'BTco_ordinator/DroppedRegularReg.html',context)
            if((studyModeCredits+examModeCredits<=34) and(studyModeCredits<=32)):
                for sub in form.myFields:
                    if(sub[6]=='R'): #Handling Regular Subjects
                        if(form.cleaned_data['Check'+str(sub[9])] == False):
                            #delete regular_record from the registration table
                            reg = BTStudentRegistrations_Staging.objects.filter(id=sub[10])
                            if len(reg) != 0:
                                BTStudentRegistrations_Staging.objects.filter(id=sub[10]).delete()
                                new_dropped_course = BTDroppedRegularCourses(student=studentInfo[0], subject_id=sub[9], RegEventId_id=reg.RegEventId, Registered=False)
                                new_dropped_course.save()
                    elif sub[6] == 'D':
                        if(form.cleaned_data['Check'+str(sub[9])]):
                            reg = BTStudentRegistrations_Staging.objects.filter(student__student__RegNo = request.POST['RegNo'], RegEventId=currentRegEventId,\
                                 sub_id = sub[9])
                            if(len(reg) == 0):
                                newRegistration = BTStudentRegistrations_Staging(student__student__RegNo = request.POST['RegNo'], RegEventId = currentRegEventId,\
                                    Mode=form.cleaned_data['RadioMode'+str(sub[9])],sub_id=sub[9])
                                newRegistration.save()
                                BTDroppedRegularCourses.objects.filter(student=studentInfo[0], subject_id=sub[9]).first().update(Registered=True)
                        else:
                            if sub[10]:
                                reg = BTStudentRegistrations_Staging.objects.filter(id=sub[10])
                                if len(reg) != 0:
                                    BTStudentRegistrations_Staging.objects.filter(id=sub[10]).delete()
                                    BTDroppedRegularCourses.objects.filter(student=studentInfo[0], subject_id=sub[9]).first().update(Registered=False)
                    else:   #Handling Backlog Subjects
                        if((sub[5]) and (form.cleaned_data['Check'+str(sub[9])])):
                            #update operation mode could be study mode or exam mode
                            BTStudentRegistrations_Staging.objects.filter(student__student__RegNo = request.POST['RegNo'], sub_id = sub[9], id=sub[10]).update(Mode=form.cleaned_data['RadioMode'+sub[0]])
                        elif(sub[5]):
                            #delete record from registration table
                            BTStudentRegistrations_Staging.objects.filter(student__student__RegNo = request.POST['RegNo'], sub_id = sub[9], id=sub[10]).delete()  
                return(render(request,'BTco_ordinator/DroppedRegularRegSuccess.html'))
            else:
                form = DroppedRegularRegistrationsForm(regIDs,request.POST)
                context = {'form':form, 'msg':1}
                context['study']=studyModeCredits
                context['exam']=examModeCredits
                if(len(studentInfo)!=0):
                    context['RollNo'] = studentInfo[0].RollNo
                    context['Name'] = studentInfo[0].Name  
                return render(request, 'BTco_ordinator/DroppedRegularReg.html',context)
        else:
            print("form validation failed")             
    else:
        form = DroppedRegularRegistrationsForm(regIDs)
    context = {'form':form}
    if(len(studentInfo)!=0):
        context['RollNo'] = studentInfo[0].RollNo
        context['Name'] = studentInfo[0].Name  
    return render(request, 'BTco_ordinator/DroppedRegularReg.html',context)
