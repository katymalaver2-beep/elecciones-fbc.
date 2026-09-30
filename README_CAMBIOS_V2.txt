ACTUALIZACION V2 - ELECCIONES FBC
=================================

Cambios incluidos:
1. Después de validar el DNI, la cédula muestra una bienvenida breve con el nombre del estudiante.
2. Se elimina el paso intermedio de confirmación: el botón EMITIR VOTO registra el voto de forma definitiva.
3. La pantalla final muestra "¡Gracias por votar! Tu voto es importante", animación de confeti electoral y retorna al inicio en 2.8 segundos.
4. Las listas/candidatos quedan protegidas contra eliminación accidental.
5. Para eliminar una lista: primero DESPROTEGER y luego ELIMINAR.
6. No se permite eliminar una lista mientras la elección esté abierta.
7. No se permite eliminar una lista si ya tiene votos registrados; en ese caso puede desactivarse.
8. Las listas que ya existían quedan protegidas automáticamente al desplegar esta actualización.

ARCHIVOS QUE DEBES REEMPLAZAR EN GITHUB:
- app.py
- templates/vote.html
- templates/thanks.html
- templates/admin.html
- static/style.css

No necesitas crear otra base de datos. app.py realiza la migración automáticamente.
