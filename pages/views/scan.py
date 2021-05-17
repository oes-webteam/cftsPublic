import os
import re
import shutil
# ====================================================================
# core
from zipfile import ZipFile
from django.conf import settings

# decorators
from django.contrib.auth.decorators import login_required

# responses
from django.shortcuts import render
from django.http import JsonResponse

# pdf parsing
from io import StringIO
from pdfminer.high_level import *
# ====================================================================


@login_required
def scan(request):
    # request context
    rc = {
        'bodyText': 'Scan Tool'
    }

    # POST
    if request.method == 'POST':
        form_files = request.FILES
##    print( form_files )

        for i, f in enumerate(form_files.getlist("toScan")):
            zf = ZipFile(f)
            zf.extractall(settings.SCANTOOL_DIR)
            results = runScan()

        # clean up after yourself
        cleanup(settings.SCANTOOL_DIR)
        return JsonResponse(results, safe=False)

    # GET
    return render(request, 'pages/scan.html', {'rc': rc})


def runScan():
    scan_results = []
    office_filetype_list = [".docx", ".dotx", ".xlsx",
                            ".xltx", ".pptx", ".potx", ".ppsx", ".onenote"]
    scan_dir = os.path.abspath(settings.SCANTOOL_DIR)

    # \cfts\scan should contain all the user folders from the zip file
    for root, subdirs, files in os.walk(scan_dir):
        for filename in files:
            file_results = None
            file_path = os.path.join(root, filename)
##      print( '\t- file %s (full path: %s)' % ( filename, file_path ) )
            temp, ext = os.path.splitext(filename)

            if(ext in office_filetype_list):
                file_results = scanOfficeFile(file_path)
            elif(ext == '.pdf'):
                textFile = open(root+"\\"+temp+".txt", "w")
                pdf2Text = StringIO()
                with open(file_path, 'rb') as pdf:
                    extract_text_to_fp(
                        pdf, pdf2Text, output_type='text', codec='utf-8')
                    textFile.write(pdf2Text.getvalue().strip())
                    textFile.close()

                text_path = os.path.join(root+"\\"+temp+".txt")
                file_results = scanFile(text_path)
                file_results['file'] = file_path
                os.remove(text_path)

            else:
                file_results = scanFile(file_path)

            if(file_results is not None):
                result = {}
                result['file'] = file_path
                result['found'] = file_results
                scan_results.append(result)

    return scan_results


def scanOfficeFile(office_file):
    results = None

    # treat as a zip and extract to \cfts\scan\temp directory
    zf = ZipFile(office_file)
    zf.extractall(settings.SCANTOOL_TEMPDIR)

    # step through the contents of the scantool 'temp' folder
    for root, subdirs, files in os.walk(settings.SCANTOOL_TEMPDIR):
        for filename in files:
            file_path = os.path.join(root, filename)
            findings = scanFile(file_path)
            if(findings is not None):
                if(results is None):
                    results = []
                results.append(findings)

    # clean up after yourself
    # done
    return results


def scanFile(text_file):
    result = {
        'file': text_file,
        'findings': []
    }

    dirty_word_list = ["SECRET", "S//", "NOFORN",
                       "C//", "CONFIDENTIAL", "PRV", "LVY"]
    reg_lst = []
    for raw_regex in dirty_word_list:
        reg_lst.append(re.compile(raw_regex))

    try:
        with open(text_file, "r", encoding="utf-8") as f:
            f_content = f.read()
            # result = {
            #    'file': text_file,
            #    'findings': []
            # }
            for compiled_reg in reg_lst:
                found = re.finditer(compiled_reg, f_content)
                for match in found:
                    #result['findings'].append( '%s <br/> %s (%s)' % ( match.string, match.group(), match.start() ) )
                    result['findings'].append(
                        'This file contains the term: %s' % (match.group()))
            if not len(result['findings']):
                result['findings'].append("Scan returned no dirty words.")

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
