import datetime
import hashlib
import io
import json
import os
import zipfile
from itertools import chain
from urllib import parse

import xlwt
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import render, redirect

from .forms import StudentForm, RegisterForm, TeacherForm, TeacherPassForm, AddHomeworkForm
from .models import *


# Create your views here.
def index(request):
    if request.session.get('is_login', None):  # 若session保持登录，跳转至个人页面
        return redirect('/profile/')
    login_form = StudentForm()
    return render(request, 'index_student.html', locals())


def login(request):
    if request.session.get('is_login', None):  # 若session保持登录，跳转至个人页面
        return redirect('/profile/')
    if request.method == "POST":
        login_form = StudentForm(request.POST)
        message = "请检查填写的内容！"
        if login_form.is_valid():
            student_id = login_form.cleaned_data['student_id']
            password = login_form.cleaned_data['password']
            try:
                student = Student.objects.get(student_id=student_id)
                if not student.has_confirmed:  # 邮箱是否验证
                    message = "该用户还未通过老师验证！"
                    return render(request, 'index_student.html', locals())
                if student.password == hash_code(password):  # 密码验证
                    request.session['is_login'] = True  # 写入session
                    request.session['student_id'] = student_id
                    message = "学生登录成功"
                    return redirect('/profile/')
                else:
                    message = "密码不正确！"
            except:
                message = "用户不存在！"  # 账号错误返回登录页面
                return render(request, 'index_student.html', locals())
    login_form = StudentForm()  # 如果是GET，返回登录页面
    return render(request, 'index_student.html', locals())


# 哈希加密密码
def hash_code(s, salt='dsa'):
    h = hashlib.sha256()
    s += salt
    h.update(s.encode())
    return h.hexdigest()


def register(request):
    if request.session.get('is_login', None):  # 若session保持登录，跳转至个人页面
        return redirect("/profile/")
    if request.method == "POST":
        register_form = RegisterForm(request.POST)
        message = "请检查填写的内容！"
        if register_form.is_valid():
            student_id = register_form.cleaned_data['student_id']
            name = register_form.cleaned_data['name']
            classroom = register_form.cleaned_data['classroom']
            password1 = register_form.cleaned_data['password1']
            password2 = register_form.cleaned_data['password2']
            if password1 != password2:  # 判断两次密码是否相同
                message = "两次输入的密码不相同！"
                return render(request, 'register.html', locals())
            else:
                try:
                    same_student = Student.objects.get(student_id=student_id)
                    classroom = Classroom.objects.all()
                    if same_student:
                        message = "用户已存在"
                except:
                    new_student = Student.objects.create(student_id=student_id, name=name, classroom=classroom)
                    new_student.password = hash_code(password1)
                    new_student.save()
                    message = "注册成功，请等待老师验证后登录！"
                finally:
                    login_form = StudentForm()
                    return render(request, 'index_student.html', locals())
    register_form = RegisterForm()
    return render(request, 'register.html', locals())


def profile(request):
    if request.session.get('is_login', None):
        result = 0
        student_id = request.session.get("student_id", None)
        try:
            student = Student.objects.get(student_id=student_id)
            student_name = student.name
        except:
            request.session.flush()
            return redirect("/")
        for i, classroom in classroom_choice():
            if classroom == student.classroom:
                result = i
        homeworks = Homework.objects.filter(classroom=result).values()
        scores = Score.objects.filter(student=student)
        submits = Submit.objects.filter(student=student)
        for h in homeworks:
            for s in submits:
                if h["id"] == s.homework_id:  # 作业与提交对应
                    h["last_submit"] = s.time
                    h["scored"] = s.scored
                    h["file"] = s.file.name.split('/')[-1]
                    if s.late:
                        h["late"] = True
            for score in scores:
                if score.homework.id == h["id"]:
                    h["score"] = score.score
                    h["comment"] = score.comment
        for h in homeworks:
            if h["cutoff"] < datetime.datetime.now():
                h["late_submit"] = True
        return render(request, 'profile.html', locals())
    return redirect("/")  # 若未登录重定向到登录页面


# 学生登出
def logout(request):
    if not request.session.get('is_login', None):  # 若未登录重定向到登录页面
        return redirect("/")
    request.session.flush()  # 销毁session
    return redirect("/")


# 学生上传作业
def upload(request):
    if request.session.get('is_login', None):
        file = request.FILES.get("file_data", None)  # 获取http传输的文件及附加信息
        homework_id = request.POST.get("homework_id", None)
        student_id = request.session.get("student_id", None)
        if file and student_id and homework_id:
            student = Student.objects.get(student_id=student_id)
            homework = Homework.objects.get(id=homework_id)
            if student and homework:
                older = Submit.objects.filter(student=student, homework=homework)  # 删除已有提交
                if older:
                    teacher = older[0].teacher
                    older.delete()
                    Score.objects.filter(student=student, homework=homework).delete()  # 删除已有分数
                    new_submit = Submit.objects.create(student=student, homework=homework,
                                                       teacher=teacher, file=file)
                else:
                    teacher = homework.owner
                    homework.save()
                    new_submit = Submit.objects.create(student=student, homework=homework, teacher=teacher, file=file)
                if datetime.datetime.now() > homework.cutoff:  # 若已过截止时间标记为补交
                    new_submit.late = True
                new_submit.save()
                data = {"success": True}
            else:
                data = {"success": False}
        else:
            data = {"success": False}
    else:
        data = {"success": False}
    return HttpResponse(json.dumps(data))


# 文件迭代器
def file_iterator(file_name, chunk_size=512):
    with open(file_name, 'rb') as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break


# 学生下载已提交作业
def download(request):
    if request.session.get('is_login', None):
        student_id = request.session.get("student_id", None)
        homework_id = request.GET.get("homework_id", None)
        homework = Homework.objects.get(id=homework_id)
        student = Student.objects.get(student_id=student_id)
        the_file_name = Submit.objects.get(homework=homework, student=student).file.name
        response = StreamingHttpResponse(file_iterator(the_file_name))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename=' + parse.quote(the_file_name.split('/')[-1])
        return response

def login_teacher(request):
    if request.session.get('t_login', None):  # 若session保持登录，跳转至个人页面
        return redirect('/t_profile/')
    if request.method == "POST":
        login_form = TeacherForm(request.POST)
        message = "请检查填写的内容！"
        if login_form.is_valid():
            teacher_id = login_form.cleaned_data['teacher_id']
            password = login_form.cleaned_data['password']
            try:
                teacher = Teacher.objects.get(teacher_id=teacher_id)
                if teacher.password == password:  # 密码验证
                    request.session['t_login'] = True  # 写入session
                    request.session['teacher_id'] = teacher_id
                    message = "教师登录成功"
                    return redirect('/t_profile/')
                else:
                    message = "密码不正确！"
            except:
                message = "用户不存在！"  # 账号错误返回登录页面
                return render(request, 'index_teacher.html', locals())
    login_form = TeacherForm()  # 如果是GET，返回登录页面
    return render(request, 'index_teacher.html', locals())

# 教师登出
def tlogout(request):
    if not request.session.get('t_login', None):  # 若未登录重定向到登录页面
        return redirect("/teacher/")
    request.session.flush()  # 销毁session
    return redirect("/teacher/")

# 教师个人页面
def teacher_profile(request):
    if request.session.get('t_login', None):
        teacher_id = request.session.get("teacher_id", None)
        teacher = Teacher.objects.get(teacher_id=teacher_id)
        manage_classrooms = Classroom.objects.filter(teacher=teacher)
        homeworks = Homework.objects.filter(owner=teacher)
        homeworklist = homeworks.values()
        for h in homeworklist:
            h["mine"] = Submit.objects.filter(teacher=teacher, homework=h["id"]).count() # 分配给老师的作业数
            h["to_score"] = Submit.objects.filter(teacher=teacher, scored=False, homework=h["id"]).count()  # 未批改的作业数
            if h["cutoff"] < datetime.datetime.now():
                h["late"] = True
            now = datetime.datetime.now()
        if teacher.password == teacher_id:
            message = "密码与工号相同，请尽快修改密码！"
        return render(request,'teacher_profile.html', locals())
    return redirect("/teacher/")

# 查看所有学生
def all_students(request):
    if request.session.get('t_login', None):
        query = request.POST.get("query")
        if query:
            try:
                search = Student.objects.get(student_id__icontains=query)
                return redirect("/o_student/?student_id={}".format(search.student_id))
            except:
                message = "没有该学生，请确认输入是否正确！"
        teacher_id = request.session.get("teacher_id", None)
        teacher = Teacher.objects.get(teacher_id=teacher_id)
        manage_classrooms = Classroom.objects.filter(teacher=teacher)
        students = Student.objects.none()
        if manage_classrooms:
            for classroom in manage_classrooms:
                students = students | Student.objects.filter(classroom=classroom)
            studentlist = students.values()
            homeworks = Homework.objects.filter(owner=teacher)
            homeworklist = homeworks.values()
            scorelist = []
            for s in students:
                scores = []
                for h in homeworks:
                    try:
                        score = Score.objects.get(student=s, homework=h)
                        scores.append(str(score.score))
                    except:
                        scores.append('-')
                scorelist.append(scores)
            i = 0
            for s in studentlist:
                s["scores"] = scorelist[i]
                i = i+1
            not_submit_dict = {}
            for h in homeworks:
                not_submit = []
                for s in students:
                    try:
                        submit = Submit.objects.get(student=s, homework=h)
                    except:
                        if s.has_confirmed:
                            not_submit.append(s.name)
                        else:
                            pass
                not_submit_dict.update({h:not_submit})
            return render(request, "all_students.html", locals())
        else:
            message = "暂无学生，请添加需要管理的班级"
            return render(request, "all_students.html", locals())
    return redirect("/teacher/")

# 查看单个学生作业信息
def one_student(request):
    if request.session.get('t_login', None):
        student_id = request.GET.get("student_id", None)
        teacher_id = request.session.get("teacher_id", None)
        teacher = Teacher.objects.get(teacher_id=teacher_id)
        student = Student.objects.get(student_id=student_id)
        submits = Submit.objects.filter(student=student)
        homeworks = Homework.objects.all().filter(owner=teacher).values()
        scores = Score.objects.filter(student=student)
        for h in homeworks:
            for s in submits:
                if s.homework.id == h["id"]:
                    h["submit"] = True
                    h["submit_time"] = s.time
                    h["scored"] = s.scored
                    h["submit_id"] = s.id
                    h["late"] = s.late
                    h["student_id"] = s.student_id
                    h["file"] = s.file.name.split('/')[-1]
                    h["teacher_name"] = s.teacher.name
            for s in scores:
                if s.homework.id == h["id"]:
                    h["score"] = s.score
        return render(request, 'one_student.html', locals())
    return redirect("/teacher/")

# 作业评分
def score(request):
    message = {"success": False}
    if request.session.get('t_login', None):
        teacher_id = request.session.get("teacher_id", None)
        submit_id = request.POST.get("submit_id", None)
        score = float(request.POST.get("score", None))
        comment = request.POST.get("comment", None)
        if submit_id and score != None and score > 0 and score < 100:
            try:  # 防止评分时上传新版本
                submit = Submit.objects.get(id=submit_id)
            except:
                message["message"] = "学生提交了新版本，请重新查看"
                return HttpResponse(json.dumps(message), content_type='application/json')
            try:
                Score.objects.get(student=submit.student, homework=submit.homework).delete()
            finally:
                new_score = Score.objects.create(student=submit.student, homework=submit.homework,
                                                        score=score)
                new_score.save()
            if comment != "":
                new_score.comment = comment
                new_score.save()
            submit.scored = True
            teacher = Teacher.objects.get(teacher_id=teacher_id)
            submit.teacher = teacher
            submit.save()
            message = {"success": True, "score": str(score), "teacher": teacher.name}
    return HttpResponse(json.dumps(message), content_type='application/json')

# 教师下载学生作业
def t_download(request):
    if request.session.get('t_login', None):
        student_id = request.GET.get("student_id", None)
        homework_id = request.GET.get("homework_id", None)
        homework = Homework.objects.get(id=homework_id)
        student = Student.objects.get(student_id=student_id)
        the_file_name = Submit.objects.get(homework=homework, student=student).file.name
        response = StreamingHttpResponse(file_iterator(the_file_name))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename=' + parse.quote(the_file_name.split('/')[-1])
        return response
    return redirect("/teacher/")

# 教师批量下载学生作业
def teacher_zip_download(request):
    if request.session.get('t_login', None):
        teacher_id = request.session.get("teacher_id", None)
        all = json.loads(request.GET.get("all", None))
        to_score = json.loads(request.GET.get("to_score", None))
        homework_id = request.GET.get("homework_id", None)
        homework = Homework.objects.get(id=homework_id)
        if not all and not to_score:
            teacher = Teacher.objects.get(teacher_id=teacher_id)
            submits = Submit.objects.filter(homework=homework, teacher=teacher)
        if not all and to_score:
            teacher = Teacher.objects.get(teacher_id=teacher_id)
            submits = Submit.objects.filter(homework=homework, scored=False, teacher=teacher)
        if all and not to_score:
            submits = Submit.objects.filter(homework=homework)
        if all and to_score:
            submits = Submit.objects.filter(homework=homework, scored=False)
        the_file_names = [s.file.name for s in submits]
        now = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        z_name = os.path.join(homework.name + "_" + now + ".zip")
        z_file = zipfile.ZipFile(z_name, 'w')
        for f in the_file_names:
            z_file.write(f, f.split('/')[-1])
        z_file.close()
        z_file = open(z_name, 'rb')
        data = z_file.read()
        z_file.close()
        os.remove(z_file.name)
        response = HttpResponse(data, content_type='application/zip')
        response['Content-Disposition'] = 'attachment;filename=' + parse.quote(z_name.split('/')[-1])
        return response
    return redirect("/teacher/")


def get_excel_stream(file):
    # StringIO操作的只能是str，如果要操作二进制数据，就需要使用BytesIO。
    excel_stream = io.BytesIO()
    # 这点很重要，传给save函数的不是保存文件名，而是一个BytesIO流（在内存中读写）
    file.save(excel_stream)
    # getvalue方法用于获得写入后的byte将结果返回给re
    res = excel_stream.getvalue()
    excel_stream.close()
    return res


# 下载所有学生名单及作业成绩excel表单
def get_excel(request):
    teacher_id = request.session.get("teacher_id", None)
    teacher = Teacher.objects.get(teacher_id=teacher_id)
    manage_classrooms = Classroom.objects.filter(teacher=teacher)
    students = Student.objects.none()
    for classroom in manage_classrooms:
        students = students | Student.objects.all().filter(classroom=classroom)
    homeworks = Homework.objects.all().filter(owner=teacher)
    lines = []
    for s in students:
        line = []
        line.append(s.student_id)
        line.append(s.name)
        line.append(s.classroom)
        for h in homeworks:
            try:
                score = Score.objects.get(student=s, homework=h)
                line.append(str(score.score))
            except:
                line.append('-')
        lines.append(line)
    file = xlwt.Workbook()
    table = file.add_sheet("this", cell_overwrite_ok=True)
    title = ['学号', '姓名', '班级'] + [h.name for h in homeworks]
    for col, t in enumerate(title):
        table.write(0, col, t)
    for row, line in enumerate(lines):
        for col, item in enumerate(line):
            table.write(row + 1, col, item)
    now = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    file_name = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), now + ".xls")
    file.save(file_name)
    res = get_excel_stream(file)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment;filename=' + parse.quote(file_name.split('/')[-1])
    # 将文件流写入到response返回
    response.write(res)
    os.remove(file_name)
    return response


def students_manage(request):
    if request.session.get('t_login', None):
        teacher_id = request.session.get("teacher_id", None)
        teacher = Teacher.objects.get(teacher_id=teacher_id)
        manage_classrooms = Classroom.objects.filter(teacher=teacher)
        students = Student.objects.none()
        for classroom in manage_classrooms:
            students = students | Student.objects.filter(classroom=classroom)
        return render(request, 'student_manage.html', locals())

# 验证学生
def students_has_confirmed(request):
    message = {"success": False}
    if request.session.get('t_login', None):
        teacher_id = request.session.get("teacher_id", None)
        teacher = Teacher.objects.get(teacher_id=teacher_id)
        student_id = request.POST.get("student_id", None)
        student = Student.objects.get(student_id=student_id)
        if not student.has_confirmed:
            student.has_confirmed = True
            student.save()
            message = {"success": True, "teacher": teacher.name}
        else:
            message = {"success": False}
        return HttpResponse(json.dumps(message), content_type='application/json')

# 删除学生
def student_delete(request):
    message = {"success": False}
    if request.session.get('t_login', None):
        teacher_id = request.session.get("teacher_id", None)
        teacher = Teacher.objects.get(teacher_id=teacher_id)
        student_id = request.POST.get("student_id", None)
        student = Student.objects.get(student_id=student_id).delete()
        message = {"success": True, "teacher": teacher.name}
        return HttpResponse(json.dumps(message), content_type='application/json')

def password_change_t(request):
    if request.session.get('t_login', None):
        teacher_id = request.session.get("teacher_id", None)
        teacher = Teacher.objects.filter(teacher_id=teacher_id)
        if request.method == "POST":
            change_password_form = TeacherPassForm(request.POST)
            message_p = "请检查填写的内容！"
            if change_password_form.is_valid():
                password1 = change_password_form.cleaned_data['password1']
                password2 = change_password_form.cleaned_data['password2']
                if password1 != password2:  # 判断两次密码是否相同
                    message = "两次输入的密码不相同！"
                    return render(request, 't_password.html', locals())
                else:
                    teacher.update(password=password1)
                    message_p = "修改成功！请重新登录"
                    request.session.flush()
                    return redirect("/teacher/")
        change_password_form = TeacherPassForm()
        return render(request, 't_password.html', locals())

# 发布作业
def add_homework(request):
    if request.session.get('t_login', None):
        teacher_id = request.session.get("teacher_id", None)
        teacher = Teacher.objects.get(teacher_id=teacher_id)
        manage_classrooms = Classroom.objects.filter(teacher=teacher)
        if request.method == "POST":
            add_homework_form = AddHomeworkForm(request.POST)
            message_add = "请检查填写的内容！"
            if add_homework_form.is_valid():
                name = add_homework_form.cleaned_data['name']
                classroom_result = 0
                classroom = add_homework_form.cleaned_data['classroom']
                for i,j in classroom_choice():
                    if j==classroom:
                        classroom_result = i
                cutoff = add_homework_form.cleaned_data['cutoff']
                new_homework = Homework.objects.create(name=name, classroom=classroom_result, cutoff=cutoff, owner=teacher)
                new_homework.save()
                message_add_homework = "发布作业成功,点击返回主页"
                return render(request, 'add_homework.html', locals())
                # return redirect("/t_profile/")
        add_homework_form = AddHomeworkForm()
        return render(request, 'add_homework.html', locals())

# 删除作业
def delete_homework(request):
    message = {"success": False}
    if request.session.get('t_login', None):
        teacher_id = request.session.get("teacher_id")
        teacher = Teacher.objects.get(teacher_id=teacher_id)
        homework_id = request.POST.get("homework_id")
        Homework.objects.get(id=homework_id).delete()
        message = {"success": True, "teacher": teacher.name}
        return HttpResponse(json.dumps(message), content_type='application/json')


