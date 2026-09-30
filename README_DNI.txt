ELECCIONES ESCOLARES FBC - VERSION CON ACCESO POR DNI
=====================================================

CAMBIO PRINCIPAL
----------------
El estudiante ya NO busca grado, seccion ni nombre.
En la pantalla publica solo digita su DNI de 8 digitos.
El sistema valida que:
- el DNI exista en el padron;
- el estudiante aun no haya votado;
- la eleccion se encuentre abierta.

PRIVACIDAD
----------
- No existe una lista publica de nombres.
- No se muestra el nombre ni el DNI en la cedula de votacion.
- El sistema registra quien participo, pero el voto se almacena de forma separada.
- El administrador puede descargar el padron con el estado SI/NO de participacion.

FORMATO DEL PADRON
------------------
Columnas obligatorias:
- dni
- apellidos_nombres

Columnas opcionales:
- grado
- seccion

Ejemplo:
dni,apellidos_nombres,grado,seccion
12345678,PEREZ LOPEZ JUAN CARLOS,5,F
87654321,RAMOS DIAZ MARIA FERNANDA,5,F
11223344,TORRES GARCIA LUIS ALBERTO,,

El DNI debe contener exactamente 8 digitos.

DESCARGA DE PARTICIPACION
-------------------------
En Administracion > Padron y participacion encontraras:
- DESCARGAR PADRON EN EXCEL
- CSV

El reporte incluye:
DNI | Apellidos y nombres | Grado | Seccion | Participo | Fecha y hora

ACTUALIZAR LA VERSION ONLINE EN RENDER
--------------------------------------
1. Descomprime esta carpeta.
2. En tu repositorio de GitHub, reemplaza app.py, templates y static con esta version.
3. Sube tambien README_DNI.txt si deseas conservar las instrucciones.
4. Haz Commit changes.
5. Render detectara el cambio y desplegara automaticamente.

IMPORTANTE: esta version incluye una migracion automatica. Si tu base PostgreSQL actual
viene de la version anterior, se agrega la columna DNI sin borrar candidatos, configuracion
o votos existentes. Como aun no has cargado padron real, puedes actualizarla sin problema.
