import sys
sys.path.append('../tests/')

# Shared DynamoDB helpers.

def query_all_pages(table, **query_kwargs):
    """Run a query and follow LastEvaluatedKey until every page has been read.

    DynamoDB caps a single query response at 1MB and signals more data with
    LastEvaluatedKey. A caller that ignores it silently sees a truncated result
    set, which is the worst kind of bug here: no error, no log line, just users
    or words quietly missing.
    """
    items = []
    while True:
        response = table.query(**query_kwargs)
        items.extend(response['Items'])

        last_evaluated_key = response.get('LastEvaluatedKey')
        if last_evaluated_key is None:
            return items
        query_kwargs['ExclusiveStartKey'] = last_evaluated_key
