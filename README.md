# Digital Health Pass data

The repository contains credential schemas, credential verification configurations with verifier rules, and other data related to configuration as well as test data templates and test scripts for automation of DHP testing.

The files are organized in the following sections in this repository:
 - **scrips** - contains the python scripts used for deployment and verification of credential schemas, verification configurations (with rules) and generation of test data
 - source
    - **schemas** - contains the JSON files with definotions of credential schemas
    - **verification-configuration** - contains the credential verification configurations including verifier rule definitions in JSON logic format
    - **verification-test** - contains the templates for test credential generation and the expected test results of these generated credentials when verified with use of the verification configurations and their rules 

The following scrips are included in this repository:
 - [**credential-schema.py**](scripts/credential-schema.readme.md) - script for deployment of credential schemas and verification of their deployment (with a compare)
 - [**verify-config.py**](scripts/verify-config.readme.md) - script for deployment of verifier configurations and verification of their deployment (with a compare)
 - **test-rules.py** - script for "unit" testing of the individual verifier rules, the test data and expected results of the tests are defined in JSON files with "test" extension - for each "rule" file there is a rorresponding "test" file defined in the source folder; the script is using the DHP python SDK with json logic 
 - [**credential-generator.py**](scripts/credential-generator.readme.md) - Creating test credentials (ground truth) for testing of verifier configuration rules
 - **test-specs.py** - script for testing of the verification configurations with the credentials generated using credential-generator.py ; the script is using the DHP python SDK with json logic 
