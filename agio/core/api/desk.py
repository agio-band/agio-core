from typing import Iterator
from uuid import UUID

from . import client
from .utils.query_tools import iter_query_list
from ..exceptions import NotFoundError


# Company

def get_current_company() -> dict:
    """
    Get current active company.
    """
    return client.make_query('desk/company/currentCompany')['data']['currentCompany']


def switch_company(company_id: str):
    return client.make_query('desk/company/switchCompany', id=company_id)


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


def iter_companies(user_id: str = None, limit: int = None) -> Iterator[dict]:
    if user_id is None:
        from .profile import get_current_user
        user_id = get_current_user()['id']
    yield from iter_query_list(
        'desk/company/getCompanyList',
        entities_data_key='companies',
        limit=limit,
        variables={
            "userId":user_id
            }
    )
