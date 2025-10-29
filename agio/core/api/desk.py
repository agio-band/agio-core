from typing import Iterator
from uuid import UUID

# from .schemas.desk import UserProfileResponseSchema, CurrentCompanyResponseSchema, CompanyResponseSchema
# from .utils.response_typing import response_schema
from . import client
from .utils.query_tools import iter_query_list
from ..exceptions import NotFoundError


# User and profile

# @response_schema(UserProfileResponseSchema)
def get_profile() -> dict:
    """
    Return current user profile. Auth required.
    """
    return client.make_query('desk/account/currentUserFull')['data']['currentUser']


# Company

def get_current_company() -> dict:
    """
    Get current active company.
    """
    return client.make_query('desk/company/currentCompany')['data']['currentCompany']

def switch_company(company_id: str):
    return client.make_query('desk/company/switchCompany', {'id': company_id})


def get_company(company_id: str|UUID) -> dict:
    return client.make_query(
        'desk/company/getCompanyById',
        id=company_id
    )['data']['company']


def get_company_by_code(code: str) -> dict|None:
    resp = client.make_query(
        'desk/company/getCompanyByCode',
        code=code
    )
    if resp['data']['companies']['edges']:
        return resp['data']['companies']['edges'][0]['node']
    else:
        raise NotFoundError(detail='Company not found')


def iter_companies(limit: int = None) -> Iterator[dict]:
    yield from iter_query_list(
        'desk/company/getCompanyList',
        entities_data_key='companies',
        limit=limit,
    )