#!/usr/bin/python
#================================================================================
# CC BY-SA 3.0 DE - Marcus Ullrich | gu471.de
# v2 - 160227
#================================================================================
#config

#mail
 #Absender
mailSender = "CRON@gu471.de"
 #Empfaenger
mailRecepient = "admin@gu471.de"
import socket
#Betreff
mailSubject = "CRON@" + socket.gethostname() + " - drive status checks"

#Hier die Festplatten eintragen, die ueberwacht werden sollen
#set your drives to the list
setDrives = ["sda",
			 "sdb",
			 "sdc",
			 "sdd"]
#Hier die logischen Datentraeger mit Bezeichnung eintragen
#set the volumes to the dict
setVolumeDescription = {"md0": "swap",
			"md1": "/boot",
			"md2": "/"}

#temporaerer Ordner zum zwischenspeichern der Ergebnisse
#temp folder for stdout
scriptTemp = r'/tmp/scriptoutput/' 

#leer lassen, damit an jedem Tag ein report gesendet wird
# ansonten Wochentag angeben, z. B.: Samstag == 6 oder Mittwoch == 3
# sollten Fehler/Warnungen auftreten, wird trotzdem gesendet
#leave empty, then every day a report will be sent
# else set the weekday, e. g.: Saturday == 6 or Wendsday == 3
# if errors or warnings are present, the report will be sent nevertheless
sendOnlyOncePerWeek = r'6'

#bash commands over os.system()
#Kommando fur Uebersicht ueber Syncronizitaet der Platten
 #command for mdstat
 #_ $cmdMdstat > $scriptTemp/mdstat
cmdMdstat = r'cat /proc/mdstat'
 #Kommando fuer S.M.A.R.T. Details
 #command for smart (apt install smartmontools)
 #_ $cmdSmart > $scriptTemp/smart_$setDrives[i]
cmdSmart = r'smartctl -A -d '
 #z.B. ata oder scsi, sh. smartctl --help (Option -d) fuer weitere Informationen
 #e.g. ata or scsi, s. smartctl --help (option -d) for more information
typeSmart = r'ata'

#================================================================================
#imports
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from subprocess import Popen, PIPE
import os
 #regex
import re
import datetime

#================================================================================
#globals
isProblem = False
isWarning = False

#================================================================================
#mdstat		
#write mdstat to tmp
def setMdstat():
	os.system(cmdMdstat + " > " + scriptTemp + "mdstat")
	os.system("cp " + scriptTemp + "mdstat" + " " + scriptTemp + "mdstat" + ".plain")

	parseMdstat()

#parse mdstat from temp without spam
def parseMdstat():
	filePath = scriptTemp + "mdstat"
		
	#clear headers of file
	 #read lines from file
	file = open(filePath,"r")
	lines = file.readlines()
	file.close()
		
	 #set patterns
	patternPersonalities = re.compile("Personalities :")
	patternUnusedDevicesNone = re.compile("unused devices: <none>")
		
	 #parse lines to html table, without headers and empty lines
	file = open(filePath, "w")
	linesToParse = []
	for line in lines:
		line = line.replace("\n", "")
		#miss headers and zero lines
		if (not patternPersonalities.match(line) and
		    not patternUnusedDevicesNone.match(line) and 
			line.strip() != ""):
			
			linesToParse.append(re.split('\s+', line.strip()))
			
	file.write(parseMdstatHTML(linesToParse))
	file.close()

#parse cleared data to HTML, with highlight and warnings
def parseMdstatHTML(lines):
	global isWarning
	global isProblem
	
	parsedArraySet = ""
	parsedDetails = ""
	
	volume = ""
	listArraySet = [];
	listDetails = [];

	#sort ArraySet and ArrayDetails for them selves
	for line in lines:
		if "md" in line[0]:
			#for adding volume to details
			volume = line[0]
			listArraySet.append(line)
		else:
			#add volume to detail list
			line.insert(0, volume)
			listDetails.append(line)
	
	#sort lists alphabetically
	listArraySet = sorted(listArraySet, key=byfirstItem)
	listDetails = sorted(listDetails, key=byfirstItem)
	
	#for each volume in array(Set)
	for i in range(0, len(listArraySet)):
		#set table for overview
		line = listArraySet[i]
		parsedArraySet += "<tr><td>" + line[0] + "</td>"
		for j in range(2,len(line)):
			parsedArraySet += "<td>" + line[j] + "</td>"
		parsedArraySet += "</tr>\n"
		
	#for each volume in array(Details)
	for i in range(0, len(listDetails)):
		line = listDetails[i]
		
		#volumename
		volume = line[0];
		parsedDetails += "<tr><td>" + volume + "</td>"
		
		#not either needed
		line.pop(0)
		#details are "stupid" delimited
		line = ' '.join(line)
		#description
		if volume in setVolumeDescription:
			parsedDetails += "<td>" + setVolumeDescription[volume] + "</td>"
		else:
			parsedDetails += "<td> (NIL) </td>"

		#pattern to match OutOfSync
		patternOutOfSync = re.compile("\[((_U+)_*|_*(U+_))\]")

		if patternOutOfSync.search(line):
			parsedDetails += "<td align='right' style='color:red'><b>" + line + "</b></td></tr>\n"
			isProblem = True
		else:
			parsedDetails += "<td align='right'>" + line + "</td></tr>\n"
		
	parsedArraySet = "<table>" + parsedArraySet + "</table>"
	parsedDetails = "<table>" + parsedDetails + "</table>"
	
	parsed = "<h2>ArraySet</h2>" + parsedArraySet + "<h2>ArrayDetails</h2>"  + parsedDetails
	
	return parsed

#for sorting by first item in an Array with an Array-item
def byfirstItem(item):
	return item[0]	

#================================================================================
#smart	
#write S.M.A.R.T. to tmp
def setSmart():
	for drive in setDrives:
		#set filePath
		filePath = scriptTemp + "smart_" + drive
		#get S.M.A.R.T. from $cmdSmart > $scriptTemp
		os.system(cmdSmart + getCmdSmartDrive(drive) + " > " + filePath)
		os.system("cp " + filePath + " " + filePath + ".plain")
		
		parseSmart(drive)

#MODIFY 
def getCmdSmartDrive(drive):
	return typeSmart + " /dev/" + drive
	
#parse mdstat from temp without spam
def parseSmart(drive):
	#set filePath
	filePath = scriptTemp + "smart_" + drive
		
	#clear headers of file and reorder temp
	 #read lines from file
	file = open(filePath,"r")
	lines = file.readlines()
	file.close()
		
	 #set patterns
	patternVersion = re.compile("smartctl [0-9]*.[0-9]* [0-9]{4}-[0-9]{2}-[0-9]{2} r[0-9]*\s")
	patternCopyright = re.compile("Copyright \(C\) 2002-[0-9]{2}, Bruce Allen, Christian Franke, www.smartmontools.org")
	patternStart = re.compile("=== START OF READ SMART DATA SECTION ===")
	patternSmartRevision = re.compile("SMART Attributes Data Structure revision number: [0-9]*")
	patternAttributeLabel = re.compile("Vendor Specific SMART Attributes with Thresholds:")
		
	 #parse lines to html table, without headers and reorder temp
	file = open(filePath, "w")
	file.write("<h2>" + drive + "</h2> <table>")
	for line in lines:
		line = line.replace("\n", "")
		#reorder temp : Min/Max
		if "0x0002" in line and "Min/Max" in line:		
			line = line.replace(" (Min/Max ", "|")
			line = line.replace(")", "")
			line = line.replace("/", "|")
			r = re.compile('([0-9]*)\|([0-9]*)\|([0-9]*)')
			line = r.sub(r'\2<\1<\3', line)
		#miss headers and zero lines
		if (not patternVersion.match(line) and
		    not patternCopyright.match(line) and 
			not patternStart.match(line) and
			not patternSmartRevision.match(line) and
			not patternAttributeLabel.match(line) and
			line != ""):
				
			line = re.split('\s+', line.strip())
			file.write(parseSmartHTML(line))

	file.write("</table>")
	file.close()

#parse cleared data to HTML, with highlight and warnings
def parseSmartHTML(line):
	global isWarning
	global isProblem

	tresh = line[5];
	parsed = "<tr>"
	for i in range(0, len(line)):
		item = line[i]
		if i == 8:
			if item != "-" and item != "WHEN_FAILED":
				parsed += "<td style='color:red'><b>" + item + "</b></td>"
			else:
				parsed += "<td>" + item + "</td>"
		elif is_number(item) and 3 <= i <= 4:
			if item <= tresh:
				parsed += "<td style='color:red'><b>" + item + "</b></td>"
				isProblem = True
			elif float(item) - 25 <= float(tresh):
				parsed += "<td style='color:orange'><b>" + str(item) + "</b></td>"
				isWarning = True
			else:
				parsed += "<td style='color:green'>" + item + "</td>"
		else:
			parsed += "<td>" + item + "</td>\n"
	parsed += "</tr>"
	
	return parsed

#================================================================================
#mail
def sendMail(subject,message,plain):
	msg = MIMEMultipart('alternative')
	#msg = MIMEText(msg)
	msg["From"] = mailSender
	msg["To"] = mailRecepient
	msg["Subject"] = subject
	
	msg.attach(MIMEText(plain, 'plain'))
	msg.attach(MIMEText(message, 'html'))
	
	p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
	p.communicate(msg.as_string())
	
#================================================================================
#globals	
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False	

#================================================================================
#main
def main():
	global isWarning
	global isProblem
	
	message = ""
	plain = ""
	subject = mailSubject
	
	if not os.path.exists(scriptTemp):
		os.makedirs(scriptTemp)
	
	#prepare
	setMdstat()
	setSmart()	
	
	#get contents
	 #mdstat
	message += "<h1>mdstat</h1>"
	f = open(scriptTemp + "mdstat", 'r')
	message += f.read()
	f.close
	
	f = open(scriptTemp + "mdstat.plain", 'r')
	plain += f.read()
	f.close	
	 #smart
	message += "<h1>S.M.A.R.T.</h1>"
	for drive in setDrives:
		filePath = scriptTemp + "smart_" + drive
		f = open(filePath, 'r')
		message += f.read()
		f.close
		
		filePath = scriptTemp + "smart_" + drive + ".plain"
		f = open(filePath, 'r')
		plain += f.read()
		f.close		
	
	#warning and problem in mails subject
	if isWarning:
		subject = "[WARN]" + subject
	if isProblem:
		subject = "[ALERT]" + subject
	
	if isWarning or isProblem or sendOnlyOncePerWeek == "" or sendOnlyOncePerWeek == datetime.date.today().strftime("%w"):
		sendMail(subject,message,plain)
	
	if os.path.exists(scriptTemp):
		os.system("rm -R " + scriptTemp)

main()
