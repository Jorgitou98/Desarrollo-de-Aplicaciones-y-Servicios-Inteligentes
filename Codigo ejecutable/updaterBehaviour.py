from spade.behaviour import CyclicBehaviour
import json
import pickle
import pandas as pd
import numpy as np
from surprise import SVD, Reader
from surprise import Dataset
from spade.message import Message
from asyncio import sleep

class UpdaterBehaviour(CyclicBehaviour):

    """
    Constituye un ciclo del comportamiento que repite el Agente Actualizador.
    Recibe un mensaje del Agente Chatbot con los parámetros necesarios para añadir
    una nueva valoración y actualizar correspondientemente los dos modelos de recomendación.

    :param self: objeto de la clase con el que se invoca.
    """  
    async def run(self):
        # Esperamos para recibir un mensaje del agente chatbot los datos de la valoración hecha por el usuario
        # Es necesario poner un timeout (tiempo máximo de espera) porque un valor a None se entiende como sin espera. Lo
        # ponemos a 10000 segundos
        msgRating = await self.receive(timeout=10000)
        ratingInfo = json.loads(msgRating.body)

        # Si pasado ese tiempo no hemos recibido el mensaje, no saltamos el resto del comportamiento y volvemos a esperar el mensaje
        if not ratingInfo:
            return

        # Cargamos los datos de valoraciones en el sistema
        ratingsOrdered = pd.read_csv("utils/ratings_ordered.csv")

        # Cargamos el identificador de película y usuario correspondientes a la valoración recibida.
        movieID, userID = self.__getUserAndMovieID(ratingInfo)

        # Actualizamos el modelo basado en contenido (se encarga de actualizar la tabla de valoraciones)
        await self.__updateContentBasedModel(ratingInfo, ratingsOrdered, userID, movieID)

        # Actualizamos el modelo colaborativo (utiliza la tabla de valoraciones ya actualizada)
        await self.__updateUserCollaborativeModel()

        # Avisamos al chatbot de que la valoración se ha añadido correctamente y el sistema se ha actualizado
        await self.send(Message(to="chatbot@xabber.de"))
        await sleep(0.2)

        

        
    """
    Actualiza la tabla de valoraciones con la nueva valoración que recibe por parte del usuario
    y recalcula el modelo basado en contenido ordenando. En caso de que ese usuario ya hubiese
    valorado esa película no se añade una nueva valoración sino que se modifica.

    :param self: objeto de la clase con el que se invoca.
    :param ratingInfo: diccionario con la información de la valoración recibida para añadir.
    :param ratingsOrdered: Dataframe con las valoraciones en el sistema ordenadas para cada usuario.
    :param userID: ID del usuario que hace la valoración.
    :param movieID: ID de la película que se valora.
    """  
    async def __updateContentBasedModel(self, ratingInfo, ratingsOrdered, userID, movieID):

        # Array de booleanos de valoración de esa película por parte del usuario
        previousRatings = np.logical_and(ratingsOrdered["userId"] == userID, ratingsOrdered["movieId"] == movieID)
        
        # Si el usuario ya valoró esa película anteriormente
        if np.sum(previousRatings) > 0:
           # Modificamos la valoración, no añadimos una nueva
            ratingsOrdered.loc[previousRatings, "rating"] = ratingInfo["rating"]

        else:
            newRatingDF = {"userId": userID, "rating": ratingInfo["rating"], "movieId": movieID}
            # Insertamos la valoración
            ratingsOrdered = ratingsOrdered.append(newRatingDF, ignore_index = True)

        # Ordenamos
        ratingsOrdered = ratingsOrdered.sort_values(by=['userId', 'rating'], ascending=False)

        # Almacenamos las nuevas valoraciones (ya con la que acabamos de añadir)
        ratingsOrdered.to_csv("utils/ratings_ordered.csv", index=False)


    """
    Reeentrena y sobreescribe el modelo colaborativo con la información sobre
    valoraciones actual.

    :param self: objeto de la clase con el que se invoca.
    """  
    async def __updateUserCollaborativeModel(self):
        # Cargamos el dataset de valoraciones actualizado
        ratings = pd.read_csv('utils/ratings_ordered.csv')
        # Transformamos los datos al formato en que espera recibirlos la libreria
        data = Dataset.load_from_df(ratings[['userId', 'movieId', 'rating']], Reader())
        # Creamos la intancia del objeto que realizará la factorización matricial
        collabModel = SVD()
        # Entrenamos el modelo con los datos
        data_train = data.build_full_trainset()
        collabModel.fit(data_train)
        # Actualizamos el modelo en el fichero "collabModel.pkl" para el recomendador
        fileTable = open("utils/collabModel.pkl", "wb")
        pickle.dump(collabModel, fileTable)
        fileTable.close()

    """
    Dada la información de la valoración proporcionada por el chatbot
    (nombre del usuario, título de la película valorada y la puntuación),
    devuelve el ID del usuario y de la película.

    :param self: objeto de la clase con el que se invoca.
    :param ratingInfo: diccionario con la información de la valoración proporcionada por el chatbot.
    :returns: ID del usuario e ID de la película valorada.
    """  
    def __getUserAndMovieID(self, ratingInfo):
            # Cargamos la tabla que dado un nombre de usuario nos devuelve su ID
            fileTable = open("utils/movieTitleIDTable.pkl", "rb")
            movieTitleIDTable = pickle.load(fileTable)
            fileTable.close()

            # Cargamos la tabla que traduce de nombre de usuario a su ID
            fileTable = open("utils/nameIDTable.pkl", "rb")
            nameIDTable = pickle.load(fileTable)
            fileTable.close()

            # Obtenemos el ID de la película valorada a través de la tabla anterior
            movieID = movieTitleIDTable[ratingInfo["moviename"]]

            name = ratingInfo["username"]

            # En caso de que el usuario no esté en la tabla (puede ser nuevo), le añadimos con un identificador más que el máximo
            if name not in nameIDTable:
                nameIDTable[name] = max(nameIDTable.values()) + 1
                fileTable = open("utils/nameIDTable.pkl", "wb")
                pickle.dump(nameIDTable, fileTable)
                fileTable.close()

            # Obtenemos el ID del usuario que valora la película a través de la tabla anterior
            userID = nameIDTable[name]

            return movieID, userID