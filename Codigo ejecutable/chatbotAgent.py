import uuid
from google.cloud.dialogflowcx_v3beta1.services.agents import AgentsClient
from google.cloud.dialogflowcx_v3beta1.services.sessions import SessionsClient
from google.oauth2 import service_account
from spade.agent import Agent
from chatbotBehaviour import ChatbotBehaviour



class ChatbotAgent(Agent):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        credentials = service_account.Credentials.from_service_account_file("./recomendador-peliculas-345318-0f1f75bf0b0d.json")
        projectID = "recomendador-peliculas-345318"
        locationID = "europe-west2"
        agentDialogflowID = "6632fe66-91f5-445e-b999-677e68270c7a"
        agentDialogflow = f"projects/{projectID}/locations/{locationID}/agents/{agentDialogflowID}"
        sessionID = uuid.uuid4()
        self.languageCode = "en-us"
        self.sessionPath = f"{agentDialogflow}/sessions/{sessionID}"
        #print(f"Session path: {self.sessionPath}\n")
        #detect_intent_texts(agent, session_id, texts, language_code)
        agentComponents = AgentsClient.parse_agent_path(agentDialogflow)
        agentLocationID = agentComponents["location"]
        if agentLocationID != "global":
            api_endpoint = f"{agentLocationID}-dialogflow.googleapis.com:443"
            #print(f"API Endpoint: {api_endpoint}\n")
            client_options = {"api_endpoint": api_endpoint}
        self.sessionClient = SessionsClient(credentials=credentials, client_options=client_options)
        #self.detect_intent_texts(sessionClient, sessionPath, language_code)

    async def setup(self):
        print("MovieBot> Hi, welcome to your movie recommender.\n")
        chatbotBehaviour = ChatbotBehaviour()
        self.add_behaviour(chatbotBehaviour)
