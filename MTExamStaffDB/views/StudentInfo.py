from django.contrib.auth.decorators import login_required, user_passes_test
from MTsuperintendent.user_access_test import is_ExamStaff
from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from MTExamStaffDB.forms import StudentInfoFileUpload, StudentInfoUpdateForm
from MTExamStaffDB.models import MTStudentInfo
from MTExamStaffDB.resources import StudentInfoResource
from tablib import Dataset
from import_export.formats.base_formats import XLSX


import pandas as pd

@login_required(login_url="/login/")
@user_passes_test(is_ExamStaff)

def StudInfoFileUpload(request):
    if(request.method=='POST'):
        form = StudentInfoFileUpload(request.POST,request.FILES)
        if(form.is_valid()):
            file = form.cleaned_data['file']
            data = bytes()
            for chunk in file.chunks():
                data+=chunk
            dataset = XLSX().create_dataset(data)
            newDataset = Dataset()
            newDataset.headers = ['RegNo','RollNo','Name','Regulation','Dept','AdmissionYear','Gender','Category','GuardianName','Phone','email','Address1','Address2']
            for i in range(len(dataset)):
                row = dataset[i]
                newRow = (row[0],row[1],row[2],row[3],row[4],row[12],row[5],row[6],row[7],row[8],row[9],row[10],row[11])
                newDataset.append(newRow)
            StudInfo_resource = StudentInfoResource()
            result = StudInfo_resource.import_data(newDataset,dry_run=True)
            if(not result.has_errors()):
                StudInfo_resource.import_data(newDataset,dry_run=False)
                msg = 'Student Info updated successfully.'
                return render(request, 'MTExamStaffDB/BTStudentInfoUpload.html',{'form':form, 'msg':msg})
            else:
                errors = result.row_errors()
                indices = set([i for i in range(len(newDataset))])
                errorIndices = set([i[0]-1 for i in errors])
                cleanIndices = indices.difference(errorIndices)
                cleanDataset = Dataset()
                for i in list(cleanIndices):
                    cleanDataset.append(newDataset[i])
                cleanDataset.headers = newDataset.headers

                result1 = StudInfo_resource.import_data(newDataset,dry_run=True)
                if not result1.has_errors():
                    StudInfo_resource.import_data(newDataset,dry_run=False)
                else:
                    print('Something went wrong in plain import')
                
                errorData = Dataset()
                for i in list(errorIndices):
                    errorData.append(newDataset[i])
                studInfoErrRows = [ (errorData[i][0],errorData[i][1],errorData[i][2],errorData[i][3],\
                    errorData[i][4],errorData[i][5],errorData[i][6],errorData[i][7],errorData[i][8],\
                        errorData[i][9], errorData[i][10], errorData[i][11],errorData[i][12] ) for i in range(len(errorData))]
                request.session['studInfoErrRows'] = studInfoErrRows
                return redirect('MTStudentInfoUploadErrorHandlerFacultyInfoStatus')
        else:
            print(form.errors)
            for row in form.fields.values(): print(row)
    else:
        form = StudentInfoFileUpload()
    return  render(request, 'MTExamStaffDB/BTStudentInfoUpload.html',{'form':form})
    
@login_required(login_url="/login/")
@user_passes_test(is_ExamStaff)
def student_info_error_handler(request):
    studInfoErrRows = request.session.get('studInfoErrRows')
    if(request.method == 'POST'):
        form = StudentInfoUpdateForm(studInfoErrRows,request.POST)
        if(form.is_valid()):
            for index, studRow in enumerate(studInfoErrRows):
                if(form.cleaned_data.get('Check' + str(studRow[0]))):
                    MTStudentInfo.objects.filter(RegNo=studRow[0]).update(RollNo = studRow[1],Name = studRow[2],\
                        Regulation = studRow[3], Dept = studRow[4], AdmissionYear = studRow[5], Gender = studRow[6],\
                        Category = studRow[7], GuardianName = studRow[8], Phone = studRow[9], email = studRow[10], Address1 = studRow[11], Address2 = studRow[12] )
            return render(request, 'MTExamStaffDB/BTStudentInfoUploadSuccess.html')

    else:
        form = StudentInfoUpdateForm(Options = studInfoErrRows)
    return(render(request, 'MTExamStaffDB/BTStudentInfoUploadErrorHandler.html',{'form':form}))
    

@login_required(login_url="/login/")
@user_passes_test(is_ExamStaff)
def download_sample_studentinfo_sheet(request):
    from MTco_ordinator.utils import ModelTemplateBookGenerator
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',)
    response['Content-Disposition'] = 'attachment; filename=sample-{model}.xlsx'.format(model='MTStudentInfo')
    BookGenerator = ModelTemplateBookGenerator(MTStudentInfo)
    workbook = BookGenerator.generate_workbook()
    workbook.save(response)
    return response