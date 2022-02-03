import uuid
import os
import re
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.contrib.auth.models import User
from django.db.models import F
from django.utils.encoding import force_text
from django.utils.functional import keep_lazy_text


def randomize_path(instance, filename):
    path = str(uuid.uuid4())
    return os.path.join('uploads/', path, filename)


class ResourceLink(models.Model):
    resourcelink_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
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


class Classification(models.Model):
    classification_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=settings.DEBUG)
    full_name = models.CharField(max_length=50)
    abbrev = models.CharField(max_length=50)
    sort_order = models.IntegerField()

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return self.full_name


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
    classifications = models.ManyToManyField(Classification)
    sort_order = models.IntegerField()
    visible = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order']

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
    auth_user = models.OneToOneField(User, default=None, null=True, blank=True, on_delete=models.DO_NOTHING)
    user_identifier = models.CharField(max_length=150, default=None, null=True, blank=True)
    name_first = models.CharField(max_length=50)
    name_last = models.CharField(max_length=50)
    source_email = models.ForeignKey(Email, null=True, blank=True, on_delete=models.DO_NOTHING, related_name="source_email")
    destination_emails = models.ManyToManyField(Email)
    notes = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=50, default=None, null=True, blank=True)
    banned = models.BooleanField(default=False)
    strikes = models.IntegerField(default=0)
    temp_ban_count = models.IntegerField(default=0)
    banned_until = models.DateField(null=True, blank=True)
    update_info = models.BooleanField(default=True)
    org = models.CharField(default=None, null=True, blank=True, max_length=20)
    other_org = models.CharField(default=None, null=True, blank=True, max_length=20)

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
        settings.AUTH_USER_MODEL, related_name='request_user_pulled', on_delete=models.DO_NOTHING, null=True, blank=True)
    date_oneeye = models.DateTimeField(null=True, blank=True)
    user_oneeye = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='request_user_oneeye', on_delete=models.DO_NOTHING, null=True, blank=True)
    date_twoeye = models.DateTimeField(null=True, blank=True)
    user_twoeye = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='request_user_twoeye', on_delete=models.DO_NOTHING, null=True, blank=True)
    date_complete = models.DateTimeField(null=True, blank=True)
    user_complete = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='request_user_complete', on_delete=models.DO_NOTHING, null=True, blank=True)
    disc_number = models.IntegerField(null=True, blank=True)
    centcom_pull = models.BooleanField(default=False)

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
    file_object = models.FileField(upload_to=randomize_path, storage=CustomFileSystemStorage(), max_length=500)
    file_name = models.CharField(max_length=255, null=True, blank=True, default=None)
    file_hash = models.CharField(max_length=40, blank=True, null=True)
    is_pii = models.BooleanField(default=False)
    is_centcom = models.BooleanField(default=False)
    rejection_reason = models.ForeignKey(
        Rejection, on_delete=models.DO_NOTHING, null=True, blank=True)
    rejection_text = models.TextField(default=None, blank=True, null=True)
    org = models.CharField(max_length=50, default="")
    NDCI = models.BooleanField(default=False)
    file_count = models.PositiveIntegerField(default=1)
    file_size = models.PositiveBigIntegerField(default=0)
    date_oneeye = models.DateTimeField(null=True, blank=True)
    user_oneeye = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='file_user_oneeye', on_delete=models.DO_NOTHING, null=True, blank=True)
    date_twoeye = models.DateTimeField(null=True, blank=True)
    user_twoeye = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='file_user_twoeye', on_delete=models.DO_NOTHING, null=True, blank=True)
    pull = models.ForeignKey(Pull, on_delete=models.DO_NOTHING, default=None, blank=True, null=True)
    scan_results = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = [F('file_name').asc(nulls_last=True)]

    def __str__(self):
        return os.path.basename(self.file_object.name)


class Request(models.Model):
    request_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    network = models.ForeignKey(Network, on_delete=models.DO_NOTHING)
    files = models.ManyToManyField(File)
    target_email = models.ManyToManyField(Email)
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
    #is_rejected = models.BooleanField(default=False)
    files_scanned = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date_created']

    def __str__(self):
        formatted_date_created = self.date_created.strftime("%d%b %H:%M:%S")
        return self.user.__str__() + ' (' + formatted_date_created + ')'


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
    user = models.ForeignKey(User, default=None, null=True, blank=True, on_delete=models.DO_NOTHING)
    category = models.CharField(max_length=50, default="")
    admin_feedback = models.BooleanField(default=False)
    date_submitted = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['completed', '-date_submitted']

    def __str__(self):
        return str(self.date_submitted.strftime("%b %d %H:%M")) + ": " + self.title
