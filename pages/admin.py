from django.contrib import admin
from pages.models import *

class UserAdmin(admin.ModelAdmin):
    list_filter = ('banned',)
    list_display = (User.__str__, 'auth_user', 'source_email','user_identifier','banned','strikes','banned_until')
    fields = ('name_first','name_last', 'auth_user','user_identifier', 'source_email','destination_emails','phone',('org','other_org'),('banned','strikes','banned_until'),'update_info','notes')
    sortable_by = (User.__str__,'banned','strikes','banned_until')

class RequestAdmin(admin.ModelAdmin):
    list_display = ('user','network','org','has_rejected','all_rejected')
    fields = ('user','request_hash','network','org','pull','date_pulled',('files','target_email'),('comments','notes'),('is_centcom','is_dupe','has_rejected','all_rejected','destFlag'),)
class FeedbackAdmin(admin.ModelAdmin):
    list_filter = ('category','admin_feedback', 'completed')
    list_display = ('title', 'category', 'completed', 'admin_feedback')
    sortable_by = ('title', 'category', 'admin_feedback')
    pass

# Register your models here.
admin.site.register( Classification )
admin.site.register( File )
admin.site.register( Network )
admin.site.register( Email )
admin.site.register( User, UserAdmin )
admin.site.register( Pull )
admin.site.register( Rejection )
admin.site.register( Request, RequestAdmin )
admin.site.register( ResourceLink )
admin.site.register( DirtyWord )
admin.site.register( Feedback, FeedbackAdmin )