# Generated by Django 4.0.4 on 2022-06-25 10:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('SupExamDBRegistrations', '0031_rename_email_facultyinfo_email'),
    ]

    operations = [
        migrations.RenameField(
            model_name='facultyinfo',
            old_name='email',
            new_name='Email',
        ),
    ]
