from django.contrib import admin
from pages.models import *


class UserAdmin(admin.ModelAdmin):
    list_filter = ('banned',)
    list_display = ('name_last', 'name_first', 'source_email', 'banned', 'strikes', 'banned_until', 'user_identifier')
    #fields = ('name_first','name_last', 'auth_user','user_identifier', 'source_email','destination_emails','phone',('banned','strikes','banned_until'),'update_info','notes')
    search_fields = ('name_last', 'name_first', 'auth_user__username', 'source_email__address', 'banned', 'strikes', 'banned_until', 'phone', 'user_identifier')
    sortable_by = ('name_last', 'name_first', 'source_email', 'banned', 'strikes', 'banned_until')
    readonly_fields = ('destination_emails','source_email')


class RequestAdmin(admin.ModelAdmin):
    list_filter = ('network', 'org')
    list_display = ('user', 'network', 'pull', 'has_rejected', 'all_rejected')
    #fields = ('user','request_hash','network','org','pull','date_pulled',('files','target_email'),('comments','notes'),('is_centcom','is_dupe','has_rejected','all_rejected','destFlag'),('ready_to_pull','is_submitted'))
    search_fields = ('user__name_last', 'user__name_first', 'user__auth_user__username', 'network__name')
    sortable_by = ('user', 'network', 'pull', 'has_rejected', 'all_rejected')
    readonly_fields = ('target_email','files')


class FeedbackAdmin(admin.ModelAdmin):
    list_filter = ('category', 'admin_feedback', 'completed')
    list_display = ('title', 'category', 'completed', 'admin_feedback')
    sortable_by = ('title', 'category', 'admin_feedback')


class EmailAdmin(admin.ModelAdmin):
    list_filter = ('network',)
    list_display = ('address', 'network')
    search_fields = ('address',)
    sortable_by = ('address', 'network')


class PullAdmin(admin.ModelAdmin):
    list_filter = ('network', ('date_pulled', admin.DateFieldListFilter))
    list_display = (Pull.__str__, 'network', 'date_pulled')
    search_fields = ('network__name', 'date_pulled')
    sortable_by = (Pull.__str__, 'network__name', 'date_pulled')


class FileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'pull')
    search_fields = ('file_name', )
    sortable_by = ('file_name', 'pull')

class ComplianceBannerAcceptanceAdmin(admin.ModelAdmin):
    list_display = ('user_name_last', 'user_name_first', 'banner_text', 'accepted_at') 

    def user_name_last(self, obj):
        return obj.user.name_last
    user_name_last.short_description = 'Last Name'

    def user_name_first(self, obj):
        return obj.user.name_first
    user_name_first.short_description = 'First Name'

    def banner_text(self, obj):
        return obj.banner.compliance_text
    banner_text.short_description = 'Banner Text'


# Register your models here.
admin.site.register(File, FileAdmin)
admin.site.register(Network)
admin.site.register(Email, EmailAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Pull, PullAdmin)
admin.site.register(Rejection)
admin.site.register(Request, RequestAdmin)
admin.site.register(ResourceLink)
admin.site.register(DirtyWord)
admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(Message)
admin.site.register(Drop_File)
admin.site.register(Drop_Request)
admin.site.register(FileCategories)
admin.site.register(ComplianceBannerSettings)
admin.site.register(ComplianceBannerAcceptance, ComplianceBannerAcceptanceAdmin)
