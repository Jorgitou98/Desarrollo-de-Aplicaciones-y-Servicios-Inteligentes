from spade.agent import Agent
from recommenderBehaviour import RecommenderBehaviour

class RecommenderAgent(Agent):

    async def setup(self):
        recommenderBehaviour = RecommenderBehaviour()
        self.add_behaviour(recommenderBehaviour)
