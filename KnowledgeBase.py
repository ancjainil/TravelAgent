import requests
from bs4 import BeautifulSoup
import re
from nltk import sent_tokenize, word_tokenize, pos_tag

HEADER_LIST = ["Regions", "Cities", "Other_destinations", "Get_in", "See", "Do", "Talk", "Buy", "Eat", "Drink","Stay_healthy", "Stay_safe", "Connect","Respect"]

def validate_sentence_length(sentences: list) -> list:
    """
    Removes "sentences" that skew the scraped data (one word sentences, lables, etc)
    Args: list
        sentences: the sentences to be validated
    Returns: list
      the valid sentences
    """
    for sent in sentences:
        num_words= len(re.findall(r'\w+', sent))
        if num_words < 5:
            sentences.remove(sent)
    return sentences


def scrape(country: str, knowledge_base_id: str) -> None:
    """
    Scrapes the wikipedia page of a country and organizes it by header
     Args: str, str
        country: the name of the country to scrape
        knowledge_base_id: the name of the knowledge base to write to (1 kb per country)
    Returns: None

    """
    if country.find(" "):
        country = country.replace(" ", "_")
    # Specify the URL of the Wikivoyage page you want to scrape
    url = f'https://en.m.wikivoyage.org/wiki/{country}'

    # Send a GET request to the URL and store the response
    response = requests.get(url)

    # Use Beautiful Soup to parse the HTML content of the page
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the header you're interested in (in this case, the "See" header)
    for key in HEADER_LIST:
        html_content = ''
        header = soup.find('span', {'id': key})

        #Get all the content under the header (i.e. everything until the next header)
        if header and header.parent:
            for sibling in header.parent.next_siblings:
                if sibling.name == 'h2': #or (sibling.name == 'span' and 'id' in sibling.attrs):
                    break
                if sibling.name is not None:
                    html_content += str(sibling)

        # Remove unwanted tags
        html_content = re.sub(r'<figcaption\b[^>]*>.*?</figcaption>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<h3\b[^>]*>.*?</h3>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<dl\b[^>]*>.*?</dl>', '', html_content, flags=re.DOTALL)
        
        soup = BeautifulSoup(html_content, 'html.parser')
        for abbr in soup.find_all('abbr'):
            abbr.decompose()
        text = soup.get_text()
        sents = sent_tokenize(text)
        sents = validate_sentence_length(sents)
        content ='\n'.join(sents)

        content = bytes(content, 'utf-8')
        create_document(knowledge_base_id, key, 'text/plain', 'EXTRACTIVE_QA', content)
        # reset parse
        soup = BeautifulSoup(response.content, 'html.parser')
        

def create_document(knowledge_base_id: str, display_name: str, mime_type: str, knowledge_type: str, content: bytes) -> None:
    """
    Creates a Document.
    Args: str, str, str, str, bytes
        knowledge_base_id: Id of the Knowledge base.
        display_name: The display name of the Document, in this case the header from the header list.
        mime_type: type of data recieved
        knowledge_type: The Knowledge type of the Document
        content: the bytes of the scraped content under that header
    Returns: None
    """
    from google.cloud import dialogflow_v2beta1 as dialogflow

    client = dialogflow.DocumentsClient()

    # create document
    document = dialogflow.Document(display_name=display_name, mime_type=mime_type, raw_content=content)
    document.knowledge_types.append(getattr(dialogflow.Document.KnowledgeType, knowledge_type))

    response = client.create_document(parent=knowledge_base_id, document=document)
    print("Waiting for results...")
    document = response.result(timeout=120)
    print("Created Document:")
    print(" - Display Name: {}".format(document.display_name))
    print(" - Knowledge ID: {}".format(document.name))
    print(" - MIME Type: {}".format(document.mime_type))
    print(" - Knowledge Types:")


def create_knowledge_base(country: str) -> str:
    """
    Creates a Knowledge base for the given country.

    Args: str
        country: The name of the country for which to create the Knowledge base.
    Returns: str
        the name of the newly created knowledge base
    
    """
    from google.cloud import dialogflow_v2beta1 as dialogflow

    client = dialogflow.KnowledgeBasesClient()
    project_path = client.common_project_path("s4395-travel-agent-bapg")

    # if a knowledge base has already been created for the country, return the existing ID
    existing_kb_list = client.list_knowledge_bases(parent='projects/s4395-travel-agent-bapg')
    for kb in existing_kb_list:
        if kb.display_name == country:
            return kb.name

    knowledge_base = dialogflow.KnowledgeBase(display_name=country)

    response = client.create_knowledge_base(
        parent=project_path, knowledge_base=knowledge_base
    )

    dialogflow.CreateKnowledgeBaseRequest()

    print("Knowledge Base created for country {}:\n".format(country))
    print("Display Name: {}\n".format(response.display_name))
    print("Name: {}\n".format(response.name))
    scrape(country,response.name)
    return response.name