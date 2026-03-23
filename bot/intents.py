# Intents disponibles en el sistema
# Cada intent tiene un nombre, descripción, y parámetros esperados

INTENTS = {
    "mis_asignaciones": {
        "description": "El usuario quiere ver sus propias asignaciones o tareas pendientes",
        "params": [],
        "examples": ["qué tengo yo", "mis archivos", "qué me toca", "tengo algo pendiente"],
    },
    "asignaciones_equipo": {
        "description": "El usuario quiere ver las asignaciones de todo su equipo",
        "params": [],
        "examples": ["qué tiene el equipo", "cómo vamos", "estado del equipo", "qué están haciendo todos"],
    },
    "buscar_archivo": {
        "description": "El usuario quiere saber quién trabaja en un archivo o asset específico",
        "params": ["query"],  # nombre o parte del nombre del archivo
        "examples": ["quién tiene la escena 4", "quién está en comp_final", "estado del archivo intro"],
    },
    "marcar_en_curso": {
        "description": "El usuario quiere marcar que empezó a trabajar en una asignación",
        "params": ["assignment_id"],
        "examples": ["empecé con el 3", "arranco la asignación 5", "estoy trabajando en el 12"],
    },
    "marcar_listo": {
        "description": "El usuario quiere marcar una asignación como terminada",
        "params": ["assignment_id"],
        "examples": ["terminé el 3", "listo el archivo 5", "entregué la asignación 2"],
    },
    "marcar_bloqueado": {
        "description": "El usuario quiere reportar que está bloqueado en una asignación",
        "params": ["assignment_id"],
        "examples": ["bloqueado en el 4", "no puedo avanzar con el 7", "tengo un problema con la asignación 3"],
    },
    "desconocido": {
        "description": "No se pudo determinar la intención",
        "params": [],
        "examples": [],
    },
}
