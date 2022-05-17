from spade.behaviour import CyclicBehaviour
from google.cloud.dialogflowcx_v3beta1.types import session
from spade.message import Message
from asyncio import sleep
import json



class ChatbotBehaviour(CyclicBehaviour):

        async def run(self):
            try:
                userText = input("User> ")
                print()
                response = self.__sendTextToAgentDialogflow(userText)
                actualPage = response.query_result.current_page.display_name
                if actualPage == "Give Recommendations":
                    await self.__makeRecommendation(response.query_result.parameters)
                    # Respondemos al agente Dialogflow para indicar que la recomendación se ha completado.
                    # Nos devuelve el siguiente mensaje para el usuario.
                    response = self.__sendTextToAgentDialogflow("completed")
                elif actualPage == "Add Rating":
                    await self.__updateRatings(response.query_result.parameters)
                    print(f"MovieBot> Okay, thanks. I have saved your rating correctly.\n")
                    response = self.__sendTextToAgentDialogflow("completed")
                elif actualPage == "End Conversation":
                    await self.agent.stop()

                self.__printMovieResponse(response)

            except:
                pass

        def __sendTextToAgentDialogflow(self, userText):
            textAPIInput = session.TextInput(text=userText)
            query_input = session.QueryInput(text = textAPIInput, language_code=self.agent.languageCode)
            request = session.DetectIntentRequest(session=self.agent.sessionPath, query_input=query_input)
            # Devolvemos la respuesta del agente al usuario
            return self.agent.sessionClient.detect_intent(request=request)


        async def __makeRecommendation(self, parameters):
            msg, parametersSend = self.__messageToRecommender(parameters)
            await self.send(msg)
            await sleep(0.2)
            msgRecommendations= await self.receive(timeout=10000)
            if not msgRecommendations:
                print("MovieBot> There was an error calculating the recommendations\n")
            else:
                recommendations = json.loads(msgRecommendations.body)
                self.__showReccommendation(recommendations, parametersSend)
     

        def __showReccommendation(self, recommendations, parametersSend):
                if "recommendationPopular" in recommendations:
                    print("MovieBot> I don't know if I'm recommending you well, you haven't rated any movie yet. I can recommend these popular movies:\n")
                    self.__showRecommendationList(recommendations["recommendationPopular"])

                elif "recommendationPopularWithGenre" in recommendations:
                    print("MovieBot> I don't know if I'm recommending you well, you haven't rated any movie yet. I can recommend these popular movies of {} genre:\n".format(parametersSend['genre']))
                    self.__showRecommendationList(recommendations["recommendationPopular"])

                elif "recommendationWithGenre" in recommendations:
                    if recommendations["recommendationWithGenre"] != []:
                        print("MovieBot> I think you might like these movies of the {} genre:\n".format(parametersSend['genre']))
                        self.__showRecommendationList(recommendations["recommendationWithGenre"])
                    else:
                        print("MovieBot> I'm sorry, but I haven't found comedy movies in my catalog that you haven't seen yet\n")

                    if "bestRecommendationNotGiven" in recommendations:
                        print("Although they are not of the {} genre, I think you might like these other movies:\n".format(parametersSend['genre']))
                        self.__showRecommendationList(recommendations["bestRecommendationNotGiven"])                        
                else:
                    print("MovieBot> Based on the content you liked I think you might also like:\n")
                    self.__showRecommendationList(recommendations["onlyContentRecommendation"]) 


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
            for recommend in recommendationList:
                print("\t{}".format(recommend))
            print()

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
                print(f"MovieBot> {' '.join(response_messages)}\n")


