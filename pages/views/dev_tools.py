# ====================================================================
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from pages.models import *
from django.contrib.auth.decorators import login_required, user_passes_test
from zipfile import BadZipFile, ZipFile
from cfts import settings
import os
import shutil
from datetime import datetime

from pages.views.auth import superUserCheck, staffCheck


# from django.core.files.base import ContentFile
# ====================================================================

# get all files in folder
def deleteFiles(directory, maxAge):
    with os.scandir(directory) as files:
        for file in files:
            if file.path.split("\\")[-1] != ".gitignore":
                # file last modified date
                modTime = datetime.fromtimestamp(file.stat().st_mtime)
                fileAge = datetime.fromtimestamp(datetime.now().timestamp())-modTime
                if fileAge.days < maxAge:
                    print("File %s is %s days old. Deleting..." % (file.path, fileAge.days))
                    # delete upload if older than maxAge variable
                    if directory == settings.UPLOADS_DIR:
                        shutil.rmtree(file.path)
                    # delete single files
                    else:
                        os.remove(file.path)

                else:
                    daysRemaining = maxAge-fileAge.days
                    if daysRemaining == 0:
                        print("File %s will be deleted in 1 day." % file.path)

                    print("File %s will be deleted in %s days." % (file.path, daysRemaining))


@login_required
@user_passes_test(superUserCheck, login_url='frontend', redirect_field_name=None)
def fileCleanup(request):
    # path to uploads folder
    uploadsPath = settings.UPLOADS_DIR
    pullsPath = settings.PULLS_DIR
    scanPath = os.path.join(settings.BASE_DIR, "cfts\\scan")

    try:
        deleteFiles(uploadsPath, 30)
        deleteFiles(pullsPath, 30)
        deleteFiles(scanPath, 1)
        return HttpResponse("Old files deleted")
    except Exception as e:
        return HttpResponse(str("Error deleting files:" + repr(e)))


def resetUpdateInfo(apps, schema_editor):
    User = apps.get_model("pages", "User")
    db_alias = schema_editor.connection.alias

    for user in User.objects.using(db_alias).all():
        user.update_info = True
        user.save()


def reverseFunction():
    pass


def stubGet(request):
    return JsonResponse({})


def stubPost(request):
    data = {}
    if request.method == 'POST':
        data = request.POST.dict()

    return JsonResponse(data)


def makeFiles(request):
    unclass = Classification.objects.get(abbrev='U')
    return HttpResponse('Made the files')
    '''
  for i in range( 16, 20 ):
    # filename
    new_f = 'textfile_' + str(i) + '.txt'
    # new CFTS File object
    new_file = File( classification = unclass )
    # save the new CFTS file
    new_file.save()
    # save the Django File into the CFTS File
    new_file.file_object.save( new_f, ContentFile( new_f ) )
  '''


@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def setupDB(request):
    if Network.objects.count() == 0:
        # Classifications
        unclass = Classification(classification_id='8cefbfbe3e5a4d46aea10c22c879569d', full_name='UNCLASSIFIED', abbrev='U', sort_order=1)
        unclass.save()
        fouo = Classification(classification_id='fbeeca2f48bc4ebebdc428a8a94a2a90', full_name='UNCLASSIFIED//FOR OFFICIAL USE ONLY', abbrev='U//FOUO', sort_order=2)
        fouo.save()
        c = Classification(classification_id='49c821fc4bd9487e86ded88610c59f54', full_name='CONFIDENTIAL', abbrev='C', sort_order=3)
        c.save()
        c_rel = Classification(classification_id='a605c8d9b6fe404d98812d944c3cf3ca', full_name='CONFIDENTIAL//RELEASABLE', abbrev='C//REL', sort_order=4)
        c_rel.save()
        cui = Classification(classification_id='b14598a66fa84472a817ee8eae488be3', full_name='CONTROLLED UNCLASSIFIED INORMATION', abbrev='CUI', sort_order=4)
        cui.save()
        s = Classification(classification_id='3fd32c420cc74af0b7a5afd1e481b92e', full_name='SECRET', abbrev='S', sort_order=5)
        s.save()
        s_rel = Classification(classification_id='b8f6928f278d4891a77f32cb7c411094', full_name='SECRET//RELEASABLE', abbrev='S//REL', sort_order=6)
        s_rel.save()

        # Networks
        nipr = Network(network_id='dabcf4d26dcf475286351de3ac7f0c49', name='NIPR', sort_order=1)
        nipr.save()
        nipr.classifications.add(unclass)
        nipr.classifications.add(fouo)
        nipr.classifications.add(cui)

        bices = Network(network_id='7cc549aba3064d5b9cb8fa8ec846f252', name='BICES', sort_order=2)
        bices.save()
        bices.classifications.add(unclass)
        bices.classifications.add(fouo)
        bices.classifications.add(c_rel)
        bices.classifications.add(cui)
        bices.classifications.add(s_rel)

        are = Network(network_id='56ea084ed72c47cab3ee48371afdb504', name='CPN-ARE', sort_order=3)
        are.save()
        are.classifications.add(unclass)
        are.classifications.add(fouo)
        are.classifications.add(c_rel)
        are.classifications.add(cui)
        are.classifications.add(s_rel)

        bhr = Network(network_id='d451005a8b5043e9b61394ea99b961d2', name='CPN-BHR', sort_order=4)
        bhr.save()
        bhr.classifications.add(unclass)
        bhr.classifications.add(fouo)
        bhr.classifications.add(c_rel)
        bhr.classifications.add(cui)
        bhr.classifications.add(s_rel)

        jor = Network(network_id='6caad0cf9f0a4160b290c2c6407aa04d', name='CPN-JOR', sort_order=5)
        jor.save()
        jor.classifications.add(unclass)
        jor.classifications.add(fouo)
        jor.classifications.add(c_rel)
        jor.classifications.add(cui)
        jor.classifications.add(s_rel)

        kwt = Network(network_id='5fde10fa2e424b5795ce76f5ece5305a', name='CPN-KWT', sort_order=6)
        kwt.save()
        kwt.classifications.add(unclass)
        kwt.classifications.add(fouo)
        kwt.classifications.add(c_rel)
        kwt.classifications.add(cui)
        kwt.classifications.add(s_rel)

        qat = Network(network_id='c8628ca885d7436e96f664e8d6c1f2d9', name='CPN-QAT', sort_order=7)
        qat.save()
        qat.classifications.add(unclass)
        qat.classifications.add(fouo)
        qat.classifications.add(c_rel)
        qat.classifications.add(cui)
        qat.classifications.add(s_rel)

        sau = Network(network_id='be27f19fd42147ebabc098da6d8bb35c', name='CPN-SAU', sort_order=8)
        sau.save()
        sau.classifications.add(unclass)
        sau.classifications.add(fouo)
        sau.classifications.add(c_rel)
        sau.classifications.add(cui)
        sau.classifications.add(s_rel)

        cpnx = Network(network_id='20c87ade9349487ba9f67b358f470add', name='CPN-X', sort_order=9)
        cpnx.save()
        cpnx.classifications.add(unclass)
        cpnx.classifications.add(fouo)
        cpnx.classifications.add(c_rel)
        cpnx.classifications.add(cui)
        cpnx.classifications.add(s_rel)

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

    # get all file records and update their file_name, file_size, and file_count fields


def updateFiles(request):
    # if the uploaded file is a zip get the info of the contente
    files = File.objects.all()
    for f in files:
        try:
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
        except FileNotFoundError:
            print("couldn not find file: " + str(f.file_object))
            pass

    return HttpResponse("File info updated")
