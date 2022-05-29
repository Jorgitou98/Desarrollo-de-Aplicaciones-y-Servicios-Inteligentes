from threading import Thread
from spade.behaviour import CyclicBehaviour
from google.cloud.dialogflowcx_v3beta1.types import session
from spade.message import Message
from asyncio import sleep
import json
import asyncio

class ChatbotBehaviour(CyclicBehaviour):

    """
    Constituye un ciclo del comportamiento que repite el Agente Chatbot.
    Cuando hay texto del usuario, se envía al Agente Dialogflow. Si la
    respuesta es del estado "Give Recommendations" se llama a la función
    "makeRecommendation" para hacer una recomendación, si es "Add Rating"
    a la función "updateRatings" para actualizar las valoraciones,
    si es "End Conversation" se esperan unos segundos y se elimina la 
    interfaz gráfica finalizando con ello la ejecución. En cualquier caso,
    al final se muestra la respuesta recibida para el usuario.

    :param self: objeto de la clase con el que se invoca.
    """  
    async def run(self):
        # Mientras no haya texto nuevo del usuario.
        while self.agent.userText is None:
            pass
        # Nos guardamos el texto y limpiamos su valor para la siguiente frase.
        userText = self.agent.userText
        self.agent.userText = None
        # Enviamos el texto del usuario al agente de Dialogflow y almacenamos la respuesta.
        response = self.__sendTextToAgentDialogflow(userText)
        actualPage = response.query_result.current_page.display_name
        # Si el estado actual es el de dar recomendaciones
        if actualPage == "Give Recommendations":
            # Hacemos una recomendación de películas
            await self.__makeRecommendation(response.query_result.parameters)
            # Respondemos al agente Dialogflow para indicar que la recomendación se ha completado.
            response = self.__sendTextToAgentDialogflow("completed")
        # Si el estado actual es el de añadir una valoración
        elif actualPage == "Add Rating":
            # Hacemos la actualización de valoraciones
            await self.__updateRatings(response.query_result.parameters)
            # Informamos al usuario de que ya está guardada su valoración.
            self.agent.gui.insertMessage("Okay, thanks. I have saved your rating correctly.", "MovieBot")
            # Respondemos al agente Dialogflow para indicar que la recomendación se ha completado.
            response = self.__sendTextToAgentDialogflow("completed")
        # Si el estado es el de que la conversación ha terminado
        elif actualPage == "End Conversation":
            # Mostramos el mensaje de despedida con el usuario.
            self.__printMovieResponse(response)
            # Esperamos unos segundos para que el usuario lea el mensaje de despedida.
            await asyncio.sleep(2)
            # Cerramos la GUI y con ello finalizamos la ejecución del sistema.
            await self.agent.gui.quit()
        # Mostramos la respuesta que recibimos para el usuario.
        self.__printMovieResponse(response)


    """
    Envía una frase del usuario al Agente Dialogflow y devuelve la información de la
    conversación tras esa frase.

    :param self: objeto de la clase con el que se invoca.
    :param userText: frase del usuario que se envía al Agente Dialogflow.
    :returns: información de la conversación tras la frase del usuario.
    """  
    def __sendTextToAgentDialogflow(self, userText):
        # Creamos un objeto con la entrada de texto.
        textAPIInput = session.TextInput(text=userText)
        # A partir del objeto anterior, creamos una query.
        query_input = session.QueryInput(text = textAPIInput, language_code=self.agent._languageCode)
        # Creamos una petición a partir de la query y la ruta de la sesión.
        request = session.DetectIntentRequest(session=self.agent._sessionPath, query_input=query_input)
        # Devolvemos la respuesta obtenida para la petición a través de la sesión cliente
        return self.agent._sessionClient.detect_intent(request=request)


    """
    Envía un mensaje al Agente Recomendador con los parámetros necesarios para
    la recomendación. Resibe de este agente la respuesta con las películas a 
    recomendar y se las muestra al usuario en la GUI.

    :param self: objeto de la clase con el que se invoca.
    :param parameters: parámetros de la conversación actual (valor de las entidades reconocidas).
    """  
    async def __makeRecommendation(self, parameters):
        # Preparamos el mensaje a enviar para el Agente Recomendador.
        msg, parametersSend = self.__messageToRecommender(parameters)
        # Enviamos el mensaje al Agente Recomendador.
        await self.send(msg)
        await sleep(0.2)
        # Resibimos la respuesta
        msgRecommendations= await self.receive(timeout=10000)
        # Si el mensaje de respuesta no es correcto.
        if not msgRecommendations:
            # Mostramos un mensaje de error al usuario.
            self.agent.gui.insertMessage("There was an error calculating the recommendations", "MovieBot")
        # Si es correcto.
        else:
            # Lo cargamos como objeto json.
            recommendations = json.loads(msgRecommendations.body)
            # Mostramos las recomendaciones al usuario.
            self.__showReccommendation(recommendations, parametersSend)
    
    """
    Muestra las recomendaciones obtenidas para un usuario, teniendo en cuenta
    de qué tipo son (sin restricción de género, con restricción de género, 
    procedentes del modelo basado en contenido, procedentes del modelo
    colaborativo, para un usuario sin valoraciones previas).

    :param self: objeto de la clase con el que se invoca.
    :param recommendations: diccionario con las listas de recomendaciones recibidas.
    :param parametersSend: parametros para la recomendación enviados al Agente Recomendador
    """  
    def __showReccommendation(self, recommendations, parametersSend):
        # Si es una recomendación por popularidad (el usuario no tenía valoraciones en el sistema)
        if "recommendationPopular" in recommendations:
            # Se indica al usuario que la recomendación no es personalizada al no tener valoraciones.
            # Son solo películas populares.
            self.agent.gui.insertMessage("I don't know if I'm recommending you well, you haven't rated any movie yet. I can recommend these popular movies:", "MovieBot")
            # Se muestra la lista de recomendaciones correspondiente.
            self.__showRecommendationList(recommendations["recommendationPopular"])
            
            # Si es una recomendación por popularidad (el usuario no tenía valoraciones en el sistema) con restricción del género.
        elif "recommendationPopularWithGenre" in recommendations:
            # Se indica al usuario que la recomendación no es personalizada al no tener valoraciones.
            # Se le indica que se le recomiendan las siguientes películas de ese género en concreto.
            self.agent.gui.insertMessage("I don't know if I'm recommending you well, you haven't rated any movie yet. I can recommend these popular movies of {} genre:".format(parametersSend['genre']), "MovieBot")
            # Se muestra la lista de recomendaciones correspondiente.
            self.__showRecommendationList(recommendations["recommendationPopularWithGenre"])

        # Si es una recomendación con restricción de género.
        elif "recommendContentBasedWithGenre" in recommendations:
            # Si hemos conseguido obtener películas a recomendar que cumplan con las restriccions.
            if len(recommendations["recommendContentBasedWithGenre"]) > 0:
                # Proporcionamos la recomendación del modelo basado en contenido.
                self.agent.gui.insertMessage("I think you might like these movies of the {} genre:".format(parametersSend['genre']), "MovieBot")
                self.__showRecommendationList(recommendations["recommendContentBasedWithGenre"])
                # Proporcionamos la recomendación del modelo colaborativo.
                self.agent.gui.insertMessage("Users similar to you also liked these {} movies:".format(parametersSend['genre']))
                self.__showRecommendationList(recommendations["recommendCollabWithGenre"])
            # Si no conseguimos encontrar películas a recomendar del género solicitado.
            else:
                # Se indica al usuario que es porque ya ha valorado todas las películas de ese género
                # que hay en el catálogo.
                self.agent.gui.insertMessage("I'm sorry, but I haven't found comedy movies in my catalog that you haven't seen yet")

            # Si existen recomendaciones muy buenas que no se han dado porque son de otro género,
            # se muestran también indicándole al usuario que no son del género que solicitó
            if "bestRecommendationNotGiven" in recommendations:
                self.agent.gui.insertMessage("Although they are not of the {} genre, I think you might like these other movies:".format(parametersSend['genre']))
                self.__showRecommendationList(recommendations["bestRecommendationNotGiven"]) 

        # Si las recomendaciones son sin rectricción de género                      
        else:
            # Proporcionamos la recomendación del modelo basado en contenido.
            self.agent.gui.insertMessage("Based on the content you liked I think you might also like:", "MovieBot")
            self.__showRecommendationList(recommendations["contentBasedRecommend"]) 

            # Proporcionamos la recomendación del modelo colaborativo.  
            self.agent.gui.insertMessage("Depending on the content that other users similar to you like, I recommend:")
            self.__showRecommendationList(recommendations["collabRecommend"]) 

    """
    Prepara el mensaje del Agente Chatbot para el Agente Recomendador,
    tranformando los parámetros para que sean serializables y se puedan
    enviar por la red.

    :param self: objeto de la clase con el que se invoca.
    :param parameters: parámetros de la conversación actual (valor de las entidades reconocidas).
    :returns: mensaje preparado para anviar y los parametros en el formato serializable.
    """  
    def __messageToRecommender(self, parameters):
        # Para empezar convertimos a diccionario python los parámetros.
        parameters = dict(parameters)
        # Preparamos un mensaje para el Agente Recomendador.
        msg = Message(to="recomendador@xabber.de")
        # Creamos un nuevo diccionario accediendo a los distintos campos de los parámetros
        # si es que están presentes, porque el objeto parameters no es serializable si no.
        if 'username' in parameters:
            parametersSend = {'username': parameters["username"]}
        elif 'newusername' in parameters:
            parametersSend = {'username': parameters["newusername"]}
        if 'genre' in parameters:
            parametersSend['genre'] = parameters["genre"]
        # Colocamos los parámetros como cuerpo del mensaje.
        msg.body = json.dumps(parametersSend)
        # Devolemos el mensaje y los parámetros en formato serializable.
        return msg, parametersSend

    """
    Muestra una lista de valores de películas a recomendar para el usuario.

    :param self: objeto de la clase con el que se invoca.
    :param recommendationList: lista de recomendaciones a mostrar al usuario.
    """ 
    def __showRecommendationList(self, recommendationList):
        # Construimos la cadena con los valores tabulados y separamos por líneas.
        recommendationStr = ""
        for recommend in recommendationList:
            recommendationStr += "\t{}\n".format(recommend)
        # Escribimos la cadena en la GUI.
        self.agent.gui.insertMessage(recommendationStr)

    """
    Envía una mensaje al Agente Actualizador con la información correspondiente
    a una valoración de contenido.

    :param self: objeto de la clase con el que se invoca.
    :param parameters: parámetros de la conversación actual (valor de las entidades reconocidas).
    """ 
    async def __updateRatings(self, parameters):
        # Para empezar convertimos a diccionario python los parámetros.
        parameters = dict(parameters)
        # Preparamos un mensaje para el Agente Actualizador.
        msgName = Message(to="actualizador@xabber.de")

        # Creamos un diccionario con el nombre de usuario, el título de la película valorada
        # y la puntuación otorgada.
        parametersSend = {'username': parameters["username"], 'moviename': parameters["moviename"],
                            'rating': parameters["rating"]}

        # Construimos el json serializable que mandar al agente actualizador
        msgName.body = json.dumps(parametersSend)

        # Enviamos el mensaje
        await self.send(msgName)
        await sleep(0.2)

        # Esperamos hasta recibir la confirmación de que la valoración se ha añadido al sistema y todo ha sido actualizado
        await self.receive(timeout=10000)

    """
    Muestra al usuario por la GUI la frase de respuesta contenida en una repuesta del Agente Dialogflow.

    :param self: objeto de la clase con el que se invoca.
    :param response: respuesta obtenida del Agente Dialogflow.
    """ 
    def __printMovieResponse(self, response):
            # Creamos la cadena con las frases de respuestas del Agente Dialogflow.
            response_messages = [" ".join(msg.text.text) for msg in response.query_result.response_messages]
            # Mostramos la cadena por la GUI
            self.agent.gui.insertMessage(f"{' '.join(response_messages)}", "MovieBot")