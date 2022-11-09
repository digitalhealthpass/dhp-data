## Script for deployment of credential schemas and for their deployment verification
**credential-schema.py**   
The script reads the credential schema definitions from JSON file and compares them with schemas already deployed in the target environment. The script can be used to deploy the schemas with the use of "deploy" parameter, if no issues are found. The following is checked when comparing schema from JSON file with already deployed schema:
  1. ID and version of schema does not exist in target environment - this allows the deployment
  2. ID and version of schema exists in target environment - this does not allow the deployment, differences are displayed, the schema version needs to be increased to be able to deploy successfully
  3. ID of schema exists in target environment and there are other version of the schema already deployed, the version numbers are displayed. This does not prevent the deployment, it is informational only, but ideally the number of newer schema version should be higher then already deployed versions of the schema.  
  
Parameters: 
 - **input** - path to folder with schemas in json files
 - **host** - host name of the deployment target (or deployment verification)
 - **user** - user name
 - **password** - password for given username
 - **issuer** - username of the issuer
 - **issuerDID** - DID of the issuer
 - deploy - optional parameter, deploys the schemas in target environment 
 
Example parameters:
```
./scripts/credential-schema.py \
        input=./source/schemas \
        host=sandbox.digitalhealthpass.com \
        user=tester@digitalhealthpass.com \
        password=tester \
        issuer=hpass.issuer \
        issuerDID=did:hpass:59cd606341eb4a4a6c1a25d94a5f842ecf83ccd441dbda8abcd9274c9acd9334:67cba75b1719b5efba1addd32602f827fd378f2654288b1a4e381f8dddf40af3 \
        deploy
```