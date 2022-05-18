from tkinter import *
from chatbotAgent import ChatbotAgent
from recommenderAgent import RecommenderAgent
from updaterAgent import UpdaterAgent

BG_GRAY = "#ABB2B9"
BG_COLOR = "#17202A"
TEXT_COLOR = "#EAECEE"

FONT = "Helvetica 12"
FONT_BOLD = "Helvetica 11 bold"

class ChatApplication:
    
    def __init__(self):
        self.window = Tk()
        self._setup_main_window()
        
    def run(self):
        self.recommenderAgent = RecommenderAgent("recomendador@xabber.de", "recomendador")
        future = self.recommenderAgent.start()
        future.result()

        self.updaterAgent = UpdaterAgent("actualizador@xabber.de", "actualizador")
        future = self.updaterAgent.start()
        future.result()
        

        self.chatbotAgent = ChatbotAgent("chatbot@xabber.de", "chatbot")
        self.chatbotAgent.setGui(self)
        future = self.chatbotAgent.start()
        future.result()


        # while chatbotAgent.is_alive() and updaterAgent.is_alive and recommenderAgent.is_alive :
        #     try:
        #         time.sleep(1)
        #     except KeyboardInterrupt:
        #         chatbotAgent.stop()
        #         updaterAgent.stop()
        #         recommenderAgent.stop()
        #         break
        self.window.mainloop()

    async def quit(self):
        await self.chatbotAgent.stop()
        await self.updaterAgent.stop()
        await self.recommenderAgent.stop()
        self.window.destroy()
        
    def _setup_main_window(self):
        self.window.title("Chat")
        self.window.resizable(width=True, height=False)
        self.window.configure(width=900, height=800, bg=BG_COLOR)
        
        # head label
        head_label = Label(self.window, bg=BG_COLOR, fg=TEXT_COLOR,
                           text="Movie recommender chatbot", font=FONT_BOLD, pady=10)
        head_label.place(relwidth=1)
        
        # tiny divider
        line = Label(self.window, width=450, bg=BG_GRAY)
        line.place(relwidth=1, rely=0.07, relheight=0.012)
        
        # text widget
        self.text_widget = Text(self.window, width=20, height=2, bg=BG_COLOR, fg=TEXT_COLOR,
                                font=FONT, padx=5, pady=5)
        self.text_widget.place(relheight=0.745, relwidth=1, rely=0.08)
        self.text_widget.configure(cursor="arrow", state=DISABLED)
        
        # scroll bar
        scrollbar = Scrollbar(self.text_widget)
        scrollbar.place(relheight=1, relx=0.974)
        scrollbar.configure(command=self.text_widget.yview)
        
        # bottom label
        bottom_label = Label(self.window, bg=BG_GRAY, height=80)
        bottom_label.place(relwidth=1, rely=0.825)
        
        # message entry box
        self.msg_entry = Entry(bottom_label, bg="#2C3E50", fg=TEXT_COLOR, font=FONT)
        self.msg_entry.place(relwidth=0.74, relheight=0.06, rely=0.008, relx=0.011)
        self.msg_entry.focus()
        self.msg_entry.bind("<Return>", self._on_enter_pressed)
        
        # send button
        send_button = Button(bottom_label, text="Send", font=FONT_BOLD, width=20, bg=BG_GRAY,
                             command=lambda: self._on_enter_pressed(None))
        send_button.place(relx=0.77, rely=0.008, relheight=0.06, relwidth=0.22)
     
    def _on_enter_pressed(self, event):
        msg = self.msg_entry.get()
        self.insert_message(msg, "User")
        self.chatbotAgent.userText = msg
        
        
    def insert_message(self, msg, sender = None):
        if not msg:
            return      
        self.msg_entry.delete(0, END)
        if sender is None:
            msg1 = f"{msg}\n\n"
        else:
            msg1 = f"{sender}: {msg}\n\n"
        self.text_widget.configure(state=NORMAL)
        self.text_widget.insert(END, msg1)
        self.text_widget.configure(state=DISABLED)
