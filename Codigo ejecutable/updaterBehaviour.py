from spade.behaviour import CyclicBehaviour
import json
import pickle
import pandas as pd
from surprise import SVD, Reader
from surprise import Dataset

class UpdaterBehaviour(CyclicBehaviour):


    async def run(self):
        # Esperamos para recibir un mensaje del agente chatbot los datos de la valoración hecha por el usuario
        # Es necesario poner un timeout (tiempo máximo de espera) porque un valor a None se entiende como sin espera. Lo
        # ponemos a 10000 segundos
        msgRating = await self.receive(timeout=10000)
        ratingInfo = json.loads(msgRating.body)

        # Si pasado ese tiempo no hemos recibido el mensaje, no saltamos el resto del comportamiento y volvemos a esperar el mensaje
        if not ratingInfo:
            return

        # Actualizamos el modelo basado en contenido (se encarga de actualizar la tabla de valoraciones)
        await self.__updateContentBasedModel(ratingInfo)

        # Actualizamos el modelo colaborativo (utiliza la tabla de valoraciones ya actualizada)
        await self.__updateUserCollaborativeModel()
        

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

        name = ratingInfo["username"]

        # En caso de que el usuario no esté en la tabla (puede ser nuevo), le añadimos con un identificador más que el máximo
        if name not in nameIDTable:
            nameIDTable[name] = max(nameIDTable.values()) + 1
            fileTable = open("nameIDTable.pkl", "wb")
            pickle.dump(nameIDTable, fileTable)
            fileTable.close()

        # Obtenemos el ID del usuario que valora la película a través de la tabla anterior
        userID = nameIDTable[name]

        return movieID, userID


    """ Función que actualiza el modelo colaborativo"""
    async def __updateUserCollaborativeModel(self):
        # Cargamos el dataset de valoraciones actualizado
        ratings = pd.read_csv('ratings_ordered.csv')
        # Transformamos los datos al formato en que espera recibirlos la libreria
        data = Dataset.load_from_df(ratings[['userId', 'movieId', 'rating']], Reader())
        # Creamos la intancia del objeto que realizará la factorización matricial
        collabModel = SVD()
        # Entrenamos el modelo con los datos
        data_train = data.build_full_trainset()
        collabModel.fit(data_train)
        # Actualizamos el modelo en el fichero "collabModel.pkl" para el recomendador
        fileTable = open("collabModel.pkl", "wb")
        pickle.dump(collabModel, fileTable)
        fileTable.close()
