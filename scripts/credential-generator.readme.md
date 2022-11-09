# Generating test credentials (ground truth)

1. Collection of test credentials - Ground truth - needs to be generated for each verifier configuration, as each configuration will cause the verifier to behave differently and therefore will have different Verified (test passed) and NotVerified (test failed) statuses.

2. The ground truth refers to a set of JSON documents that contain the payloads that will be passed into the Issue API to generate the credential. It contains variables that get populated during the generation process. It is critical that you correctly use these variables.

3. When creating a new configuration, you can copy an existing configuration file under source/verification-test/

4. The credentials template file naming has a specific syntax that you should follow:

	type.subtype--extra-info-about-the-payload.json
	For example; ghp.vaccination--complete-expired.json

5. The files in the verification-test folder are prefixed by credential specification: DHP, GHP, VC, SHC, DCC. 

	DHP = a JSON-LD verifiable credential with "DigitalHealtHPass" in the type array
	
	GHP = a JSON-LD verifiable credential with "GoodHealthPass" in the type array
	
	VC = a JSON-LD verifiable credential without any specific type value; so it only has the "VerifiableCredential" type value
	
	* Note: If a GHP or DHP does not have a category (a sub-type in the type array) that the rules engine recognizes, such as "Vaccination", "Test", "Pass", ...), then the verifier reclassifies the credential as a basic VC, and falls back to the VC configuration (which is only an expiration check rule and displays ALL fields in the credential, since VCs require manual inspection)
	
	SHC = a JWT verifiable credential with "https://smarthealth.cards#health-card" in the type array. 
	
	* There is no fallback for SHCs, so they also need to have a sub-type, currently either "https://smarthealth.cards#immunization" (vaccination rules) or "https://smarthealth.cards#laboratory" (test rules)
	
	DCC = a Digital Covid Certification

## Execution of the text credential generation script
**credential-generator.py** 

Variables defined inside the script:
 - hpass_path_api = "/api/v1/hpass"
 - user_login_path = hpass_path_api + "/users/login"
 - header_issuer
 - api_paths_qr
 - api_paths_json
 - valid_specs
 - save_generated_credential_json
 - add_expiration_date_to_payload_for_dcc_shc

Parameters: 
 - **-i** - path to input folder with test credential templates in json files
 - **-o** - path to output folder into which the generated credentials are saved
 - **-c** - path to folder with JSON files defining the expected test results of each generated test credential verification for given verification configuration - one file per each verification configuration (file name needs to match the ID of the configuration) 
 - **-l** - path to log folder
 - **--host** - host name of the server with issuer service
 - **--login** - user name
 - **--password** - password for given username
 - **-s** - comma separated list of credential types to generate, e.g.: DHP, SHC,VC
 - **--did** - DID of the issuer
 
Example parameters:
```
./scripts/credential-generator.py \
        -i ./source/verification-test/credential-templates \
        -o ./generated-credentials \
        -c ./source/verification-test \
        -l ./logs \
        --login tester@digitalhealthpass.com \
        --password tester \
        --host sandbox.digitalhealthpass.com \
        -s VC \
        --did did:hpass:59cd606341eb4a4a6c1a25d94a5f842ecf83ccd441dbda8abcd9274c9acd9334:67cba75b1719b5efba1addd32602f827fd378f2654288b1a4e381f8dddf40af3
```
	
