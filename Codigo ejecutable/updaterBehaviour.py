from spade.behaviour import CyclicBehaviour
import json
import pickle
import pandas as pd

class UpdaterBehaviour(CyclicBehaviour):

    # Establecemos un atributo de clase Python con el threshold de valoraciones mínimo para realicar una actualización
    thresholdUpdate = 10

    async def run(self):
        # Esperamos para recibir un mensaje del agente chatbot los datos de la valoración hecha por el usuario
        # Es necesario poner un timeout (tiempo máximo de espera) porque un valor a None se entiende como sin espera. Lo
        # ponemos a 10000 segundos
        msgRating = await self.receive(timeout=10000)
        ratingInfo = json.loads(msgRating.body)

        # Si pasado ese tiempo no hemos recibido el mensaje, no saltamos el resto del comportamiento y volvemos a esperar el mensaje
        if not ratingInfo:
            return

        await self.__updateContentBasedModel(ratingInfo)

        ## Esta parte del código se utilizará cuando introduzcamos el modelo colaborativo,
        ## por ahora la dejamos comentada, aunque ya preparada
        # filePending = open("ratingsPending.pkl", "rb")
        # ratingsPending = pickle.load(filePending)
        # filePending.close()
        # # Añadimos la valoración a las pendientes de actualizarse
        # ratingsPending.append(ratingInfo)

        # # Si ya hemos alcanzado el mínimo de valoraciones para actualizar los modelos
        # if len(ratingsPending) >= self.thresholdUpdate:
        #     # Realizamos la actualización de los modelos
        #     await self.__updateUserCollaborativeModel(ratingsPending)
        #     # Dejamos de tener valoraciones pendientes de actualizar
        #     ratingsPending = []

        # #Escribimos en el fichero guardando la nueva lista de valoraciones pendientes
        # filePending = open("ratingsPending.pkl", "wb")
        # pickle.dump(ratingsPending, filePending)
        # filePending.close()

    async def __updateContentBasedModel(self, ratingInfo):
        ratingsOrdered = pd.read_csv("ratings_ordered.csv")

        movieID, userID = self.__getUserAndMovieID(ratingInfo)

        # Si el usuario ya valoró esa película anteriormente
        # if ratingsOrdered[ratingsOrdered["userId"] == userID & ratingsOrdered["movieId"] == movieID].size > 0:
        #     #Modificamos la valoración, no añadimos una nueva
        #     ratingsOrdered[ratingsOrdered["userId"] == userID & ratingsOrdered["movieId"] == movieID]["rating"] = ratingInfo["rating"]
        #     return
    
        # Insertamos la valoración ordenada
        newRatingDF = {"userId": userID, "rating": ratingInfo["rating"], "movieId": movieID}

        ratingsOrdered = ratingsOrdered.append(newRatingDF, ignore_index = True)
        ratingsOrdered = ratingsOrdered.sort_values(by=['userId', 'rating'], ascending=False)
        # Almacenamos las nuevas valoraciones (ya con la que acabamos de añadir)
        ratingsOrdered.to_csv("ratings_ordered.csv", index=False)

    def __getUserAndMovieID(self, ratingInfo):
        # Cargamos la tabla que dado un nombre de usuario nos devuelve su ID
        fileTable = open("movieTitleIDTable.pkl", "rb")
        movieTitleIDTable = pickle.load(fileTable)
        fileTable.close()

        # Cargamos la tabla que traduce de nombre de usuario a su ID
        fileTable = open("nameIDTable.pkl", "rb")
        nameIDTable = pickle.load(fileTable)
        fileTable.close()

        # Obtenemos el ID de la película valorada a través de la tabla anterior
        movieID = movieTitleIDTable[ratingInfo["moviename"]]

        # Obtenemos el ID del usuario que valora la película a través de la tabla anterior
        userID = nameIDTable[ratingInfo["username"]]

        return movieID, userID


    """ Función que actualiza el modelo colaborativo, aún por implementar"""
    async def __updateUserCollaborativeModel(self, ratingsPending):
        pass

