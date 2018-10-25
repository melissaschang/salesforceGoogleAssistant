'''Melissa Chang
Trend Micro
Business Applications Intern
7-02-18
Salesforce Assistant APP

Welcome to my salesforce APP, please read the grey comments marked with a '#' to follow along the code.
'''

import json, os, sys, logging, requests, beatbox, os.path, time #import necessary modules, use pip to install: simple-salesforce, beatbox, pycryptodome, flask. and requests
from simple_salesforce import Salesforce, SFType
from flask import request, Flask, make_response
from Crypto.Cipher import AES
from Crypto import Random
from os import listdir
from os.path import isfile,join

app = Flask(__name__) #start object of Flask class and assign to variable "app"

class Encryptor: #create class 'Encryptor' to create function to encrypt password file

    def __init__(self, key): #constructor that passes key as argument, which is a string used to encrypt or decrypt data
        self.key = key

    def pad(self, s): #pad data to match block size of cipher
        return s + b"\0" * (AES.block_size - len(s) % AES.block_size)

    def encrypt(self, message, key, key_size=256):
        message = self.pad(message) #pad message
        iv = Random.new().read(AES.block_size) #create initialization vector, or a random string
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(message) #encrypt string and append it to initialization vector

    def encrypt_file(self, file_name):
        with open(file_name, 'rb') as fo:#open file with file_name
            plaintext = fo.read()
        enc = self.encrypt(plaintext, self.key)
        with open(file_name + ".enc", 'wb') as fo: #create new encrypted file, named file_name.enc
            fo.write(enc)
        os.remove(file_name)

    def decrypt(self, ciphertext, key):
        iv = ciphertext[:AES.block_size] #separate iv from cipher text
        cipher = AES.new(key, AES.MODE_CBC, iv) #creatr object for cipher
        plaintext = cipher.decrypt(ciphertext[AES.block_size:]) #decrypt text
        return plaintext.rstrip(b"\0") #remove padding and return final string

    def decrypt_file(self, file_name):
        with open(file_name, 'rb') as fo: #open  and read encrypted file
            ciphertext = fo.read()
        dec = self.decrypt(ciphertext, self.key) #decrypt data
        with open(file_name[:-4], 'wb') as fo:
            fo.write(dec) #store decrypted data in new file
        os.remove(file_name)




@app.route('/webhook', methods=['POST']) #create POST request and define route
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = makeWebhookResult(req) #pass request thru makeWebhookResult
    res = json.dumps(res, indent=4)
    print(res) #print output from console
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def makeWebhookResult(req):
    intent = req['queryResult']['intent'].get('displayName') #intent var is equal to the intent name from the JSON file generated by dialogflow
    param = req['queryResult'].get('parameters')
    input = req['queryResult'].get('queryText')

  #  key = b'[EX\xc8\xd5\xbfI{\xa2$\x05(\xd5\x18\xbf\xc0\x85)\x10nc\x94\x02)j\xdf\xcb\xc4\x94\x9d(\x9e'
    key = b'[EX\xc8\xd5\xbfI{\xa2$\x05(\xd5\x18\xbf\xc0\x85)\x10nc\x94\x02)j\xdf\xcb\xc4\x94\x9d(\xe9'
    enc = Encryptor(key)
    clear = lambda: os.system('cls') #clear sceen in shell method
    if intent == "Default Welcome Intent":
        if os.path.isfile('data.txt.enc'): #if this file exists in he directory
            while True:
                password = param.get('codeword') #retrieve password from dialogflow JSON's file
                enc.decrypt_file("data.txt.enc") #decrypt stored password to see if it matches
                p = ''
                with open("data.txt", "r") as f:
                    p = f.readlines()
                if p[0] == password: #if it matches, the salesforce userinfo to login is decrypted
                    enc.decrypt_file("userinfo.json.enc")
                    enc.encrypt_file("data.txt")
                    return {"fulfillmentText": "Success! You have decrypted your user information. Welcome to the salesforce assistant. Type 'login' to login if this is your first time.",
                            "source": "salesforceCRM"}
                else:
                    enc.encrypt_file("data.txt")
                    return {"fulfillmentText": "Password was incorrect, try again",
                            "source": "salesforceCRM"}



        else:
            while True:
                clear()
                password = param.get('codeword')

                f = open("data.txt", "w+") #otherwise, if this is the user's first time (no encrypted file), create a new codeword
                f.write(password)
                f.close()
                enc.encrypt_file("data.txt")
                enc.encrypt_file("userinfo.json")
               # time.sleep(15)
                return {"fulfillmentText": "Please type 'restart' and press enter to complete setup",
                        "source": "salesforceCRM"}

    if intent == "exit":
        enc.encrypt_file("userinfo.json")
        return {}

    with open("userinfo.json") as file:  # load userinfo file, storing the username, password, and security token
        read_data = json.load(file)
    file.close()



    if intent == "login":
        with open("userinfo.json", "r") as jsonFile:
            data = json.load(jsonFile)  # revise username and password if intent is "login"

        data["queryResult"]["parameters"]["email"] = param.get('email')
        data["queryResult"]["parameters"]["password"] = param.get('password')
        data["queryResult"]["parameters"]["security_token"] = param.get('security_token')

        with open("userinfo.json", "w") as jsonFile:
            json.dump(data, jsonFile)
        file.close()
        return {
        }

    # login to salesforce thru beatbox and simple-salesforce with info stored in JSON file

    sf = Salesforce(username=read_data["queryResult"]["parameters"]["email"],
                    password=read_data["queryResult"]["parameters"]["password"],
                    security_token=read_data["queryResult"]["parameters"]["security_token"])
    sf2 = beatbox._tPartnerNS
    svc = beatbox.Client()
    svc.login(read_data["queryResult"]["parameters"]["email"],
              read_data["queryResult"]["parameters"]["password"] + read_data["queryResult"]["parameters"]["security_token"])

    string = ""

    if intent != "newLead" and intent != "newContact" and intent != "newOpportunity" and intent != "newAccount" and intent != "newTask" and intent != "readContacts" and intent != "readLeads" and intent != "readTasks" and intent != "readOpportunities" and intent != "taskInfo" and intent != "opportunityInfo" and intent != "leadInfo" and intent != "updateContact":
        return {} #if the intent is none of these methods listed below, nothing is returned

    if intent == "newLead":
        new_lead = sf.Lead.create( #if the intent is new lead, get the necessary paraemeters to create a new lead with simple-salesforce API
            {"FirstName": param.get('first_name'), "LastName": param.get('last_name'), "Company": param.get('company')})
        return {"fulfillmentText": "Your new lead was created!",
                "source": "salesforceCRM"}

    if intent == "newContact":
        new_contact = sf.Contact.create(
            {'FirstName': param.get('first_name'), 'LastName': param.get('last_name'), 'Email': param.get('email')})
        return {"fulfillmentText": "Your new contact was created!",
                "source": "salesforceCRM"}

    if intent == "newOpportunity":
        new_opportunity = sf.Opportunity.create(
            {"Name": param.get("name"), "CloseDate": param.get("close_date"), "StageName": param.get("stage_name"),
             "Amount": param.get("amount")})
        return {"fulfillmentText": "Your new opportunity was created!",
                "source": "salesforceCRM"}

    if intent == "newAccount":
        new_account = sf.Account.create(
            {'Name': param.get('account_name'), 'Site': param.get('account_site'), 'Phone': param.get('phone'),
             'Rating': param.get('rating'), 'AccountNumber': param.get('account_number')})
        return {"fulfillmentText": "Your new account was created!",
                "source": "salesforceCRM"}

    if intent == "newTask":
        new_task = sf.Task.create(
            {'Subject': param.get('subject'), 'Priority': param.get('priority'), 'Status': param.get('status'),
             'ActivityDate': param.get('due_date')})
        return {"fulfillmentText": "Your new task was created!",
                "source": "salesforceCRM"}

    if intent == "readContacts": #use beatbox API to read out recent contacts
        count = int(param.get('number'))
        qr = svc.query("select Id, Name from Contact")
        string = str(qr[sf2.size])

        recent_contacts = ""
        for x in range(0, count):
            if (x == int(string)):
                recent_contacts += (" and you have no more contacts")
                break
            if (x == count - 1):
                recent_contacts += (" and " + str(qr[sf2.records:][x][3]))
            else:
                recent_contacts += (str(qr[sf2.records:][x][3]) + ", ")
        bank = {2: "action finished", 1: "action finished"}

        return {
            "fulfillmentText": "Your " + str(count) + " most recent contacts are: " + recent_contacts,
            "source": "salesforceCRM"
        }

    if intent == "readLeads":
        count = int(param.get('number'))
        qr = svc.query("select Id, Name from Lead")
        string = str(qr[sf2.size])

        recent_leads = ""
        for x in range(0, count):
            if (x == int(string)):
                recent_leads += (" and you have no more leads")
                break
            if (x == count - 1):
                recent_leads += (" and " + str(qr[sf2.records:][x][3]))
            else:
                recent_leads += (str(qr[sf2.records:][x][3]) + ", ")
        return {
            "fulfillmentText": "Your " + str(count) + " most recent leads are: " + recent_leads,
            "source": "salesforceCRM"
        }

    if intent == "readTasks":
        count = int(param.get('number'))
        qr = svc.query("select Id, Subject from Task")
        string = str(qr[sf2.size])

        recent_tasks = ""
        for x in range(0, count):
            if (x == int(string)):
                recent_tasks += (" and you have no more tasks")
                break
            if (x == count - 1):
                recent_tasks += (" and " + str(qr[sf2.records:][x][3]))
            else:
                recent_tasks += (str(qr[sf2.records:][x][3]) + ", ")
        return {
            "fulfillmentText": "Your " + str(count) + " most recent tasks are: " + recent_tasks,
            "source": "salesforceCRM"
        }

    if intent == "readOpportunities":
        count = int(param.get('number'))
        qr = svc.query("select Id, Name from Opportunity")
        string = str(qr[sf2.size])

        recent_opportunities = ""
        for x in range(0, count):
            if (x == int(string)):
                recent_opportunities += (" and you have no more opportunities")
                break
            if (x == count - 1):
                recent_opportunities += (" and " + str(qr[sf2.records:][x][3]))
            else:
                recent_opportunities += (str(qr[sf2.records:][x][3]) + ", ")
        return {
            "fulfillmentText": "Your " + str(count) + " most recent opportunities are: " + recent_opportunities,
            "source": "salesforceCRM"
        }

    if intent == "taskInfo": #use beatbox API to indentify specific tasks based of given parameters and provide more info about those tasks
        qr = svc.query("select Id, Status, ActivityDate, Subject, Priority From Task")
        if param.get('task') != "":
            for rec in qr[sf2.records:]: #loop that goes thru array of all the task names
                if (str(rec[5]).lower() == param.get('task').lower()):
                    string += "The task " + str(rec[5]) + " is due on " + str(rec[4]) + ", it's status is " + str(
                        rec[3]) + " and it's priority is " + str(rec[6]) + ". "

        if param.get('date') != "":
            for rec in qr[sf2.records:]:
                if (str(rec[4]) == param.get('date')[:10]):
                    string += " The task " + str(rec[5]) + " is due on " + str(rec[4]) + ", it's status is " + str(
                        rec[3]) + " and it's priority is " + str(rec[6]) + ". "
        return {
            "fulfillmentText": string,
            "source": "salesforceCRM"
        }

    if intent == "opportunityInfo":
        qr = svc.query("select Id, Name, StageName, CloseDate, Amount From Opportunity")
        if param.get('name') != "":
            for rec in qr[sf2.records:]:
                if (str(rec[3]).lower() == param.get('name').lower()):
                    string += "The opportunity" + str(rec[3]) + " was closed " + str(rec[5]) + " and is in its " + str(
                        rec[4]) + " stage and is worth " + str(rec[6]) + ". "

        if param.get('stage_name') != "":
            for rec in qr[sf2.records:]:
                if (str(rec[3]).lower() == param.get('stage_name').lower()):
                    string += "The opportunity" + str(rec[3]) + " was closed " + str(rec[5]) + " and is in its " + str(
                        rec[4]) + " stage and is worth " + str(rec[6]) + ". "

        if param.get('date') != "":
            for rec in qr[sf2.records:]:
                if (str(rec[5]) == param.get('date')[:10]):
                    string += "The opportunity" + str(rec[3]) + " was closed " + str(rec[5]) + " and is in its " + str(
                        rec[4]) + " stage and is worth " + str(rec[6]) + ". "

        return {
            "fulfillmentText": string,
            "source": "salesforceCRM"
        }

    if intent == "leadInfo":
        qr = svc.query("select Id, Name, Company, Status, Phone, Title From Lead")
        if param.get('name') != "":
            for rec in qr[sf2.records:]:
                if (str(rec[3]).lower() == param.get('name').lower()):
                    string += "The lead titled" + str(rec[7]) + " under the name " + str(
                        rec[3]) + " and the company " + str(rec[4]) + " has a status of  " + str(
                        rec[5]) + ". You can reach them at " + str(rec[6])[:3] + "-" + str(rec[6])[3:6] + "-" + str(
                        rec[6])[6:10] + ". "

        if param.get('company') != "":
            for rec in qr[sf2.records:]:
                if (str(rec[4]).lower() == param.get('company').lower()):
                    string += "The lead titled" + str(rec[7]) + " under the name " + str(
                        rec[3]) + " and the company " + str(rec[4]) + " has a status of  " + str(
                        rec[5]) + ". You can reach them at " + str(rec[6]) + "-" + str(rec[6])[3:6] + "-" + str(rec[6])[
                                                                                                            6:10] + ". "

        return {
            "fulfillmentText": string,
            "source": "salesforceCRM"
        }

    if intent == "updateContact":
        id = ""
        qr = svc.query("select Id, Name, Phone From Contact")
        if param.get('given-name') != "": #search for contact given a  specific name
            for rec in qr[sf2.records:]:
                if (str(rec[3]).lower() == (param.get('given-name') + " " + param.get('last-name')).lower()):
                    id = str(rec[2]) #retrieve the id with beatbox API
        sf.Contact.update(id, {'Phone': param.get('phone-number')}) #update contact with simple-salesforce API
        return {
            "fulfillmentText": "Your contact's number has been updated!",
            "source": "salesforceCRM"
        }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 500))  # host app on local server (port 500, type 'ngrok http 500' in ngrok
    print("Starting app on port %d" % port)
    app.run(debug=True, port=port, host='0.0.0.0')


