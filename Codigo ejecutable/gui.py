from time import sleep
from tkinter import *
from chatbotAgent import ChatbotAgent
from recommenderAgent import RecommenderAgent
from updaterAgent import UpdaterAgent
from threading import Thread

BG_GRAY = "#ABB2B9"
BG_COLOR = "#17202A"
TEXT_COLOR = "#EAECEE"

FONT = "Helvetica 12"
FONT_BOLD = "Helvetica 11 bold"

WELCOME_MSG = "Hi, welcome to your movie recommender."

class GUI:
    
    """
    Constructor de la interfaz gráfica con el usuario.
    
    :param self: objeto de la clase con el que se invoca.
    """
    def __init__(self):
        # Creación de la ventana para la interfaz.
        self.window = Tk()
        # Configuración de la ventana
        self._setupMainWindow()
        # Mostramos un primer mensaje de bienvenida al usuario por la GUI
        self.insertMessage(WELCOME_MSG, "MovieBot")


    """
    Permite utilizar la entrada de ficheros como prueba para el sistema.
    Va leyendo el contenido de los ficheros que recibe y lo introduce en la GUI
    como si de las frases dadas por el usuario se tratase. Espera 2 segundos para
    introducir cada una de las frases (y que la conversación vaya apareciendo poco a poco).
    
    :param self: objeto de la clase con el que se invoca.
    :param filesTestPaths: lista de rutas a los ficheros de prueba para ejecutar.
    """
    def __testFile(self, filesTestPaths):
        # Por cada ruta a un fichero de prueba
        for fileTestPath in filesTestPaths:
            # Creamos una nueva sesión de conversación con el chatbot
            self.chatbotAgent.startChatSession() 
            # Mostramos por la interfaz el nombre de la prueba automática que se está ejecutando
            self.insertMessage("\nEJECUTANDO PRUEBA AUTOMÁTICA {}\n".format(fileTestPath))
            # Con el fichero abierto
            with open(fileTestPath) as testFile:
                # Recorremos cada una de sus líneas
                for entry in testFile.read().splitlines():
                    # Escribimos la línea en la entrada
                    self.msg_entry.insert(END, entry)
                    # Presionamos el enter para introducir el texto
                    self._onEnterPressed(None)
                    # Esperamos 2 segundo antes de escribir la siguiente entrada.
                    sleep(2)

    """
    Método que se ejecuta para lanzar la interfaz gráfica una vez está configurada.
    
    :param self: objeto de la clase con el que se invoca.

    """
    def run(self, filesTestPaths):
        # Creamos al Agente Recomendador e iniciamos su comportamiento.
        self.recommenderAgent = RecommenderAgent("recomendador@xabber.de", "recomendador")
        future = self.recommenderAgent.start()
        future.result()

        # Creamos al Agente Actualizador e iniciamos su comportamiento.
        self.updaterAgent = UpdaterAgent("actualizador@xabber.de", "actualizador")
        future = self.updaterAgent.start()
        future.result()
        
        # Creamos al Agente Chatbot e iniciamos su comportamiento.
        self.chatbotAgent = ChatbotAgent("chatbot@xabber.de", "chatbot")
        self.chatbotAgent.setGui(self)
        future = self.chatbotAgent.start()
        future.result()

        if len(filesTestPaths) > 0:
            testThread = Thread(target=self.__testFile, args=(filesTestPaths,))
            testThread.start()

        # Entramos en el bucle infinito de funcionamiento de la interfaz.
        self.window.mainloop()

    """
    Método que se ejecuta para finalizar la interfaz gráfica.
    
    :param self: objeto de la clase con el que se invoca.
    """   
    async def quit(self):
        # Finalizamos el comportamiento Agente Chatbot.
        await self.chatbotAgent.stop()
        # Finalizamos el comportamiento Agente Actualizador.
        await self.updaterAgent.stop()
        # Finalizamos el comportamiento Agente Recomendador.
        await self.recommenderAgent.stop()
        # Destruimos la ventana de la interfaz.
        self.window.destroy()
    
    """
    Método de configuración de la interfaz gráfica.
    
    :param self: objeto de la clase con el que se invoca.
    """     
    def _setupMainWindow(self):
        # Colocamos el título de la interfaz
        self.window.title("Chat")
        # Permitimos redimensionarla en anchura pero no en altura.
        self.window.resizable(width=True, height=False)
        # Configuramos las dimensiones y el color de fondo de la interfaz.
        self.window.configure(width=900, height=800, bg=BG_COLOR)
        
        # Colocamos la etiqueta de la cabecera de la interfaz
        head_label = Label(self.window, bg=BG_COLOR, fg=TEXT_COLOR,
                           text="Movie recommender chatbot", font=FONT_BOLD, pady=10)
        head_label.place(relwidth=1)
        
        # Colocamos un separador entre la cabecera y el widget de texto
        line = Label(self.window, width=450, bg=BG_GRAY)
        line.place(relwidth=1, rely=0.07, relheight=0.012)
        
        # Colocamos un widget done aparecerá el texto de la conversación.
        self.text_widget = Text(self.window, width=20, height=2, bg=BG_COLOR, fg=TEXT_COLOR,
                                font=FONT, padx=5, pady=5)
        self.text_widget.place(relheight=0.745, relwidth=1, rely=0.08)
        self.text_widget.configure(cursor="arrow", state=DISABLED)
        
        # Colocamos una barra de desplazamiento vertical.
        scrollbar = Scrollbar(self.text_widget)
        scrollbar.place(relheight=1, relx=0.974)
        scrollbar.configure(command=self.text_widget.yview)
        
        # Preparamos una etiqueta para un botón que permitrá introducir el texto de la entrada.
        bottom_label = Label(self.window, bg=BG_GRAY, height=80)
        bottom_label.place(relwidth=1, rely=0.825)
        
        # Colocamos una caja para la entrada de texto.
        self.msg_entry = Entry(bottom_label, bg="#2C3E50", fg=TEXT_COLOR, font=FONT)
        self.msg_entry.place(relwidth=0.74, relheight=0.06, rely=0.008, relx=0.011)
        self.msg_entry.focus()
        self.msg_entry.bind("<Return>", self._onEnterPressed)

        
        # Colocamos un botón que permitirá introducir el texto escrito en la entrada.
        # Presionar este botón invocará al método "_onEnterPressed".
        send_button = Button(bottom_label, text="Send", font=FONT_BOLD, width=20, bg=BG_GRAY,
                             command=lambda: self._onEnterPressed(None))
        send_button.place(relx=0.77, rely=0.008, relheight=0.06, relwidth=0.22)
     
    """
    Método que se ejecuta cuando el usuario presiona el botón "enter".
    
    :param self: objeto de la clase con el que se invoca.
    :param event: evento que desencadena la ejecución del método.
    """ 
    def _onEnterPressed(self, event):
        # Tomamos el mensaje escrito en la entrada.
        msg = self.msg_entry.get()
        # Mostramos el mensaje en la ventana de texto de la conversación.
        self.insertMessage(msg, "User")
        # Nos desplazamos hasta la última línea que se haya escrito en la ventana de texto.
        self.text_widget.see("end")
        # Le dejamos al chatbot el texto escrito por el usuario.
        self.chatbotAgent.userText = msg

    """
    Método que muestra el mensaje recibido por la ventana de texto
    de la interfaz gráfica.
    
    :param self: objeto de la clase con el que se invoca.
    :param msg: cadena con el texto a mostrar.
    :param sender: quién dice la frase mostrada (habitualmente user o movieBot para mostrarlo antes del mensaje).
    """         
    def insertMessage(self, msg, sender = None):
        # Si el mensaje es vacío, no se hace nada.
        if not msg:
            return
        # Borramos la entrada de la GUI.
        self.msg_entry.delete(0, END)

        # Si no nos han indicado quién dice la frase.
        if sender is None:
            # Preparamos la cadena con el mensaje introduciendo saltos de linea.
            msg1 = f"{msg}\n\n"
        # Si nos han indicado quién dice la frase.
        else:
            # Preparamos la cadena con el remitente seguido del mensaje introduciendo saltos de linea.
            msg1 = f"{sender}: {msg}\n\n"
        self.text_widget.configure(state=NORMAL)
        # Colocamos en la ventana de texto la cadena creada.
        self.text_widget.insert(END, msg1)
        self.text_widget.configure(state=DISABLED)
        # Nos desplazamos hasta la última línea que se haya escrito en la ventana de texto.
        self.text_widget.see("end")
