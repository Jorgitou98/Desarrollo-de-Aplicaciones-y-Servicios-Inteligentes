from chatbotAgent import ChatbotAgent
from recommenderAgent import RecommenderAgent
from updaterAgent import UpdaterAgent
import time
from gui import ChatApplication

if __name__ == "__main__":
    gui = ChatApplication()
    gui.insert_message("Hi, welcome to your movie recommender.", "MovieBot")
    gui.run()

    # recommenderAgent = RecommenderAgent("recomendador@xabber.de", "recomendador")
    # future = recommenderAgent.start()
    # future.result()

    # updaterAgent = UpdaterAgent("actualizador@xabber.de", "actualizador")
    # future = updaterAgent.start()
    # future.result()
    

    # chatbotAgent = ChatbotAgent("chatbot@xabber.de", "chatbot")
    # future = chatbotAgent.start()
    # future.result()


    # while chatbotAgent.is_alive() and updaterAgent.is_alive and recommenderAgent.is_alive :
    #     try:
    #         time.sleep(1)
    #     except KeyboardInterrupt:
    #         chatbotAgent.stop()
    #         updaterAgent.stop()
    #         recommenderAgent.stop()
    #         break