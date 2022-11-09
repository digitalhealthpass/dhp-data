#!/usr/bin/env python
# coding: utf-8
#
# (c) Copyright Merative US L.P. and others 2020-2022 
#
# SPDX-Licence-Identifier: Apache 2.0
import json
import os
import sys
import requests

from datetime import datetime
import pytz

from dhp-verify-python-lib.lib.json_logic import jsonLogic
from dhp-verify-python-lib.helper.rule_utils import setup_operations

setup_operations()

pathToDataRepo = "."
configDirectory = "config"
scriptConfigFile = "config.json"
pathToConfigFiles = os.path.join(pathToDataRepo, configDirectory)

with open(os.path.join(pathToConfigFiles, scriptConfigFile), encoding='utf-8') as jsonFile:
    globalConfig = json.load(jsonFile)

objectID = sys.argv[1]
host = sys.argv[2]
user = sys.argv[3]
passwd = sys.argv[4]
pathToSampleData = os.path.normpath(os.path.join(sys.argv[5] + objectID))

if not os.path.exists(pathToSampleData):
    print("Path does not exist:")
    print(pathToSampleData)
else:

    hpassBaseURL = globalConfig["httpsProtocol"] + \
        host + globalConfig["healtpassAPI"]
    verifyConfigBaseURL = globalConfig["httpsProtocol"] + \
        host + globalConfig["verifyierConfigAPI"]


    session = requests.Session()
    bodyJSON = {
        "email": user,
        "password": passwd
    }

    headers = {
        'Content-Type': 'application/json'
    }

    loginURL = hpassBaseURL + "/users/login"
    loginResponse = session.post(loginURL, json=bodyJSON, headers=headers)

    if loginResponse.status_code == 200:
        responseObject = json.loads(loginResponse.text)
        accessTokenAdmin = responseObject["access_token"]
        print("Successfull logged in.")
    else:
        print("Login failed")
        print("Status code:", loginResponse.status_code)
        print("Response text:", loginResponse.text)

    cnt = 0

    headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' +  accessTokenAdmin
    }

    apiCallURL = verifyConfigBaseURL + "/verifier-configurations/" + objectID + "/1.0.0/content"
    apiCallResponse = session.get(apiCallURL, headers=headers)
    
    i=1
    failedTests = 0
    verifierConfig = {}

    postResponseCode = apiCallResponse.status_code
    
    if not postResponseCode == 200:
        print("ERROR: Getting expanded verifier config failed for v1.0.0 ID='" + objectID + "':", postResponseCode, apiCallResponse.text)
        if os.path.exists("./scripts/verifier-config-expanded-"+ objectID +".json"):
            print("")
            print("USING CACHED VERSION (might not be the latest):")
            print("FROM FILE:", "./scripts/verifier-config-expanded-"+ objectID +".json")
            with open("./scripts/verifier-config-expanded-"+ objectID +".json", encoding='utf-8') as jsonFile:  
                verifierConfig = json.load(jsonFile)
    else:
        print("SUCCESSFULLY RETRIEVED config FROM '" + host + "' for v1.0.0 ID='" + objectID + "'.")
        verifierConfig = json.loads(apiCallResponse.text)

        with open("./scripts/verifier-config-expanded-"+ objectID +".json", 'w', encoding='utf-8', newline='\n') as jsonFile:
            json.dump(json.loads(apiCallResponse.text), jsonFile, indent=3)

    specTypeStats = {}

    if verifierConfig != {}:
        for root, dirs, files in os.walk(pathToSampleData, topdown=True):
            for fileName in sorted(files):
                if fileName.split(".")[-1].upper() == "JSON":
                    print(i, root + os.path.sep + fileName)
                    i=i+1
                    with open(root + os.path.sep + fileName, encoding='utf-8') as jsonFile:
                        sampleData = json.load(jsonFile)

                    with open(root + os.path.sep + fileName, 'w', encoding='utf-8', newline='\n') as jsonFile:
                        json.dump(sampleData, jsonFile, indent=3)

                    testData = {}
                    testData["payload"] = sampleData
                    # if "dcc" in sampleData:
                    #     #print("DCC")
                    #     testData["payload"] = sampleData["dcc"]
                    #     testData["payload"]["expirationDate"] = sampleData.get("expirationDate", "")
                    # elif "type" in sampleData:
                    #     if "GoodHealthPass" in sampleData["type"]  or "DigitalHealthPass" in sampleData["type"]:
                    #         #print("GHP/DHP")
                    #         testData["payload"] = sampleData
                    #         testData["payload"]["credentialSubject"] = sampleData["data"]
                    #     elif "VerifiableCredential" in sampleData["type"]:
                    #         #print("VC")
                    #         testData["payload"] = sampleData
                    #         testData["payload"]["credentialSubject"] = sampleData["data"]        
                    #     elif "https://smarthealth.cards#health-card" in sampleData["type"]:
                    #         #print("SHC")
                    #         testData["payload"] = {}
                    #         testData["payload"]["vc"] = sampleData
                    #         testData["payload"]["vc"]["credentialSubject"] = sampleData["data"]
                    #         testData["payload"]["expirationDate"] = sampleData.get("expirationDate", "")

                    #print(json.dumps(testData, indent=3))

                    classifierResults = []
                    for specConfig in verifierConfig["payload"]["specificationConfigurations"]:
                        rulePredicate = json.loads(specConfig["classifierRule"]["predicate"])
                        #print(rulePredicate)
                        classifierResults.append(jsonLogic(rulePredicate, testData))
                        #if classifierResult != False:
                        #    break
                    classifierResult = [cr for cr in classifierResults if cr]

                    if len(classifierResult) == 1:
                        classifierResult = classifierResult[0]

                        if classifierResult not in specTypeStats:
                            specTypeStats[classifierResult] = [fileName]
                        else:
                            specTypeStats[classifierResult].append(fileName)

                        print("-"*50)
                        print("classifierResult:", classifierResult)
                        print("-"*50)

                        disabledRules = [dr["specID"] + dr["id"] for dr in verifierConfig["payload"]["disabledRules"]]

                        testData["external"] = {vs["name"]: [item["value"] for item in vs["items"]] for vs in verifierConfig["payload"]["valueSets"]}
                        testData["external"]["validationClock"] = datetime.now().utcnow().now(pytz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                        #print("validationClock:", testData["external"]["validationClock"])

                        if classifierResult:
                            for specConfig in verifierConfig["payload"]["specificationConfigurations"]:
                                if specConfig["name"] == classifierResult:
                                    specRulesResult = True
                                    ruleResults = []
                                    specRules = [rule for rule in specConfig["rules"] if specConfig["id"] + rule["id"] not in disabledRules]
                                    #print([rule["name"] for rule in specRules])
                                    for specRule in specRules:
                                        rulePredicate = json.loads(specRule["predicate"])
                                        #print(rulePredicate)
                                        ruleResult = jsonLogic(rulePredicate, testData)
                                        specRulesResult = specRulesResult and ruleResult
                                        ruleResults.append(ruleResult)
                                        print("[" + specRule["name"] + "]" + ":", ruleResult)

                            specRulesResultExpected = False if "NotVerified" in root.split(os.path.sep) else True
                            #print(specRulesResult, ":", ruleResults)
                            print("")
                            print("OVERALL:")
                            print("Actual result:", specRulesResult)
                            print("Expected result:", specRulesResultExpected)
                            if specRulesResult != specRulesResultExpected:
                                failedTests += 1
                                #print("FAILED", "Expected:", specRulesResultExpected)
                                print("Test: FAILED")
                            else:
                                print("Test: PASSED")

                            print("")
                            print("")
                            print("-"*200)

print("failedTests", failedTests)
#print("")
#print("CLASSIFIER STATS:")
#print(json.dumps(specTypeStats, indent=3))