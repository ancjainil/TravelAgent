import os
import json
from typing import Optional

from google.cloud import dialogflow_v2beta1 as dialogflow
from google.cloud.dialogflow_v2beta1 import DetectIntentResponse

PROJECT_ID = 's4395-travel-agent-bapg'
CURRENT_COUNTRIES = ['United States', 'Canada', 'Mexico', 'Brazil', 'Argentina', 'United Kingdom', 'France', 'Germany', 'Italy', 'Spain', 'Russia', 'China', 'Japan', 'South Korea', 'India', 'Australia', 'New Zealand', 'Egypt', 'South Africa', 'Nigeria']

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

def make_dialogflow_request(session, session_client, user_input: str, kb_id: str = None) -> DetectIntentResponse:
    """
    Makes a basic request to the Google Dialogflow agent
    Args:
        user_input: the string that the user typed to the agent
        kb_id (optional): knowledge base id you want to reference for the response
    Returns: dict
      the raw response from Dialogflow
    """
    if user_input == '':
        user_input = 'Null'
    text_input = dialogflow.types.TextInput(text=user_input, language_code='en-US')
    query_input = dialogflow.types.QueryInput(text=text_input)

    if kb_id:
        query_params = dialogflow.QueryParameters(
            knowledge_base_names=[kb_id]
        )
    else:
        query_params = None

    request = dialogflow.DetectIntentRequest(
        session=session, query_input=query_input, query_params=query_params
    )
    return session_client.detect_intent(request=request)

def search_knowledge_base_by_intent(session, session_client, user_input, kb_id, intent, current_kbid_doc_mapping) -> Optional[str]:
    """
    Queries a specific Dialogflow knowledge base document
    Args:
        user_input: the string that the user typed to the agent
        kb_id: knowledge base id you want to reference for the response
        intent: the name of the intent the user had (maps to a knowledge base document)
    Returns: str
      the raw response from the Dialogflow knowledge base query
    """

    response = make_dialogflow_request(session, session_client, user_input, kb_id)
    knowledge_base_answers = response.query_result.knowledge_answers.answers
    for result in response.alternative_query_results:
        knowledge_base_answers += result.knowledge_answers.answers
    for answer in knowledge_base_answers:
        if current_kbid_doc_mapping[intent] in answer.source:
            return answer.answer
    return None

