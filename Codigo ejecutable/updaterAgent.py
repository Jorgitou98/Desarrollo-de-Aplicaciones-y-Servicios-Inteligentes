from spade.agent import Agent
from updaterBehaviour import UpdaterBehaviour

class UpdaterAgent(Agent):

    """
    Configura el Agente Actualizador. Crea y añade el comportamiento de este agente.

    :param self: objeto de la clase con el que se invoca.
    """  
    async def setup(self):
        updaterBehaviour = UpdaterBehaviour()
        self.add_behaviour(updaterBehaviour)
