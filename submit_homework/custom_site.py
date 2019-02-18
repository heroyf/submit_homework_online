from django.contrib.admin import AdminSite


class CustomSite(AdminSite):
    site_header = '作业提交评分系统'
    site_title = '作业提交评分系统'
    index_title = '首页'


custom_site = CustomSite(name='cus_admin')