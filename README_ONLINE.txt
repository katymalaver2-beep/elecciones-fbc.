ELECCIONES FBC - VERSION ONLINE MULTI-LAPTOP
============================================

Esta versión está preparada para que cada laptop utilice su propia conexión a Internet.
La plataforma online usa PostgreSQL para guardar padrón, candidatos, participación y votos.
Los símbolos de los candidatos también se guardan dentro de la base de datos para evitar
que se pierdan al reiniciar el servidor.

ACCESOS LOCALES PARA PROBAR
---------------------------
Votación:        http://127.0.0.1:8000
Administración:  http://127.0.0.1:8000/admin/login
Contraseña inicial: FBC2026!

PUBLICACIÓN ONLINE
------------------
1. Sube TODOS los archivos de esta carpeta a un repositorio de GitHub.
2. Crea una cuenta en Render.
3. En Render selecciona New > Blueprint.
4. Conecta GitHub y selecciona tu repositorio.
5. Render leerá render.yaml y creará:
   - un servicio web Python
   - una base de datos PostgreSQL
6. Espera a que ambos recursos indiquen que están activos.
7. Render te mostrará una URL pública, por ejemplo:
   https://elecciones-fbc.onrender.com
8. Esa URL será la que usarán los estudiantes desde cualquier laptop con Internet.
9. Administración:
   https://TU-URL.onrender.com/admin/login
10. Cambia la contraseña FBC2026! antes de cargar datos reales.

IMPORTANTE
----------
- No publiques la contraseña de administrador.
- Mantén los resultados ocultos mientras la elección esté abierta.
- Realiza un simulacro y luego usa REINICIAR antes de la elección real.
- Exporta los resultados y participación al terminar.
- La página pública del estudiante NO muestra el acceso de administración.
