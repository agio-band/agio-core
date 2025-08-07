from collections import defaultdict

from agio.core.api import client


def iter_query_list(query: str,
                    entities_data_key: str,
                    variables: dict = None,
                    limit: int = None,
                    items_per_page: int = 50,
                    ):
    """
    required in response:

    pageInfo {
        hasNextPage
        hasPreviousPage
        startCursor
        endCursor
    }
    """
    current_cursor = None
    variables = variables or {}
    count = 0
    while True:
        response = client.make_query(
            query,
            **variables,
            first=items_per_page,
            afterCursor=current_cursor,
        )
        items = response['data'][entities_data_key]['edges']
        if not items:
            break
        for item in items:
            yield item['node']
            # check limit
            if limit is not None:
                count += 1
                if count >= limit:
                    return
        page_info = response['data'][entities_data_key]['pageInfo']
        if page_info['hasNextPage']:
            current_cursor = page_info['endCursor']
        else:
            break


def deep_dict():
    return defaultdict(deep_dict)
