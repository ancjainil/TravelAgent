# Travel Guide Chatbot
There are two ways to run this chatbot, the first one being easier and less time-consuming than the second. Both will result in our python code connecting to the dialogflow chatbot, but the second option is more stable than the first.

## Option 1
To allow for easy testing purposes, you can simply click on this dialog flow generated [link](https://console.dialogflow.com/api-client/demo/embedded/1ed112ff-ab5a-4e7a-96d4-dd4d7c29b09c) that will allow you to simply talk to to our chatbot running at this link.

However, this option requires that we are actively running our flask web server. We will try and keep our server running during the grading period, but please message us before you attempt to run the project so we can ensure it is running for you.

## Option 2 - Recommended but requires local setup
### Installation process
1. Ensure nltk is installed. If not already installed, install nltk by running pip install nltk

    A. To further ensure all necessary packages are installed for nltk to not get run time errors follow these steps:

        i. type in 'python' or similar to enter the python interpreter on your command line
        ii. type in import nltk
        iii. type in nltk.download(), select all and wait for a successful download
        
2. Ensure locationtagger is installed. Install it by running  `pip install locationtagger`

3. Configure the Google Cloud set up

    A. Install the [google cloud CLI](https://cloud.google.com/sdk/docs/install), by following the first two steps for your OS
    B. When prompted to enter google account details to access a project use the following. If you weren't prompted you can run this command gcloud auth application-default login

        email - nlpchatbotproject@gmail.com
        password - cs4395password
    select the only project listed under this account and that will complete the configuration of the google cloud
4. Run these 2 commands to install the final necessary libraries

    a. `pip install google-cloud-dialogflow`
    
    b. `python -m spacy download en_core_web_sm`

5. You can now run the chatbot by running the chatbot.py file

* If at any point, you are dealing with issues or unexpected behaviors while running or installing either of these options, please reach out!
