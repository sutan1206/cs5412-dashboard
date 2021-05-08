import logging

import azure.functions as func

import json
from azure.cosmos import CosmosClient

url = 'https://cs5412finalprocosmos.documents.azure.com:443/'
key = 'lKQOG519VP60ez0hT5aah945IV0eyRIuYN3cu2caZulDUJHYhOdQOCnbWd7s8lXOTlufv7yaJBjPI3GnnTqASQ=='

logger = logging.getLogger("azure.core.pipeline.policies.http_logging_policy")
logger.setLevel(logging.WARNING)

def main(req: func.HttpRequest, outdoc: func.Out[func.Document]):
    logging.info('Python HTTP trigger function processed a request.')

    dbClient = CosmosClient(url, credential=key, logging_enable=False)
    db = dbClient.get_database_client(database='OutputDB')
    container = db.get_container_client('test')

    try:
        newdocs = func.DocumentList() 
        req_body = req.get_body().decode()
        req_body = json.loads(req_body)
        animals = {}
        for idx, row in enumerate(req_body):
            if row["id"] not in animals:
                animals[row["id"]] = row
                item = list(container.query_items(
                    query = f"""
                    SELECT *
                    FROM container c
                    WHERE c.id = @id
                    """,
                    parameters=[
                        dict(name='@id', value=row["id"])
                    ],
                    enable_cross_partition_query=True
                ))
                if len(item) > 0:
                    row["Temperature"] = [*row["Temperature"], *item[0]["Temperature"]]
                    row["Stomach_Activity"] = [*row["Stomach_Activity"], *item[0]["Stomach_Activity"]]
            else:
                d = animals[row["id"]]
                d["Temperature"] = [*d["Temperature"], *row["Temperature"]]
                d["Stomach_Activity"] = [*d["Stomach_Activity"], *row["Stomach_Activity"]]
        for k, value in animals.items():
            newdocs.append(func.Document.from_dict(value))
        outdoc.set(newdocs)
    except Exception as e:
            logging.error('Error:')
            logging.error(e)
