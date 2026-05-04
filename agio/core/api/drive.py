from __future__ import annotations

import time
from typing import Callable
from uuid import UUID

from agio.core.api import client as default_client
from agio.core.api.utils import api_call
from agio.tools import network


@api_call
def get_upload_link(upload_path: str, company_id: str|UUID, facility_id: str|UUID, client=default_client) -> str:
    resp = client.make_query(
        'drive/createPutDriveFileUrl',
        companyId=company_id,
        filePath=upload_path,
        facilityId=facility_id,
    )
    return resp['data']['putDriveFileLink']


@api_call
def upload_file(local_file, upload_path: str, company_id: str|UUID, facility_id: str|UUID,
                read_mode='rb', client=default_client, callback: Callable = None) -> str:
    url = get_upload_link(upload_path, company_id, facility_id, client=client)
    network.upload_file(url, local_file, 'PUT', read_mode, callback=callback)
    return upload_path


@api_call
def get_file_id(company_id: str, file_path: str, attempts: int = 5, delay: int = 1, client=default_client) -> str:
    def get_file_id_wrapper():
        resp = client.make_query(
            'drive/getDriveFileId',
            companyId=company_id,
            filePath=file_path,
        )
        nodes = resp["data"]["driveObjects"]["edges"]
        if nodes:
            return nodes[0]["node"]["id"]
        raise FileNotFoundError
    for _ in range(attempts):
        try:
            return get_file_id_wrapper()
        except FileNotFoundError:
            print('Retrying...')
            time.sleep(delay)
    raise FileNotFoundError


@api_call
def get_file_url_by_id(drive_file_id: str, client=default_client) -> str:
    # TODO add lifetime with ISO_8601 format
    resp = client.make_query(
        'drive/getDriveFileUrl',
        driveFileId=drive_file_id,
    )
    return resp['data']['getDriveFileLink']


@api_call
def get_file_url_by_path(drive_file_path: str, company_id: str, client=default_client) -> str:
    file_id = get_file_id(company_id, drive_file_path, client=client)
    return get_file_url_by_id(file_id, client=client)


@api_call
def get_facility_list(company_id: str|UUID, client=default_client) -> list[dict]:
    resp = client.make_query('drive/getFacilityList', companyId=company_id)
    return [node["node"] for node in resp["data"]["facilities"]["edges"]]


@api_call
def get_default_facility(company_id: str|UUID, client=default_client) -> dict|None:
    facility_list = get_facility_list(company_id, client=client)
    for facility in facility_list:
        if facility["default"]:
            return facility
    return None