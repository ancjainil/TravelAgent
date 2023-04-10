import random
import os
import json
from typing import Optional

from google.cloud import dialogflow_v2beta1 as dialogflow
from google.cloud.dialogflow_v2beta1 import DetectIntentResponse
from google.protobuf.json_format import MessageToDict
from KnowledgeBase import create_knowledge_base, HEADER_LIST
from IntentParsing import *

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

# Define a function to load a user's data from a file
def load_user_data(file_name: str) -> dict:
    """
   Extracts users information from their user file
    Args: str
        file_name: the file to pull from aka the user file
    returns dict
        the extracted user data
    """
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    else:
        return {}

def get_random_intro_sentence() -> str:
    """
    Returns a random sentence to introduce the knowledge base results in a conversational way
    Args: None
    Returns: str
      the randomly chosen string
    """
    potential_sentences = [
        'Here are some ideas from the web:',
        'I found a few options for you online!',
        'What do you think about these ideas I found?',
        'Here are some results I found:'
    ]
    return random.choice(potential_sentences)

def make_dialogflow_request(user_input: str, kb_id: str = None) -> DetectIntentResponse:
    """
    Makes a basic request to the Google Dialogflow agent
    Args:
        user_input: the string that the user typed to the agent
        kb_id (optional): knowledge base id you want to reference for the response
    Returns: dict
      the raw response from Dialogflow
    """
    text_input = dialogflow.types.TextInput(text=user_input, language_code='en-US')
    query_input = dialogflow.types.QueryInput(text=text_input)

    if kb_id:
        knowledge_base_path = dialogflow.KnowledgeBasesClient.knowledge_base_path(
            PROJECT_ID, current_kbid[len(kb_id) - 27:]
        )

        query_params = dialogflow.QueryParameters(
            knowledge_base_names=[knowledge_base_path]
        )
    else:
        query_params = None

    request = dialogflow.DetectIntentRequest(
        session=session, query_input=query_input, query_params=query_params
    )
    return session_client.detect_intent(request=request)

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

def search_knowledge_base_by_intent(user_input, kb_id, intent, current_kbid_doc_mapping) -> Optional[str]:
    """
    Queries a specific Dialogflow knowledge base document
    Args:
        user_input: the string that the user typed to the agent
        kb_id: knowledge base id you want to reference for the response
        intent: the name of the intent the user had (maps to a knowledge base document)
    Returns: str
      the raw response from the Dialogflow knowledge base query
    """
    response = make_dialogflow_request(user_input, kb_id)

    knowledge_base_answers = response.query_result.knowledge_answers.answers

    for result in response.alternative_query_results:
        knowledge_base_answers += result.knowledge_answers.answers

    for answer in knowledge_base_answers:
        if current_kbid_doc_mapping[intent] in answer.source:
            return answer.answer

    if len(knowledge_base_answers) > 0:
        return knowledge_base_answers[0].answer

    return None


if __name__ == '__main__':
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(PROJECT_ID, 'current-user-id')
    user_dict = {"name":"","countries":[], "interests":[]}

    # TODO: should we be able to support multiple countries in the current context?
    ## ^ You can switch between countries now if you say the name explicitly, 
    current_kbid = None
    current_kbid_doc_mapping = None
    user_input = 'Hello'
    filename = None
    country = None
    while user_input != 'exit':
        response = make_dialogflow_request(user_input, None)

        # convert response to a dictionary for parsing
        response_dict = MessageToDict(response.query_result._pb)

        # collect information about the user
        parameters_dict = response_dict['parameters']
        if 'person' in parameters_dict:
            user_name = parameters_dict['person']['name']
            print("LOG - Detected new user: " + user_name)
            filename = f"{user_name}.json"
            if not os.path.exists(filename):
                    user_dict["name"] = user_name
                    save_user_data(filename, user_dict)
            else:
                user_dict = load_user_data(filename)
                print(f"Welcome back {user_name}! How can I help you?")
                user_input = input()
                continue


        # country detected
        if 'geo-country' in parameters_dict:
            country = parameters_dict['geo-country']
            print("LOG - Detected country: " + country)
            if country in CURRENT_COUNTRIES:
                current_kbid = get_kb_name_of_country(country)
            else:
                # build a knowledge base for that country if it does not already exist
                current_kbid = create_knowledge_base(country)
                CURRENT_COUNTRIES.append(country)
            current_kbid_doc_mapping = map_doc_name_to_id(current_kbid)
            user_dict["countries"].append(country)       
    

        # extract what information the user would like to know
        if 'intent' in response_dict and 'displayName' in response_dict['intent']:
            intent_name = response_dict['intent']['displayName']

            print("LOG - Detected new user intent: " + intent_name)

            # check if we should reference the knowledge base of a certain header
            if intent_name in HEADER_LIST and country:
                user_dict["interests"].append(intent_name)
                kb_response = search_knowledge_base_by_intent(user_input, current_kbid, intent_name, current_kbid_doc_mapping)
                if kb_response is not None:
                    print(response.query_result.fulfillment_text + ' ' + kb_intent_response(kb_response, intent_name, country))
                else:
                    print(response.query_result.fulfillment_text)
            else:
                print(response.query_result.fulfillment_text)
        else:
            print(response.query_result.fulfillment_text)
        
        user_input = input()
        if filename:
            save_user_data(filename, user_dict)