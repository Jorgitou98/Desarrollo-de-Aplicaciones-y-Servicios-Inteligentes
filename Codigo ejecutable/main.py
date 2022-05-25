import sys
from gui import GUI

if __name__ == "__main__":
    # Creamos un objeto interfaz gráfica
    gui = GUI()
    # Ejecutamos la GUI con los parámetros recibidos para la ejecución
    gui.run(sys.argv[1:])