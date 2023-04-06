import random

from google.cloud import dialogflow_v2beta1 as dialogflow
from google.cloud.dialogflow_v2beta1 import DetectIntentResponse
from google.protobuf.json_format import MessageToDict
from KnowledgeBase import create_knowledge_base, HEADER_LIST
from nltk import sent_tokenize

PROJECT_ID = 's4395-travel-agent-bapg'

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

def search_knowledge_base_by_intent(user_input, kb_id, intent, current_kbid_doc_mapping) -> str:
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

    # TODO: should we be able to support multiple countries in the current context?
    current_kbid = None
    current_kbid_doc_mapping = None

    user_input = 'Hello'
    while user_input != 'exit':
        response = make_dialogflow_request(user_input, None)

        # convert response to a dictionary for parsing
        response_dict = MessageToDict(response.query_result._pb)

        # collect information about the user
        parameters_dict = response_dict['parameters']
        if 'person' in parameters_dict:
            user_name = parameters_dict['person']['name']
            print("LOG - Detected new user: " + user_name)

        # country detected
        if 'geo-country' in parameters_dict:
            country = parameters_dict['geo-country']
            print("LOG - Detected new country: " + country)

            # build a knowledge base for that country if it does not already exist
            current_kbid = create_knowledge_base(country)
            current_kbid_doc_mapping = map_doc_name_to_id(current_kbid)

        # extract what information the user would like to know
        if 'intent' in response_dict and 'displayName' in response_dict['intent']:
            intent_name = response_dict['intent']['displayName']

            print("LOG - Detected new user intent: " + intent_name)
            print(response.query_result.fulfillment_text)

            # check if we should reference the knowledge base of a certain header
            if intent_name in HEADER_LIST:
                kb_response = search_knowledge_base_by_intent(user_input, current_kbid, intent_name, current_kbid_doc_mapping)
                if kb_response:
                    print(get_random_intro_sentence())
                    print(kb_response)
        else:
            print(response.query_result.fulfillment_text)

        user_input = input()