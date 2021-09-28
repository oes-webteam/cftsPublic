import uuid
import os
from django.conf import settings
from django.db import models

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


class File(models.Model):
  file_id = models.UUIDField(
    primary_key=True, default=uuid.uuid4, editable=False)
  file_object = models.FileField(upload_to=randomize_path, max_length=500)
  file_hash = models.CharField(max_length=40, blank=True, null=True)
  classification = models.ForeignKey(
    Classification, on_delete=models.DO_NOTHING)
  is_pii = models.BooleanField(default=False)
  is_centcom = models.BooleanField(default=False)
  rejection_reason = models.ForeignKey(
    Rejection, on_delete=models.DO_NOTHING, null=True, blank=True)
  rejection_text = models.TextField(default=None, blank=True, null=True)

  class Meta:
    ordering = ['file_object']

  def __str__(self):
    return os.path.basename(self.file_object.name)


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

  class Meta:
    ordering = ['address']

  def __str__(self):
    return self.address


class User(models.Model):
  user_id = models.UUIDField(
    primary_key=True, default=uuid.uuid4, editable=False)
  user_identifier = models.CharField(
   max_length=50, default="00000.0000.0.0000000")
  name_first = models.CharField(max_length=50)
  name_last = models.CharField(max_length=50)
  email = models.ForeignKey(Email, on_delete=models.DO_NOTHING)
  notes = models.TextField(null=True, blank=True)
  phone = models.CharField(max_length=50, default="000-000-0000")

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
  #is_rejected = models.BooleanField(default=False)

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
  user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
  category = models.CharField(max_length=50, default="")
  admin_feedback = models.BooleanField(default=False)
  date_submitted = models.DateTimeField(auto_now_add=True)

  class Meta:
    ordering = ['-date_submitted']

  def __str__(self):
    return self.title

#  def pending_by_network( self, netName ):
#   return self.__class__.objects.filter( network__name=netName, is_submitted=True, date_complete__isnull=True ).order_by( '-date_created' )
#
#  def pending_count_by_network( self, netName ):
#   return self.pending_by_network( netName ).count()
