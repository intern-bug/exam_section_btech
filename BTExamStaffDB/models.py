from django.db import models

# Create your models here.

class BTStudentInfo(models.Model):
    CYCLE_CHOICES = (
        (10,'PHYSICS'),
        (9,'CHEMISTRY')
    )
    RegNo = models.IntegerField()
    RollNo = models.IntegerField()
    Name = models.CharField(max_length=255)
    Regulation = models.IntegerField()
    Dept = models.IntegerField()
    AdmissionYear = models.IntegerField()
    Gender = models.CharField(max_length=10)
    Category = models.CharField(max_length=30)
    GuardianName = models.CharField(max_length=255)
    Phone = models.TextField()
    email = models.TextField()
    Address1 = models.TextField()
    Address2 = models.TextField(null=True)
    Cycle = models.IntegerField(default=0, choices=CYCLE_CHOICES)

    class Meta:
        db_table = 'BTStudentInfo'
        constraints = [
            models.UniqueConstraint(fields=['RegNo'], name='unique_BTStudentInfo_RegNo'),
            models.UniqueConstraint(fields=['RollNo'], name='unique_BTStudentInfo_RollNo'),
        ]
        managed = True


class BTYearMandatoryCredits(models.Model):
    Regulation = models.IntegerField()
    Dept = models.IntegerField()
    BYear = models.IntegerField()
    Credits = models.IntegerField()
    class Meta:
        db_table = 'BTYearMandatoryCredits'
        unique_together = (('Regulation', 'Dept', 'BYear'))
        managed = True


class BTIXGradeStudents(models.Model):
    GRADE_CHOICES = (
        ('I', 'I'),
        ('X', 'X')
    )
    Registration = models.ForeignKey('BTco_ordinator.BTStudentRegistrations', on_delete=models.CASCADE)
    Grade = models.CharField(max_length=1, choices=GRADE_CHOICES)

    class Meta:
        db_table = 'BTIXGradeStudents'
        unique_together = (('Registration', 'Grade'))
        managed = True


class BTFacultyInfo(models.Model):
    FacultyId = models.IntegerField(default=100)
    Name = models.CharField(max_length=255)
    Phone = models.TextField()
    Email = models.CharField(max_length=255)
    Dept = models.IntegerField()
    Working = models.BooleanField()
    class Meta:
        db_table = 'BTFacultyInfo'
        constraints = [
            models.UniqueConstraint(fields=['FacultyId'], name='unique_BTfacultyinfo_facultyid')
        ]
        managed = True
