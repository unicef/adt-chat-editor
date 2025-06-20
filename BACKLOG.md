Ideas

## Prompts
- control de versiones para prompts
    - levantar la ultima versión a menos que se especifique una versión específica (carpeta de versiones, Langfuse?, DVC?)
    - Mantener misma versión para todas las prompts
- mover las prompts a los grafos que correspondan (en vez de tener un prompt en el workflow, tener un prompt en el grafo)
- structured output
    - ver si es facil tener un fallback o un flag para no usar esto


## Structs
- mover los específicos a los agentes que correspondan
- dejar los generales en structs


## Nodos
- usar base nodes y dejar un template para los nodos con los pasos comunes (messages, vars, llm_call, parsing, update_state)


## Settings
- FastAPI base settings


## Formating
- isort
- black
- ruff


## Tests
- FastAPI test client (health check)



