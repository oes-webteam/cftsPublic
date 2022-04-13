# ====================================================================
from email import message
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from pages.models import *
from django.contrib.auth.decorators import login_required, user_passes_test
from zipfile import BadZipFile, ZipFile
from cfts import settings
import os
import shutil
from datetime import datetime
from django.contrib import messages
import traceback
from pages.views.auth import superUserCheck, staffCheck
from django.utils import timezone
# ====================================================================

# function called from fileCleanup() to delete files in a directory that are over a number of days old
def deleteFiles(directory, maxAge):
    # get all files in directory passed in from args
    with os.scandir(directory) as files:
        for file in files:
            # don't delete the gitignore
            if file.path.split("\\")[-1] != ".gitignore":
                # calculate age of file from the files 'last modified' time
                modTime = datetime.fromtimestamp(file.stat().st_mtime)
                fileAge = datetime.fromtimestamp(datetime.now().timestamp())-modTime
                # if file is older that maxAge passed in from args then delete it and any parent folders
                if fileAge.days > maxAge:
                    print("File %s is %s days old. Deleting..." % (file.path, fileAge.days))
                    # delete upload if older than maxAge variable
                    try:
                        shutil.rmtree(file.path)
                    # delete single files
                    except:
                        try:
                            os.remove(file.path)
                        except:
                            pass

                else:
                    daysRemaining = maxAge-fileAge.days
                    if daysRemaining == 0:
                        print("File %s will be deleted in 1 day." % file.path)

                    print("File %s will be deleted in %s days." % (file.path, daysRemaining))

def deleteDrops():
    oldDrops = Drop_Request.objects.filter(delete_on__lte=timezone.now())

    for drop in oldDrops:
        for file in drop.files.all():
            file.delete()
        drop.delete()

# function to call deleteFiles() from a url, only available to superusers
@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def fileCleanup(request):
    # paths to directories you want to nuke
    uploadsPath = settings.UPLOADS_DIR
    pullsPath = settings.PULLS_DIR
    scanPath = os.path.join(settings.BASE_DIR, "cfts\\scan")
    dropsPath = settings.DROPS_DIR

    # call deleteFiles() with a path and maximum file age
    try:
        deleteFiles(uploadsPath, 30)
        deleteFiles(pullsPath, 30)
        deleteFiles(scanPath, 1)
        deleteFiles(dropsPath, 5)
        deleteDrops()
    except Exception as e:
        messages.error(request, "Could not perform scheduled file deletion." + str(traceback.format_exc()))


# function to update all users update_info field to force them to update their user info.
# this is meant to by imported into a blank db migration, python manage.py makemigrations --empty appName
# in the operations list of the migration call RunPython() with resetUpdateInfo() and reverseFunction() as args
# the migration can be deleted once migrated
def resetUpdateInfo(apps, schema_editor):
    User = apps.get_model("pages", "User")
    db_alias = schema_editor.connection.alias

    for user in User.objects.using(db_alias).all():
        user.update_info = True
        user.save()


def reverseFunction():
    pass


# function to populate an empty database with data, will need to be updated to refect current production environment
@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def setupDB(request):
    if Network.objects.count() == 0:

        # Networks
        nipr = Network(network_id='dabcf4d26dcf475286351de3ac7f0c49', name='NIPR', sort_order=1)
        nipr.save()

        sipr = Network(network_id='9db4f002-78ef-4a90-9b76-baaf28603dc3', name='SIPR', sort_order=2)
        sipr.save()

        bices = Network(network_id='7cc549aba3064d5b9cb8fa8ec846f252', name='BICES', sort_order=3)
        bices.save()

        are = Network(network_id='56ea084ed72c47cab3ee48371afdb504', name='CPN-ARE', sort_order=4)
        are.save()

        bhr = Network(network_id='d451005a8b5043e9b61394ea99b961d2', name='CPN-BHR', sort_order=5)
        bhr.save()

        jor = Network(network_id='6caad0cf9f0a4160b290c2c6407aa04d', name='CPN-JOR', sort_order=6)
        jor.save()

        kwt = Network(network_id='5fde10fa2e424b5795ce76f5ece5305a', name='CPN-KWT', sort_order=7)
        kwt.save()

        qat = Network(network_id='c8628ca885d7436e96f664e8d6c1f2d9', name='CPN-QAT', sort_order=8)
        qat.save()

        sau = Network(network_id='be27f19fd42147ebabc098da6d8bb35c', name='CPN-SAU', sort_order=9)
        sau.save()

        cpnx = Network(network_id='20c87ade9349487ba9f67b358f470add', name='CPN-X', sort_order=10)
        cpnx.save()

        # Rejection Reasons

        policy = Rejection(name='failure to follow policy', subject='CFTS Rejection - Policy', text='''As a customer it is your responsibility to follow the policies that govern the use of this service.
      %0D%0D
      Our policy is available on the main page of CFTS.
      %0D%0D
      Continued failure to follow our policy will result in you to no longer be able to use our service.''')
        policy.save()

        hidden = Rejection(name='Hidden/Comments/Tracked changes', subject='CFTS Request Rejected  Hidden/Comments/Tracked changes', text='''Due to several incidents of data compromise, files with hidden data will not be transferred.  Please ensure all data is readily visible for the review process. 
       %0D%0D
      Files with tracked changes, hidden data, hidden worksheets, hidden names, active filters or comments will not be transferred.  Please ensure documents submitted for transfer do not contain any of these items. 
       %0D%0D
      Please ensure you are utilizing two person integrity in reviewing your files prior to submitting through CFTS, and that your SSO has reviewed and approved the file to be transferred.''')
        hidden.save()

        unableOpen = Rejection(name='Unable to open file', subject='CFTS Request Rejected -- Unable to Open File',
                               text='''The file submitted for transfer is not a format we are unable to open, and therefore cannot be transferred to NIPR.  If there is a way you can convert this file to a format we are able to open such as .ppt, .xlsx, .doc or .pdf and the file contains proper classification markings we will transfer it.''')
        unableOpen.save()

        multiS = Rejection(name='SECRET Markings  multi', subject='CFTS Request Rejected  SECRET Markings in File', text='''The files submitted for transfer contain SECRET classification markings and cannot be transferred to NIPR. Please correct the issues, have your SSO review and resubmit through CFTS.
      %0D%0D
      The CENTCOM IM Transfer team cannot transfer files to the NIPRnet that contain classified markings anywhere in the file (i.e., PowerPoint Master Slides, Document Properties, etc.). The team is regularly audited, and if caught making file transfers containing classified markings the team member will lose rights to transfer files. This adversely affects our ability to provide transfer services to yourself or other customers. 
      %0D%0D
      It is your responsibility to utilize two person integrity in reviewing your files prior to submitting through CFTS, and that your SSO has reviewed and approved the file to be sent to the NIPRnet. 
      %0D%0D
      We also recommend that you utilize IC Clear to review your files prior to submitting them through CFTS for transfer: https://icclears01.oni.nmci.navy.smil.mil/Clear/
      %0D%0D
      The IM team does not retain files that have been rejected.''')
        multiS.save()

        missingClassMulti = Rejection(name='Missing Classification multi', subject='CFTS Transfer Request Rejected  Missing Classification Markings', text='''The files submitted for transfer to NIPR do not contain classification markings.  Documents being transferred from SIPR to NIPR must be marked, please ensure each file contains classification markings on each page/slide/sheet and resubmit through CFTS for transfer.
      %0D%0D
      Every document that is on a classified network is required to have the appropriate classification markings per CAPCO guidance. It does not matter whether the documents contain information or not.
       %0D%0D
      “(U) On purely unclassified documents (i.e., no control markings) transmitted over a classified system, the designation “UNCLASSIFIED” must be conspicuously placed in the banner line.  However, portion marks, i.e., “(U)” are not required.  When transmitting purely unclassified documents (i.e., no control markings) over unclassified systems, classification markings are not required.”
       %0D%0D
      In other words, if an item is coming from NIPR, it is not required, but because we are bringing these documents down from SIPR, they must be marked.  Not only that, but we like to have all of our bases covered when transferring documents across networks (especially to lower networks) because the amount we process is so high, the risk for spillage is high as well.  This is our office policy.  Please mark it for transfer and feel free to remove the markings once you have it on NIPR.
      %0D%0D
      Additionally, prior to uploading your file you had to acknowledge that all files submitted were marked with the proper classification markings
      %0D%0D
      Classification in the file name is not sufficient.
      %0D%0D
      The IM team does not retain files that have been rejected.''')
        missingClassMulti.save()

        redact = Rejection(name='redacted', subject='CFTS Transfer Request Rejected Redaction',
                           text='''Per DoD Regulation 5200 01 (pg 66 para (2); a redacted document requires a memo from the current Original Classification Authority (OCA) stating the document has been redacted and is authorized for the target network.''')
        redact.save()

        singleS = Rejection(name='SECRET markings single', subject='CFTS Request Rejected  SECRET markings', text='''The file submitted for transfer contains SECRET classification markings and cannot be transferred to NIPR. Please correct the issues, have your SSO review and resubmit through CFTS.
      %0D%0D
      The CENTCOM IM Transfer team cannot transfer files to the NIPRnet that contain classified markings anywhere in the file (i.e., PowerPoint Master Slides, Layout, Document Properties, etc.). The team is regularly audited, and if caught making file transfers containing classified markings the team member will lose rights to transfer files. This adversely affects our ability to provide transfer services to yourself or other customers. 
      %0D%0D
      It is your responsibility to utilize two person integrity in reviewing your files prior to submitting through CFTS, and that your SSO has reviewed and approved the file to be sent to the NIPRnet. 
      %0D%0D
      We also recommend that you utilize IC Clear to review your files prior to submitting them through CFTS for transfer: https://icclears01.oni.nmci.navy.smil.mil/Clear/
      %0D%0D
      The IM team does not retain files that have been rejected.''')
        singleS.save()

        missingClassSingle = Rejection(name='Missing Classification Markings  single', subject='CFTS Transfer Request Rejected Missing Classification Markings', text='''The file submitted for transfer to NIPR does not contain classification markings. Documents being transferred from SIPR to NIPR must be marked, please ensure file contains classification markings on each page/slide/sheet and resubmit through CFTS for transfer.
      %0D%0D
      Every document that is on a classified network is required to have the appropriate classification markings per CAPCO guidance. It does not matter whether the documents contain information or not. 
       %0D%0D
      “(U) On purely unclassified documents (i.e., no control markings) transmitted over a classified system, the designation “UNCLASSIFIED” must be conspicuously placed in the banner line.  However, portion marks, i.e., “(U)” are not required.  When transmitting purely unclassified documents (i.e., no control markings) over unclassified systems, classification markings are not required.”
       
      In other words, if an item is coming from NIPR, it is not required, but because we are bringing these documents down from SIPR, they must be marked.  Not only that, but we like to have all of our bases covered when transferring documents across networks (especially to lower networks) because the amount we process is so high, the risk for spillage is high as well.  This is our office policy.  Please mark it for transfer and feel free to remove the markings once you have it on NIPR.
       %0D%0D
      Additionally, prior to uploading your file you had to acknowledge that all files submitted were marked with the proper classification markings.
      %0D%0D
      Classification in the file name is not sufficient.
      %0D%0D
      The IM team does not retain files that have been rejected.''')
        missingClassSingle.save()

        missingMarks = Rejection(name='Missing Markings page/slide/sheet', subject='CFTS Request Rejected Missing Markings page/slide/sheet', text='''Documents being transferred from SIPR must be marked on each page/slide/sheet. Correct the issues and resubmit through CFTS for transfer.
      %0D%0D
      The IM team does not retain files that have been rejected.''')
        missingMarks.save()

        dupe = Rejection(name='Duplicate - No Email', subject='[N/T]', text='''Delete. Do not send.''')
        dupe.save()

        testMsg = Rejection(name='Test Msg', subject='CFTS Request Rejected  Test Message', text='''We are in the process of reviewing and moving files. The Combined File Transfer Service is not automated, it relies upon reliable human review. We do our best to ensure all transfers are completed within four hours of submission during our normal hours. 
      %0D%0D
      Our normal business hours are 0600-1700 EST Monday - Friday. On Saturday and Sunday our desk is manned 0700-1500 EST.
      %0D%0D
      We do not transfer test messages.''')
        testMsg.save()

        jopes = Rejection(name='JOPES', subject='CFTS Request Rejected -- JOPES Data', text='''Due to several incidents of data compromise via NIPR, we are awaiting HQ USAF A-3 promulgate policy to subordinate USAF units regarding process and procedure to ensure OPSEC is not violated, placing our personnel, equipment, and mission at risk. Per our SSO we cannot transfer information with any future troop movement dates or past movement rosters that have locations on them, or ones with RLD, ALD, or RDD codes. Pending official promulgation from HQ USAF A-3, USCENTCOM will not pass JOPES/DCAPES type data to include PRF and LVY files from SIPR to NIPR.
      %0D%0D
      The issue is with RDD, RLD, ALD etc columns showing future force movement, according to CENTCOM classification guidance any indication of future movement makes this secret. We were recently told that in order for it to be UNCLASS it must be 21 days after these dates. 
      %0D%0D
      The SIPRNET has always been available to share data of this type of information.  Please address questions to Mr. Ralph Rueda: ralph.a.rueda.civ@mail.smil.mil.  Thank you for your patience and understanding.''')
        jopes.save()

        other = Rejection(name='Other', subject='CFTS Request Rejected', text='')
        other.save()

    # scan dirty words
    if DirtyWord.objects.count() == 0:
        secret = DirtyWord(word="SECRET", case_sensitive=False)
        secret.save()

        sSlash = DirtyWord(word="S//", case_sensitive=False)
        sSlash.save()

        noforn = DirtyWord(word="NOFORN", case_sensitive=False)
        noforn.save()

        cSlash = DirtyWord(word="C//", case_sensitive=False)
        cSlash.save()

        confid = DirtyWord(word="CONFIDENTIAL", case_sensitive=False)
        confid.save()

        PRV = DirtyWord(word="PRF", case_sensitive=True)
        PRV.save()

        LVY = DirtyWord(word="LVY", case_sensitive=True)
        LVY.save()

        RDD = DirtyWord(word="RDD", case_sensitive=True)
        RDD.save()

        RLD = DirtyWord(word="RLD", case_sensitive=True)
        RLD.save()

        ALD = DirtyWord(word="ALD", case_sensitive=True)
        ALD.save()

        sSlashCom = DirtyWord(word="\(S/", case_sensitive=False)
        sSlashCom.save()

    return render(request, 'pages/setupdb.html')


# function to update all File objects file_size, file_count, and file_name from the actual uploaded file
# this was only used once, in ye olden times none of this information was kept on the File object
# anytime this info was needed it had to be read from the file itself, but files take up server space
# this was used to migrate all file information to the File object so that old files could be deleted
def updateFiles(request):
    # get all File objects
    files = File.objects.all()

    for f in files:
        try:
            # file is a zip
            if str(f.file_object).split('.')[-1] == "zip":
                try:
                    with ZipFile(f.file_object, 'r') as zip:
                        # get info for all files
                        info = zip.infolist()
                        # count of all files in zip
                        f.file_count = len(info)

                        # count the total uncompressed file size for all files in the zip
                        fileSize = 0
                        for file in info:
                            fileSize += file.file_size

                        f.file_size = fileSize
                except BadZipFile:
                    print("could not extract zip file: " + str(f.file_object))

            else:
                # if its not a zip just get the file size from the file object, file count defaults to 1
                f.file_size = f.file_object.size

            f.file_name = str(f.file_object).split('/')[-1]

            f.save()

        # file probably deleted
        except FileNotFoundError:
            print("couldn not find file: " + str(f.file_object))
            pass

    return HttpResponse("File info updated")
