ELECCIONES ESCOLARES FBC - VERSION FINAL ONLINE
===============================================

Esta version esta preparada para:
1) Probarse localmente en una laptop.
2) Subirse a GitHub.
3) Desplegarse online en Render para que varias laptops entren desde distintos internet.

-----------------------------------------------
A. USO LOCAL (PRUEBAS)
-----------------------------------------------
1. Instala Python 3 y marca "Add Python to PATH".
2. Ejecuta INSTALAR.bat una sola vez.
3. Ejecuta INICIAR.bat.
4. Abre en tu navegador:
   http://127.0.0.1:8000
5. Administrador:
   http://127.0.0.1:8000/admin/login
   Contraseña inicial: FBC2026!

-----------------------------------------------
B. FORMATO DEL PADRON
-----------------------------------------------
Columnas requeridas:
- grado
- seccion
- apellidos_nombres

Ejemplo:
1,A,PEREZ LOPEZ, JUAN CARLOS
1,A,RAMOS DIAZ, MARIA FERNANDA
5,F,MALAVER PEREZ, ANA SOFIA

Tambien puedes usar el archivo padron_ejemplo.csv como modelo.

-----------------------------------------------
C. PUBLICAR ONLINE CON GITHUB + RENDER
-----------------------------------------------
1. Crea una cuenta en GitHub.
2. Crea un repositorio nuevo, por ejemplo: elecciones-fbc
3. Sube todos los archivos de esta carpeta al repositorio.
4. Crea una cuenta en https://render.com/
5. Elige "New Web Service".
6. Conecta tu cuenta de GitHub.
7. Selecciona el repositorio elecciones-fbc.
8. Render detectara el archivo render.yaml.
9. Espera a que termine el despliegue.
10. Render te dara una URL publica, por ejemplo:
    https://elecciones-fbc.onrender.com

Con esa URL, cada laptop podra votar desde su propio internet.

-----------------------------------------------
D. IMPORTANTE SOBRE LA BASE DE DATOS
-----------------------------------------------
Esta version usa SQLite, que funciona muy bien para:
- pruebas locales,
- una sola instancia web,
- elecciones escolares de tamano moderado.

Si mas adelante deseas una version aun mas robusta para uso intensivo,
se puede migrar a PostgreSQL.

-----------------------------------------------
E. FUNCIONES PRINCIPALES
-----------------------------------------------
- Panel de administracion con contraseña.
- Carga de padron por CSV o XLSX.
- Registro de candidatos con simbolo/logo.
- Pantalla de votacion por grado, seccion y estudiante.
- Bloqueo de doble voto.
- Voto en blanco.
- Confirmacion antes de emitir voto.
- Mensaje "Gracias por votar".
- Conteo automatico.
- Grafico profesional de barras.
- Estadisticas por grado y seccion.
- Exportacion de participacion y resultados.
- Apertura y cierre de votacion.
- Reinicio del proceso para simulacros.

-----------------------------------------------
F. ARCHIVOS CLAVE
-----------------------------------------------
- app.py               -> aplicacion principal
- run.py               -> inicio local amigable
- requirements.txt     -> dependencias Python
- render.yaml          -> despliegue rapido en Render
- static/onpe_logo.png -> logo ONPE
- templates/           -> vistas HTML
- static/style.css     -> estilos visuales

