#!/usr/bin/env python
# coding: utf-8
#
# (c) Copyright Merative US L.P. and others 2020-2022 
#
# SPDX-Licence-Identifier: Apache 2.0
import requests, json, os, difflib, sys

#loggingLevel = ["verbose", "info", "warning", "error"]
loggingLevel = ["info", "warning", "error"]


def info(*args):
    if args[0] in loggingLevel:
        for argItem in args[1:]:
            print(argItem, end=" ")
        print("")


httpsProtocol = "https://"
healtpassAPI = "/api/v1/hpass"
verifyierConfigAPI = "/api/v1/verifier/config/api/v1"
issuerIDHeader = "x-hpass-issuer-id"

requiretArgs = set(["input", "host", "user", "password", "issuer", "issuerDID"])
argDict = {av.split("=")[0]: (av.split("=")[1] if len(av.split("=")) > 1 else "") for index, av in enumerate(list(sys.argv)) if index > 0}

print(argDict)
if len(list(requiretArgs & set(argDict.keys()))) != len(requiretArgs):
    print("Some required arguments are missing:")
    print(list(requiretArgs - set(argDict.keys())))
    print("Example use:")
    print("./scripts/credential-schema.py \\")
    print("input=./source/schemas \\")
    print("host=sandbox.digitalhealthpass.com \\")
    print("user=myUserName \\")
    print("password=myUserPwd \\")
    print("issuer=hpass.issuer \\")
    print("issuerDID=did:hpass:59cd606341eb4a4a6c1a25d94a5f842ecf83ccd441dbda8abcd9274c9acd9334:67cba75b1719b5efba1addd32602f827fd378f2654288b1a4e381f8dddf40af3")
    raise SystemExit

pathToSchemas = argDict["input"]
info("verbose", "pathToSchemas:", pathToSchemas)
info("verbose", "")

host = argDict["host"] 
info("info", "Execution enviroment host:", host)
info("info", "")

hpassBaseURL = httpsProtocol + host + healtpassAPI
info("verbose", "hpassBaseURL:", hpassBaseURL)
verifyConfigBaseURL = httpsProtocol + host + verifyierConfigAPI
info("verbose", "verifyConfigBaseURL:", verifyConfigBaseURL)
info("verbose", "")

adminuser = argDict["user"]
adminpass = argDict["password"]

info("info", "issuerIDHeader:", issuerIDHeader)
info("info", )

issuerID = argDict["issuer"]
info("info", "issuerID:", issuerID)

issuerDID = argDict["issuerDID"]
info("info", "issuerDID:", issuerDID)

runDeployment = not argDict.get("deploy", "false").lower() == "false"

####################################
# Login using username and password
####################################

logged = False

session = requests.Session()
bodyJSON = {
    "email": adminuser,
    "password": adminpass
}

headers = {
    'Content-Type': 'application/json'
}

loginURL = hpassBaseURL + "/users/login"
loginResponse = session.post(loginURL, json=bodyJSON, headers=headers)

if loginResponse.status_code == 200:
    responseObject = json.loads(loginResponse.text)
    accessTokenAdmin = responseObject["access_token"]
    print("Successfull login.")
    logged = True
else:
    info("error", "Login failed")
    info("error", "Status code:", loginResponse.status_code)
    info("error", "Response text:", loginResponse.text)


####################################
# Get Schemas
####################################

schemaFiles = []
for root, dirs, files in os.walk(pathToSchemas, topdown=True):
    for fileName in files:
        if fileName.split(".")[-1].upper() == "JSON":
            #print(root + os.path.sep + fileName)
            schemaFiles.append(root + os.path.sep + fileName)

for schemaFile in schemaFiles:

    print("")

    with open(os.path.join(schemaFile), encoding='utf-8') as jsonFile:
        schemaFromFile = json.load(jsonFile)

    schemaID = schemaFromFile["id"]
    schemaVersion = schemaFromFile["version"]

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + accessTokenAdmin,
        issuerIDHeader: issuerID
    }

    apiCallURL = hpassBaseURL + "/schemas?author=" + issuerDID + "&id=" + schemaID + "&version=" + schemaVersion
    apiCallResponse = session.get(apiCallURL, headers=headers)

    if apiCallResponse.status_code == 200:
        responseObject = json.loads(apiCallResponse.text)

        if len(responseObject.get("payload", [])) == 0:
            info("info", "FILE:", os.sep.join(schemaFile.split(os.sep)[-2:]), "ID:", schemaID, "VERSION:", schemaVersion)
            info("info", "Schema with this ID and version number was not found in target environment and can be safely created there.")
        else:

            schemaDeployed = responseObject.get("payload")[0]["schema"]
            schamaFromSource = schemaFromFile["schema"]

            # now compare the schema definition to establish whether there are upodates and if there are inform that a version number needs to be updated/increased.
            # if there are no updates, continue, there is no reason to re-deploy a schema which was not updated
            if json.dumps(schemaDeployed, sort_keys=True) != json.dumps(schamaFromSource, sort_keys=True):
                info("error", "FILE:", os.sep.join(schemaFile.split(os.sep)[-2:]), "ID:", schemaID, "VERSION:", schemaVersion)
                info("error", "Schema with this ID and version number is already in target environment.")
                info("error", "DID:", responseObject.get("payload")[0]["id"])

                info("error", "The deployed schema does not match the source schema. If the updates are genuine a version number needs to be updated for successfull deployment.")
                info("error", "If the updates are irrelevant, the schema in GIT file should be replaced with the one from the target environment.")

                info("error", "Listing the differences:")
                for diff in difflib.unified_diff(json.dumps(schemaDeployed, sort_keys=True, indent=3).split("\n"), json.dumps(schamaFromSource, sort_keys=True, indent=3).split("\n")):
                    info("info", diff)
            else:
                info("info", "FILE:", os.sep.join(schemaFile.split(os.sep)[-2:]), "ID:", schemaID, "VERSION:", schemaVersion)
                info("info", "Schema with this ID and version number is already in target environment.")
                info("info", "DID:", responseObject.get("payload")[0]["id"])
                info("info", "The deployed schema matches the source schema. Nothing to update.")
    else:
        info("error", "FILE:", os.sep.join(schemaFile.split(os.sep)[-2:]), "ID:", schemaID, "VERSION:", schemaVersion)
        info("error", apiCallResponse.status_code)
        info("error", apiCallResponse.text)

    # Check there is not a higher version already in deployed which has not been put into source control to github repo
    # Using the same endpoint just without the version number and get all versions and assess if number of any if the versions is higher than what we have in github
    apiCallURL = hpassBaseURL + "/schemas?author=" + issuerDID + "&id=" + schemaID
    apiCallResponse = session.get(apiCallURL, headers=headers)

    if apiCallResponse.status_code == 200:
        responseObject = json.loads(apiCallResponse.text)
    else:
        responseObject = {"payload": []}

    if len(responseObject["payload"]) > 0:
        allVersionList = [pl["modelVersion"] for pl in responseObject.get("payload") if ";id=" + schemaID + ";" in pl["id"]]
        info("info", "ALL version of schemaID:", schemaID, sorted(allVersionList))
        if sorted(allVersionList)[-1] == schemaVersion:
            info("info", "Schema version in source Github repo does match the latest version in target environment.")
        else:
            if schemaVersion in allVersionList:
                info("error", "FILE:", os.sep.join(schemaFile.split(os.sep)[-2:]), "ID:", schemaID, "VERSION:", schemaVersion)
                info("error", "!!! THE VERSION IN SOURCE GITHUB REPO IS IN TARGET ENVIRONMENT ALREADY, BUT IS NOT THE LATEST VERSION !!!")
            if sorted(allVersionList)[-1] > schemaVersion:
                info("error", "FILE:", os.sep.join(schemaFile.split(os.sep)[-2:]), "ID:", schemaID, "VERSION:", schemaVersion)
                info("error", "!!! THE VERSION IN SOURCE GITHUB REPO IS NOT YET IN TARGET ENVIRONMENT, BUT THE VERSION FROM GITHUB IS SMALLER THAN THE LATEST DEPLOYED VERSION  !!!")
                info("error", "!!! GITHUB VERSION:", schemaVersion, "LATEST DEPLOYED VERSION:", sorted(allVersionList)[-1])
    else:
        info("error", "FILE:", os.sep.join(schemaFile.split(os.sep)[-2:]), "ID:", schemaID, "VERSION:", schemaVersion)
        info("error", apiCallResponse.status_code)
        info("error", apiCallResponse.text)

if runDeployment:

    for schemaFile in schemaFiles:

        with open(schemaFile, encoding='utf-8') as jsonFile:
            schemaFromFile = json.load(jsonFile)

        schemaID = schemaFromFile["id"]
        schemaVersion = schemaFromFile["version"]

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + accessTokenAdmin,
            issuerIDHeader: issuerID
        }

        apiCallURL = hpassBaseURL + "/schemas"
        apiCallResponse = session.post(apiCallURL, json=schemaFromFile, headers=headers)

        if apiCallResponse.status_code == 201:
            info("info", "FILE:", os.sep.join(schemaFile.split(os.sep)[-2:]), "ID:", schemaID, "VERSION:", schemaVersion)
            info("info", "Schema successfully created.")
        else:
            info("info", "FILE:", os.sep.join(schemaFile.split(os.sep)[-2:]), "ID:", schemaID, "VERSION:", schemaVersion)
            info("info", "ERROR: Schema could not be created.")