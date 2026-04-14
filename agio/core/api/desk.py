from typing import Iterator
from uuid import UUID

from . import client as default_client
from .utils.query_tools import iter_query_list
from ..exceptions import NotFoundError
from agio.core.api._utils import set_client

# Company

@set_client
def get_current_company(client=default_client) -> dict:
    """
    Get current active company.
    """
    return client.make_query('desk/company/currentCompany')['data']['currentCompany']


@set_client
def switch_company(company_id: str, client=default_client):
    return client.make_query('desk/company/switchCompany', id=company_id)


@set_client
def get_company(company_id: str|UUID, client=default_client) -> dict:
    return client.make_query(
        'desk/company/getCompanyById',
        id=company_id
    )['data']['company']


@set_client
def get_company_by_code(code: str, client=default_client) -> dict|None:
    resp = client.make_query(
        'desk/company/getCompanyByCode',
        code=code
    )
    if resp['data']['companies']['edges']:
        return resp['data']['companies']['edges'][0]['node']
    else:
        raise NotFoundError(detail='Company not found')


@set_client
def iter_companies(user_id: str = None, limit: int = None, items_per_page: int = 25, client=default_client) -> Iterator[dict]:
    if user_id is None:
        from .profile import get_current_user
        user_id = get_current_user()['id']
    yield from iter_query_list(
        'desk/company/getCompanyList',
        entities_data_key='companies',
        limit=limit,
        items_per_page=items_per_page,
        variables={
            "userId": user_id
            },
        client=client
    )
