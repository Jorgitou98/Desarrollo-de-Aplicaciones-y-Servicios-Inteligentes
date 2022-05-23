import uuid
from google.cloud.dialogflowcx_v3beta1.services.agents import AgentsClient
from google.cloud.dialogflowcx_v3beta1.services.sessions import SessionsClient
from google.oauth2 import service_account
from spade.agent import Agent
from chatbotBehaviour import ChatbotBehaviour


class ChatbotAgent(Agent):

    """
    Constructor del agente Chatbot. A partir del fichero de credenciales crea la sesión
    con el agente Dialogflow.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Toma las credenciales a partir de un fichero externo
        credentials = service_account.Credentials.from_service_account_file("./Credentials/recomendador-peliculas-345318-0f1f75bf0b0d.json")
        projectID = "recomendador-peliculas-345318"
        locationID = "europe-west2"
        agentDialogflowID = "6632fe66-91f5-445e-b999-677e68270c7a"
        # Ruta del agente
        agentDialogflow = f"projects/{projectID}/locations/{locationID}/agents/{agentDialogflowID}"
        sessionID = uuid.uuid4()
        self._languageCode = "en-us"
        self._sessionPath = f"{agentDialogflow}/sessions/{sessionID}"
        agentComponents = AgentsClient.parse_agent_path(agentDialogflow)
        agentLocationID = agentComponents["location"]
        if agentLocationID != "global":
            api_endpoint = f"{agentLocationID}-dialogflow.googleapis.com:443"
            client_options = {"api_endpoint": api_endpoint}
        # Se crea la sesión como clientes
        self._sessionClient = SessionsClient(credentials=credentials, client_options=client_options)
        # Se marca como vacío el texto que inicialmente ha escrito el usuario en la GUI
        self.userText = None

    """
    Configura el Agente Chatbot. Crea y añade el comportamiento de este agente.

    :param self: objeto de la clase con el que se invoca.
    """  
    async def setup(self):
        chatbotBehaviour = ChatbotBehaviour()
        self.add_behaviour(chatbotBehaviour)

    """
    Método setter para añadir la interfaz gráfica asociada a la
    interacción de este agente con el usuario.

    :param self: objeto de la clase con el que se invoca.
    :param gui: objeto de la clase GUI que constituye la interfaz gráfica asociada al chatbot.
    """  
    def setGui(self, gui):
        self.gui = gui