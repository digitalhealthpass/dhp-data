## Script for deployment of verifier configurations and for their deployment verification
**verify-config.py**   
The script reads the items of the verifier configurations from JSON file and verifies them against already deployed configurations in the target environment and deployes them (with the use of "deploy" parameter) if no issues are found. The following is checked when comparing content from JSON file with already deployed configurations:
  1. ID of verification configuration item does not exist in target environment - this allows the deployment
  2. ID of verification configuration item exists in target environment and the version number from JSON file is bigger than the latest version of the deployed item - this allows the deployment
  3. ID of verification configuration item exists in target environment and the version number from JSON file is smaller than the latest version of the deployed item - this **does not** allow the deployment, the number of version to deploy must be increased, or any invalid items removed from target devironment
  4. ID of verification configuration item exists in target environment and the version number from JSON file is the same as the latest version of the deployed item and content matches the content from JSON file - this allows the deployment - existing matching items are skipped
  5. ID of verification configuration item exists in target environment and the version number from JSON file is the same as the latest version of the deployed item and content **does not** match the content from JSON file - this **does not** allow the deployment, either there have been changes done directly in the envrionment or with the updates in the JSON files, the version was not increased  
  
  
Parameters: 
 - **input** - path to folder with verifier configuration items in json files
 - **host** - host name of the deployment target (or deployment verification)
 - **user** - user name
 - **password** - password for given username
 - deploy - optional parameter, deploys the verifier configuration items only if the if verification in target env does not report issues 
 
Example parameters:
```
./scripts/verify-config.py \
        input=./source/verification-configuration/model-v2022-02 \
        host=sandbox.digitalhealthpass.com \
        user=tester@digitalhealthpass.com \
        password=tester \
        deploy
```