from django import forms
from BTsuperintendent.models import BTProgrammeModel,BTRegulation
from BTco_ordinator.models import BTStudentBacklogs, BTFacultyAssignment, BTSubjects, BTStudentRegistrations
from BTfaculty.models import BTMarks_Staging
import datetime


class DBYBSAYASSelectionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(DBYBSAYASSelectionForm, self).__init__(*args, **kwargs)
        departments = BTProgrammeModel.objects.filter(ProgrammeType='UG')
        deptChoices =[(rec.Dept, rec.Specialization) for rec in departments ]
        deptChoices = [(0,'--Select Dept--')] + deptChoices
        bYearChoices = [(0,'--Select BYear--'),(1,1), (2, 2),(3, 3),(4, 4)]
        bSemChoices = [(0,'--Select BSem--'),(1,1),(2,2)]
        aYearChoices = [(0,'--Select AYear--')] + [(i,i) for i in range(2015,datetime.datetime.now().year+1)]
        aSemChoices = [(0,'--Select ASem--')] + [(1,1),(2,2),(3,3)]
        aYearBox = forms.IntegerField(label='Select AYear', required=False, widget=forms.Select(choices=aYearChoices,attrs={'onchange':'submit();', 'required':'True'}))
        aSemBox = forms.IntegerField(label='Select ASem', required=False, widget=forms.Select(choices=aSemChoices, attrs={'required':'True'}))
        bYearBox = forms.IntegerField(label='Select BYear', required=False, widget=forms.Select(choices=bYearChoices,attrs={'onchange':'submit();', 'required':'True'}))
        bSemBox = forms.IntegerField(label='Select BSem', required=False, widget=forms.Select(choices=bSemChoices, attrs={'required':'True'}))
        deptBox = forms.CharField(label='Select Department', required=False, widget=forms.Select(choices=deptChoices, attrs={'required':'True'}))
        rChoices = [(0,'--Select Regulation--')]
        statusBox = forms.ChoiceField(label='Status', required=False, widget=forms.RadioSelect(attrs={'required':'True'}), choices=[(0, 'Disable'), (1, 'Enable')])
        rollBox = forms.ChoiceField(label='RollList Status', required=False, widget=forms.RadioSelect(attrs={'required':'True'}), choices=[(0, 'Disable'), (1, 'Enable')])
        regBox = forms.ChoiceField(label='Registration Status', required=False, widget=forms.RadioSelect(attrs={'required':'True'}), choices=[(0, 'Disable'), (1, 'Enable')])
        marksBox = forms.ChoiceField(label='Marks Status', required=False, widget=forms.RadioSelect(attrs={'required':'True'}), choices=[(0, 'Disable'), (1, 'Enable')])
        gradesBox = forms.ChoiceField(label='Grades Status', required=False, widget=forms.RadioSelect(attrs={'required':'True'}), choices=[(0, 'Disable'), (1, 'Enable')])
        modeBox = forms.ChoiceField(label='Select Mode', required=False, widget=forms.RadioSelect(attrs={'required':'True'}),choices = [('R', 'Regular'),('B','Backlog'),('D','DroppedRegular'),('M','Makeup')])
        regulationBox = forms.IntegerField(label='Select Regulation', required=False, widget=forms.Select(choices=rChoices, attrs={'required':'True'}))
        self.fields['aYear'] = aYearBox
        self.fields['aSem'] = aSemBox
        self.fields['bYear'] = bYearBox
        self.fields['bSem'] = bSemBox
        self.fields['dept'] = deptBox
        self.fields['regulation'] = regulationBox
        self.fields['status'] = statusBox
        self.fields['roll-status'] = rollBox
        self.fields['reg-status'] = regBox
        self.fields['marks-status'] = marksBox
        self.fields['grades-status'] = gradesBox
        self.fields['mode'] = modeBox
        if 'aYear' in self.data and 'bYear' in self.data and self.data['aYear']!='' and \
            self.data['bYear']!='' and self.data['aYear']!='0' and \
            self.data['bYear']!='0':
            regulations = BTRegulation.objects.filter(AYear=self.data.get('aYear')).filter(BYear = self.data.get('bYear'))
            dropped_course_regulations = BTRegulation.objects.filter(AYear=str(int(self.data.get('aYear'))-1),BYear=self.data.get('bYear'))
            backlog_course_regulations = BTStudentBacklogs.objects.filter(BYear=self.data.get('bYear'))
            backlog_course_regulations = [(regu.Regulation,regu.Regulation) for regu in backlog_course_regulations]
            dropped_course_regulations = [(regu.Regulation,regu.Regulation) for regu in dropped_course_regulations]
            regulations = [(regu.Regulation,regu.Regulation) for regu in regulations]
            regulations +=  dropped_course_regulations + backlog_course_regulations
            regulations = list(set(regulations))
            rChoices += regulations
            self.fields['regulation'] = forms.IntegerField(label='Select Regulation', required=False, widget=forms.Select(choices=rChoices, attrs={'required':'True'}))
            if self.data.get('bYear')!='1':
                departments = BTProgrammeModel.objects.filter(ProgrammeType='UG').exclude(Dept__in=[10,9])
            else:
                departments = BTProgrammeModel.objects.filter(ProgrammeType='UG',Dept__in=[10,9])
            deptChoices +=[(rec.Dept, rec.Specialization) for rec in departments ]
            deptBox = forms.CharField(label='Select Department', required=False, widget=forms.Select(choices=deptChoices, attrs={'required':'True'}))
            self.fields['dept'] = deptBox
        elif self.data.get('bYear'):
            if self.data.get('bYear') != '1':
                departments = BTProgrammeModel.objects.filter(ProgrammeType='UG').exclude(Dept__in=[10,9])
            else:
                departments = BTProgrammeModel.objects.filter(ProgrammeType='UG',Dept__in=[10,9])
            deptChoices +=[(rec.Dept, rec.Specialization) for rec in departments ]
            deptBox = forms.CharField(label='Select Department', required=False, widget=forms.Select(choices=deptChoices, attrs={'required':'True'}))
            self.fields['dept'] = deptBox



class CreateRegistrationEventForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(CreateRegistrationEventForm, self).__init__(*args, **kwargs)
        deptChoices = [('','--Select Dept--')]
        bYearChoices = [('','--Select BYear--'),(1,1), (2, 2),(3, 3),(4, 4)]
        bSemChoices = [('','--Select BSem--'),(1,1),(2,2)]
        aYearChoices = [('','--Select AYear--')] + [(i,i) for i in range(2015,datetime.datetime.now().year+1)]
        aSemChoices = [('','--Select ASem--')] + [(1,1),(2,2),(3,3)]
        aYearBox = forms.IntegerField(label='Select AYear', required=False, widget=forms.Select(choices=aYearChoices,attrs={'onchange':'submit();', 'required':'True'}))
        aSemBox = forms.IntegerField(label='Select ASem', required=False, widget=forms.Select(choices=aSemChoices, attrs={'required':'True'}))
        bYearBox = forms.IntegerField(label='Select BYear', required=False, widget=forms.Select(choices=bYearChoices,attrs={'onchange':'submit();', 'required':'True'}))
        bSemBox = forms.IntegerField(label='Select BSem', required=False, widget=forms.Select(choices=bSemChoices, attrs={'required':'True'}))
        deptBox = forms.CharField(label='Select Department', required=False, widget=forms.Select(choices=deptChoices, attrs={'required':'True'}))
        rChoices = [('','--Select Regulation--')]
        regulationBox = forms.IntegerField(label='Select Regulation', required=False, widget=forms.Select(choices=rChoices, attrs={'required':'True'}))
        modeBox = forms.ChoiceField(label='Select Mode', required=False, widget=forms.RadioSelect(attrs={'required':'True'}),choices = [('R', 'Regular'),('B','Backlog'),('D','DroppedRegular'),('M','Makeup')])
        self.fields['aYear'] = aYearBox
        self.fields['aSem'] = aSemBox
        self.fields['bYear'] = bYearBox
        self.fields['bSem'] = bSemBox
        self.fields['dept'] = deptBox
        self.fields['regulation'] = regulationBox
        self.fields['mode'] = modeBox
        if self.data.get('aYear') and self.data.get('bYear'):
            regulations = BTRegulation.objects.filter(AYear=self.data.get('aYear')).filter(BYear = self.data.get('bYear'))
            dropped_course_regulations = BTRegulation.objects.filter(AYear=str(int(self.data.get('aYear'))-1),BYear=self.data.get('bYear'))
            backlog_course_regulations = BTStudentBacklogs.objects.filter(BYear=self.data.get('bYear'))
            backlog_course_regulations = [(regu.Regulation,regu.Regulation) for regu in backlog_course_regulations]
            dropped_course_regulations = [(regu.Regulation,regu.Regulation) for regu in dropped_course_regulations]
            regulations = [(regu.Regulation,regu.Regulation) for regu in regulations]
            regulations +=  dropped_course_regulations + backlog_course_regulations
            regulations = list(set(regulations))
            rChoices += regulations
            self.fields['regulation'] = forms.IntegerField(label='Select Regulation', required=False, widget=forms.Select(choices=rChoices, attrs={'required':'True'}))
            if self.data.get('bYear')!='1':
                departments = BTProgrammeModel.objects.filter(ProgrammeType='UG').exclude(Dept__in=[10,9])
            else:
                departments = BTProgrammeModel.objects.filter(ProgrammeType='UG',Dept__in=[10,9])
            deptChoices +=[(rec.Dept, rec.Specialization) for rec in departments ]
            deptChoices += [('all', 'All Departments')]
            deptBox = forms.CharField(label='Select Department', required=False, widget=forms.Select(choices=deptChoices, attrs={'required':'True'}))
            self.fields['dept'] = deptBox

        elif self.data.get('bYear'):
            if self.data.get('bYear') != '1':
                departments = BTProgrammeModel.objects.filter(ProgrammeType='UG').exclude(Dept__in=[10,9])
            else:
                departments = BTProgrammeModel.objects.filter(ProgrammeType='UG',Dept__in=[10,9])
            deptChoices +=[(rec.Dept, rec.Specialization) for rec in departments ]
            deptChoices += [('all', 'All Departments')]
            deptBox = forms.CharField(label='Select Department', required=False, widget=forms.Select(choices=deptChoices, attrs={'required':'True'}))
            self.fields['dept'] = deptBox


class GradeChallengeForm(forms.Form):
    def __init__(self, co_ordinator, *args, **kwargs):
        super(GradeChallengeForm, self).__init__(*args, **kwargs)
        faculty = BTFacultyAssignment.objects.filter(Faculty__Dept=co_ordinator.Dept, RegEventId__BYear=co_ordinator.BYear, RegEventId__Status=1)
        # regIDs = BTRegistrationStatus.objects.filter(Status=1, Dept=co_ordinator.Dept, BYear=faculty.BYear)
        regEventIDKVs = [(fac.RegEventId.id,fac.RegEventId.__str__()) for fac in faculty]
        regEventIDKVs = [('','-- Select Registration Event --')] + regEventIDKVs
        SUBJECT_CHOICES = [('', 'Choose Subject')]
        ROLL_CHOICES = [('', '--------')]
        EXAM_TYPE_CHOICES = [('', '--------')]
        self.fields['regID'] = forms.CharField(label='Registration Event', widget = forms.Select(choices=regEventIDKVs, attrs={'onchange':"submit()"}))
        self.fields['subject'] = forms.CharField(label='Choose Subject', widget = forms.Select(choices=SUBJECT_CHOICES))
        self.fields['regd_no'] = forms.ChoiceField(label='Choose Roll Number', widget=forms.Select(choices=ROLL_CHOICES))
        self.fields['exam-type'] = forms.ChoiceField(label='Choose Exam Type', widget=forms.Select(choices=EXAM_TYPE_CHOICES))

        if self.data.get('regID') and self.data.get('subject') and self.data.get('regd_no'):
            subject = BTSubjects.objects.get(id=self.data.get('subject'))
            self.subject = subject
            EXAM_TYPE_CHOICES += subject.MarkDistribution.distributions()
            self.fields['exam-type'] = forms.ChoiceField(label='Choose Exam Type', widget=forms.Select(choices=EXAM_TYPE_CHOICES))
            self.fields['mark'] = forms.CharField(label='Enter Marks', widget=forms.TextInput(attrs={'type':'number'}))
        elif self.data.get('regID') and self.data.get('subject'):
            marks_list = BTMarks_Staging.objects.filter(Registration__RegEventId=self.data.get('regID'), Registration__sub_id=self.data.get('subject')).order_by('Registration__RegNo')
            ROLL_CHOICES += [(mark.id, mark.Registration.RegNo) for mark in marks_list]
            self.fields['regd_no'] = forms.ChoiceField(label='Choose Roll Number', widget=forms.Select(choices=ROLL_CHOICES, attrs={'onchange':"submit()"}))
        elif self.data.get('regID'):
            student_registrations = BTStudentRegistrations.objects.filter(RegEventId=self.data.get('regID'))
            self.regs = student_registrations
            subjects = BTSubjects.objects.filter(id__in=student_registrations.values_list('sub_id', flat=True))
            SUBJECT_CHOICES += [(sub.id, sub.SubCode) for sub in subjects]
            self.fields['subject'] = forms.CharField(label='Choose Subject', widget = forms.Select(choices=SUBJECT_CHOICES, attrs={'onchange':"submit()"}))
    
    def clean_mark(self):
        if 'mark' in self.cleaned_data.keys():
            mark = self.cleaned_data.get('mark')
            exam_type = self.cleaned_data.get('exam-type')
            exam_inner_index = exam_type.split(',')[1]
            exam_outer_index = exam_type.split(',')[0]
            mark_dis_limit = self.subject.MarkDistribution.get_mark_limit(exam_outer_index, exam_inner_index)
            if mark > mark_dis_limit:
                raise forms.ValidationError('Entered mark is greater than the maximum marks.')
            return mark
        return None

    
class GradeChallengeStatusForm(forms.Form):
    def __init__(self, subjects, *args, **kwargs):
        super(GradeChallengeStatusForm, self).__init__(*args, **kwargs)
        subject_Choices=[]
        for sub in subjects:
            subject_Choices+= [(str(sub.Subject.id)+':'+str(sub.RegEventId.id),sub.RegEventId.__str__()+', '+\
                str(sub.Subject.SubCode))]
        subject_Choices = list(set(subject_Choices))
        subject_Choices = [('','--Select Subject--')] + subject_Choices
        self.fields['subject'] = forms.CharField(label='Choose Subject', max_length=26, widget=forms.Select(choices=subject_Choices))
