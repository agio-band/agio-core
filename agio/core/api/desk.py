from uuid import UUID

from . import client
from .schemas.desk import UserProfileResponseSchema, CurrentCompanyResponseSchema, CompanyResponseSchema


# User and profile

def get_profile() -> UserProfileResponseSchema:
    """
    Return current user profile. Auth required.
    """
    return UserProfileResponseSchema(
        **client.make_query('desk/account/currentUser')['data']['currentUser']
    )


def update_profile(update_data: dict):
    raise NotImplementedError


# Company


def get_current_company() -> CurrentCompanyResponseSchema:
    """
    Get current active company.
    """
    return CurrentCompanyResponseSchema(
        **client.make_query('desk/company/currentCompany')['data']['currentCompany']
    )


def get_company(company_id: UUID) -> CompanyResponseSchema:
    raise NotImplementedError


def update_company(company_id: UUID, update_data: dict) -> CompanyResponseSchema:
    raise NotImplementedError
