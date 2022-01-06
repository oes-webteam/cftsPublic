import os
import re
import shutil
# ====================================================================
# core
from zipfile import ZipFile, BadZipFile
from django.conf import settings
import shutil
from django.db.models import Sum, Count, Q, IntegerField

# decorators
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache

from pages.views.auth import superUserCheck, staffCheck

# responses
from django.shortcuts import redirect, render
from django.http import JsonResponse

# pdf parsing
from io import StringIO
import PyPDF2

# db models
from pages.models import *

# regular expressions
import re

import logging
logger = logging.getLogger('django')

# ====================================================================

@login_required
@user_passes_test(staffCheck, login_url='frontend', redirect_field_name=None)
def viewScan(request, pull_id):
    requests = Request.objects.filter(pull__pull_id=pull_id).annotate(imgCount=Sum('files__scan_results__0__imgCount', output_field=IntegerField()), cleanCount=Count('files', filter=Q(files__scan_results__0="empty"))).order_by('user','-date_created')
    folderNames = []

    for rqst in requests:
        folder = str(rqst.user) + "/request_1"

        if folder in folderNames:
            i = 2
            while folder in folderNames:
                folder = str(rqst.user) + "/request_" + str(i)
                i+=1
        folderNames.append(folder)

    folderNames = list(reversed(folderNames))

    return render(request, 'pages/scan.html', {'requests': requests, 'requestFolders': folderNames})

def scan(request, rqst_id):
    rqst = Request.objects.get(request_id=rqst_id)
    files = rqst.files.all()

    scan_folder = settings.SCANTOOL_DIR+"\\scan_1"

    i = 2
    while True:
        if os.path.isdir(scan_folder):
            scan_folder = settings.SCANTOOL_DIR+"\\scan_"+str(i)
            i+=1
        else:
            break

    try:
        for file in files:
            os.makedirs(scan_folder)
            shutil.copy(file.file_object.path, scan_folder)
            results = runScan(scan_folder)

            if results == []:
                results = ['empty']

            file.scan_results = results
            file.save()
            shutil.rmtree(scan_folder, ignore_errors=True)

        rqst.files_scanned = True
        rqst.save()

    except Exception as e:
        shutil.rmtree(scan_folder)
        for file in files:
            if file.scan_results == []:
                results = [{
                    'file': file.file_object.path,
                    'found': [{'file': file.file_object.path,
                    'findings': [str('Error in scan: ' + repr(e))]}]
                }]

                file.scan_results = results
                file.save()

    if request.method == 'GET':
        return redirect('transfer-request' , id=rqst_id)

def runScan(scan_folder):
    scan_results = []
    fileList = []
    office_filetype_list = [".docx", ".dotx", ".xlsx",
                            ".xltx", ".pptx", ".potx", ".ppsx", ".onenote"]
    
    # scan_dir = os.path.abspath(scan_folder)

    with os.scandir(scan_folder) as files:
        for file in files:
            fileList.append(file.path)
    
    # \cfts\scan should contain all the user folders from the zip file
    printBin = re.compile('printerSettings(\d+).bin')
    imgFiles = re.compile('(jpe?g|png|gif|bmp|emf)', re.IGNORECASE)
    # scanSkip = ["_email.txt", "_encrypt.txt", "_notes.txt"]

    imgCount = 0
    # if filename.split("\\")[-1] not in scanSkip:
    for filename in fileList:
        readablePath = filename.split(scan_folder+"\\")[1]
        try:
            readablePath = readablePath.split("extracted_files\\")[-1]
        except:
            pass

        if printBin.match(filename.split("\\")[-1]) == None:
            try:
                file_results = None
                temp, ext = os.path.splitext(filename)
                ext = ext.lower()

                if(ext in office_filetype_list):
                    file_results = scanOfficeFile(filename)

                    if file_results is not None:
                        removeResults = []
                        for result in file_results:
                            try:
                                if imgFiles.match(result['file'].split(".")[-1]) == None:
                                    if result['findings'] != ['File is corrupt. Cannot scan.']:
                                        temp, ext = os.path.splitext(result['file'])
                                        ext = ext.lower()

                                        if ext in office_filetype_list:
                                            embedOffFilePath = os.path.dirname(filename)+"\\"+result['file'].split('\\')[-1]
                                            shutil.move(result['file'], embedOffFilePath)
                                            fileList.append(embedOffFilePath)
                                else:
                                    imgCount+=1
                                    removeResults.append(result)

                            except KeyError:
                                pass
                        
                        if removeResults is not []:
                            for result in removeResults:
                                file_results.remove(result)
                            
                    # clean up after yourself
                    if os.path.isdir(os.path.dirname(filename)+"\\office"):
                        shutil.rmtree(os.path.dirname(filename)+"\\office", ignore_errors=True)

                elif(ext == '.pdf'):
                    textFile = open(temp+".txt", "w", encoding="utf-8")
                    with open(filename, 'rb') as pdf:
                        pdfReader = PyPDF2.PdfFileReader(pdf)
                        pages = pdfReader.pages
                        
                        for page in pages:
                            pageText = page.extractText()
                            textFile.write("".join(pageText.split()))
                            
                        pdf.close()

                    textFile.close()
                    text_path = os.path.join(temp+".txt")
                    file_results = [scanFile(readablePath, text_path)]
                    if file_results[0] is not None:
                        file_results[0]['file'] = readablePath
                    else:
                        file_results = None

                elif(ext == '.zip'):
                    isZip = True
                    fileZip = ZipFile(filename)
                    extractDir = os.path.dirname(filename)+"\\extracted_files\\"+filename.split("\\")[-1]
                    fileZip.extractall(extractDir)
                    for zipRoot, zipDirs, zipFiles in os.walk(extractDir):
                        for file in zipFiles:
                            fileList.append(zipRoot+"\\"+file)

                else:
                    file_results = [scanFile(readablePath, filename)]
                    if file_results[0] is not None:
                        if imgFiles.match(file_results[0]['file'].split(".")[-1]) != None:
                            imgCount+=1
                            file_results = []
                    else:
                        file_results = None

            except Exception as e:
                file_results = []
                result = {
                    'file': readablePath,
                    'findings': [str('Error in scan: ' + repr(e))]
                    }
                file_results.append(result)

            if(file_results is not None):
                result = {}
                result['file'] = readablePath
                result['found'] = file_results
                if imgCount > 0:
                    result['imgCount'] = imgCount
                    imgCount = 0
                    #result['image']=True
                scan_results.append(result)

    return scan_results

def scanOfficeFile(office_file):
    results = None
    printBin = re.compile('printerSettings(\d+).bin')

    # treat as a zip and extract to \cfts\scan\temp directory
    try:
        name, ext = os.path.splitext(office_file)
        name = name.split("\\")[-1]
        ext = ext.split(".")[-1]
        extractPath = os.path.join(os.path.dirname(office_file),"office",office_file.split("\\")[-1])
        
        zf = ZipFile(office_file)
        zf.extractall(extractPath)    

        # step through the contents of the scantool 'temp' folder
        for root, subdirs, files in os.walk(extractPath):
            for filename in files:
                if printBin.match(filename.split("\\")[-1]) == None:
                    file_path = os.path.join(root, filename)
                    readablePath = file_path.split("scan\\")[1].split("\\")
                    readablePath = "\\".join(readablePath[1:])

                    readablePath = readablePath.split("extracted_files\\")[-1]
                    readablePath = readablePath.replace("office\\","")

                    findings = scanFile(readablePath, file_path)

                    if(findings is not None):
                        if(results is None):
                            results = []
                        results.append(findings)
    except BadZipFile:
        if results is None:
            results = []
            
        result = {
            'file': office_file,
            'findings': ['File is corrupt. Cannot scan.'],
            }
        results.append(result)
    # done
    return results

def scanFile(readablePath, text_file):
    # result = {
    #     'file': text_file,
    #     'findings': []
    # }
    result = None

    reg_lst = []

    for raw_regex in DirtyWord.objects.filter(case_sensitive = False):
        reg_lst.append(re.compile(raw_regex.word, re.IGNORECASE))
    
    for raw_regex in DirtyWord.objects.filter(case_sensitive = True):
        reg_lst.append(re.compile(raw_regex.word))

    try:
        with open(text_file, "r", encoding="utf-8") as f:
            f_content = f.read()
            result = {
                'file': readablePath,
                'findings': []
            }
            for compiled_reg in reg_lst:
                found = re.finditer(compiled_reg, f_content)
                for match in found:
                    #result['findings'].append( '%s <br/> %s (%s)' % ( match.string, match.group(), match.start() ) )
                    result['findings'].append(
                        'This file contains the term: %s' % (match.group()))

            if not len(result['findings']):
                result = None

    except UnicodeDecodeError:
        # Found non-text data
        result = {'file': readablePath, 'findings': ['Unable to scan file.']}

    return result