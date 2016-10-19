#!/usr/bin/python

import csv
import requests
import json
import MySQLdb
from datetime import datetime, timedelta

ips = {}
ipConfidence = {}
topTenIps = [None] * 10
dateObj = (datetime.now() + timedelta(hours=4))
password = ""
token = ""
with open('PATH/TO/TOKEN/token.txt') as f:
		token = f.readline().rstrip()

def readIpsFromMySQLCowrie():

	print "Getting ip's from MySQL for Cowrie"

	with open('PATH/TO/PASSWORD/password.txt') as f:
		password = f.readline().rstrip()

	#Connects and performs query
	db = MySQLdb.connect("HOST","USER",password,"DATABASE" )
	cursor = db.cursor()
	query = ("SELECT ip FROM (SELECT * FROM auth) A LEFT JOIN (SELECT * FROM sessions) B on A.session = B.id LEFT JOIN (SELECT * FROM input) C on B.id = C.session WHERE A.timestamp >= DATE_ADD(CURDATE(), INTERVAL -1 DAY)")
	cursor.execute(query)
	data = cursor.fetchall()

	found = "no"

	#Goes through each line in the data and sees if it is in the ip dict, if not, add it. If yes, increase its count
	for row in data:
		for key, value in ips.iteritems():
			if row[0] == key:
				ips[key] = value + 1
				found = "yes"

		if found == "no":
			ips[row[0]] = 1
		else:
			found = "no"
	for key, value in ips.iteritems():
		print "Found", key, value, "times in the last day"

	db.close()

	assignConfidenceCowrie()

def readIpsFromMySQLRDP():

	print "Getting ip's from MySQL for RDP"

	with open('PATH/TO/PASSWORD/password.txt') as f:
		password = f.readline().rstrip()

	#Connects and performs query
	db = MySQLdb.connect("HOST","USER",password,"DATABASE" )
	cursor = db.cursor()
	query = ("SELECT ip FROM data WHERE timestamp >= DATE_ADD(CURDATE(), INTERVAL -1 DAY)")
	cursor.execute(query)
	data = cursor.fetchall()

	found = "no"

	#Goes through each line in the data and sees if it is in the ip dict, if not, add it. If yes, increase its count
	for row in data:
		for key, value in ips.iteritems():
			if row[0] == key:
				ips[key] = value + 1
				found = "yes"

		if found == "no":
			ips[row[0]] = 1
		else:
			found = "no"
	for key, value in ips.iteritems():
		print "Found", key, value, "times in the last day"

	db.close()

	assignConfidenceRDP()

def readIpsFromCSV():

	with open('PATH/TO/CSV/Export_allActivity.csv', 'rb') as csvfile:
			reader = csv.reader(csvfile)
			found = "no"
			first = "yes"
			for row in reader:
				if first == "yes":
					first = "no"
					continue
				i = 1
				for col in row:
					if i == 1:
						if (dateObj - datetime.strptime(col, "%Y-%m-%d %H:%M:%S") > timedelta(1)):
							break
					if i == 3:
						for key, value in ips.iteritems():
							if col == key:
								ips[key] = value + 1
								found = "yes"
						if found == "no":
							ips[col] = 1
						else:
							found = "no"
					i += 1
	assignConfidenceCowrie()

def getConfidence(ip, required=75):

	#Sets up all data needed to be passsed to the api
	threeDaysAgo = (dateObj - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
	url = "https://CIFSERVER.COM/observables?confidence=" + str(required) + "&q=" + str(ip) + "&reporttime=" + str(threeDaysAgo)
	headers = {"Accept" : "application/vnd.cif.v2+json", "Authorization" : "Token token=" + token}

	#Makes request and reads data. If c level of 75+ return true
	r = requests.get(url, headers=headers, verify=False)
	data = json.loads(r.text)
	for i in data:
		confidence = False
		for key, value in i.iteritems():
			if key == "confidence":
				if value > required:
					return True
				else:
					return False

def assignConfidenceCowrie():

	print "Assigning Confidence"
	#Gets the top ten IP's and checks them against cif
	for ip in getTopTen():
		if ip in ips.keys():
			if getConfidence(ip):
				ipConfidence[ip] = 85
				print ip, "was found in cif: confidence being set to 85"
			else:
				print ip, "was not found in cif: confidence being set based on attempts"
				if ips.get(ip) >= 10000:
					ipConfidence[ip] = 85
				elif ips.get(ip) >= 1000:
					ipConfidence[ip] = 75
				elif ips.get(ip) >= 500:
					ipConfidence[ip] = 65
				elif ips.get(ip) >= 100:
					ipConfidence[ip] = 55
				elif ips.get(ip) >= 50:
					ipConfidence[ip] = 45
				elif ips.get(ip) >= 25:
					ipConfidence[ip] = 35
				elif ips.get(ip) >= 15:
					ipConfidence[ip] = 25
				elif ips.get(ip) >= 10:
					ipConfidence[ip] = 15
				elif ips.get(ip) >= 5:
					ipConfidence[ip] = 10
				elif ips.get(ip) >= 1:
					ipConfidence[ip] = 5
				else:
					ipConfidence[ip] = 0

	print "Printing final values before submission"
	for key, value in ipConfidence.iteritems():
		print key, ":", value

	print "Submitting ip's to cif"
	for key, value in ipConfidence.iteritems():
		postObservable(key, value, "SSH")

def assignConfidenceRDP():

	print "Assigning Confidence"
	#Gets the top ten IP's and checks them against cif
	for ip in getTopTen():
		if ip in ips.keys():
			if getConfidence(ip):
				ipConfidence[ip] = 85
				print ip, "was found in cif: confidence being set to 85"
			else:
				print ip, "was not found in cif: confidence being set based on attempts"
				if ips.get(ip) >= 25:
					ipConfidence[ip] = 85
				elif ips.get(ip) >= 20:
					ipConfidence[ip] = 75
				elif ips.get(ip) >= 15:
					ipConfidence[ip] = 65
				elif ips.get(ip) >= 12:
					ipConfidence[ip] = 55
				elif ips.get(ip) >= 10:
					ipConfidence[ip] = 45
				elif ips.get(ip) >= 8:
					ipConfidence[ip] = 35
				elif ips.get(ip) >= 6:
					ipConfidence[ip] = 25
				elif ips.get(ip) >= 4:
					ipConfidence[ip] = 15
				elif ips.get(ip) >= 2:
					ipConfidence[ip] = 10
				elif ips.get(ip) >= 1:
					ipConfidence[ip] = 5
				else:
					ipConfidence[ip] = 0

	print "Printing final values before submission"
	for key, value in ipConfidence.iteritems():
		print key, ":", value

	print "Submitting ip's to cif"
	for key, value in ipConfidence.iteritems():
		postObservable(key, value, "RDP")

def getTopTen():

	#Gets the top 10 IP's and checks for duplicates
	i = 0
	j = 0
	while i < 10 and i < len(ips):
		if sorted(ips, key=ips.get, reverse=True)[j] not in topTenIps:
			topTenIps[i] = sorted(ips, key=ips.get, reverse=True)[j]
			i += 1
			j += 1
		else:
			j += 1

	return topTenIps

def postObservable(ip, confidence, dataType):

	#Sets up all data needed for the api and creates json content
	url = "https://CIFSERVER.COM/observables"
	headers = {"Accept" : "application/vnd.cif.v2+json", "Authorization" : "Token token=" + token, "Content-Type" : "application/x-www-form-urlencoded"}
	data = {"observable": ip,"tlp":"green","confidence": str(confidence),"tags": ["honeypot","scanner", dataType],"provider":"honeypot@DOMAIN.COM","group":"everyone","description":"This is DOMAIN honeypot data"}

	jsonData = json.dumps(data)

	#Makes post request to server
	r = requests.post(url, jsonData, headers=headers, verify=False)

	print "Response from server for ip [" + ip + "]:", r.text

print "Starting script for", datetime.now()
readIpsFromMySQLCowrie()
readIpsFromMySQLRDP()