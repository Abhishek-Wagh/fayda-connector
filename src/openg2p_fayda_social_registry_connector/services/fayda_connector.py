import time
import threading
import logging
from typing import List
import httpx
from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.utils.ctx_thread import CTXThread
from fayda_mock.controllers.fayda_number_controller import FaydaNumberController
from ..config import Settings
from datetime import datetime, timedelta
import ssl
import xmlrpc.client

_config = Settings.get_config()

_logger = logging.getLogger(_config.logging_default_logger_name)
config_dict = _config.model_dump()


class FaydaIdConnectorService(BaseService):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.runner_thread = CTXThread(target=self.job_runner)
        self.runner_thread.start()

    def job_runner(self):
        time.sleep(_config.initial_delay_secs)
        while True:
            try:
                self.run_task()
            except Exception as e:
                _logger.error(f"An error occurred: {e}", exc_info=True)
                raise e
            time.sleep(_config.interval_secs)

    def run_task(self):
        _logger.info("Running task at %s", time.ctime())
        # Step1 : call the fetch registration ids toget the ids
        # Odoo server details
        # ODOO_URL = 'https://localhost:8069'
        # ODOO_DB = 'fayda-new'
        # ODOO_USERNAME = 'admin'
        # ODOO_PASSWORD = 'admin'
        # # XML-RPC endpoints
        # COMMON_ENDPOINT = f'{ODOO_URL}/xmlrpc/2/common'
        # common = xmlrpc.client.ServerProxy(COMMON_ENDPOINT)
        # context = ssl._create_unverified_context()
        # common = xmlrpc.client.ServerProxy(COMMON_ENDPOINT, context=context)
        # print("@@@@@@@@@@@", common.version())
        # uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        # print("########", uid)
        # if uid:
        registration_ids = self.fetch_registration_ids()

        if registration_ids:
            # Step 2: Call the Fayda number API with the registration IDs
            request_data = {
                "id":"openg2p-test",
                "requestTime":datetime.utcnow().isoformat(),
                "version":"v1",
                "request":[{"registrationId": rid} for rid in registration_ids]
            }

            fayda_response = self.call_fayda_number_api(request_data)

            # Step 3: Transform and call the update API with the response
            self.update_fayda_number_status(fayda_response)

        _logger.info("Task completed at %s", time.ctime())

    def fetch_registration_ids(self) -> List[str]:
        reg_id_url = config_dict.get(
                    "reg_ids_api", None
                )
        params = {"include_id_type": "rid", "exclude_id_type": "UIN"}
        try:

            response = httpx.get(reg_id_url, params=params, cookies={"session_id": "dc8a5fa2269aa982b9e0e1dc3f046bd7a286c7da"})
            response.raise_for_status()
            data = response.json()
            return data
        except httpx.HTTPError as e:
            _logger.error(f"Failed to fetch registration IDs: {e}")
            return []

    def call_fayda_number_api(self, request):
        get_fayda_number_url = config_dict.get(
                    "get_fayda_number_api", None
                )
        try:
            response = httpx.post(get_fayda_number_url, json=request)
            response.raise_for_status()
            data = response.json()
            print("!!!!!!!!!!!!!!!!!", data)
            return data
        except httpx.HTTPError as e:
            _logger.error(f"Failed to call Fayda number API: {e}")

    def transform_response(self, response):
        transformed_data = []

        for entry in response['response']:
            if entry["status"] == "PROCESSED" and entry["data"]:
                # Extract the full name in English
                full_name_eng = [name["value"] for name in entry["data"]["fullName"] if name["language"] == "eng"]
                full_name_str = " ".join(full_name_eng)

                # Extract given, additional, and family names
                name_parts = full_name_str.split()
                given_name = name_parts[0] if name_parts else ""
                family_name = name_parts[-1] if len(name_parts) > 1 else ""
                addl_name = " ".join(name_parts[1:-1]) if len(name_parts) > 2 else ""

                # Extract the gender in English
                gender_eng = [gender["value"] for gender in entry["data"]["gender"] if gender["language"] == "eng"]
                gender_str = ", ".join(gender_eng)

                transformed_entry = {
                    "name": full_name_str,
                    "ids": [
                        {
                            "id_type": "UIN",
                            "value": entry["data"]["fin"],
                            "expiry_date": (datetime.utcnow() + timedelta(days=365)).date().isoformat()  # Example expiry date
                        }
                    ],
                    "registration_date": datetime.utcnow().date().isoformat(),
                    "given_name": given_name,
                    "addl_name": addl_name,
                    "family_name": family_name,
                    "gender": gender_str,
                    "birthdate": entry["data"]["dateOfBirth"],
                    "birth_place": entry["data"].get("birth_place", ""),
                    "is_group": False,
                    "updateId": entry["registrationId"]
                }
                transformed_data.append(transformed_entry)
            else:
                _logger.info(f"Skipping entry with status {entry['status']} for registrationId {entry['registrationId']}")

        return transformed_data

    def update_fayda_number_status(self, response):
        transformed_data = self.transform_response(response)
        if not transformed_data:
            _logger.info("No processed entries to update.")
            return

        update_partner= config_dict.get(
                    "update_partner_using_rid", None
                )
        params = {"id_type": "rid"}
        try:
            response = httpx.put(update_partner, json=transformed_data, params=params, cookies={"session_id": "dc8a5fa2269aa982b9e0e1dc3f046bd7a286c7da"})
            response.raise_for_status()
            _logger.info(f"Successfully updated Fayda number status: {response.json()}")
        except httpx.HTTPError as e:
            _logger.error(f"Failed to update Fayda number status: {e}")

    def is_runner_thread_alive(self):
        return self.runner_thread.is_alive()

