from typing import Iterator
from uuid import UUID

from . import client
from .schemas.desk import UserProfileResponseSchema, CurrentCompanyResponseSchema, CompanyResponseSchema
from .utils.query_tools import iter_query_list
from .utils.response_typing import response_schema


# User and profile

# @response_schema(UserProfileResponseSchema)
def get_profile() -> dict:
    """
    Return current user profile. Auth required.
    """
    return client.make_query('desk/account/currentUserFull')['data']['currentUser']



def update_profile(update_data: dict):
    raise NotImplementedError


# Company

# @response_schema(CurrentCompanyResponseSchema)
def get_current_company() -> dict|CurrentCompanyResponseSchema:
    """
    Get current active company.
    """
    return client.make_query('desk/company/currentCompany')['data']['currentCompany']


def get_company(company_id: UUID) -> CompanyResponseSchema:
    raise NotImplementedError


def update_company(company_id: UUID, update_data: dict) -> CompanyResponseSchema:
    raise NotImplementedError


def iter_companies(limit: int = None) -> Iterator[dict]:
    yield from iter_query_list(
        'desk/company/getCompanyList',
        entities_data_key='companies',
        limit=limit,
    )