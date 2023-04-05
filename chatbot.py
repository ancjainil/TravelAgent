from google.cloud import dialogflow_v2beta1 as dialogflow
from google.protobuf.json_format import MessageToDict
from KnowledgeBase import create_knowledge_base, scrape
from nltk import sent_tokenize

if __name__ == '__main__':
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path('s4395-travel-agent-bapg', 'current-user-id')

    current_kbid = None

    user_input = 'Hello'
    while user_input != 'exit':
        text_input = dialogflow.types.TextInput(text=user_input, language_code='en-US')
        query_input = dialogflow.types.QueryInput(text=text_input)

        if current_kbid:
            # TODO: replace this ID with dynamic ID
            knowledge_base_path = dialogflow.KnowledgeBasesClient.knowledge_base_path(
                's4395-travel-agent-bapg', 'MTgwOTk3NjI5NDI5OTUwNzA5NzY'
            )

            query_params = dialogflow.QueryParameters(
                knowledge_base_names=[knowledge_base_path]
            )
        else:
            query_params=None

        request = dialogflow.DetectIntentRequest(
            session=session, query_input=query_input, query_params=query_params
        )
        response = session_client.detect_intent(request=request)

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

        # extract what information the user would like to know
        if 'intent' in response_dict:
            intent_name = response_dict['intent']['displayName']
            print("LOG - Detected new user intent: " + intent_name)

        endConversation = str(response.query_result.intent.display_name)

        # get all possible answers from the knowledge base
        knowledge_base_answers = response.query_result.knowledge_answers

        # for now, just print the first sentence from the returned text (TODO: refine results manually)
        if len(knowledge_base_answers.answers) > 0:
            most_likely_answer = knowledge_base_answers.answers[0].answer
            sentences = sent_tokenize(most_likely_answer)
            print(sentences[0])
        else:
            print(response.query_result.fulfillment_text)
        user_input = input()




