import uuid
import os
import re
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.contrib.auth.models import User
from django.db.models import F
from django.utils.functional import keep_lazy_text


def randomize_path_file(instance, filename):
    path = str(uuid.uuid4())
    return os.path.join('uploads/', path, filename)

def randomize_path_drop_file(instance, filename):
    path = str(uuid.uuid4())
    return os.path.join('drops/', path, filename)


class ResourceLink(models.Model):
    resourcelink_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    file_object = models.FileField(
        upload_to='resources/', blank=True, null=True)
    url_path = models.CharField(max_length=255, blank=True)
    sort_order = models.IntegerField()
    policy = models.BooleanField(default=False)

    @property
    def file_name(self):
        path_as_list = self.file_object.name.split('/')
        last_two = path_as_list[-1:]
        return '/'.join(last_two)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['sort_order']


class Rejection(models.Model):
    rejection_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    subject = models.CharField(max_length=255)
    text = models.TextField()
    visible = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=99)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.name


class Network(models.Model):
    network_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=settings.DEBUG)
    name = models.CharField(max_length=50)
    sort_order = models.IntegerField()
    visible = models.BooleanField(default=True)
    cfts_deployed = models.BooleanField(default=False)
    skip_file_review = models.BooleanField(default=False)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Email(models.Model):
    email_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    address = models.CharField(max_length=255)
    network = models.ForeignKey(Network, default=None, null=True, blank=True, on_delete=models.DO_NOTHING)
    class Meta:
        ordering = ['address']

    def __str__(self):
        return self.address


class User(models.Model):
    user_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    auth_user = models.OneToOneField(User, default=None, null=True, blank=True, on_delete=models.SET_NULL)
    user_identifier = models.CharField(max_length=150, default=None, null=True, blank=True)
    name_first = models.CharField(max_length=50)
    name_last = models.CharField(max_length=50)
    source_email = models.ForeignKey(Email, null=True, blank=True, on_delete=models.DO_NOTHING, related_name="source_email")
    destination_emails = models.ManyToManyField(Email, blank=True)
    notes = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=50, default=None, null=True, blank=True)
    banned = models.BooleanField(default=False)
    strikes = models.IntegerField(default=0)
    temp_ban_count = models.IntegerField(default=0)
    account_warning_count = models.IntegerField(default=0)
    last_warned_on = models.DateTimeField(null=True, blank=True)
    banned_until = models.DateField(null=True, blank=True)
    update_info = models.BooleanField(default=True)
    org = models.CharField(default=None, null=True, blank=True, max_length=20)
    other_org = models.CharField(default=None, null=True, blank=True, max_length=20)
    read_policy = models.BooleanField(default=False)

    class Meta:
        ordering = ['name_last']

    def __str__(self):
        return self.name_last + ', ' + self.name_first


class Pull(models.Model):
    pull_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    pull_number = models.IntegerField(null=True, blank=True)
    network = models.ForeignKey(Network, on_delete=models.DO_NOTHING)
    date_pulled = models.DateTimeField(null=True, blank=True)
    user_pulled = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='request_user_pulled', on_delete=models.SET_NULL, null=True, blank=True)
    date_complete = models.DateTimeField(null=True, blank=True)
    user_complete = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='request_user_complete', on_delete=models.SET_NULL, null=True, blank=True)
    disc_number = models.IntegerField(null=True, blank=True)
    queue_for_delete = models.BooleanField(default=False)
    pull_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date_pulled']

    def __str__(self):
        return self.network.__str__() + '_' + str(self.pull_number)


@keep_lazy_text
def get_valid_filename(name):
    """
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot, keeps parentheses.
    """
    s = str(name).strip().replace(' ', '_')
    s = re.sub(r'(?u)[^-\w.()]', '', s)
    if s in {'', '.', '..'}:
        raise SuspiciousFileOperation("Could not derive file name from '%s'" % name)
    return s


class CustomFileSystemStorage(FileSystemStorage):

    def get_valid_name(self, name):
        return get_valid_filename(name)


class File(models.Model):
    file_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    file_object = models.FileField(upload_to=randomize_path_file, storage=CustomFileSystemStorage(), max_length=500)
    file_name = models.CharField(max_length=255, null=True, blank=True, default=None)
    file_hash = models.CharField(max_length=40, blank=True, null=True)
    is_pii = models.BooleanField(default=False)
    is_centcom = models.BooleanField(default=False)
    rejection_reasons = models.ManyToManyField(Rejection, related_name='file_rejection_reasons', blank=True)
    rejection_text = models.TextField(default=None, blank=True, null=True)
    org = models.CharField(max_length=50, default="")
    NDCI = models.BooleanField(default=False)
    file_count = models.PositiveIntegerField(default=1)
    file_size = models.PositiveBigIntegerField(default=0)
    date_oneeye = models.DateTimeField(null=True, blank=True)
    user_oneeye = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='file_user_oneeye', on_delete=models.SET_NULL, null=True, blank=True)
    date_twoeye = models.DateTimeField(null=True, blank=True)
    user_twoeye = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='file_user_twoeye', on_delete=models.SET_NULL, null=True, blank=True)
    pull = models.ForeignKey(Pull, on_delete=models.DO_NOTHING, default=None, blank=True, null=True)
    scan_results = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = [F('file_name').asc(nulls_last=True)]

    def __str__(self):
        return os.path.basename(self.file_object.name)
    
    def is_first_review_complete(self):
        return self.date_oneeye is not None
    def is_second_review_complete(self):
        return self.date_twoeye is not None
    def review_status(self):
        if self.is_first_review_complete() and self.is_second_review_complete():
            return "Fully reveiwed"
        elif self.is_first_review_complete() and not self.is_second_review_complete():
            return "First Review Complete"
        else:
            return "Not Reviewed"

class FileCategories(models.Model):
    file_category_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_category = models.CharField(null=True, max_length=35)
    visible = models.BooleanField(default=False)

    def __str__(self):
        return str(self.file_category)

class Request(models.Model):
    request_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    network = models.ForeignKey(Network, on_delete=models.DO_NOTHING)
    files = models.ManyToManyField(File)
    target_email = models.ManyToManyField(Email)
    RHR_email = models.CharField(max_length=75, default="")
    comments = models.TextField(null=True, blank=True)
    is_submitted = models.BooleanField(default=False)
    pull = models.ForeignKey(
        Pull, on_delete=models.DO_NOTHING, default=None, null=True, blank=True)
    is_centcom = models.BooleanField(default=False)
    date_pulled = models.DateTimeField(null=True, blank=True)
    request_hash = models.CharField(max_length=255, default="")
    is_dupe = models.BooleanField(default=False)
    org = models.CharField(max_length=50, default="")
    notes = models.TextField(null=True, blank=True)
    has_rejected = models.BooleanField(default=False)
    all_rejected = models.BooleanField(default=False)
    rejected_dupe = models.BooleanField(default=False)
    destFlag = models.BooleanField(default=False)
    ready_to_pull = models.BooleanField(default=False)
    has_encrypted = models.BooleanField(default=False)
    files_scanned = models.BooleanField(default=False)
    file_categories = models.ManyToManyField(FileCategories)

    class Meta:
        ordering = ['-date_created']

    def __str__(self):
        formatted_date_created = self.date_created.strftime("%d%b %H:%M:%S")
        return self.user.__str__() + ' (' + formatted_date_created + ')'

class Drop_File(models.Model):
    file_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_object = models.FileField(upload_to=randomize_path_drop_file, storage=CustomFileSystemStorage(), max_length=500)
    file_name = models.CharField(max_length=255, null=True, blank=True, default=None)

    class Meta:
        ordering = [F('file_name').asc(nulls_last=True)]

    def __str__(self):
        return os.path.basename(self.file_object.name)


class Drop_Request(models.Model):
    request_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    files = models.ManyToManyField(Drop_File)
    target_email = models.ForeignKey(Email, null=True, blank=True, on_delete=models.DO_NOTHING)
    request_info = models.CharField(max_length=5000, null=True, blank=True)
    user_retrieved = models.BooleanField(default=False)
    delete_on = models.DateTimeField()
    request_code = models.CharField(max_length=50)
    email_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date_created']

    def __str__(self):
        formatted_date_created = self.date_created.strftime("%d%b %H:%M:%S")
        return self.target_email.address + ' (' + formatted_date_created + ')'


class DirtyWord(models.Model):
    dirtyword_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    word = models.CharField(max_length=255)
    case_sensitive = models.BooleanField(default=False)

    class Meta:
        ordering = ['word']

    def __str__(self):
        return self.word


class Feedback(models.Model):
    feedback_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150, default="")
    body = models.TextField(default="")
    user = models.ForeignKey(User, default=None, null=True, blank=True, on_delete=models.CASCADE)
    category = models.CharField(max_length=50, default="")
    admin_feedback = models.BooleanField(default=False)
    date_submitted = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['completed', '-date_submitted']

    def __str__(self):
        return str(self.date_submitted.strftime("%b %d %H:%M")) + ": " + self.title

class Message(models.Model):
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.TextField(null=True)
    visible = models.BooleanField(default=False)
    colorChoices = [('danger', "red"), ('warning', "yellow"), ('success', "green"), ('info', "blue")]
    color = models.CharField(choices=colorChoices, default='warning', max_length=20)

    def __str__(self):
        return str(self.message)
    
#  These classes are used to store the settings for the compliance banner
#  and the acceptance of the banner by users.
    
class ComplianceBannerSettings(models.Model):
    compliance_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    compliance_text = models.TextField(null=True)
    visible = models.BooleanField(default=False)
    accept_button_text = models.CharField(max_length=50, default="Accept")
    start_date = models.DateTimeField(null=True, blank=True)  # When the banner becomes active
    end_date = models.DateTimeField(null=True, blank=True)    # When the banner expires

    def __str__(self):
        # Use compliance_text or another field for a meaningful string representation
        return self.compliance_text if self.compliance_text else "Compliance Banner"
    
class ComplianceBannerAcceptance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    banner = models.ForeignKey(ComplianceBannerSettings, on_delete=models.CASCADE)
    accepted_at = models.DateTimeField(auto_now=True)  

    class Meta:
        unique_together = ('user', 'banner')

    def __str__(self):
        return f"{self.user.username} accepted {self.banner.compliance_text} on {self.accepted_at}"