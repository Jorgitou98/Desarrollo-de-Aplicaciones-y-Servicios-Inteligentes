from spade.agent import Agent
from updaterBehaviour import UpdaterBehaviour

class UpdaterAgent(Agent):

    async def setup(self):
        updaterBehaviour = UpdaterBehaviour()
        self.add_behaviour(updaterBehaviour)
