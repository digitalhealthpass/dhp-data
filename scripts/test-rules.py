#!/usr/bin/env python
# coding: utf-8
#
# (c) Copyright Merative US L.P. and others 2020-2022 
#
# SPDX-Licence-Identifier: Apache 2.0
from dis import pretty_flags
from genericpath import exists
from jsonpath import JSONPath
import json, os
from dhp-verify-python-lib.lib.json_logic import jsonLogic
from dhp-verify-python-lib.helper.rule_utils import setup_operations

setup_operations()

pathToRepo = os.path.normpath("./")
configDirectory = "config"
scriptConfigFile = "config.json"
pathToConfigFiles = os.path.join(pathToRepo, configDirectory)

with open(os.path.join(pathToConfigFiles, scriptConfigFile), encoding='utf-8') as jsonFile:  
        globalConfig = json.load(jsonFile)

typeFolders = globalConfig["typeFolders"]
sourceFolder = globalConfig["sourceFolder"]
rulesFolders = globalConfig["rulesFolders"]
verificationConfigurationFolder = globalConfig["verificationConfigurationFolder"]
modelVersionFolders = globalConfig["modelVersionFolders"]

valueSets = {}

pathToSourceFiles = os.path.join(pathToRepo, sourceFolder)
pathToConfigurations = os.path.join(pathToSourceFiles, verificationConfigurationFolder)

type2FilesDict = {}
failedTestsLog = []

for model in modelVersionFolders:
        model = os.path.normpath(model)
        pathToConfigurationsModel = os.path.join(pathToConfigurations, model)

        for objectTypeFolder in typeFolders:
                configurationFiles = []
                for root, dirs, files in os.walk(os.path.join(pathToConfigurationsModel, objectTypeFolder), topdown=True):
                        for fileName in files:
                                if fileName.split(".")[-1].upper() == "JSON":
                                        configurationFiles.append(root + os.path.sep + fileName)

                type2FilesDict[objectTypeFolder] = type2FilesDict.get(objectTypeFolder, []) + configurationFiles

allTestPassed = True

#reading all valuesets into dictionary for later use
for configFile in type2FilesDict["value-sets"]:

    with open(configFile, encoding='utf-8') as jsonFile:
            objectFromFile = json.load(jsonFile)

    objectFromFile["valueList"] = [item["value"] for item in objectFromFile["items"]]

    valueSets[objectFromFile["name"]] = objectFromFile
        

for objectType, configFiles in type2FilesDict.items():

    for configFile in configFiles:

        # TO-DO:
        # 1) check references (correct IDs)
        #     - specification-configurations in verification-configuration
        #     - value-sets in verification-configuration
        #     - classification-rule in specification-configurations
        #     - rules in specification-configurations
        #     - displays in specification-configurations
        #     - trustlists in specification-configurations
        # 2) check value-set references from rule predicates (name based)
        #     - check that a referenced veluset exists
        #     - check that a referenced valueset is included(referenced) in verification-configuration 
        #         (make sure that rule is included in specification-configuration which 
        #          is referenced in verification-conf and it has refs to thos value-sets)
        # 3) classifier rule returns value which is name of specification-configuration
        #        - also make sure all specification-configuration have classifier rule which returns its name ,referenced in classifier-rule property
        # 4) check values from masterdata are used 
        #     - for all credential-category fields of all specification-configuration
        #     - for all credential-spec fields of all specification-configuration
        # 5) check all values in value sets also have description
        #
        # 6) make sure all config-items have all required fields?
        #
        # 7) make sure all config-items are valid JSONS
        #
        # Q: do we need separate trustlist and display for each specification-configuration ?

        with open(configFile, encoding='utf-8') as jsonFile:
                objectFromFile = json.load(jsonFile)

        objectName = objectFromFile["name"]
        objectID = objectFromFile["id"]
        objectVersion = objectFromFile["version"]

        specType = configFile.split(os.path.sep)[-2]

        print("TYPE:", objectType, "SPEC:", specType, "NAME:", objectName)
        print("ID:", objectID, "VERSION:", objectVersion)
    
        #starting with testing of the rules
        if objectType in rulesFolders:

            rulePredicateFile = configFile.replace(".json", ".rule")

            if not(os.path.exists(rulePredicateFile)):
                print("!!!MISSING RULE PREDICATE!!!")
                #allTestPassed = False
            else:
                with open(rulePredicateFile, encoding='utf-8') as jsonFile:
                    rulePredicate = json.load(jsonFile)

                testFile = configFile.replace(".json", ".test")
                
                if not(os.path.exists(testFile)):
                    print("!!!MISSING TEST FILE!!!")
                    #allTestPassed = False
                else:
                    ruleTestResults = []
                    with open(testFile, encoding='utf-8') as jsonFile:
                        ruleTests = json.load(jsonFile)

                    for test in ruleTests:
                        
                        #in case we want to replace hardcoded paramaters with lists from value sets and save the test files this way
                        if False:
                            if "external" in test["data"]: 
                                for param in test["data"]["external"]:
                                    if param != "validationClock":
                                        if set(test["data"]["external"][param]) == set(valueSets[param]["valueList"]):
                                            test["data"]["external"][param] = param

                            with open(testFile, 'w', encoding='utf-8', newline='\n') as jsonFile:
                                json.dump(ruleTests, jsonFile, indent='\t')

                        if "external" in test["data"]:
                            for param in test["data"]["external"]:
                                if param != "validationClock":
                                    if type(test["data"]["external"][param]) == str:
                                        if param in valueSets:
                                            test["data"]["external"][param] = valueSets[param]["valueList"]
                                        else:
                                            test["data"]["external"][param] = []

                        testResult = "pass" if jsonLogic(rulePredicate, test["data"]) == test["expectedResult"] else "fail"
                        ruleTestResults.append(testResult)

                        if testResult == "fail":
                            True
                            #print("RULE:", rulePredicate)
                            #print("DATA:", test["data"])
                            #print("Actual Result:", jsonLogic(rulePredicate, test["data"]))
                            #print("Expected Result:", test["expectedResult"])
                            #print("QUICKTEST:", jsonLogic({'var': 'payload.v.0'}, test["data"]))

                    print("-"*50)  
                    print("Test Result:", "FAIL" if "fail" in ruleTestResults else "PASS", "( All test results:", ruleTestResults, ")")
                    print("-"*50)
                    if "fail" in ruleTestResults:
                        allTestPassed = False
                        failedTestsLog.append(["TYPE: " + objectType + " SPEC: " + specType + " NAME: " + objectName,
                        "ID: " + objectID + " VERSION: "+ objectVersion,
                        "All test results: " +  str(ruleTestResults)])
        print("")

print("")
print("-"*50)
if not allTestPassed:
    print("Failed Rules Details:")
    for failedTestsRec in failedTestsLog:
        for line in failedTestsRec:
            print(line)
        print("-"*50)
    print("-"*50)
print("allTestPassed:", allTestPassed)

#for vs in valueSets.values():
#  print(vs["id"], vs["name"], vs["valueList"])
