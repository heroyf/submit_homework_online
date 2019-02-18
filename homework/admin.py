from django.contrib import admin

from submit_homework.custom_site import custom_site
from .models import *

@admin.register(Student, site=custom_site)
class StudentAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_filter = ['classroom']
    list_display = ['id', 'name', 'student_id', 'classroom', 'register_time']

    list_display_links = ['name']


@admin.register(Submit, site=custom_site)
class SubmitAdmin(admin.ModelAdmin):
    search_fields = ['student__name']
    list_filter = ["homework__name"]
    list_display = ['id', 'homework_name', 'student_id', 'student_name', 'teacher']
    ordering = ["-time"]

    def homework_name(self, obj):
        return obj.homework.name

    def student_id(self, obj):
        return obj.student.student_id

    def student_name(self, obj):
        return obj.student.name

    def assistant_name(self, obj):
        return obj.teacher.name


@admin.register(Homework, site=custom_site)
class HomeWorkAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'cutoff', 'can_submit']
    list_display_links = ['name']


@admin.register(Teacher, site=custom_site)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['teacher_id', 'name']
    list_display_links = ['teacher_id']
    search_fields = ['name']


@admin.register(Score, site=custom_site)
class ScoreAdmin(admin.ModelAdmin):
    search_fields = ['student__name']
    list_filter = ['homework__name']
    list_display = ('student_id', 'student_name', 'homework_name', 'score')

    def student_id(self, obj):
        return obj.student.student_id

    def student_name(self, obj):
        return obj.student.name

    def homework_name(self, obj):
        return obj.homework.name


@admin.register(Classroom, site=custom_site)
class ClassroomAdmin(admin.ModelAdmin):
    search_fields = ['classroom']
    list_filter = ['owner']
    list_display = ['classroom', 'status', 'owner', 'created_time']
    filter_horizontal = ('teacher',)


from django.contrib import admin

# Register your models here.
