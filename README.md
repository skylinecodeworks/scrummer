# 🧩 Scrummer

**Scrummer** es una herramienta asistida por LLM que automatiza el desarrollo de tareas técnicas a partir de historias de usuario de Jira. Dado un tablero de Jira conectado a un repositorio de GitHub, el sistema detecta automáticamente la historia activa de menor esfuerzo, analiza el código del repositorio y genera un `diff` con los cambios sugeridos, que luego se guarda como un archivo `.patch`.

## 🚀 Funcionalidad principal

1. **Identifica** automáticamente la historia más simple del sprint activo (usando Jira).
2. **Clona** el repositorio de GitHub vinculado.
3. **Construye** un prompt de contexto técnico para el modelo LLM (Deepseek).
4. **Invoca** una tool compatible con OpenAI API (`plan_least_story`) para generar el cambio.
5. **Valida** que el resultado sea un diff unificado.
6. **Guarda** el parche como un archivo `.patch` listo para aplicar con `git apply`.

## 🧱 Estructura del proyecto

```

.
├── patch/                # Contiene los parches generados por el modelo
├── pyproject.toml        # Metadatos del proyecto
├── README.md             # Este archivo
├── requirements.txt      # Dependencias de Python
├── run_chat.py           # Script principal que orquesta el flujo
├── tool.json             # Definición formal de la tool para el modelo
└── tool.py               # Lógica de extracción de historias desde Jira y GitHub

````

## ⚙️ Configuración

Crear un archivo `.env` con los siguientes valores:

```env
# Jira
JIRA_URL=https://<mi-dominio>.atlassian.net/
JIRA_USER=usuario@email.com
JIRA_TOKEN=mi_token_jira
JIRA_BOARD_ID=ID-del-board

# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxx
OWNER=usuario_o_organizacion
REPO=nombre-del-repo

# DeepSeek API
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DEEPSEEK_MODEL=deepseek-coder
````

> **Nota:** Tu token de Jira necesita permisos de lectura de issues. El token de GitHub debe tener permisos de `repo`.

## 🧪 Uso con Astral UV

1. Instalá las dependencias en un entorno virtual usando [Astral UV](https://astral.sh/docs/uv):

   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

2. Ejecutá el script principal:

   ```bash
   uv run run_chat.py
   ```

> Requiere tener `uv` instalado previamente. Podés instalarlo con:

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

## 🛠 Cómo aplicar el parche que genera la aplicación

Una vez generado el archivo `.patch`, podés aplicarlo al repo clonado con:

```bash
git apply patch/TEST1-10.patch
```

## 🤖 Arquitectura LLM Tool Use

* El archivo `tool.json` define una función OpenAI-compatible llamada `plan_least_story`.
* La llamada inicial fuerza al modelo a invocar esa tool.
* El resultado es pasado de nuevo al modelo como un `tool_call`.
* Se intenta hasta 3 veces que la respuesta sea un `diff` unificado.
* El proyecto es compatible con Ollama y Deepseek (actualmente configurado para Deepseek).


## 🧩 Requisitos

* Python 3.12+
* Acceso a Jira Cloud y GitHub
* Cuenta activa en [Deepseek](https://deepseek.com) con clave de API
* Astral UV instalado (`uv`)

## 📄 Licencia

MIT License. © Skyline Codeworks 2025.


