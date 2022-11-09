#!/usr/bin/env python3
# coding: utf-8
#
# (c) Copyright Merative US L.P. and others 2020-2022 
#
# SPDX-Licence-Identifier: Apache 2.0

from datetime import date, datetime, timedelta

import os
import io
import json
import requests
import pytz
import sys
import getopt
import PIL.Image as Image
import zlib
import base64
import base45
import cbor2
import time

class IssueCredentialsUtils:
    log_time = datetime.now().strftime("%y%m%d%H%M")

    # Durations
    fifteen_minutes = timedelta(minutes=15)
    day = timedelta(days=1)
    two_days = timedelta(days=2)
    week = timedelta(weeks=1)
    two_weeks = timedelta(weeks=2)
    six_weeks = timedelta(weeks=6)
    month = timedelta(weeks=4)
    two_months = timedelta(weeks=8)
    year = timedelta(weeks=52)
    three_hours = timedelta(hours=3)
    now = datetime.now().astimezone(pytz.utc)

    # Dates
    today_date = date.today()
    last_year_date = today_date - year - day  # only used on SHC JSN expired and old - should be over year older
    two_months_ago_date = today_date - two_months
    six_weeks_ago_date = today_date - six_weeks
    last_month_date = today_date - month
    two_weeks_ago_date = today_date - two_weeks
    last_week_date = today_date - week
    two_days_ago_date = today_date - two_days
    yesterday_date = today_date - day
    tomorrow_date = today_date + day
    next_week_date = today_date + week
    next_month_date = today_date + month
    six_weeks_date = today_date + six_weeks
    next_year_date = today_date + year
    three_hours_ago = now - three_hours
    # adding extra minutes from now will prevent expired date when creating multiple credentials
    today_now = now + fifteen_minutes
    ten_minutes_from_now = now + timedelta(minutes=10)
    twenty_five_minutes_from_now = now + timedelta(minutes=25)

    today_now_f = today_now.strftime("%Y-%m-%dT%H:%M:%SZ")
    ten_minutes_from_now_f = ten_minutes_from_now.strftime("%Y-%m-%dT%H:%M:%SZ")
    twenty_five_minutes_from_now_f = twenty_five_minutes_from_now.strftime("%Y-%m-%dT%H:%M:%SZ")

    last_year_datetime = last_year_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    two_months_ago_datetime = two_months_ago_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    six_weeks_ago_datetime = six_weeks_ago_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    last_month_datetime = last_month_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    two_weeks_ago_datetime = two_weeks_ago_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    last_week_datetime = last_week_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    two_days_ago_datetime = two_days_ago_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    yesterday_datetime = yesterday_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    now_datetime = today_now.strftime("%Y-%m-%dT%H:%M:%SZ")
    today_datetime = today_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    tomorrow_datetime = tomorrow_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    next_week_datetime = next_week_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    next_month_datetime = next_month_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    six_weeks_datetime = six_weeks_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    next_year_datetime = next_year_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    last_year_tzdatetime = last_year_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    two_months_ago_tzdatetime = two_months_ago_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    six_weeks_ago_tzdatetime = six_weeks_ago_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    last_month_tzdatetime = last_month_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    two_weeks_ago_tzdatetime = two_weeks_ago_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    last_week_tzdatetime = last_week_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    two_days_ago_tzdatetime = two_days_ago_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    yesterday_tzdatetime = yesterday_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    now_tzdatetime = today_now.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    today_tzdatetime = today_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    tomorrow_tzdatetime = tomorrow_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    next_week_tzdatetime = next_week_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    next_month_tzdatetime = next_month_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    six_weeks_tzdatetime = six_weeks_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    next_year_tzdatetime = next_year_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    hpass_path_api = "/api/v1/hpass"
    user_login_path = hpass_path_api + "/users/login"

    api_paths_qr = {
        "default": hpass_path_api + "/credentials?output=qrcode",
        "SHC": hpass_path_api + "/credentials/vci?output=qrcode",
        "DCC": hpass_path_api + "/credentials/dcc?output=qrcode"
    }

    api_paths_json = {
        "default": hpass_path_api + "/credentials?type=string",
        "SHC": hpass_path_api + "/credentials/vci",
        "DCC": hpass_path_api + "/credentials/dcc"
    }

    header_issuer = {
        "default": "hpass.issuer1",
        "SHC": "hpass.testdhpissuer",
        "DCC": "hpass.dssissuer1"
    }

    valid_specs = ["SHC", "GHP", "DHP", "VC", "DCC"]

    save_generated_credential_json = True

    # extracting payloads for DCC and SHC similarly how the verifiers do it currently,
    # once there will be expirationDate added to payload by verifier apps and SDKs will also add here
    add_expiration_date_to_payload_for_dcc_shc = False

    # dict for files where the API has already been run
    generated_credentials_qr = {}
    generated_credentials_json = {}

    payloads_dict = {}
    cfg_test = {}

    retries = 5

    def __init__(self):
        self.specs = self.valid_specs
        self._email = ""
        self._password = ""
        self._ground_truth = ""
        self._results = ""
        self._configs = ""
        self._host = ""
        self._did = ""
        self._log_dir = ""
        self.log = None
        self.info = None
        # versions
        self._version_verifierlogin = ""
        self._version_random = ""
        self._version_dhp_pass = ""
        self._version_dhp_temperature = ""
        self._version_dhp_test = ""
        self._version_dhp_vaccination = ""
        self._version_ghp_testcredential = ""
        self._version_ghp_vaccinationcredential = ""

    def set_ground_truth(self, value):
        self._ground_truth = value

    def set_results(self, value):
        self._results = value

    def set_configs(self, value):
        self._configs = value

    def set_host(self, value):
        self._host = value

    def set_did(self, value):
        self._did = value

    def set_password(self, value):
        self._password = value

    def set_log_dir(self, value):
        self._log_dir = value

    def set_email(self, value):
        self._email = value

    def set_specs(self, value):
        self.specs = value

    def set_log(self, value):
        self.log = value

    def set_info(self, value):
        self.info = value

    def set_version_verifierlogin(self, value):
        self._version_verifierlogin = value

    def set_version_random(self, value):
        self._version_random = value

    def set_version_dhp_pass(self, value):
        self._version_dhp_pass = value

    def set_version_dhp_temperature(self, value):
        self._version_dhp_temperature = value

    def set_version_dhp_test(self, value):
        self._version_dhp_test = value

    def set_version_dhp_vaccination(self, value):
        self._version_dhp_vaccination = value

    def set_version_ghp_testcredential(self, value):
        self._version_ghp_testcredential = value

    def set_version_ghp_vaccinationcredential(self, value):
        self._version_ghp_vaccinationcredential = value

    def set_variables(self):
        argv = sys.argv[1:]
        opts, args = getopt.getopt(argv, "hi:o:c:s:l:", ["host=", "login=", "password=", "did="])
        for opt, arg in opts:
            if opt == '-h':
                print('test.py -i <input folder> -o <output folder> -c <configs folder> -l <log folder> \\')
                print('        --login <usernam> --password <password> \\')
                print('        --host  <host>')
                print('        -s ' + ",".join(self.valid_specs))
                print('        --did <issuer schema did>')
                sys.exit()
            elif opt == "-i":
                self.set_ground_truth(arg)
            elif opt == "-o":
                self.set_results(arg)
            elif opt == "-c":
                self.set_configs(arg)
            elif opt == '--host':
                self.set_host(arg)
            elif opt == '-s':
                self.set_specs(list(set(arg.split(","))))
            elif opt == '-l':
                self.set_log_dir(arg)
            elif opt == '--login':
                self.set_email(arg)
            elif opt == '--password':
                self.set_password(arg)
            elif opt == '--did':
                self.set_did(arg)
        
        if not os.path.isdir(self._results):
            os.mkdir(self._results)

        if not os.path.isdir(self._log_dir):
            os.mkdir(self._log_dir)

        log_file = self._log_dir + "/errors_" + self.log_time + ".logs"
        info_file = self._log_dir + "/info_" + self.log_time + ".logs"
        self.set_log(open(log_file, "a+"))
        self.set_info(open(info_file, "a+"))

    def login(self):
        response = None
        access_token = None
        try:
            payload = json.dumps({
                "email": self._email,
                "password": self._password
            })
            headers = {
                'Content-Type': 'application/json'
            }
            try:
                api_url = "https://" + \
                          self._host + \
                          self.user_login_path
                print(api_url)
                response = requests.request("POST", api_url, headers=headers, data=payload)

                access_token = response.json()['access_token']
            except Exception as err:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(err).__name__, err.args)
                print(message)

            if "error" not in str(response.text):
                return access_token
            else:
                self.log.write("ERROR IN DURING LOGIN [" + self._host + "]: " + str(response.text) + "\n")

        except Exception as e:
            self.log.write("ERROR IN DURING LOGIN [" + self._host + "]: " + str(response.text) + " : ")
            self.log.write(str(e))
            self.log.write("\n")

    def create_single_payload(self, file):
        try:
            with open(file) as infile:
                json_file = json.load(infile)
                payload = json.dumps(json_file)
                replacements = {
                    "{{TODAY_NOW_F}}": str(self.today_now_f),
                    "{{TEN_MINUTES_FROM_NOW_F}}": str(self.ten_minutes_from_now_f),
                    "{{TWENTY_FIVE_MINUTES_FROM_NOW_F}}": str(self.ten_minutes_from_now_f),
                    "{{LAST_YEAR_DATE}}": str(self.last_year_date),
                    "{{LAST_YEAR_DATETIME}}": str(self.last_year_datetime),
                    "{{LAST_YEAR_TZDATETIME}}": str(self.last_year_tzdatetime),
                    "{{SIX_WEEKS_AGO_DATE}}": str(self.six_weeks_ago_date),
                    "{{SIX_WEEKS_AGO_DATETIME}}": str(self.six_weeks_ago_datetime),
                    "{{SIX_WEEKS_AGO_TZDATETIME}}": str(self.six_weeks_ago_tzdatetime),
                    "{{TWO_MONTHS_AGO_DATE}}": str(self.two_months_ago_date),
                    "{{TWO_MONTHS_AGO_DATETIME}}": str(self.two_months_ago_datetime),
                    "{{TWO_MONTHS_AGO_TZDATETIME}}": str(self.two_months_ago_tzdatetime),
                    "{{LAST_MONTH_DATE}}": str(self.last_month_date),
                    "{{LAST_MONTH_DATETIME}}": str(self.last_month_datetime),
                    "{{LAST_MONTH_TZDATETIME}}": str(self.last_month_tzdatetime),
                    "{{TWO_WEEKS_AGO_DATE}}": str(self.two_weeks_ago_date),
                    "{{TWO_WEEKS_AGO_DATETIME}}": str(self.two_weeks_ago_datetime),
                    "{{TWO_WEEKS_AGO_TZDATETIME}}": str(self.two_weeks_ago_tzdatetime),
                    "{{LAST_WEEK_DATE}}": str(self.last_week_date),
                    "{{LAST_WEEK_DATETIME}}": str(self.last_week_datetime),
                    "{{LAST_WEEK_TZDATETIME}}": str(self.last_week_tzdatetime),
                    "{{TWO_DAYS_AGO_DATE}}": str(self.two_days_ago_date),
                    "{{TWO_DAYS_AGO_DATETIME}}": str(self.two_days_ago_datetime),
                    "{{TWO_DAYS_AGO_TZDATETIME}}": str(self.two_days_ago_tzdatetime),
                    "{{YESTERDAY_DATE}}": str(self.yesterday_date),
                    "{{YESTERDAY_DATETIME}}": str(self.yesterday_datetime),
                    "{{YESTERDAY_TZDATETIME}}": str(self.yesterday_tzdatetime),
                    "{{NOW_DATETIME}}": str(self.now_datetime),
                    "{{TODAY_DATE}}": str(self.today_date),
                    "{{TODAY_DATETIME}}": str(self.today_datetime),
                    "{{TODAY_TZDATETIME}}": str(self.today_tzdatetime),
                    "{{TOMORROW_DATE}}": str(self.tomorrow_date),
                    "{{TOMORROW_DATETIME}}": str(self.tomorrow_datetime),
                    "{{TOMORROW_TZDATETIME}}": str(self.tomorrow_tzdatetime),
                    "{{NEXT_WEEK_DATE}}": str(self.next_week_date),
                    "{{NEXT_WEEK_DATETIME}}": str(self.next_week_datetime),
                    "{{NEXT_WEEK_TZDATETIME}}": str(self.next_week_tzdatetime),
                    "{{NEXT_MONTH_DATE}}": str(self.next_month_date),
                    "{{NEXT_MONTH_DATETIME}}": str(self.next_month_datetime),
                    "{{NEXT_MONTH_TZDATETIME}}": str(self.next_month_tzdatetime),
                    "{{SIX_WEEKS_DATE}}": str(self.six_weeks_date),
                    "{{SIX_WEEKS_DATETIME}}": str(self.six_weeks_datetime),
                    "{{SIX_WEEKS_TZDATETIME}}": str(self.six_weeks_tzdatetime),
                    "{{NEXT_YEAR_DATE}}": str(self.next_year_date),
                    "{{NEXT_YEAR_DATETIME}}": str(self.next_year_datetime),
                    "{{NEXT_YEAR_TZDATETIME}}": str(self.next_year_tzdatetime)
                }

                replacements.update({
                    "{{VERIFIERLOGIN_SCHEMA_ID}}": f"{self._did};id=verifierlogin;version={self._version_verifierlogin}",
                    "{{RANDOM_SCHEMA_ID}}": f"{self._did};id=random;version={self._version_random}",
                    "{{DHP_PASS_SCHEMA_ID}}": f"{self._did};id=dhp-pass;version={self._version_dhp_pass}",
                    "{{DHP_TEMP_SCHEMA_ID}}": f"{self._did};id=dhp-temperature;version={self._version_dhp_temperature}",
                    "{{DHP_TEST_SCHEMA_ID}}": f"{self._did};id=dhp-test;version={self._version_dhp_test}",
                    "{{DHP_VACCINE_SCHEMA_ID}}": f"{self._did};id=dhp-vaccination;version={self._version_dhp_vaccination}",
                    "{{GHP_TEST_SCHEMA_ID}}": f"{self._did};id=ghp-testcredential;version={self._version_ghp_testcredential}",
                    "{{GHP_VACCINE_SCHEMA_ID}}": f"{self._did};id=ghp-vaccinationcredential;version={self._version_ghp_vaccinationcredential}",
                    "{{ISS}}": "https://dhp.github.io/hpass/testdhpissuer"
                })
                
                for src, target in replacements.items():
                    payload = payload.replace(src, target)

            return payload

        except Exception as e:
            self.log.write("ERROR IN DURING PAYLOAD [" + self._host + "]: " + str(file) + " : ")
            self.log.write(str(e))
            self.log.write("\n")

    def create_payloads(self, access_token=None):
        path_out_list = []

        for file in os.listdir(self._configs):
            if os.path.isfile(os.path.join(self._ground_truth, file)):
                if file.endswith(".json"):
                    config_id = file.replace(".json", "")
                    with open(os.path.join(os.path.join(self._configs, file)), encoding='utf-8') as jsonFile:
                        self.cfg_test[config_id] = json.load(jsonFile)

        specs = ["verifierlogin"] + self.specs
        env_configurations = self.get_configurations(access_token)

        # get the latest versions of schemas
        self.set_version_verifierlogin(self.get_schema_latest_version(access_token, 'verifierlogin'))
        self.set_version_random(self.get_schema_latest_version(access_token, 'random'))
        self.set_version_dhp_pass(self.get_schema_latest_version(access_token, 'dhp-pass'))
        self.set_version_dhp_temperature(self.get_schema_latest_version(access_token, 'dhp-temperature'))
        self.set_version_dhp_test(self.get_schema_latest_version(access_token, 'dhp-test'))
        self.set_version_dhp_vaccination(self.get_schema_latest_version(access_token, 'dhp-vaccination'))
        self.set_version_ghp_testcredential(self.get_schema_latest_version(access_token, 'ghp-testcredential'))
        self.set_version_ghp_vaccinationcredential(self.get_schema_latest_version(access_token, 'ghp-vaccinationcredential'))

        for file in os.listdir(self._ground_truth):
            if os.path.isfile(os.path.join(self._ground_truth, file)):
                if file.endswith(".json"):
                    self.payloads_dict[file] = json.loads(self.create_single_payload(os.path.join(self._ground_truth, file)))

        for config_id in self.cfg_test:
            if config_id in env_configurations:

                for spec in [s for s in specs if s != "verifierlogin"]:
                    os.makedirs(self._results + "/" + str(config_id) + "/Verified" + "/" + spec)
                    os.makedirs(self._results + "/" + str(config_id) + "/NotVerified" + "/" + spec)

                for verified_status, file_names in self.cfg_test[config_id]:
                    for file_name in file_names:
                        path_out_new = self._results + "/" + config_id + "/" + verified_status + "/"

                        if "dcc" in file_name and "DCC" in specs:
                            path_out_new += "DCC/" + file_name

                        elif "shc" in file_name and "SHC" in specs:
                            path_out_new += "SHC/" + file_name

                        elif "dhp" in file_name and "vc" not in file_name and "DHP" in specs:
                            path_out_new += "DHP/" + file_name

                        elif "ghp" in file_name and "vc" not in file_name and "GHP" in specs:
                            path_out_new += "GHP/" + file_name

                        elif "vc" in file_name and "VC" in specs:
                            path_out_new += "VC/" + file_name

                        elif "verifierlogin" in file_name and "verifierlogin" in specs:
                            path_out_new = self._results + "/" + config_id + '/' + file_name

                        if path_out_new != "":
                            path_out_list.append(path_out_new)

        return path_out_list

    def generate_credentials(self, path_out_list, access_token, credential_spec):
        for path_out in path_out_list:
            credential_dirname = path_out.split('/')[-2]
            credential_filename = path_out.split('/')[-1]

            # the second part of condition is for "verifierlogin"
            if credential_spec in credential_dirname or \
                    credential_spec in credential_filename:

                payload = json.dumps(self.payloads_dict[credential_filename])

                headers = {
                    'Authorization': 'Bearer ' + access_token,
                    'Content-Type': 'application/json',
                    'x-hpass-issuer-id': self.header_issuer.get(credential_spec, self.header_issuer["default"])
                }

                # JPG files
                self.generate_jpg(credential_filename, credential_spec, headers, payload, path_out)

                # JSON files
                if self.save_generated_credential_json:
                    self.generate_json(credential_filename, credential_spec, headers, payload, path_out)

    def generate_jpg(self, credential_filename, credential_spec, headers, payload, path_out):
        response = None

        if credential_filename not in self.generated_credentials_qr:
            attempts = 0
            while attempts < self.retries:
                try:
                    api_url = "https://" + \
                              self._host + \
                              self.api_paths_qr.get(credential_spec, self.api_paths_qr["default"])
                    response = requests.request("POST", api_url, headers=headers, data=payload)
                    print("")
                    print(path_out.replace(".json", ""))
                    print(api_url, response.status_code)
                except Exception as err:
                    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                    message = template.format(type(err).__name__, err.args)
                    print(message)
                if response.status_code == 200:
                    self.generated_credentials_qr[credential_filename] = response.content
                    break
                else:
                    print(f"Error: [{response.text}], retrying...")
                attempts += 1
                time.sleep(2)
            if attempts == self.retries:
                raise Exception(f"API call for {credential_filename} failed after {self.retries} attempts")
        if credential_filename in self.generated_credentials_qr:
            image = Image.open(io.BytesIO(bytearray(self.generated_credentials_qr[credential_filename])))
            output_image_file = path_out.replace('.json', '.jpg')
            image.save(output_image_file)
            print(output_image_file)

    def generate_json(self, credential_filename, credential_spec, headers, payload, path_out):
        response = None

        if credential_filename not in self.generated_credentials_json:
            attempts = 0
            while attempts < self.retries:
                try:
                    api_url = "https://" + \
                              self._host + \
                              self.api_paths_json.get(credential_spec, self.api_paths_json["default"])
                    response = requests.request("POST", api_url, headers=headers, data=payload)
                    print(api_url, response.status_code)
                except Exception as err:
                    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                    message = template.format(type(err).__name__, err.args)
                    print(message)
                if response.status_code == 200:
                    self.generated_credentials_json[credential_filename] = response.content
                    break
                else:
                    print(f"Error: [{response.text}], retrying...")
                attempts += 1
                time.sleep(2)
            if attempts == self.retries:
                raise Exception(f"API call for {credential_filename} failed after {self.retries} attempts")
        if credential_filename in self.generated_credentials_json:
            # extracting payloads for DCC and SHC similarly how the verifier does it currently,
            # once there will be expirationDate added to payload by verifier apps and SDKs will
            # also add here
            expiration_date_key = "expirationDate"
            if credential_spec == "SHC":
                shc_credential = json.loads(self.generated_credentials_json[credential_filename])["payload"]
                json_output = json.loads(
                    zlib.decompress(
                        base64.urlsafe_b64decode(
                            shc_credential.split(".")[1] + '==='), -15).decode("utf-8"))

                if self.add_expiration_date_to_payload_for_dcc_shc:
                    if "exp" in json_output:
                        json_output[expiration_date_key] = datetime.utcfromtimestamp(
                            json_output["exp"]).strftime("%Y-%m-%dT%H:%M:%SZ")
            elif credential_spec == "DCC":
                dcc_credential = json.loads(self.generated_credentials_json[credential_filename])["payload"]

                # keeping it the same as it arrives to verifier just extracting the health payload part
                # (not adding expiry date, issue date or country)
                credential_key = -260
                certificate_key = "certificate"
                json_output = cbor2.loads(
                    cbor2.loads(
                        zlib.decompress(
                            base45.b45decode(
                                dcc_credential[certificate_key][4:]))).value[2])[credential_key][1]

                if self.add_expiration_date_to_payload_for_dcc_shc:
                    expiration_data_dcc_key = 4
                    exp = cbor2.loads(
                        cbor2.loads(
                            zlib.decompress(
                                base45.b45decode(
                                    dcc_credential[certificate_key][4:]))).value[2])[expiration_data_dcc_key]
                    json_output[expiration_date_key] = datetime.utcfromtimestamp(exp) \
                        .strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                json_output = json.loads(self.generated_credentials_json[credential_filename])["payload"]

            print(path_out)
            with open(path_out, 'w', encoding='utf-8', newline='\n') as json_file:
                json.dump(json_output, json_file, indent=3)

    def get_configurations(self, access_token):
        response = None
        configuration_list = []

        attempts = 0
        while attempts < self.retries:
            try:
                api_url = "https://" + \
                          self._host + \
                          "/api/v1/verifier/config/api/v1/verifier-configurations"
                headers = {
                    'Authorization': 'Bearer ' + access_token,
                    'Content-Type': 'application/json'
                }
                response = requests.request("GET", api_url, headers=headers)
            except Exception as err:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(err).__name__, err.args)
                print(message)
            if response.status_code == 200:
                json_data = response.json()

                for i in json_data['payload']:
                    configuration_list.append(i['id'])
                break
            else:
                print(f"Error: [{response.text}], retrying...")
                attempts += 1
                time.sleep(2)
        if attempts == self.retries:
            raise Exception(f"Failed after {self.retries} attempts")
        return configuration_list

    def get_schema_latest_version(self, access_token, schema_id):
        response = None
        schema_version_list = []

        attempts = 0
        while attempts < self.retries:
            try:
                api_url = "https://" + \
                          self._host + \
                          f"/api/v1/hpass/schemas?author={self._did}&id={schema_id}"
                headers = {
                    'Authorization': 'Bearer ' + access_token,
                    'Content-Type': 'application/json'
                }
                response = requests.request("GET", api_url, headers=headers)
            except Exception as err:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(err).__name__, err.args)
                print(message)
            if response.status_code == 200:
                json_data = response.json()

                for i in json_data['payload']:
                    schema_version_list.append(i['modelVersion'])
                break
            else:
                print(f"Error: [{response.text}], retrying...")
                attempts += 1
                time.sleep(2)
        if attempts == self.retries:
            raise Exception(f"Failed after {self.retries} attempts")
        
        return max(schema_version_list, key=lambda x: float(x))


test = IssueCredentialsUtils()  # creating an instance of the generator
test.set_variables()

invalidSpecs = list(set(test.specs) - set(test.valid_specs))
if len(invalidSpecs) > 0:
    print("Invalid specs passed as argument:", invalidSpecs)
    print("Valid specs are:", test.valid_specs)
else:
    access_token = test.login()  # generating access token

    path_out_list = test.create_payloads(access_token)  # creating array of .json object to put it in the results

    # always generate verifierlogin credentials
    test.generate_credentials(path_out_list, access_token, "verifierlogin")

    # pass comma separated specs as argument of generator.py, e.g.: -s SHC,GHP,DHP,VC,DCC
    for spec in test.specs:
        test.generate_credentials(path_out_list, access_token, spec)
