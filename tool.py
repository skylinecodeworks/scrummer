import os
import tempfile
import shutil
import logging
from jira import JIRA
from dotenv import load_dotenv
from git import Repo

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def plan_least_story(
    jira_url: str,
    jira_user: str,
    jira_token: str,
    jira_board_id: str,
    github_token: str,
    owner: str,
    repo_name: str
) -> dict:
    """
    Recupera la story con menor esfuerzo del sprint activo y construye
    el prompt que Ollama usará para generar un patch unificado.

    Args:
      jira_url: URL de la instancia de Jira.
      jira_user: Usuario de Jira.
      jira_token: Token o contraseña de Jira.
      jira_board_id: ID del board de Jira.
      github_token: Token de acceso a GitHub.
      story_points_field: Nombre del campo de Story Points en Jira.
      owner: Propietario de GitHub.
      repo_name: Nombre del repositorio.

    Returns:
      Un dict con claves: story_key, story_summary, story_points, prompt.
    """
    logger.info("=== plan_least_story iniciado para %s/%s ===", owner, repo_name)

    try:
        jira = JIRA(server=jira_url, basic_auth=(jira_user, jira_token))
        logger.info("Cliente Jira inicializado: %s", jira_url)
    except Exception as e:
        logger.exception("Error al inicializar cliente Jira")
        return {"error": f"Falló inicialización Jira: {e}"}

    jql = f"project = {jira_board_id}"
    logger.info("Ejecutando JQL: %s", jql)
    try:
        issues = jira.search_issues(jql, maxResults=100)
    except Exception as e:
        logger.exception("Error buscando issues en Jira")
        return {"error": f"Falló búsqueda de issues: {e}"}

    if not issues:
        return {"error": "No se encontraron stories"}
    least = issues[0]
    print(f"Story: {least}")
    story_key = least.key
    story_summary = least.fields.summary
    logger.info("Story seleccionada: %s - %s", story_key, story_summary)

    temp_dir = tempfile.mkdtemp()
    repo_url = f"https://{github_token}@github.com/{owner}/{repo_name}.git"
    logger.info("Clonando repo: %s -> %s", repo_url, temp_dir)
    try:
        Repo.clone_from(repo_url, temp_dir)
        logger.info("Repositorio clonado con éxito")
    except Exception as e:
        logger.exception("Error clonando repositorio GitHub")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return {"error": f"Error clonando repo: {e}"}

    files_content = {}
    logger.info("Leyendo archivos en %s", temp_dir)
    for root, _, files in os.walk(temp_dir):
        for fname in files:
            if fname.endswith(('.py', '.ini', '.cfg', '.yaml', '.yml', '.json', '.toml')):
                rel = os.path.relpath(os.path.join(root, fname), temp_dir)
                try:
                    with open(os.path.join(root, fname), 'r', encoding='utf-8') as f:
                        files_content[rel] = f.read()
                    logger.debug("Leído archivo: %s (%d chars)", rel, len(files_content[rel]))
                except Exception as e:
                    logger.warning("No se pudo leer %s: %s", rel, e)
                    files_content[rel] = ''
    logger.info("Total archivos leídos: %d", len(files_content))
    logger.info("Contenido: %s", files_content)

    logger.info("Eliminando directorio temporal %s", temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)

    logger.info("Construyendo prompt para Ollama")
    context = ''.join(f"-- FILE: {name}\n{content}\n" for name, content in files_content.items())
    prompt = (
        f"JIRA USER STORY: {story_key}={story_summary})\n"
        f"GITHUB REPOSITORY: {owner}/{repo_name}.\n"
        f"FULL REPOSITORY SOURCE CODE WITH REFERENCE TO ALL FILES: {context}.\n"
        f"GENERATE A PATCH (diff -u) that implements the JIRA STORY SUMMARY INTO THE SOURCE CODE:" + "\n"
        f"Return only the diff file that represents the changes to apply into the source code"
    )
    logger.info("Prompt: %s", prompt.replace('\n',' '))

    logger.info("plan_least_story completado correctamente")
    return {
        "story_key": story_key,
        "story_summary": story_summary,
        "prompt": prompt
    }