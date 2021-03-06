## .eml file generation

# zip manipulation
from zipfile import ZipFile
import os
import re
import shutil

# email creation
from email.generator import Generator
from email.mime.text import MIMEText
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
import mimetypes

try:
    currentDir = os.path.dirname(os.path.realpath(__file__))

    fromZip = True
    emldirs = []

    for dir in os.scandir(currentDir):
        emldirs.append(dir.path)
        if dir.name.split('.')[-1] == "zip":
                zipPath = dir.path
                zipExtractPath = os.path.dirname(zipPath.split('.zip')[0])+"\\encrypted requests"

    try:
        print("zip folder: ", zipPath)
        print("extract folder:", zipExtractPath)
        zip = ZipFile(zipPath, 'r')
        zip.extractall(zipExtractPath)
    except NameError:
        fromZip = False
        print("no zip, assuming unzipped folder exists")
        print("searching for folder...")
        for dir in emldirs:
            if dir.split(".")[-1] != "eml":
                shutil.copytree(dir, os.path.dirname(dir)+"\\encrypted requests")
                zipExtractPath = os.path.dirname(dir)+"\\encrypted requests"
                break;

        print("extract folder:", zipExtractPath)
    requestRE = re.compile('request_\d+')
    email = re.compile('_email(\d+)?.txt')
    encrypt = re.compile('_encrypt(\d+)?.txt')
    notes = re.compile('_notes(\d+)?.txt')

    requestPaths = []

    def treeScan(path):
        for dir in os.scandir(path):
            if dir.is_file():
                requestPaths.append(os.path.dirname(dir.path))
            else:
                treeScan(dir)


    treeScan(zipExtractPath)
except NotADirectoryError:
    print("could not find a pull folder/zip")
    exit()

requestPaths = set(requestPaths)
print("\n Request paths:")
print(requestPaths)

for path in requestPaths:
    print("\nscanning from request: ", path)
    print("creating email file...")
    encrpytEmail = False
    msg = MIMEMultipart()
    body = ""

    for f in os.scandir(path):
        filePath = f.path
        if email.match(f.name)!= None:
            msg['Subject'] = 'CFTS File Transfer'
            body += 'Attached files transferred across domains from CFTS.'

            with open(filePath,'r') as _email:
                msg['To'] = ";".join(_email.read().splitlines())
                _email.close()

        elif encrypt.match(f.name)!= None:
            msg['Subject'] = 'DoD SAFE Encryption Phrase'
            encrpytEmail = True
            
            with open(filePath,'r') as _email:
                to_email = _email.read()
                msg['To'] = to_email
                body += "Use the following passphrase to decrypt your DoD SAFE file drop: "
                body += to_email
                _email.close()
                
    for f in os.scandir(path):
        filePath = f.path
                
        if notes.match(f.name) != None:
            body += '''<p style="color: blue;"><b>!!!! Found _notes.txt file in request. Check notes before sending. !!!!</b></p>'''
            
        elif encrpytEmail == False and email.match(f.name )== None and encrypt.match(f.name) == None:
            fileMime = mimetypes.guess_type(filePath)
            file = open(filePath.encode('utf-8'),'rb')
            attachment = MIMEBase(fileMime[0],fileMime[1])
            attachment.set_payload(file.read())
            file.close()
            encode_base64(attachment)
            attachment.add_header('Content-Disposition','attachment',filename=filePath.split("\\")[-1])
            msg.attach(attachment)
            
            
    msg.attach(MIMEText(body,'html'))
    pathParts = path.split("\\")
    emlBase = "   " + pathParts[-2] + "   " + pathParts[-1] + ".eml"
    
    if encrpytEmail == False:
        emlFile = emlBase
        msgPath = currentDir + "/" + emlFile
        shutil.rmtree(path)
        if not os.listdir(os.path.dirname(path)):
            shutil.rmtree(os.path.dirname(path))
        
    elif encrpytEmail == True:
        emlFile = "__ENCRYPTED" + emlBase
        msgPath = currentDir + "/" + emlFile

    msg.add_header('X-Unsent', '1')
    
    with open(msgPath, 'w') as eml:
        gen = Generator(eml)
        gen.flatten(msg)

    print("File created: " + emlFile)
    

print("all email files created")
