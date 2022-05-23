from gui import GUI

if __name__ == "__main__":
    # Creamos un objeto interfaz gráfica
    gui = GUI()
    # Mostramos un primer mensaje de bienvenida al usuario por la GUI
    gui.insertMessage("Hi, welcome to your movie recommender.", "MovieBot")
    # Ejecutamos la GUI
    gui.run()