La puesta en marcha del sistema está explicada con todo detalle
en el "Anexo A: manual de instalación y ejecución" de la memoria.

No obstante, a continuación resumimos los pasos para ejecutar el sistema
por primera vez:

1) En caso de que no se haya hecho este paso anteriormente, descargar
   el modelo basado en contenido del siguiente enlace (no se incluye
   en la entrega porque incluso comprimido excede el límite de espacio
   que permite el Campus Virtual):

   https://drive.google.com/file/d/1d7jMOMH4HPH0EfqfA2GSWjBLxZptyYis/view

2) Mover el fichero descargado "contenteBasedModel.npy" a la ruta
   "base\Proyecto final DASI\Codigo ejecutable\utils", siendo "base"
   la ubicación del directorio raíz de la entrega, es decir, donde
   se haya ubicado "Proyecto final DASI".

3) En caso de que aún no se haya hecho, instalar el lenguaje de programación
   Python en su versión 3.8 o superior, así como las siguientes librerías en
   las versiones que se indican a continuación:
   
	- google-cloud-dialogflow-cx versión 1.10.0.
	- numpy versión 1.22.3 (es muy importante que sea esta versión o superior).
	- pandas versión 1.3.3.
	- spade versión 3.2.2.
	- surprise versión 0.1.

4) Moverse desde un terminal al directorio "base\Proyecto final DASI\Codigo ejecutable"
   e iniciar la ejecución del sistema con el comando "python main.py".

5) Para ejecutar los test automáticos del sistema ejecutar de manera normal,
   pasando como argumentos al programa la ruta de los ficheros de prueba.
   Por ejemplo, "python main.py test/usuarioEscribeInformal.txt test/variasRecomendacionesYValoraciones.txt"
