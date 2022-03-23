from os import name
from django.urls import path
from . import static_views
import pages.views as views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('CFTS.cfm', views.frontend, name='index'),
    path('cfts.cfm', views.frontend, name='index'),
    path('', views.frontend, name='index'),
    path('consent', views.consent, name='consent'),
    path('howTo', static_views.howTo, name='howTo'),
    path('resources', static_views.resources, name='resources'),

    # auth
    path('register', views.register, name='register'),
    path('login', views.userLogin, name='login'),
    path('logout', auth_views.LogoutView.as_view(), name='logout'),
    path('user-info', views.editUserInfo, name='user-info'),
    path('password-change', views.changeUserPassword, name='password-change'),
    path('password-reset', views.passwordResetRequest, name='password-reset'),
    path('password-reset/done', auth_views.PasswordResetDoneView.as_view(template_name='authForms/passwordResetForms/passwordResetDone.html'), name='password-reset-done'),
    path('password-reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(template_name='authForms/passwordResetForms/passwordResetConfirm.html'), name='password-reset-confirm'),
    path('password-reset/complete', auth_views.PasswordResetCompleteView.as_view(template_name='authForms/passwordResetForms/passwordResetComplete.html'), name='password_reset_complete'),
    path('password-reset-admin', views.passwordResetAdmin, name='password-reset-admin'),
    path('password-reset-email/<int:id>/<uuid:feedback>', views.passwordResetEmail, name='password-reset-email'),
    path('username-lookup', views.usernameLookup, name='username-lookup'),

    # resources
    path('resources/<str:file>', views.resources, name='resources'),

    # frontend
    path('frontend', views.frontend, name='frontend'),

    # user requests
    path('my-requests', views.userRequests, name='userRequests'),
    path('request/<uuid:id>', views.requestDetails, name='userRequests'),

    # queue
    path('queue', views.queue, name='queue'),
    path('queue/cookie', views.queue, name='cookie'),
    path('transfer-request/<uuid:id>', views.transferRequest, name='transfer-request'),
    path('create-zip/<str:network_name>/<str:rejectPull>', views.createZip, name='create-zip'),
    path('getFile/uploads/<str:fileID>/<str:fileName>', views.getFile, name='getFile'),
    path('updateFileReview/<uuid:fileID>/<uuid:rqstID>/', views.updateFileReview, name='reviewFile'),
    path('updateFileReview/<uuid:fileID>/<uuid:rqstID>/<str:quit>', views.updateFileReview, name='reviewFile'),
    path('removeFileReviewer/<int:stage>', views.removeFileReviewer, name='removeReview'),

    # scan
    path('scan/<uuid:rqst_id>', views.scan, name="scan"),
    path('viewscan/<uuid:pull_id>', views.viewScan, name="viewscan"),

    # pulls
    path('pulls', views.pulls, name='pulls'),
    path('getPull/<str:fileName>', views.getPull, name='getPull'),
    path('pulls-done/<uuid:id>/<int:cd>', views.pullsDone, name='pulls-done'),
    path('cancelPull/<uuid:id>/', views.cancelPull, name='cancelPull'),

    # archive
    path('archive', views.archive, name='archive'),
    path('filterArchive', views.filterArchive, name='filterArchive'),

    # reporting
    path('reports', views.reports, name='reports'),

    # feedback
    path('ban-request/<uuid:requestid>', views.feedback, name='ban-request'),
    path('feedback', views.feedback, name='feedback'),
    path('ban-request/submitfeedback', views.submitFeedback, name='submitfeedback'),
    path('submitfeedback', views.submitFeedback, name='submitfeedback'),

    # APIs
    path('api-setreject', views.setReject, name='api-setreject'),
    path('api-setrejectdupes', views.setRejectDupes, name='api-setrejectdupes'),
    path('api-unreject', views.unReject, name='api-unreject'),
    path('api-setencrypt', views.setEncrypt, name='api-setencrypt'),
    path('api-numbers', views.runNumbers, name='api-numbers'),
    path('api-numbers/<int:api_call>', views.runNumbers, name='api-numbers'),
    path('api-processrequest', views.process, name='api-processrequest'),
    path('api-setconsentcookie', views.setConsentCookie, name='api-setconsentcookie'),
    #path('api-getclassifications', views.getClassifications, name='api-getclassifications'),
    path('api-removeCentcom/<uuid:id>', views.removeCentcom, name='api-removeCentcom'),
    path('api-requestnotes/<uuid:requestid>', views.requestNotes, name='api-requestnotes'),
    # path('api-banuser/<uuid:userid>/<uuid:requestid>/', views.banUser, name='api-banuser'),
    path('api-banuser/<uuid:userid>/<uuid:requestid>/<str:ignore_strikes>/<str:perma_ban>', views.banUser, name='api-banuser'),
    path('api-fileCleanup', views.fileCleanup, name='api-fileCleanup'),


    # dev tools
    path('tools-setupdb', views.setupDB, name="setupdb"),
    path('tools-updateFileInfo', views.updateFiles, name='api-updateFileInfo'),
]
