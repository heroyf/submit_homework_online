from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.dispatch import receiver
import os

# Create your models here.

# 学生
class Student(models.Model):
    student_id = models.CharField(max_length=10, null=False, blank=False, verbose_name="学生学号")  # 学号
    classroom = models.CharField(max_length=50, verbose_name="班级")  # 班级
    name = models.CharField(max_length=128, null=False, blank=False, verbose_name="学生姓名")  # 姓名
    password = models.CharField(max_length=256, null=False, blank=False, verbose_name="密码")  # 密码
    register_time = models.DateTimeField(auto_now_add=True, verbose_name="注册时间")  # 注册时间
    has_confirmed = models.BooleanField(default=False, verbose_name="已验证")  # 是否已邮箱验证

    class Meta:
        ordering = ["student_id"]
        verbose_name = verbose_name_plural = "学生"

    def __str__(self):
        return self.name


# 班级
class Classroom(models.Model):
    STATUS_ITEM = (
        (1, '可用'),
        (2, '过期'),
    )
    classroom = models.CharField(max_length=50, default="", verbose_name="班级")
    status = models.PositiveIntegerField(default=1, choices=STATUS_ITEM, verbose_name="状态")
    teacher = models.ManyToManyField('Teacher', verbose_name='所属管理的老师')

    owner = models.ForeignKey(User, verbose_name="创建人")
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = verbose_name_plural = "班级"

    def __str__(self):
        return self.classroom

# 教师
class Teacher(models.Model):
    teacher_id = models.CharField(max_length=10, null=False, blank=False, verbose_name="教师工号")  # 学号
    name = models.CharField(max_length=128, null=False, blank=False, verbose_name="教师姓名")  # 姓名
    password = models.CharField(max_length=256, null=False, blank=False, verbose_name="密码")  # 密码

    class Meta:
        verbose_name = verbose_name_plural = "教师"

    def __str__(self):
        return self.name



# 评分
class Score(models.Model):
    score = models.PositiveSmallIntegerField(null=False, blank=False, default=0, verbose_name="分数")  # 分数
    comment = models.TextField(max_length=512, default="", verbose_name="反馈")  # 反馈
    student = models.ForeignKey('Student', default="", verbose_name="学生")  # 关联学生，级联删除
    homework = models.ForeignKey('Homework', default="", verbose_name="作业")  # 关联作业，级联删除

    class Meta:
        verbose_name = verbose_name_plural = "评分"



# 定义文件存储路径
def upload_to(instance, filename):
    return '/'.join([settings.MEDIA_ROOT, instance.homework.name,
                     instance.homework.name + "_" + instance.student.student_id + "_" + instance.student.name + "." +
                     filename.split('.')[-1]])

def classroom_choice():
    classroom_choices=[]
    i=1
    for obj in Classroom.objects.all():
        classroom_choices.append([i, obj.classroom])
        i+=1
    return classroom_choices

# 作业
class Homework(models.Model):

    name = models.CharField(max_length=128, null=False, blank=False, verbose_name="作业名")  # 名称
    cutoff = models.DateTimeField(verbose_name="截止日期")  # 截止日期
    can_submit = models.BooleanField(default=True, verbose_name="允许提交")  # 是否允许提交

    owner = models.ForeignKey(Teacher, verbose_name="创建人")
    classroom = models.IntegerField(default=1, choices=classroom_choice(), verbose_name="所属班级")
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = verbose_name_plural = "作业"

    def __str__(self):
        return self.name


# 作业提交
class Submit(models.Model):
    student = models.ForeignKey(Student, default="", verbose_name="学生")  # 关联学生，级联删除
    homework = models.ForeignKey(Homework, default="", verbose_name="作业")  # 关联作业，级联删除
    teacher = models.ForeignKey(Teacher, default="", verbose_name="批改人")  # 分配助教，级联删除
    file = models.FileField(upload_to=upload_to, verbose_name="文件")  # 上传文件
    scored = models.BooleanField(default=False, verbose_name="已评分")  # 是否已评分
    late = models.BooleanField(default=False, verbose_name="补交")  # 是否为补交
    time = models.DateTimeField(auto_now=True, verbose_name="提交时间")  # 提交时间

    class Meta:
        verbose_name = verbose_name_plural = "作业提交"


# 文件随提交记录级联删除
@receiver(models.signals.post_delete, sender=Submit)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)



