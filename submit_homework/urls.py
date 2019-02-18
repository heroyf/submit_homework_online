"""submit_homework URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

from homework import views
from .custom_site import custom_site

urlpatterns = [
    url(r'^$', views.index),
    url(r'^admin/', admin.site.urls),
    url(r'^cus_admin/', custom_site.urls),
    url(r'^register/', views.register, name="student_register"),
    url(r'^login/', views.login, name="student_login"),
    url(r'^logout/', views.logout, name="student_logout"),
    url(r'^tlogout/', views.tlogout, name="teacher_logout"),
    url(r'^teacher/', views.login_teacher, name="teacher_login"),
    url(r'^profile/', views.profile, name="student_profile"),
    url(r'^upload/', views.upload, name="homework_upload"),
    url(r'^download/', views.download, name="homework_download"),
    url(r'^t_profile/', views.teacher_profile, name="teacher_profile"),
    url(r'^a_students/', views.all_students, name="all_students"),
    url(r'^o_student/', views.one_student, name="one_student"),
    url(r'^score/', views.score, name="give_score"),
    url(r'^t_download/', views.t_download, name="teacher_download"),
    url(r'^t-z/', views.teacher_zip_download, name="teacher_zip_download"),
    url(r'^t_get_excel/', views.get_excel, name="teacher_get_excel"),
    url(r'^s_manage/', views.students_manage, name="students_manage"),
    url(r'^s_confirm/', views.students_has_confirmed, name="students_has_confirmed"),
    url(r'^s_delete/', views.student_delete, name="student_delete"),
    url(r'^t_cp/', views.password_change_t, name="password_change_t"),
    url(r'^add_h/', views.add_homework, name="add_homework"),
    url(r'^del_h/', views.delete_homework, name="delete_homework"),
]
