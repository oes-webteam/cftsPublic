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


currentDir = os.path.dirname(os.path.realpath(__file__))

fromZip = True
emldirs = []

for dir in os.scandir(currentDir):
    emldirs.append(dir.path)
    if dir.name.split('.')[-1] == "zip":
            zipPath = dir.path
            zipExtractPath = zipPath.split('.')[0]

try:
    print("zip folder: ", zipPath)
    print("extract folder:", zipExtractPath)
        
    zip = ZipFile(zipPath, 'r')
    zip.extractall(zipExtractPath)
except NameError:
    fromZip = False
    print("no zip, assuming unzipped folder exists")
    zipExtractPath = emldirs[0]
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

for path in requestPaths:
    print("\nscanning from request: ", path)
    print("creating email file...")
    encrpytEmail = False
    msg = MIMEMultipart()

    for root, subdirs, files in os.walk(path):
        for f in files:
            filePath = os.path.join(root,f)
            
            if email.match(f)!= None:
                msg['Subject'] = 'CFTS File Transfer'
                msg.attach(MIMEText('Attatched files transfered across domains from CFTS.'))

                with open(filePath,'r') as _email:
                    msg['To'] = "".join(_email.read().splitlines())
                    _email.close()

            elif encrypt.match(f)!= None:
                msg['Subject'] = 'CFTS File Transfer'
                msg.attach(MIMEText('''<p style="color: red;"><b>!!!! Found _encrypt.txt file in request. This email must be sent encrypted. !!!!</b></p><br>Attatched files transfered across domains from CFTS.''', 'html'))
                encrpytEmail = True
                
                with open(filePath,'r') as _email:
                    msg['To'] = "".join(_email.read().splitlines())
                    _email.close()
                    
            elif notes.match(f) == None:
                fileMime = mimetypes.guess_type(filePath)
                file = open(filePath.encode('utf-8'),'rb')
                attachment = MIMEBase(fileMime[0],fileMime[1])
                attachment.set_payload(file.read())
                file.close()
                encode_base64(attachment)
                attachment.add_header('Content-Disposition','attachment',filename=filePath.split("\\")[-1])
                msg.attach(attachment)

        pathParts = path.split("\\")
        emlBase = "   " + pathParts[-2] + "   " + pathParts[-1] + ".eml"
        
        if encrpytEmail == False:
            emlFile = emlBase
            msgPath = currentDir + "/" + emlFile
            
        elif encrpytEmail == True:
            emlFile = "__ENCRYPTED" + emlBase
            msgPath = currentDir + "/" + emlFile

        msg.add_header('X-Unsent', '1')
        
        with open(msgPath, 'w') as eml:
            gen = Generator(eml)
            gen.flatten(msg)

        print("File created: " + emlFile)

print("all email files created")
if fromZip == True:
    shutil.rmtree(zipExtractPath)