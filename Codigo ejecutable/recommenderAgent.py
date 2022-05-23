from spade.agent import Agent
from recommenderBehaviour import RecommenderBehaviour

class RecommenderAgent(Agent):

    """
    Configura el Agente Recomendador. Crea y añade el comportamiento de este agente.

    :param self: objeto de la clase con el que se invoca.
    """  
    async def setup(self):
        recommenderBehaviour = RecommenderBehaviour()
        self.add_behaviour(recommenderBehaviour)
