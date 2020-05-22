
import fileinput
import glob
import os
import os.path
import re
import shutil
import subprocess
from os import path

custompath = "/home/vagrant/VM2/customers/"

### Methods that are used ###

# Write a line to a file method
def addToFile(path, append):
	with open(path, "a") as file:
		file.write(append)

# Create new environment
def createNewEnvironment(type, customerName):
	# Start with ID 1
	id = 1
	for name in glob.glob(custompath + customerName + "/" + type + "*"):
		# For every environment that exists, add one
		id += 1
	# Settings for production environment
	if type == "prod":
		dirpath = "prod" + str(id)
		webservers = 2
		databases = 1
		loadbalancers = 1
	# Settings for test environment
	else:
		dirpath = "test" + str(id)
		webservers = 1
		databases = 0
		loadbalancers = 0
	environmentID = nextEnvID()
	# jsonObject with config
	jsonObject = {
		"_cname":_cname, 
		"webservers": str(webservers),
		"databases": str(databases),
		"loadbalancers": str(loadbalancers),
		"environmentID": str(environmentID),
		"dirPath": dirpath
		}
	# Create environment folder
	path = custompath+customerName+"/"+dirpath
	os.mkdir(path)

	# Copy all basefiles to new directory
	for file in glob.glob('/home/vagrant/VM2/basefiles/*'):
		shutil.copy(file, path)
	# Replace all objects in json for Vagrantfile
	replaceVagrant(path, jsonObject)
	print"dirpath created, files copied"

	# Write to hosts file
	addToFile(path+"/hosts", "[all:vars]\n")
	addToFile(path + "/hosts", "ansible_python_interpreter=/usr/bin/python3\n")

	# array for all the ips
	ips = []
	# array for the web ips
	webips = []
	# start at IP 20
	nextIP = 20
	if webservers > 0:
		# Write to hosts file
		addToFile(path + "/hosts", "[webservers]\n")
		for i in range(webservers):
			# Calculate IP address
			ipaddress = str("10.0." + str(environmentID) + "." + str(nextIP))
			# Add IP to arrays
			ips.append(ipaddress)
			webips.append(ipaddress)
			# Next IP is previous + 1
			nextIP += 1
			# VM name
			name = customerName + "-" + dirpath + "-" + "web" + str(i + 1)
			print ipaddress + " " + name
			var = name + " ansible_host=" + ipaddress +  " ansible_user=vagrant"
			# Write information to hosts file
			addToFile(path + "/hosts", var+"\n")

	else:
		print "No webservers"
	# Same see webservers section
	dbips = []
	if databases > 0:
		addToFile(path + "/hosts", "[databaseservers]\n")
		for i in range(databases):
			ipaddress = str("10.0." + str(environmentID) + "." + str(nextIP))
			nextIP += 1
			ips.append(ipaddress)
			dbips.append(ipaddress)
			name = customerName + "-" + dirpath + "-" + "db" + str(i + 1)
			print ipaddress + " " + name
			var = name + " ansible_host=" + ipaddress +  " ansible_user=vagrant"
			addToFile(path + "/hosts", var+"\n")

	else:
		print "No databases"
	# See webservers section
	lbips = []
	if loadbalancers > 0:
		addToFile(path + "/hosts", "[loadbalancers]\n")
		for i in range(loadbalancers):
			ipaddress = str("10.0." + str(environmentID) + "." + str(nextIP))
			nextIP += 1
			ips.append(ipaddress)
			lbips.append(ipaddress)
			name = customerName + "-" + dirpath + "-" + "lb" + str(i + 1)
			print ipaddress + " " + name
			var = name + " ansible_host=" + ipaddress +  " ansible_user=vagrant"
			addToFile(path + "/hosts", var+"\n")

	else:
		print "No webservers"
	# Navigate to the environment path
	os.chdir(path)
	# Vagrant up
	subprocess.call(["vagrant", "up"])
	# For all IPs in the array, do a keyscan and write to hosts file
	for ip in ips:
		string = "ssh-keyscan -t rsa " + ip + " >> ~/.ssh/known_hosts"
		os.system(string)
		# write to ip file
		addToFile(path + "/ips", ip)
	if type == "prod":
		# Execute the ansible playbook for production
		var = "web1_name=web1 web1_ip="+ webips[0] + " web2_name=web2 web2_ip=" + webips[1] + " lb_ip= " + lbips[0] +" db_ip=" + dbips[0]
		subprocess.call(["ansible-playbook", "-i", "hosts", "/home/vagrant/VM2/production.yml", "-e", var])
	else:
		# Execute the ansible playbook for test
		subprocess.call(["ansible-playbook", "-i", "hosts", "/home/vagrant/VM2/test.yml"])

# Destroy environment, remove VMs and remove public keys from ~/.ssh/known_hosts
def destroyEnvironment(path):
	os.chdir(path)
	print("Stop all machines if they are running")
	subprocess.call(["vagrant", "halt", "-f"])
	print("Destroy all machines")
	subprocess.call(["vagrant", "destroy", "-f"])
	print("Remove all public keys")
	try:
		with open(path+"/ips") as file:
			for line in file:
				subprocess.call(["ssh-keygen", "-f", "/home/vagrant/.ssh/known_hosts", "-R", line ])
				print("Removing public key "+line)
	except:
		print("Error removing keys")
	print("Remove file in "+path)
	subprocess.call(["rm -rf "+path], shell=True)

# Check if a directory exists, return inversed boolean
def directoryExists(file):
	return not path.exists(file)

# Print the header, clear previous code
def header():
	os.system("clear")
	print("~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~")
	print
	print(" Welcome to the Self Service Portal (made by s1130596, Robin Wichgers)")
	print
	print("~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~=~")
	print

# Show all available customers
def printAvailableCustomers():
	print("Available customers: ")
	print
	os.chdir(custompath)
	subprocess.call(["dir"])
	print

# Calculate next environment ID
def nextEnvID():
	id = 1
	for name in glob.glob(custompath + "/*" + "/*"):
		id += 1
	return id

# Replace memory in vagrantfile
def replaceMemory(path, amount):
	os.chdir(path)
	file = open(path + "/Vagrantfile", "r")
	text = file.read()
	file.close()

	file = open(path + "/Vagrantfile", "w")
	file.write(re.sub("vb.memory = .[0-9][0-9][0-9]*", "vb.memory = "+amount, text))
	file.close()

# Set default variables in vagrantfile using json object
def replaceVagrant(path, object):
	checks = ("%databaseservers%", 
		"%webservers%",
		"%loadbalancers%", 
		"%customerName%", 
		"%environment%", 
		"%ipaddress%",
		"%customerID%"
		)
	replaces = (object["databases"], 
		object["webservers"],
		object["loadbalancers"], 
		object["_cname"],
		object["dirPath"], 
		str(20),
		object["environmentID"]
		)

	for check, replace in zip(checks, replaces):
		file = open(path + "/Vagrantfile", "r")
		text = file.read()
		file.close()

		file = open(path + "/Vagrantfile", "w")
		file.write(re.sub(check, replace, text))
		file.close()


### Script ###
header()
print("[1] Create new user")
print("[2] Modify existing user")
print("[3] Delete user environment")
print("[4] Delete user, including environment")
option = input("Choose your option: ")
header()

# Create user
if option == 1:
	_cname = raw_input("What is your name?: ")
	print(custompath + _cname)
	if directoryExists(custompath + _cname):
		os.mkdir(custompath+_cname)
		header()
		print("Welcome, "+_cname+", what would you like to do?")
		print("[1] Create production environment: 2 webservers, 1 database, 1 loadbalancer")
		print("[2] Create test environment: 1 webserver")
		option = input("Choose your option: ")
		if option == 1:
			createNewEnvironment("prod", _cname)
		else:
			createNewEnvironment("test", _cname)
	else:
		print("This name already exists, try again")
elif option == 2:
	header()
	printAvailableCustomers()
	_cname = raw_input("What is your name?: ")
	if directoryExists(custompath + _cname) == False:
		header()
		print("Choose an environment:")
		print
		# Show available directories to choose from
		os.chdir(custompath + _cname)
		subprocess.call(["dir"])
		print
		option = raw_input("Choose your option: ")
		if directoryExists(custompath+_cname+"/"+option) == False:
			# change existing directory, probably memory in vagrantfile
			header()
			print("Choose the amount of memory for the VMs:")
			print("[1] 1536 MB")
			print("[2] 1024 MB")
			print("[3] 512 MB")
			memory = input("Choose your option: ")
			if memory == 1:
				qty = 1536
			elif memory == 2:
				qty = 1024
			else:
				qty = 512
			print("Changed memory to " + str(qty))
			replaceMemory(custompath+_cname+"/"+option, str(qty))
			print
		else:
			print("not valid")
	else:
		print("Directory does not exist")

		
elif option == 3:
	header()
	printAvailableCustomers()
	_cname = raw_input("What is your name?: ")
	if directoryExists(custompath + _cname) == False:
		header()
		print("Choose an environment:")
		print
		os.chdir(custompath + _cname)
		subprocess.call(["dir"])
		print
		option = raw_input("Choose your option: ")
		if directoryExists(custompath+_cname+"/"+option) == False:
			destroyEnvironment(custompath+_cname+"/"+option)
		else:
			print("not valid")

elif option == 4:
	header()
	printAvailableCustomers()
	_cname = raw_input("What is your name?: ")
	if directoryExists(custompath + _cname) == False:
		for name in glob.glob(custompath + _cname+"/*"):
			destroyEnvironment(name)
		print("Removing customer "+_cname)
		subprocess.call(["rm -rf "+custompath+_cname], shell = True)
	else:
		print("Not an valid option")

else:
	print("Not a valid option")