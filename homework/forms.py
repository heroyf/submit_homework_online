from django import forms

from .models import Classroom


class StudentForm(forms.Form):
    student_id = forms.CharField(label="学号", max_length=10,
                                 widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '学号'}))
    password = forms.CharField(label="密码", max_length=256,
                               widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '密码(请务必记住，丢失请联系管理员)'}))


def get_classroom():
    r = []
    for obj in Classroom.objects.all():
        r.append((obj.classroom, obj.classroom))
    return r


class RegisterForm(forms.Form):
    student_id = forms.CharField(label="学号", max_length=20, widget=forms.TextInput(attrs={'class': 'form-control'}))
    name = forms.CharField(label="姓名", max_length=128, widget=forms.TextInput(attrs={'class': 'form-control'}))
    classroom = forms.ChoiceField(label="班级",
                                  choices=get_classroom(),
                                  widget=forms.Select(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label="密码", max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="确认密码", max_length=256,
                                widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class TeacherForm(forms.Form):
    teacher_id = forms.CharField(label="教师工号", max_length=10,
                                 widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '工号'}))
    password = forms.CharField(label="密码", max_length=256,
                               widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '密码'}))


class TeacherPassForm(forms.Form):
    password1 = forms.CharField(label="密码", max_length=256, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="确认密码", max_length=256,
                                widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class AddHomeworkForm(forms.Form):
    name = forms.CharField(label="作业名", max_length=10,
                           widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '作业名'}))
    classroom = forms.ChoiceField(label="分配的班级",
                                  choices=get_classroom(),
                                  widget=forms.Select(attrs={'class': 'form-control'}))
    cutoff = forms.DateTimeField(label="截止日期", input_formats=['%Y/%m/%d %H:%M'], widget=forms.DateTimeInput(
        attrs={'class': 'form-control datetimepicker-input','placeholder': '截止日期'}))
