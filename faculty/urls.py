from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from faculty.views import attendance_shortage, grades_threshold, courses, marks_upload, grades_generate

urlpatterns =[
    path('AttendanceShoratgeUpload',attendance_shortage.attendance_shortage_upload,name='AttendanceShoratgeUpload'),
    path('DownloadSampleAttendanceShortageSheet', attendance_shortage.download_sample_attendance_shortage_sheet, name='DownloadSampleAttendanceShortageSheet'),
    path('AttendanceShoratgeStatus',attendance_shortage.attendance_shortage_status,name='AttendanceShoratgeStatus'),
    path('GradesThreshold', grades_threshold.grades_threshold, name='GradesThreshold'),
    path('GradesThresholdAssign/<int:pk>', grades_threshold.grades_threshold_assign, name='GradesThresholdAssign'),
    path('GradesThresholdStatus', grades_threshold.grades_threshold_status, name='GradesThresholdStatus'),
    path('CoursesAssigned', courses.courses_assigned, name='CoursesAssigned'),
    path('MarksUpload', marks_upload.marks_upload, name='MarksUpload'),
    path('MarksUploadStatus', marks_upload.marks_upload_status, name='MarksUploadStatus'),
    path('MarksUpdate/<int:pk>', marks_upload.marks_update, name='MarksUpdate'),
    path('MarksHodSubmission', marks_upload.marks_hod_submission, name='MarksHodSubmission'),
    path('SampleMarksExcelSheetDownload', marks_upload.download_sample_excel_sheet, name='SampleMarksExcelSheetDownload'),
    path('GradesGenerate', grades_generate.grades_generate, name='GradesGenerate'),
    path('GradesStatus', grades_generate.grades_status, name='GradesStatus'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
