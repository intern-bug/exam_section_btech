
from django.contrib.auth.decorators import login_required, user_passes_test 
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from MTco_ordinator.forms import RegistrationsEventForm, SubjectsUploadForm, \
    SubjectDeletionForm, SubjectFinalizeEventForm,StudentRegistrationUpdateForm
from MTco_ordinator.models import MTSubjects_Staging, MTSubjects
from MTco_ordinator.resources import SubjectStagingResource
from ADPGDB.models import MTRegistrationStatus
from MTsuperintendent.models import MTHOD, MTMarksDistribution
from MThod.models import MTCoordinator
from tablib import Dataset
from import_export.formats.base_formats import XLSX
from MTsuperintendent.user_access_test import subject_home_access, subject_access



@login_required(login_url="/login/")
@user_passes_test(subject_access)
def subject_upload(request):
    user = request.user
    groups = user.groups.all().values_list('name', flat=True)
    regIDs = []
    msg = ''
    
    if 'Co-ordinator' in groups:
        coordinator = MTCoordinator.objects.filter(User=user, RevokeDate__isnull=True).first()
        regIDs = MTRegistrationStatus.objects.filter(Status=1, RegistrationStatus=1, Dept=coordinator.Dept, Mode='R')
    if regIDs:
        regIDs = [(row.AYear, row.ASem, row.MYear, row.MSem, row.Dept, row.Mode, row.Regulation) for row in regIDs]
    if(request.method=='POST'):
        form = SubjectsUploadForm(regIDs, request.POST,request.FILES)
        if request.POST.get('upload_file_submit'):
            (ayear,asem,myear,msem,dept,mode,regulation) = regIDs[int(request.POST['regID'])]
            currentRegEventId = MTRegistrationStatus.objects.filter(AYear=ayear, MYear=myear, ASem=asem, MSem=msem, Dept=dept, Mode=mode, Regulation=regulation).first().id
            if(form.is_valid()):
                if(form.cleaned_data['regID']!='--Choose Event--'):
                    file = form.cleaned_data['file']
                    data = bytes()
                    for chunk in file.chunks():
                        data += chunk
                    dataset = XLSX().create_dataset(data)
                    newDataset= Dataset()
                    errorDataset = Dataset()#To store subjects rows which are not related to present registration event
                    errorDataset.headers = ['SubCode', 'SubName', 'MYear', 'MSem', 'Dept','OfferedYear', 'Regulation',\
                        'Creditable', 'Credits','Type','Category', 'OfferedBy', 'ProgrammeCode']
                    newDataset.headers = ['SubCode', 'SubName', 'Creditable', 'Credits', 'Type', 'Category', 'RegEventId', 'OfferedBy', 'ProgrammeCode',\
                        'DistributionRatio', 'MarkDistribution']
                    currentRegEventId = MTRegistrationStatus.objects.filter(AYear=ayear,ASem=asem,MYear=myear,MSem=msem,\
                        Dept=dept,Mode=mode,Regulation=regulation)
                    currentRegEventId = currentRegEventId[0].id
                    marks_distribution = MTMarksDistribution.objects.all()
                    for i in range(len(dataset)):
                        row = dataset[i]
                        if((row[2],row[3],row[4],row[5],row[6])==(myear,msem,dept,ayear,regulation)):
                            newRow = (row[0],row[1],row[7],row[8],row[9],row[10],currentRegEventId, row[11], row[12], '', '')
                            print(newRow)
                            newDataset.append(newRow)
                        else:
                            newRow = (row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10], row[11], row[12])
                            errorDataset.append(newRow)
                    request.session['newDataset'] = list(newDataset)
                    request.session['currentRegEventId'] = currentRegEventId              
                return render(request, 'MTco_ordinator/BTSubjectsUpload.html', {'form':form, 'errorRows':errorDataset, \
                    'validRows':newDataset, 'marks_distribution':marks_distribution})
        elif request.POST.get('mark_dis_submit'):
            newDataset = Dataset()
            newDataset.headers = ['SubCode', 'SubName', 'Creditable', 'Credits', 'Type', 'Category', 'RegEventId', 'OfferedBy', 'ProgrammeCode', \
                    'DistributionRatio', 'MarkDistribution']
            errorRows = []
            for row in request.session.get('newDataset'):
                row[9] = request.POST.get('ratio_distribution_'+str(row[0])).strip()
                row[10] = int(request.POST.get('mark_distribution_'+str(row[0])))
                newRow = (row[0],row[1],row[2],row[3],row[4],row[5],row[6], row[7], row[8], row[9], row[10])
                mark_distribution = MTMarksDistribution.objects.filter(id=row[10]).first()
                if len(mark_distribution.Distribution.split(',')) != len(row[9].split(':')):
                    errorRows.append(newRow)
                else:
                    newDataset.append(newRow)
            Subject_resource = SubjectStagingResource()
            result = Subject_resource.import_data(newDataset, dry_run=True)
            if not result.has_errors():
                Subject_resource.import_data(newDataset, dry_run=False)
            else:
                errors = result.row_errors()
                indices = set([i for i in range(len(newDataset))])    
                errorIndices = set([i[0]-1 for i in errors])
                cleanIndices = indices.difference(errorIndices)
                cleanDataset = Dataset()
                for i in list(cleanIndices):
                    cleanDataset.append(newDataset[i])
                cleanDataset.headers = newDataset.headers
            
                result1 = Subject_resource.import_data(cleanDataset, dry_run=True)
                if not result1.has_errors():
                    Subject_resource.import_data(cleanDataset, dry_run=False)
                else:
                    print('Something went wrong in plain import')
                errorData = Dataset()
                for i in list(errorIndices):
                    newRow = (newDataset[i][0],newDataset[i][1],newDataset[i][2],\
                        newDataset[i][3],newDataset[i][4],newDataset[i][5],newDataset[i][6], newDataset[i][7], newDataset[i][8], newDataset[i][9], newDataset[i][10])
                    errorData.append(newRow)
                subErrRows = [ (errorData[i][0],errorData[i][1],errorData[i][2],errorData[i][3],\
                errorData[i][4],errorData[i][5],errorData[i][6],errorData[i][7], errorData[i][8], errorData[i][9], errorData[i][10]) for i in range(len(errorData))]
                request.session['subErrRows'] = subErrRows
                request.session['errorRows'] = errorRows
                # request.session['currentRegEventId'] = currentRegEventId              
                return HttpResponseRedirect(reverse('MTSupBTSubjectsUploadErrorHandler'))
            if errorRows:
                return render(request, 'MTco_ordinator/BTSubjectsUpload.html', {'form':form, 'errorRows1':errorRows})
            msg = 'Subjects Uploaded successfully.'

    else:
        form = SubjectsUploadForm(Options=regIDs)
    return (render(request, 'MTco_ordinator/BTSubjectsUpload.html', {'form':form, 'msg':msg}))

@login_required(login_url="/login/")
@user_passes_test(subject_access)
def subject_upload_error_handler(request):
    subjectRows = request.session.get('subErrRows')
    errorRows = request.session.get('errorRows')
    currentRegEventId = request.session.get('currentRegEventId')
    if(request.method=='POST'):
        form = StudentRegistrationUpdateForm(subjectRows,request.POST)
        if(form.is_valid()):
            for cIndex, fRow in enumerate(subjectRows):
                if(form.cleaned_data.get('Check'+str(fRow[0]))):
                    MTSubjects_Staging.objects.filter(SubCode=fRow[0],RegEventId=currentRegEventId).update(SubName=fRow[1],\
                        Creditable=fRow[2],Credits=fRow[3],Type=fRow[4],Category=fRow[5],OfferedBy=fRow[7], ProgrammeCode=fRow[8],\
                             DistributionRatio=fRow[9], MarkDistribution=fRow[10])
            return render(request, 'MTco_ordinator/BTSubjectsUploadSuccess.html')
    else:
        form = StudentRegistrationUpdateForm(Options=subjectRows)
    return(render(request, 'MTco_ordinator/BTSubjectsUploadErrorHandler.html',{'form':form, 'errorRows':errorRows}))

@login_required(login_url="/login/")
@user_passes_test(subject_home_access)
def subject_upload_status(request):
    user = request.user
    groups = user.groups.all().values_list('name', flat=True)
    regIDs = None
    if 'Superintendent' in groups or 'Associate-Dean' in groups:
        regIDs = MTRegistrationStatus.objects.filter(Status=1, Mode='R')
    elif 'HOD' in groups:
        hod = MTHOD.objects.filter(User=user, RevokeDate__isnull=True).first()
        regIDs = MTRegistrationStatus.objects.filter(Status=1, Dept=hod.Dept, Mode='R')
    elif 'Co-ordinator' in groups:
        co_ordinator = MTCoordinator.objects.filter(User=user, RevokeDate__isnull=True).first()
        regIDs = MTRegistrationStatus.objects.filter(Status=1, Dept=co_ordinator.Dept, Mode='R')
   
    if(request.method=='POST'):
        form = RegistrationsEventForm(regIDs, request.POST)
        if(form.is_valid()):
            depts = ['BTE','CHE','CE','CSE','EEE','ECE','ME','MME']
            years = {1:'I',2:'II'}
            deptDict = {dept:ind+1 for ind, dept  in enumerate(depts)}
            rom2int = {'I':1,'II':2}
            if(form.cleaned_data['regID']!='--Choose Event--'):
                strs = form.cleaned_data['regID'].split(':')
                dept = deptDict[strs[0]]
                ayear = int(strs[3])
                asem = int(strs[4])
                myear = rom2int[strs[1]]
                msem = rom2int[strs[2]]
                regulation = int(strs[5])
                mode = strs[6]
                currentRegEventId = MTRegistrationStatus.objects.filter(AYear=ayear,ASem=asem,MYear=myear,MSem=msem,\
                    Dept=dept,Mode=mode,Regulation=regulation)
                currentRegEventId = currentRegEventId[0].id
                subjects = []
                subjects = MTSubjects_Staging.objects.filter(RegEventId=currentRegEventId)
                return render(request, 'MTco_ordinator/BTSubjectsUploadStatus.html',{'subjects':subjects,'form':form})
    else:
        form = RegistrationsEventForm(regIDs)
    return render(request, 'MTco_ordinator/BTSubjectsUploadStatus.html',{'form':form})

@login_required(login_url="/login/")
@user_passes_test(subject_access)
def subject_delete(request):
    user = request.user
    groups = user.groups.all().values_list('name', flat=True)
    regIDs = []
    msg = ''
    
    if 'Co-ordinator' in groups:
        coordinator = MTCoordinator.objects.filter(User=user, RevokeDate__isnull=True).first()
        regIDs = MTRegistrationStatus.objects.filter(Status=1, RegistrationStatus=1, Dept=coordinator.Dept, Mode='R')
    if(request.method=='POST'):
        form = SubjectDeletionForm(regIDs, request.POST)
        if('regID' in request.POST.keys()):
            if(form.is_valid()):
                depts = ['BTE','CHE','CE','CSE','EEE','ECE','ME','MME']
                years = {1:'I',2:'II'}
                deptDict = {dept:ind+1 for ind, dept  in enumerate(depts)}
                rom2int = {'I':1,'II':2}
                strs = form.cleaned_data['regID'].split(':')
                dept = deptDict[strs[0]]
                ayear = int(strs[3])
                asem = int(strs[4])
                myear = rom2int[strs[1]]
                msem = rom2int[strs[2]]
                regulation = int(strs[5])
                mode = strs[6]
                currentRegEventId = MTRegistrationStatus.objects.filter(AYear=ayear,ASem=asem,MYear=myear,MSem=msem,\
                    Dept=dept,Mode=mode,Regulation=regulation)
                currentRegEventId = currentRegEventId[0].id
                if(mode=='R'): # deleting is only valid for regular registrations, the other case is not even possible
                    subjects = []
                    deletedSubjects = []
                    for sub in form.myFields:
                        if(form.cleaned_data['Check'+sub[0]]==True):
                            subject = MTSubjects_Staging.objects.filter(SubCode=sub[0],RegEventId=currentRegEventId)
                            subject.delete()
                            deletedSubjects.append(sub[0]+':' + str(sub[4]))
                        else:
                            subjects.append(sub[0])
                    if(len(deletedSubjects)!=0):
                        msg = 'Subject(s) Deleted successfully.'
                        form = SubjectDeletionForm(regIDs, request.POST)
                        return render(request,'MTco_ordinator/BTSubjectsDelete.html',{'form':form,'msg': msg})
    else:
        form = SubjectDeletionForm(regIDs)
    return render(request, 'MTco_ordinator/BTSubjectsDelete.html',{'form':form})




@login_required(login_url="/login/")
@user_passes_test(subject_access)
def subject_finalize(request):
    user = request.user
    groups = user.groups.all().values_list('name', flat=True)
    regIDs = None
    msg = ''
    if 'Co-ordinator' in groups:
        coordinator = MTCoordinator.objects.filter(User=user, RevokeDate__isnull=True).first()
        regIDs = MTRegistrationStatus.objects.filter(Status=1, RegistrationStatus=1, Dept=coordinator.Dept, Mode='R')
    if(request.method=='POST'):
        form = SubjectFinalizeEventForm(regIDs, request.POST)
        if(form.is_valid()):
            print('valid form')
            depts = ['BTE','CHE','CE','CSE','EEE','ECE','ME','MME']
            years = {1:'I',2:'II'}
            deptDict = {dept:ind+1 for ind, dept  in enumerate(depts)}
            rom2int = {'I':1,'II':2}
            if(form.cleaned_data['regID']!='--Choose Event--'):
                strs = form.cleaned_data['regID'].split(':')
                dept = deptDict[strs[0]]
                ayear = int(strs[3])
                asem = int(strs[4])
                myear = rom2int[strs[1]]
                msem = rom2int[strs[2]]
                regulation = int(strs[5])
                mode = strs[6]
                currentRegEventId = MTRegistrationStatus.objects.filter(AYear=ayear,ASem=asem,MYear=myear,MSem=msem,\
                    Dept=dept,Mode=mode,Regulation=regulation)
                currentRegEventId = currentRegEventId[0].id
                subjects = []
                subjects = MTSubjects_Staging.objects.filter(RegEventId=currentRegEventId)
                for sub in subjects:
                   s=MTSubjects(SubCode=sub.SubCode,SubName=sub.SubName,Creditable=sub.Creditable,Credits=sub.Credits,\
                           OfferedBy=sub.OfferedBy,Type=sub.Type,Category=sub.Category,RegEventId=sub.RegEventId, ProgrammeCode=sub.ProgrammeCode, \
                            DistributionRatio=sub.DistributionRatio, MarkDistribution=sub.MarkDistribution)
                   s.save() 
                msg = 'Subjects finalized successfully.'
    else:
        form = SubjectFinalizeEventForm(regIDs)
    return render(request, 'MTco_ordinator/BTSubjectFinalize.html',{'form':form, 'msg':msg})

@login_required(login_url="/login/")
@user_passes_test(subject_access)
def open_subject_upload(request):
    user = request.user
    groups = user.groups.all().values_list('name', flat=True)
    regIDs = []
    msg = ''
    
    if 'Co-ordinator' in groups:
        coordinator = MTCoordinator.objects.filter(User=user, RevokeDate__isnull=True).first()
        regIDs = MTRegistrationStatus.objects.filter(Status=1, RegistrationStatus=1, Dept=coordinator.Dept, Mode='R')
    if regIDs:
        regIDs = [(row.AYear, row.ASem, row.MYear, row.MSem, row.Dept, row.Mode, row.Regulation) for row in regIDs]
    if(request.method=='POST'):
        form = SubjectsUploadForm(regIDs, request.POST,request.FILES)
        if request.POST.get('upload_file_submit'):
            (ayear,asem,myear,msem,dept,mode,regulation) = regIDs[int(request.POST['regID'])]
            currentRegEventId = MTRegistrationStatus.objects.filter(AYear=ayear, MYear=myear, ASem=asem, MSem=msem, Dept=dept, Mode=mode, Regulation=regulation).first().id
            if(form.is_valid()):
                if(form.cleaned_data['regID']!='--Choose Event--'):
                    file = form.cleaned_data['file']
                    data = bytes()
                    for chunk in file.chunks():
                        data += chunk
                    dataset = XLSX().create_dataset(data)
                    newDataset= Dataset()
                    errorDataset = Dataset()#To store subjects rows which are not related to present registration event
                    errorDataset.headers = ['SubCode', 'SubName', 'MYear', 'MSem', 'Dept','OfferedYear', 'Regulation',\
                        'Creditable', 'Credits','Type','Category', 'OfferedBy', 'ProgrammeCode']
                    newDataset.headers = ['SubCode', 'SubName', 'Creditable', 'Credits', 'Type', 'Category', 'RegEventId', 'OfferedBy', 'ProgrammeCode'\
                        'DistributionRatio', 'MarkDistribution']
                    currentRegEventId = MTRegistrationStatus.objects.filter(AYear=ayear,ASem=asem,MYear=myear,MSem=msem,\
                        Dept=dept,Mode=mode,Regulation=regulation)
                    currentRegEventId = currentRegEventId[0].id
                    marks_distribution = MTMarksDistribution.objects.all()
                    for i in range(len(dataset)):
                        row = dataset[i]
                        if((row[2],row[3],row[4],row[5],row[6])==(myear,msem,dept,ayear,regulation) and row[10]=='OEC'):
                            newRow = (row[0],row[1],row[7],row[8],row[9],row[10],currentRegEventId, row[11], row[12], '', '')
                            newDataset.append(newRow)
                        else:
                            newRow = (row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10], row[11], row[12])
                            errorDataset.append(newRow)
                    request.session['newDataset'] = list(newDataset)
                    request.session['currentRegEventId'] = currentRegEventId              
                return render(request, 'MTco_ordinator/BTSubjectsUpload.html', {'form':form, 'errorRows':errorDataset, \
                    'validRows':newDataset, 'marks_distribution':marks_distribution})
        elif request.POST.get('mark_dis_submit'):
            newDataset = Dataset()
            newDataset.headers = ['SubCode', 'SubName', 'Creditable', 'Credits', 'Type', 'Category', 'RegEventId', 'OfferedBy', 'ProgrammeCode', \
                    'DistributionRatio', 'MarkDistribution']
            errorRows = []
            for row in request.session.get('newDataset'):
                row[9] = request.POST.get('ratio_distribution_'+str(row[0])).strip()
                row[10] = int(request.POST.get('mark_distribution_'+str(row[0])))
                newRow = (row[0],row[1],row[2],row[3],row[4],row[5],row[6], row[7], row[8], row[9], row[10])
                mark_distribution = MTMarksDistribution.objects.filter(id=row[10]).first()
                if len(mark_distribution.Distribution.split(',')) != len(row[9].split(':')):
                    errorRows.append(newRow)
                else:
                    newDataset.append(newRow)
            Subject_resource = SubjectStagingResource()
            result = Subject_resource.import_data(newDataset, dry_run=True)
            if not result.has_errors():
                Subject_resource.import_data(newDataset, dry_run=False)
            else:
                errors = result.row_errors()
                indices = set([i for i in range(len(newDataset))])    
                errorIndices = set([i[0]-1 for i in errors])
                cleanIndices = indices.difference(errorIndices)
                cleanDataset = Dataset()
                for i in list(cleanIndices):
                    cleanDataset.append(newDataset[i])
                cleanDataset.headers = newDataset.headers
            
                result1 = Subject_resource.import_data(cleanDataset, dry_run=True)
                if not result1.has_errors():
                    Subject_resource.import_data(cleanDataset, dry_run=False)
                else:
                    print('Something went wrong in plain import')
                errorData = Dataset()
                for i in list(errorIndices):
                    newRow = (newDataset[i][0],newDataset[i][1],newDataset[i][2],\
                        newDataset[i][3],newDataset[i][4],newDataset[i][5],newDataset[i][6], newDataset[i][7], newDataset[i][8], newDataset[i][9], newDataset[i][10])
                    errorData.append(newRow)
                subErrRows = [ (errorData[i][0],errorData[i][1],errorData[i][2],errorData[i][3],\
                errorData[i][4],errorData[i][5],errorData[i][6],errorData[i][7], errorData[i][8], errorData[i][9], errorData[i][10]) for i in range(len(errorData))]
                request.session['subErrRows'] = subErrRows
                request.session['errorRows'] = errorRows
                # request.session['currentRegEventId'] = currentRegEventId              
                return HttpResponseRedirect(reverse('MTSupBTSubjectsUploadErrorHandler'))
            if errorRows:
                return render(request, 'MTco_ordinator/BTSubjectsUpload.html', {'form':form, 'errorRows1':errorRows})
            msg = 'Subjects Uploaded successfully.'

    else:
        form = SubjectsUploadForm(Options=regIDs)
    return (render(request, 'MTco_ordinator/BTSubjectsUpload.html', {'form':form, 'msg':msg}))


@login_required(login_url="/login/")
@user_passes_test(subject_access)
def download_sample_subject_sheet(request):
    from MTco_ordinator.utils import SubjectsTemplateBookGenerator
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',)
    response['Content-Disposition'] = 'attachment; filename=sample-{model}.xlsx'.format(model='BTSubjects')
    BookGenerator = SubjectsTemplateBookGenerator()
    workbook = BookGenerator.generate_workbook()
    workbook.save(response)
    return response
