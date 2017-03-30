from django.conf.urls import url
from . import views
from django.contrib.auth import views as auth_views

app_name='archapp'

urlpatterns = [
        # home page
        url(r'^$', views.WelcomePage.as_view(), name = 'welcome'),

        # site CRUD
        url(r'^new/$', views.SiteCreate.as_view(), name = 'newsite'),
        url(r'^(?P<pk>[0-9]+)/$', views.SitePage.as_view(), name = 'sitepage'),
        url(r'^(?P<pk>[0-9]+)/edit/$', views.SiteEdit.as_view(), name = 'editsite'),
        url(r'^(?P<pk>[0-9]+)/delete/$', views.SiteDelete.as_view(), name = 'deletesite'),

        # sites overview and search
        url(r'^all/$', views.AllSites.as_view(), name = 'allsites'),
        url(r'^search/$', views.Search.as_view(), name = 'results'),

        # auth / registration
        url(r'^signup/$', views.SignUp.as_view(), name = 'signup'),
        url(r'^accounts/login/$', auth_views.login, {'template_name': 'archapp/login.html'} , name = 'login'),
        url(r'^accounts/logout/$', auth_views.logout, {'template_name': 'archapp/logout.html'} , name = 'logout'),

        # user account
        url(r'user/(?P<slug>[\w.@+-]+)/profile/$', views.UserProfileAndCreateProject.as_view(), name='userprofile'),
        url(r'user/(?P<slug>[\w.@+-]+)/update/$', views.UserUpdate.as_view(), name = 'user-update'),
        url(r'user/(?P<slug>[\w.@+-]+)/delete/$', views.UserDelete.as_view(), name = 'user-delete'),
        ]
