import os
import json


from google.cloud import dialogflow_v2beta1 as dialogflow
from google.cloud.dialogflow_v2beta1 import DetectIntentResponse

PROJECT_ID = 's4395-travel-agent-bapg'
CURRENT_COUNTRIES = ["Canada", "Chile", "France", "Germany","Peru", "Italy"]

def save_user_data(file_name: str, data: dict) -> None:
    """
    Saves user information in their personal user file
    Args: str, dict
        file_name: the file to write to
        data: the data to write to the file
    Returns: None
    """
    with open(file_name, 'w') as f:
        json.dump(data, f)

def load_user_data(file_name: str) -> dict:
    """
   Extracts users information from their user file
    Args: str
        file_name: the file to pull from aka the user file
    returns dict
        the extracted user data
    """
    if os.path.exists(file_name):
        with open(file_name, 'r') as f:
            return json.load(f)
    else:
        return {}

def get_kb_name_of_country(country: str) -> str:
    """
    Returns the knowledgebase id for a country
    Args: str
       country: the country to find the knowledgebase of
    Returns: str
      the knowledgebase ID of that country
    """
    # Create a client
    client = dialogflow.KnowledgeBasesClient()
    request = dialogflow.ListKnowledgeBasesRequest(parent=f"projects/{PROJECT_ID}")
    page_result = client.list_knowledge_bases(request=request)

    # Handle the response
    for response in page_result:
       if response.display_name == country:
           return response.name

def map_doc_name_to_id(kb_id) -> dict:
    """
    Returns a dict of a knowledge base's documents and their ID values
    Args:
        kb_id: knowledge base id you want to list documents for
    Returns: dict
      maps a document's display name (e.g. "Cities") to its ID
    """
    mapping = {}
    client = dialogflow.DocumentsClient()
    request = dialogflow.ListDocumentsRequest(
        parent=kb_id,
    )
    page_result = client.list_documents(request=request)

    # Handle the response
    for response in page_result:
        mapping[response.display_name] = response.name
    return mapping


