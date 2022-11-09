#!/usr/bin/env python
# coding: utf-8
#
# (c) Copyright Merative US L.P. and others 2020-2022 
#
# SPDX-Licence-Identifier: Apache 2.0

import requests, json, os, difflib, sys

loggingLevel = ["info", "warning", "error"]
def info(*args):
    if args[0] in loggingLevel :
        for argItem in args[1:]:
            print(argItem, end =" ")
        print("")

httpsProtocol = "https://"
healtpassAPI = "/api/v1/hpass"
verifyierConfigAPI = "/api/v1/verifier/config/api/v1"

typeFolders = [
    "master-data",
    "displays",
    "trust-lists",
    "value-sets",
    "classifier-rules",
    "rules",
    "rule-sets",
    "specification-configurations",
    "verifier-configurations"
    ]

rulesFolders = ["rules", "classifier-rules"]

requiretArgs = set(["input", "host", "user", "password"])
argDict = {av.split("=")[0]: (av.split("=")[1] if len(av.split("=")) > 1 else "") for index, av in enumerate(list(sys.argv)) if index > 0}
print(argDict)
if len(list( requiretArgs & set(argDict.keys()))) != len(requiretArgs):
    print("Some required arguments are missing:")
    print(list(requiretArgs - set(argDict.keys())))
    print("Example use:")
    print("./scripts/verify-config.py \\")
    print("input=./source/verification-configuration/model-v2022-02 \\")
    print("host=sandbox.digitalhealthpass.com \\")
    print("user=myUserName \\")
    print("password=myUserPwd")
    raise SystemExit

host = argDict["host"] #sys.argv[2]
info("info", "Execution enviroment host:", host)
info("info", "")

hpassBaseURL = httpsProtocol + host + healtpassAPI
info("verbose", "hpassBaseURL:", hpassBaseURL)
verifyConfigBaseURL = httpsProtocol + host + verifyierConfigAPI
info("verbose", "verifyConfigBaseURL:", verifyConfigBaseURL)
info("verbose", "")

adminuser = argDict["user"] #sys.argv[3]
adminpass = argDict["password"] #sys.argv[4]

verificationConfigurationFolder = argDict["input"] #sys.argv[1]
info("verbose", "verificationConfigurationFolder:", verificationConfigurationFolder)
info("verbose", "")

runDeployment = not argDict.get("deploy", "false").lower() == "false"

# ## Login using username and password
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
    info("verbose", "Successfull login, token:")
    info("verbose", accessTokenAdmin)
else:
    info("error", "Login failed")
    info("error", "Status code:", loginResponse.status_code)
    info("error", "Response text:", loginResponse.text)
    raise SystemExit

type2FilesDict = {}

stats = {
    "readyToDeploy": 0,
    "alreadyDeployed": 0,
    "alreadyDeployedMatch": 0,
    "alreadyDeployedDifferent": 0,
    "higherVersionExists": 0,
    "otherError": 0
}


for objectTypeFolder in typeFolders:
    configurationFiles = []
    for root, dirs, files in os.walk(os.path.join(verificationConfigurationFolder, objectTypeFolder), topdown=True):
        for fileName in files:
            if fileName.split(".")[-1].upper() == "JSON":
                configurationFiles.append(root + os.path.sep + fileName)
    if len(configurationFiles) > 0:
        type2FilesDict[objectTypeFolder] = type2FilesDict.get(objectTypeFolder, []) + configurationFiles

info("info", "Files:", len([item for sublist in list(type2FilesDict.values()) for item in sublist]))
info("info", "")

# ### Get Verification Configurations
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' +  accessTokenAdmin
}

i = 1

safetToDeploy = True
objectsToDeploy = []

for objectType, configFiles in type2FilesDict.items():

    # getting all objects of all version for a given type in objectType
    apiCallURL = verifyConfigBaseURL + "/" + objectType
    apiCallResponse = session.get(apiCallURL, headers=headers)

    if apiCallResponse.status_code != 200:
        info("verbose", apiCallResponse.status_code, apiCallResponse.text)
        continue

    configItems = json.loads(apiCallResponse.text)

    configItemsVersions = {}
    for ci in configItems["payload"]:
        configItemsVersions[ci["id"]] = configItemsVersions.get(ci["id"], []) + [ci["version"]]


    for configFile in configFiles:

        with open(configFile, encoding='utf-8') as jsonFile:
            objectFromFile = json.load(jsonFile)

        objectID = objectFromFile["id"]
        objectVersion = objectFromFile["version"]

        #expand predicate from other file if predicate contains file name ending with ".rule" (when running it using source files and not output of build)
        if objectType in rulesFolders:
            if objectFromFile["predicate"][-5:] == ".rule":
                rulePredicateFile = configFile.replace(".json", ".rule")
                with open(rulePredicateFile, encoding='utf-8') as jsonFile:
                    objectFromFile["predicate"] = json.dumps(json.load(jsonFile))
            

        ## Check whether there is not a higher version already deployed 
        higherVersionExists = False

        if objectID in configItemsVersions:
            latestVersion = sorted(configItemsVersions[objectID], key=lambda version: list(map(int, version.split('.'))))[-1]
            
            if list(map(int, latestVersion.split('.'))) > list(map(int, objectVersion.split('.'))):
                info("warning", "TYPE:", objectType, "FILE:", os.sep.join(configFile.split(os.sep)[-3:]), "ID:", objectID, "VERSION:", objectVersion)
                info("warning", "Latest version in the target environment:", objectID, latestVersion)
                info("warning", "!!! THE VERSION FROM FILE IS SMALLER THAN THE LATEST VERSION IN TARGET ENIRONMENT!!!")

                if objectID in configItemsVersions:
                    info("warning", "!!! ALL VERSIONS", configItemsVersions[objectID])
                info("warning", "")
                
                higherVersionExists = True
                safetToDeploy = False
                stats["higherVersionExists"] += 1

        #if higher version does not exist: either version number is the same or smaller or objectID not there eat all.
        if not higherVersionExists:

            #looking for existing item already with same objectID and version number
            apiCallURL = verifyConfigBaseURL + "/" + objectType + "/" + objectID + "/" + objectVersion
            info("verbose", i)
            i = i + 1
            info("verbose", "URL:" + apiCallURL)
            apiCallResponse = session.get(apiCallURL, headers=headers)
            
            #existing objectID and version found
            if apiCallResponse.status_code == 200:

                stats["alreadyDeployed"] += 1

                responseObject = json.loads(apiCallResponse.text)
                objectDeployed = responseObject.get("payload")

                #removing properties that are only added in DB by the API
                del objectDeployed["created_at"]
                del objectDeployed["created_by"]
                del objectDeployed["updated_at"]

                #expanding the predicate (it is still a valid json) for a better compare
                if objectType in rulesFolders:
                    if "predicate" in objectFromFile: 
                        objectFromFile["predicate"] = json.loads(objectFromFile["predicate"])
                    if "predicate" in objectDeployed: 
                        objectDeployed["predicate"] = json.loads(objectDeployed["predicate"])

                ## now compare the config object definition to establish whether there are updates and if there are inform that a version number needs to be updated/increased.  
                # if there are no updates, continue, there is no reason to re-deploy a config object which was not updated
                if json.dumps(objectDeployed, sort_keys=True) != json.dumps(objectFromFile, sort_keys=True):
                    info("warning", "TYPE:", objectType, "FILE:", os.sep.join(configFile.split(os.sep)[-3:]), "ID:", objectID, "VERSION:", objectVersion)
                    info("warning", "Schema with this ID and version number is already in target environment.")
                    info("warning", "!!! THE DEPLOYED CONFIG OBJECT DOES NOT MATCH THE CONFIG OBJECT FROM FILE. If the updates are genuine a version number needs to be updated for successfull deployment.")
                    
                    info("warning", "Listing the differences:")
                    for diff in difflib.unified_diff(json.dumps(objectDeployed, sort_keys=True, indent=3).split("\n"), json.dumps(objectFromFile, sort_keys=True, indent=3).split("\n"), n=5):
                        #save the different to a file instead of printing to console?
                        info("warning", diff)

                    safetToDeploy = False
                    stats["alreadyDeployedDifferent"] += 1
                else:
                    info("verbose", "TYPE:", objectType, "FILE:", os.sep.join(configFile.split(os.sep)[-3:]), "ID:", objectID, "VERSION:", objectVersion)
                    info("verbose", "Schema with this ID and version number is already in target environment.")
                    info("verbose", "The deployed config object matches the config object in file. Nothing to update.")
                    info("verbose", "")
                    stats["alreadyDeployedMatch"] += 1
            else:
                if apiCallResponse.status_code == 404:
                    info("info", "TYPE:", objectType, "FILE:", os.sep.join(configFile.split(os.sep)[-3:]), "ID:", objectID, "VERSION:", objectVersion)
                    info("info", "Config object with this ID and version number was not found in target environment and can be safely created there.")
                    if objectID in configItemsVersions:
                        info("info", "Other already deployed versions:", configItemsVersions[objectID])
                    info("info", "")  
                    stats["readyToDeploy"] += 1
                    objectsToDeploy.append(objectID)
                else:
                    info("error", "TYPE:", objectType, "FILE:", os.sep.join(configFile.split(os.sep)[-3:]), "ID:", objectID, "VERSION:", objectVersion)
                    info("error", apiCallResponse.status_code)
                    info("error", apiCallResponse.text)
                    info("error", "")
                    stats["otherError"] += 1
                    safetToDeploy = False

    
info("info", "Stats:")
info("info", json.dumps(stats, indent=3))
info("info", "")

if stats["readyToDeploy"] == 0 and safetToDeploy:
    info("info", "Nothing to deploy.")

if stats["readyToDeploy"] > 0 and safetToDeploy:
    info("info", "Safe to deploy", stats["readyToDeploy"], "objects.")
    
    if not runDeployment:
        info("info", "Run the script again with additional 'deploy' parameter for deployment.")

if not safetToDeploy:
    info("info", "Issues found that require fixing:")
    if stats["alreadyDeployedDifferent"] > 0:
        info("info", " - alreadyDeployedDifferent:", stats["alreadyDeployedDifferent"])
    if stats["higherVersionExists"] > 0:
        info("info", " - higherVersionExists:", stats["higherVersionExists"])
    if stats["otherError"] > 0:
        info("info", " - otherError:", stats["otherError"])

    sys.exit(1)

if runDeployment and safetToDeploy and stats["readyToDeploy"] > 0:
    info("info", "")
    info("info", "Starting deployment of object which are not in target environment")
    info("info", "Number of config objects to deploy:", len(objectsToDeploy))
    info("info", "")

    successfullyDeployed = True

    for objectType, configFiles in type2FilesDict.items():
        for configFile in configFiles:

            with open(configFile, encoding='utf-8') as jsonFile:
                objectFromFile = json.load(jsonFile)

            objectID = objectFromFile["id"]
            objectVersion = objectFromFile["version"]

            if objectID in objectsToDeploy:

                info("info", "TYPE:", objectType, "FILE:", os.sep.join(configFile.split(os.sep)[-3:]), "ID:", objectID, "VERSION:", objectVersion)

                #expand predicate from other file if predicate contains file name ending with ".rule" (when running it using source files and not output of build)
                if objectType in rulesFolders:
                    if objectFromFile["predicate"][-5:] == ".rule":
                        rulePredicateFile = configFile.replace(".json", ".rule")
                        with open(rulePredicateFile, encoding='utf-8') as jsonFile:
                            objectFromFile["predicate"] = json.dumps(json.load(jsonFile))

                bodyString = (json.dumps(objectFromFile))

                apiCallURL = verifyConfigBaseURL + "/" + objectType
                apiCallResponse = session.post(apiCallURL, data=bodyString, headers=headers)

                postResponseCode = apiCallResponse.status_code
                if postResponseCode == 201:
                    info("info", "Created successfully.", postResponseCode)   
                    info("info", "") 
                else:
                    info("error", "Creating failed:", postResponseCode, apiCallResponse.text)
                    info("error", "")
                    successfullyDeployed = False

    if successfullyDeployed:
        info("info", "")
        info("info", "All config items created successfully.")
    else:
        info("info", "")
        info("info", "Some config items were not created successfully.")
        sys.exit(1)