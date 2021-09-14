import os
import re
import shutil
# ====================================================================
# core
from zipfile import ZipFile, BadZipFile
from django.conf import settings
import shutil

# decorators
from django.contrib.auth.decorators import login_required

# responses
from django.shortcuts import render
from django.http import JsonResponse

# pdf parsing
from io import StringIO
import PyPDF2
# cfts settings
from cfts import settings as cftsSettings

# db models
from pages.models import *

# regular expressions
import re

import logging
logger = logging.getLogger('django')

# ====================================================================


@login_required
def scan(request,pullZip):
    # request context
    rc = {
        'bodyText': 'Scan Tool'
    }

    # POST
    if request.method == 'POST':

        extractPath = settings.SCANTOOL_DIR+"\\scan_1"

        i = 2
        while True:
            if os.path.isdir(extractPath):
                extractPath = settings.SCANTOOL_DIR+"\\scan_"+str(i)
                i+=1
            else:
                break
                
        if pullZip !="none":
            pullZip = os.path.join(cftsSettings.BASE_DIR,"pulls",pullZip)
            zf = ZipFile(pullZip)
            zf.extractall(extractPath)    
            results = runScan(extractPath)

        else:
            form_files = request.FILES
            for i, f in enumerate(form_files.getlist("toScan")):
                zf = ZipFile(f)
                zf.extractall(extractPath)
                results = runScan(extractPath)

        # clean up after yourself
        shutil.rmtree(extractPath)
        
        return JsonResponse(results, safe=False)

    # GET
    if pullZip !="none":
        return render(request, 'pages/scan.html', {'rc': rc, 'pullZip': pullZip })
    else:
        return render(request, 'pages/scan.html', {'rc': rc})
    

def runScan(extractPath):
    scan_results = []
    fileList = []
    office_filetype_list = [".docx", ".dotx", ".xlsx",
                            ".xltx", ".pptx", ".potx", ".ppsx", ".onenote"]
    
    scan_dir = os.path.abspath(extractPath)

    # \cfts\scan should contain all the user folders from the zip file
    #txt = re.compile('_email(\d+)?.txt')
    #eml = re.compile('_email(\d+)?.eml')
    scanSkip = ["_email.txt", "_encrypt.txt"]


    for root, subdirs, files in os.walk(scan_dir):

        for filename in files:            
            fileList.append(root+"\\"+filename)
    for filename in fileList:
        if filename.split("\\")[-1] not in scanSkip:
            try:
                file_results = None
                temp, ext = os.path.splitext(filename)

                if(ext in office_filetype_list):
                    file_results = scanOfficeFile(filename)

                    if file_results is not None:
                        for result in file_results:
                            if result['findings'] != ['File is corrupt. Cannot scan.']:
                                temp, ext = os.path.splitext(result['file'])    
                                if ext in office_filetype_list:
                                    embedOffFilePath = os.path.dirname(filename)+"\\"+result['file'].split('\\')[-1]
                                    shutil.move(result['file'], embedOffFilePath)
                                    fileList.append(embedOffFilePath)
                            
                    # clean up after yourself
                    if os.path.isdir(os.path.dirname(filename)+"\\office"):
                        shutil.rmtree(os.path.dirname(filename)+"\\office")

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
                    file_results = scanFile(text_path)
                    if file_results is not None:
                        file_results['file'] = filename

                elif(ext == '.zip'):
                    fileZip = ZipFile(os.path.join(root,filename))
                    extractDir = os.path.dirname(filename)+"\\extracted_files\\"+filename.split("\\")[-1]
                    fileZip.extractall(extractDir)
                    for zipRoot, zipDirs, zipFiles in os.walk(extractDir):
                        for file in zipFiles:
                            fileList.append(zipRoot+"\\"+file)

                else:
                    file_results = scanFile(filename)

            except Exception as e:
                file_results = []
                result = {
                    'file': filename,
                    'findings': [str('Error in scan: ' + repr(e))]
                    }
                file_results.append(result)

            if(file_results is not None):
                result = {}
                result['file'] = filename
                result['found'] = file_results
                scan_results.append(result)

    return scan_results

def scanOfficeFile(office_file):
    results = None
    # treat as a zip and extract to \cfts\scan\temp directory
    try:
        zf = ZipFile(office_file)
        zf.extractall(os.path.dirname(office_file)+"\\office")    

        # step through the contents of the scantool 'temp' folder
        for root, subdirs, files in os.walk(os.path.dirname(office_file)+"\\office"):
            for filename in files:
                file_path = os.path.join(root, filename)
                findings = scanFile(file_path)
                if(findings is not None):
                    if(results is None):
                        results = []
                    results.append(findings)

    except BadZipFile:
        if results is None:
            results = []
            
        result = {
            'file': office_file,
            'findings': ['File is corrupt. Cannot scan.']
            }
        results.append(result)
    # done
    return results


def scanFile(text_file):
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
               'file': text_file,
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
        result = {'file': text_file, 'findings': ['Unable to scan file.']}

    return result


def cleanup(folder):
    for oldfile in os.listdir(folder):
        old = os.path.join(folder, oldfile)
        try:
            if os.path.isfile(old) or os.path.islink(old):
                os.unlink(old)
            elif os.path.isdir(old):
                shutil.rmtree(old)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (old, e))