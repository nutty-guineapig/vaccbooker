import datetime
import requests
import json
import time
proxy_values = {'https':'http://127.0.0.1:8080', 'http':'http://127.0.0.1:8080'}

#procusre authtoken from finishing the captcha, the site is designed such that completing a captcha grants an auth token, then the auth token can be used to call subsequent APIS (another great example of questionable use of capctha...)
SESSION_TOKEN ='<jwt>'
#Checks for appointments and returns an appointment list with preregdates, and date 
#Takes in bounds for date window 
def checkAppointments(authtoken,after_date,before_date):

	date_format= '%Y-%m-%d'
	
	datetime_after = datetime.datetime.strptime(after_date,date_format)
	datetime_before = datetime.datetime.strptime(before_date,date_format)
	
	appoint_list = []
	http_headers = {'Host': 'vaccinesite-sample.gov',
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0',
	'Accept': 'application/json, text/plain, */*',
	'Accept-Language': 'en-US,en;q=0.5',
	'Accept-Encoding': 'gzip, deflate',
	'Referer': 'https://vaccinesite-sample.gov/en-US/selectDateTime/times',
	'Authorization': authtoken,
	'Content-Type': 'application/json',
	'Origin': 'https://vaccinesite-sample.gov'}

	r = requests.get(url='https://vaccinesite-sample.gov/p/api/v1/appointment/available/event/date/<eventsite>', headers=http_headers, verify=False, proxies=proxy_values)

	if r.status_code == 200:
		print (r.text)
		appointment_data = json.loads(r.text)
		
		print (len(appointment_data["appointmentInfo"]))
		if len(appointment_data["appointmentInfo"])>= 1:
			for appointments in appointment_data["appointmentInfo"]:
				print ("ID %s, Date %s" % (appointments["preregdateidGuid"],appointments["preregdate"]))
				appt_date = appointments["preregdate"]
					
				datetime_obj = datetime.datetime.strptime(appointments["preregdate"],date_format)
				if (datetime_obj > datetime_after and datetime_obj < datetime_before):
					appoint_list.append( {"appointmentID":appointments["preregdateidGuid"], "date":appointments["preregdate"]})
			#print (appointment_data["appointmentInfo"])

	print (appoint_list)
	return(appoint_list)
	
#For a given appointmentID, retrieve time slots	
def retrieveTimeSlots(authtoken, appoint_list):

	found_slots = []
	found_time = []
	http_headers = {'Host': 'vaccinesite-sample.gov',
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0',
	'Accept': 'application/json, text/plain, */*',
	'Accept-Language': 'en-US,en;q=0.5',
	'Accept-Encoding': 'gzip, deflate',
	'Referer': 'https://vaccinesite-sample.gov/en-US/selectDateTime/times',
	'Authorization': authtoken,
	'Content-Type': 'application/json',
	'Origin': 'https://vaccinesite-sample.gov'}
	
	for appointment in appoint_list:
		eventURL = 'https://vaccinesite-sample.gov/p/api/v1/appointment/available/event/date/slot/' + appointment['appointmentID']
		print (eventURL)
		r = requests.get(url = eventURL, headers=http_headers, verify=False, proxies=proxy_values)
		
		json_data = json.loads(r.text)
		print (json_data)
		#print (r.text)
		if "GONE" not in r.text or "NOT_FOUND" in r.text:
			for i in json_data:
				print ("found a slot!: %s at time: %s" % (i["preregtimeslotidGuid"], i["starttime"] ))
				#didnt want to create a dict, then would have to retest
				found_slots.append({"slotID": i["preregtimeslotidGuid"], "timeslot": i["starttime"]}) 
								
	return found_slots

#Iterate through the slots and lock in the time slot
#Returns a slot tracker ID used to lock the appointment
def lockInSlot(authtoken, found_slots):
	http_headers = {'Host': 'vaccinesite-sample.gov',
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0',
	'Accept': 'application/json, text/plain, */*',
	'Accept-Language': 'en-US,en;q=0.5',
	'Accept-Encoding': 'gzip, deflate',
	'Referer': 'https://vaccinesite-sample.gov/en-US/selectDateTime/times',
	'Authorization': authtoken,
	'Content-Type': 'application/json',
	'Origin': 'https://vaccinesite-sample.gov'}

	for slot in found_slots:
		lockinURL = 'https://vaccinesite-sample.gov/p/api/v1/appointment/available/event/date/slot/lock/'+ slot["slotID"]
		r = requests.post(lockinURL, headers=http_headers, verify=False,proxies=proxy_values)

		json_resp = json.loads(r.text)
		if r.status_code == 200:
			if "GONE" not in r.text:
				print("Slot ID: " + json_resp["slotTrackerGuid"])
				return json_resp["slotTrackerGuid"], slot["timeslot"] #we locked in a slot, lets just return and move on quickly..

#Retrieve disclaimers for age, and zip code (returns null), not sure if needed, but lets make it look legit.
def age_zipRetrieval(authtoken):
	http_headers = {'Host': 'vaccinesite-sample.gov',
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0',
	'Accept': 'application/json, text/plain, */*',
	'Accept-Language': 'en-US,en;q=0.5',
	'Accept-Encoding': 'gzip, deflate',
	'Referer': 'https://vaccinesite-sample.gov/en-US/review',
	'Authorization': authtoken,
	'Content-Type': 'application/json',
	'Origin': 'https://vaccinesite-sample.gov'}
	ageURL = 'https://vaccinesite-sample.gov/p/api/v1/appointment/available/event/minimumage/<vaccsite>'
	zipURL = 'https://vaccinesite-sample.gov/p/api/v1/appointment/available/event/allowedzipcodes/<vaccsite>'
	r = requests.get(url=ageURL, headers=http_headers, verify=False,proxies=proxy_values)
	print (r.text)
	r = requests.get(url = zipURL, headers=http_headers,verify=False,proxies=proxy_values)
	print (r.text)

#finalizes the appointment, passes in JSON patient info 
def finalizeAppointment(authtoken,slotID,patient_data):
	http_headers = {'Host': 'vaccinesite-sample.gov',
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0',
	'Accept': 'application/json, text/plain, */*',
	'Accept-Language': 'en-US,en;q=0.5',
	'Accept-Encoding': 'gzip, deflate',
	'Referer': 'https://vaccinesite-sample.gov/en-US/review',
	'Authorization': authtoken,
	'Content-Type': 'application/json',
	'Origin': 'https://vaccinesite-sample.gov'}

	patient_data['slotTrackerGuid']=slotID
	#finalURL = 'https://vaccinesite-sample.gov/p/api/v1/recipient/save'
	finalURL = 'http://127.0.0.1:8888'
	r = requests.post(finalURL, headers=http_headers,json= patient_data,proxies= proxy_values, verify=False)

	print(r.text) # leave this for debug in case it crashes lol
	
	#untested code
	if r.status_code == 200:
		json_resp = json.loads(r.text)
		if "confirmed" in json_resp["message"]:
			apptConfID = json_resp["appointmentConfId"]
			print ("Appointment confirmed! ID is %s" %apptConfID)
			return apptConfID, True #we found an appointment
		else: 
			return "NONE", False


with open("dummydata.json") as f:
	data = json.load(f)
	

slotID=""
#search window - too lazy to put args f it
after_date = "2021-04-07"
before_date = "2021-04-10"
bookedBoolean = False
while not bookedBoolean:#while loop here 
	appointment_list = checkAppointments(SESSION_TOKEN,after_date,before_date)
	if len(appointment_list) > 0:
		found_slots = retrieveTimeSlots(SESSION_TOKEN,appointment_list)
		if len(found_slots) > 0:
			for i in found_slots: #iterate through all time slots until we can lock in
				slotID, timeSlot = lockInSlot(SESSION_TOKEN,found_slots)
				if len(slotID) > 0:
					age_zipRetrieval(SESSION_TOKEN)
					time.sleep(30) #pretend we're reading and stuff... but read at 100 wpm
					apptConfID, bookedBoolean = finalizeAppointment(SESSION_TOKEN,slotID,data)
					if bookedBoolean:
						print ("Confirmed Appointment for %s with ID: %s. Wait for the text/email" % (apptConfID,timeSlot)) 
						exit() # exit out 
	time.sleep(1.5)


