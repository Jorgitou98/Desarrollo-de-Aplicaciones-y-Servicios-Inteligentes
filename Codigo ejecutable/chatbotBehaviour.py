from threading import Thread
from spade.behaviour import CyclicBehaviour
from google.cloud.dialogflowcx_v3beta1.types import session
from spade.message import Message
from asyncio import sleep
import json
import asyncio

class ChatbotBehaviour(CyclicBehaviour):

    async def run(self):
        while self.agent.userText is None:
            pass
        userText = self.agent.userText
        self.agent.userText = None
        response = self.__sendTextToAgentDialogflow(userText)
        actualPage = response.query_result.current_page.display_name
        if actualPage == "Give Recommendations":
            await self.__makeRecommendation(response.query_result.parameters)
            # Respondemos al agente Dialogflow para indicar que la recomendación se ha completado.
            # Nos devuelve el siguiente mensaje para el usuario.
            response = self.__sendTextToAgentDialogflow("completed")
        elif actualPage == "Add Rating":
            await self.__updateRatings(response.query_result.parameters)
            self.agent.gui.insert_message("Okay, thanks. I have saved your rating correctly.", "MovieBot")
            response = self.__sendTextToAgentDialogflow("completed")
        elif actualPage == "End Conversation":
            await asyncio.sleep(2)
            await self.agent.gui.quit()

        self.__printMovieResponse(response)


    def __sendTextToAgentDialogflow(self, userText):
        textAPIInput = session.TextInput(text=userText)
        query_input = session.QueryInput(text = textAPIInput, language_code=self.agent.languageCode)
        request = session.DetectIntentRequest(session=self.agent.sessionPath, query_input=query_input)
        return self.agent.sessionClient.detect_intent(request=request)


    async def __makeRecommendation(self, parameters):
        msg, parametersSend = self.__messageToRecommender(parameters)
        await self.send(msg)
        await sleep(0.2)
        msgRecommendations= await self.receive(timeout=10000)
        if not msgRecommendations:
            self.agent.gui.insert_message("There was an error calculating the recommendations", "MovieBot")
        else:
            recommendations = json.loads(msgRecommendations.body)
            self.__showReccommendation(recommendations, parametersSend)
    

    def __showReccommendation(self, recommendations, parametersSend):
            if "recommendationPopular" in recommendations:
                self.agent.gui.insert_message("I don't know if I'm recommending you well, you haven't rated any movie yet. I can recommend these popular movies:", "MovieBot")
                self.__showRecommendationList(recommendations["recommendationPopular"])

            elif "recommendationPopularWithGenre" in recommendations:
                self.agent.gui.insert_message("I don't know if I'm recommending you well, you haven't rated any movie yet. I can recommend these popular movies of {} genre:".format(parametersSend['genre']), "MovieBot")
                self.__showRecommendationList(recommendations["recommendationPopular"])

            elif "recommendContentBasedWithGenre" in recommendations:
                if recommendations["recommendContentBasedWithGenre"] != []:
                    self.agent.gui.insert_message("I think you might like these movies of the {} genre:".format(parametersSend['genre']), "MovieBot")
                    self.__showRecommendationList(recommendations["recommendContentBasedWithGenre"])
                    self.agent.gui.insert_message("Users similar to you also liked these {} movies:".format(parametersSend['genre']))
                    self.__showRecommendationList(recommendations["recommendCollabWithGenre"])
                else:
                    self.agent.gui.insert_message("I'm sorry, but I haven't found comedy movies in my catalog that you haven't seen yet")

                if "bestRecommendationNotGiven" in recommendations:
                    self.agent.gui.insert_message("Although they are not of the {} genre, I think you might like these other movies:".format(parametersSend['genre']), "MovieBot")
                    self.__showRecommendationList(recommendations["bestRecommendationNotGiven"])                        
            else:
                self.agent.gui.insert_message("Based on the content you liked I think you might also like:", "MovieBot")
                self.__showRecommendationList(recommendations["contentBasedRecommend"]) 

                self.agent.gui.insert_message("Depending on the content that other users similar to you like, I recommend:")
                self.__showRecommendationList(recommendations["collabRecommend"]) 


    def __messageToRecommender(self, parameters):
        parameters = dict(parameters)
        msg = Message(to="recomendador@xabber.de")
        # Es necesario introducir así las valores en un nuevo diccionario porque si no no son serializables
        if 'username' in parameters:
            parametersSend = {'username': parameters["username"]}
        elif 'newusername' in parameters:
            parametersSend = {'username': parameters["newusername"]}
        if 'genre' in parameters:
            parametersSend['genre'] = parameters["genre"]
        msg.body = json.dumps(parametersSend)
        return msg, parametersSend

    def __showRecommendationList(self, recommendationList):
        recommendationStr = ""
        for recommend in recommendationList:
            recommendationStr += "\t{}\n".format(recommend)
        self.agent.gui.insert_message(recommendationStr)

    async def __updateRatings(self, parameters):
        parameters = dict(parameters)
        msgName = Message(to="actualizador@xabber.de")

        # Es necesario introducir así las valores en un nuevo diccionario porque si no no son serializables
        parametersSend = {'username': parameters["username"], 'moviename': parameters["moviename"],
                            'rating': parameters["rating"]}

        # Construimos el JSON serializable que mandar al agente actualizador
        msgName.body = json.dumps(parametersSend)

        # Enviamos el mensaje (no necesitamos una respuesta del actualizador que nos haría esperar,
        # podemos seguir atentiendo al usuario)
        await self.send(msgName)
        await sleep(0.2)

    def __printMovieResponse(self, response):
            response_messages = [" ".join(msg.text.text) for msg in response.query_result.response_messages]
            self.agent.gui.insert_message(f"{' '.join(response_messages)}", "MovieBot")