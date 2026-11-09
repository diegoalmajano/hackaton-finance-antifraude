# Finalización del MVP con Codex — 09-11-2026

Autorización: prompt maestro del usuario. Trabajo en feat/fase-0 desde dd3e4fb, inicialmente limpio y sincronizado. Se permiten tareas técnicas, subagentes y commits locales; no nuevos pushes, releases, gasto, instalaciones ni cuentas reales sin permiso específico. IA=0, presupuesto=0, Opus=0, integraciones reales bloqueadas. No leer/crear sellado.

## Plan priorizado hasta la presentación prevista el 12 de noviembre
Hora exacta de cierre pendiente; no se presupone disponibilidad de todo ese día.

| Prioridad | Alcance | Criterio verificable | Estado inicial |
|---|---|---|---|
| A | Continuidad y dependencias | HEAD/estado, Python3.12, pip check, suites y saltos identificados | 746 Python, 11 JS; 4 integraciones saltadas, 1 xfail; SDK reales ausentes |
| B | Detector | Reproducir defectos nuevos y contrapartidas legítimas; mínimos conservados; regresiones sin cambiar dev ni sellado | Auditoría delegada; rules-0.3.2 |
| F/D | Seguridad y gasto | Uso remoto malformado no libera reserva; libro inconsistente falla cerrado; reinicios/concurrencia probados | Auditoría delegada; ninguna API real |
| C | Gmail en aplicación | Consentimiento explícito, sesión aislada, recepción→minimización→pipeline→alerta explicada, errores visibles, stop/desconexión/caducidad/shutdown; apagado por defecto | Conector preparado; unión al panel pendiente |
| E | Evaluación defendible | Fórmulas/coste/caché/preflight correctos; procedimiento humano y ambiguos; independencia no atribuida a dev | Auditoría delegada; sellado no autorizado |
| G/H | UX y diseño final | Tras estabilizar flujos: tres preguntas claras, HTML semántico, foco/reflujo/200%, estilo coherente, sin audio | Manual Narrador/contraste Windows siguen no verificados |
| I/J | Demo y entrega | Servidor real + copia limpia; fuentes/PPTX/PDF coherentes; ZIP local revisado sin privados/venv; commit local | Materiales previos disponibles; no publicación nueva |

## Criterios de la unión Gmail antes de cambiar comportamiento
- Ningún OAuth, import de SDK o acceso de red por arrancar o visitar el panel. Activación local explícita y confirmación del usuario en el formulario antes de conectar; configuración fuera de URLs/HTML.
- La autorización de Gmail no autoriza transmitir sus mensajes a Claude. Este flujo analiza localmente con IA desactivada hasta consentimiento y presupuesto específicos futuros.
- Una sola conexión ligada a la sesión que la autoriza; otra sesión no ve alertas ni puede controlarla. Cerrar sesión/caducar desconecta la recepción y descarta datos en memoria; la actividad automática no prolonga la sesión.
- Primera consulta fija el cursor sin leer buzón anterior; resincronización reciente según conector existente y consentimiento explicado. No enviar/modificar mensajes. Errores de cuota/autorización/ingesta visibles y nunca BAJO por fallo.
- No retener cuerpos completos ni identificadores de mensaje en las vistas/logs; solo alertas y explicaciones minimizadas en memoria, acotadas y eliminables. No guardar OAuth ni tokens en evidencias.
- Pruebas con cliente inyectado y etiqueta SIMULADO, sin Google real ni SDK. Cuenta de pruebas/GCP/OAuth/instalación serán autorizaciones independientes; no declarar integración real verificada por estas pruebas.
- Reutilizar conectores/pipeline/seguridad actuales; sin SQLite, escritorio, canales nuevos ni cambio de proveedor.

## Separación de responsabilidades
Detector: rules.py + test_b_finalizacion.py. Gasto: ai/budget.py, ai/claude.py + test_c_seguridad_final.py. Evaluación: evaluation.py + test_f_finalizacion.py y procedimiento si falta. Coordinación: integración app/Gmail, UI, docs compartidas, entrega y regresión global. Los agentes no crean commits ni pisan archivos de otro responsable.

## Resultado de ejecución

A/B/C/D/E/F/G/H realizados dentro del alcance sin gasto. C/D reales quedan pendientes de credenciales y autorizaciones específicas; E independiente requiere revisión humana y conjunto bajo custodia. I/J: materiales actualizados, pruebas completas y empaquetado local documentados en VERIFICACION_FINAL_MVP.md. No se modifica main ni se publica nada. La aceptación de accesibilidad sigue parcial y está delimitada en ACCESIBILIDAD_CODEX.md.
