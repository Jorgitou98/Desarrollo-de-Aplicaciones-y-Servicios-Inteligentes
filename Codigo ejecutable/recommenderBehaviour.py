from spade.behaviour import CyclicBehaviour
import numpy as np
import pandas as pd
import pickle
import time
from spade.message import Message
import json
class RecommenderBehaviour(CyclicBehaviour):

        async def run(self):
            # Esperamos para recibir un mensaje del agente chatbot con el nombre y quizás las preferencias de la recomendación
            # Es necesario poner un timeout (tiempo máximo de espera) porque un valor a None se entiende como sin espera. Lo
            # ponemos a 10000 segundos
            msgName = await self.receive(timeout=10000)
            userInfo = json.loads(msgName.body)

            # Si pasado ese tiempo no hemos recibido el mensaje, no saltamos el resto del comportamiento y volvemos a esperar el mensaje
            if not msgName:
                return

            # Cargamos las distintas tablas con la información necesaria para calcular las recomendaciones
            contentBasedModelIdx, ratingsOrdered, movieIDIndexTable, movieIDTitleTable = self.__loadTables(userInfo["username"])

            # Calculamos las recomendaciones para el usuario apoyandonos en las tablas cargadas
            recommendationResponse = self.__calculateRecommendations(userInfo, ratingsOrdered, contentBasedModelIdx, movieIDIndexTable, movieIDTitleTable)

############################################################################################################################            

            # # Si el usuario aún no ha alcanzado un pequeño número de valoraciones, es posible que las recomendaciones que le proporcionemos
            # # no sean muy buenas. Es conveniente detectar la situación para informarle de ello.
            # if sum(ratingsOrdered["userId"] == nameIDTable[name]) < 7:
            #     print("I have little information about you and the recommendations may not be very good. Cheer up to add ratings!")
############################################################################################################################
            msgRecommendations = Message(to="chatbot@xabber.de")
            msgRecommendations.body = json.dumps(recommendationResponse)
            await self.send(msgRecommendations)
            time.sleep(0.2)


        def __loadTables(self, name):
            # Cargamos la tabla que traduce de nombre de usuario a su identificador
            fileTable = open("nameIDTable.pkl", "rb")
            nameIDTable = pickle.load(fileTable)
            fileTable.close()

            # Cargamos el modelo Content Based que es una matriz Nx(N-1) donde la fila i-ésima contiene las N-1 peliculas distintas a la i
            # ordenadas según su similitud con la película i. Con mmap_mode='r' lo tratamos perezosamente (sin cargarlo entero en RAM) ya
            # solo querremos acceder a una de sus filas y es una matriz con miles de millones de elementos
            contentBasedModelIdx = np.load("contentBasedModel.npy", mmap_mode='r')

            # Cargamos las valoraciones de los usuarios que tenemos almacenadas, ordenadas de mayor a menor cada una de ellas
            ratingsOrdered = pd.read_csv("ratings_ordered.csv")

            # En caso de que el usuario no esté en la tabla (puede ser nuevo), le añadimos con un identificador más que el máximo
            if name not in nameIDTable:
                nameIDTable[name] = max(nameIDTable.values()) + 1
                fileTable = open("nameIDTable.pkl", "wb")
                pickle.dump(nameIDTable, fileTable)
                fileTable.close()
            
            # Solo necesitaremos las de nuestro usuario (notemos que nameIDTable[name] es el identificador de nuestro usuario)
            ratingsOrdered = ratingsOrdered[ratingsOrdered["userId"] == nameIDTable[name]]

            # Cargamos la tabla que, dado un id de película, proporciona su posición en los arrays de recomendación
            fileTable = open("movieIDIndexTable.pkl", "rb")
            movieIDIndexTable = pickle.load(fileTable)
            fileTable.close()

            # Cargamos la tabla que traduce de identificador de película a su título (devolveremos los títulos de las películas recomendadas)
            fileTable = open("movieIDTitleTable.pkl", "rb")
            movieIDTitleTable = pickle.load(fileTable)
            fileTable.close()

            return contentBasedModelIdx, ratingsOrdered, movieIDIndexTable, movieIDTitleTable




        def __calculateRecommendations(self, userInfo, ratingsOrdered, contentBasedModelIdx, movieIDIndexTable, movieIDTitleTable):
            # Si se trata de un usuario sin ninguna valoración, devolvemos una recomendación especial (no se basa en su perfil) 
            if ratingsOrdered.size == 0:
                return self.__recommendUserWithoutRatings(userInfo)

            # Si no hay ninguna preferencia en cuanto al género de la película
            if "genre" not in userInfo or userInfo["genre"] is None:
                return self.__calculateRecommendationsWithoutGenre(ratingsOrdered, contentBasedModelIdx, movieIDIndexTable, movieIDTitleTable)

            # En caso de que tenga valoraciones y haya preferencias en el género de la película
            return self.__calculateRecommendationsWithGenre(userInfo, ratingsOrdered, contentBasedModelIdx, movieIDIndexTable, movieIDTitleTable)
            
            

        def __calculateRecommendationsWithoutGenre(self, ratingsOrdered, contentBasedModelIdx, movieIDIndexTable, movieIDTitleTable):
            # Tomamos las películas valoradas por el usuario con al menos un 4
            favMovies = ratingsOrdered[ratingsOrdered["rating"] >= 4][:1]["movieId"].values
            
            # Elegimos aleatoriamente una película de entre las 5 mejor valoradas por el usuario.
            favMovie = ratingsOrdered[:5]["movieId"].sample(n=1).values[0] if favMovies.size == 0 else favMovies[0]

            # Recuperamos la lista ordenada con las películas más similares a la favorita, según su contenido (director, actores, palabra clave, género)
            # favMovie es el id de la película favorita y movieIDIndexTable[favMovie] es la posición que ocupa en los arrays de recomendaciones
            recommendationOrder = contentBasedModelIdx[movieIDIndexTable[favMovie]]

            # Quitamos de las recomendaciones aquellas películas que el usuario ya haya valorado (si las ha visto no tiene sentido recomendarselas)
            recommendationOrder = recommendationOrder[~np.in1d(recommendationOrder, ratingsOrdered["movieId"].values)]

            # Devolvemos la información de las recomendaciones solo basadas en contenido
            return {"onlyContentRecommendation": list(map(lambda id: movieIDTitleTable[id], recommendationOrder[:5]))}


        def __calculateRecommendationsWithGenre(self, userInfo, ratingsOrdered, contentBasedModelIdx, movieIDIndexTable, movieIDTitleTable):
            recommendationResponse = {}
            # Calculamos los IDs de películas que son del género solicitado por el usuario (userInfo["genre"] es el género indicado por el usuario)
            movieClean = pd.read_csv("movies_catalog_clean.csv")
            genreMovies = movieClean["id"][movieClean["genres"].apply(lambda l: userInfo["genre"] in l)]

            # Cogemos el ID de la película mejor valorada por el usuario que pertenezca al género que nos ha pedido,
            # exigiendo que sea de al menos un 4 de puntuación.
            favMovies = ratingsOrdered[np.isin(ratingsOrdered["movieId"], genreMovies) & (ratingsOrdered["rating"] >= 4)][:1]["movieId"].values
            
            # Si no habia ninguna película valorada por el usuario de ese género con al menos un 4,
            # elegimos aleatoriamente una de entre las 5 mejor valoradas por dicho usuario.
            favMovie = ratingsOrdered[:5]["movieId"].sample(n=1).values[0] if favMovies.size == 0 else favMovies[0]

            # Recuperamos la lista ordenada con las películas más similares a la favorita, según su contenido.
            # Notemos que movieIDIndexTable[favMovie] es la posición que ocupa la película favorita en los arrays de recomendaciones
            recommendationOrder = contentBasedModelIdx[movieIDIndexTable[favMovie]]

            # Quitamos de las recomendaciones aquellas películas que el usuario ya haya valorado (si ya las ha visto no tiene sentido recomendárselas)
            recommendationOrder = recommendationOrder[~np.in1d(recommendationOrder, ratingsOrdered["movieId"].values)]

            # Preservando el orden de las recomendaciones recuperadas, tomamos las recomendaciones que estén en los índices que cumplen
            # las preferencias de género dadas por el usuario
            recommendationWithPreferences = recommendationOrder[np.isin(recommendationOrder, genreMovies)][:5]

            recommendationResponse["recommendationWithGenre"] = list(map(lambda id: movieIDTitleTable[id], recommendationWithPreferences))
    
            # En caso de que alguna de las 5 mejores recomendaciones no haya sido dada por no cumplir las preferencias
            # se la sugeriremos también, pero indicandole que no pertenece al género que nos pidió
            bestRecommendation = recommendationOrder[:5]
            bestRecommendationNotGiven = bestRecommendation[np.logical_not(np.isin(bestRecommendation, genreMovies))]

            # Si entre las mejores recomendaciones hay algunas que no hemos dado por motivos de género
            if bestRecommendationNotGiven.size > 0:
                # Las añadimos con la correspondiente clave al diccionario
                recommendationResponse["bestRecommendationNotGiven"] = list(map(lambda id: movieIDTitleTable[id], bestRecommendationNotGiven))

            return recommendationResponse

        """ Método para recomendar películas a usuarios de los que no han hecho aún ninguna valoración, simplemente por popularidad."""
        def __recommendUserWithoutRatings(self, userInfo):
            # Cargamos las películas del catálogo
            movieClean = pd.read_csv("movies_catalog_clean.csv")
           
            # Ordenamos las películas según su número de votos para tenerlas en orden decreciende te popularidad
            popularMovies = movieClean[["title","vote_count"]].sort_values(by=["vote_count"], ascending=False)["title"]#[:5].to_list()
           
            # Si no hay restricción de género
            if ("genre" not in userInfo) or (userInfo["genre"] is None):
                # Devolvemos como recomendación las 5 más populares
                return {"recommendationPopular": popularMovies[:5].to_list()}

            # Si hay alguna restricción de género, filtramos por las que sean de ese género
            popularMovies = popularMovies[popularMovies["genres"].apply(lambda l: userInfo["genre"] in l)]

            # Devolvemos las más populares que sean de ese género
            return {"recommendationPopularWithGenre": popularMovies[:5].to_list()}