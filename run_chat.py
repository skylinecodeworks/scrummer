import json, os, logging
from dotenv import load_dotenv
import requests
from tool import plan_least_story

load_dotenv()

JIRA_URL              = os.getenv("JIRA_URL")
JIRA_USER             = os.getenv("JIRA_USER")
JIRA_TOKEN            = os.getenv("JIRA_TOKEN")
JIRA_BOARD_ID         = os.getenv("JIRA_BOARD_ID")
JIRA_STORY_POINTS_FIELD = os.getenv("JIRA_STORY_POINTS_FIELD", "customfield_10002")
GITHUB_TOKEN          = os.getenv("GITHUB_TOKEN")
OWNER                 = os.getenv("OWNER")
REPO                  = os.getenv("REPO")
DEEPSEEK_API_KEY      = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL      = os.getenv("DEEPSEEK_API_URL")
DEEPSEEK_MODEL        = os.getenv("DEEPSEEK_MODEL", "deepseek-coder")

HEADERS = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json"
}

def deepseek_chat(messages, tools=None, force_tool_call=False):
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": 0.2,
    }

    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = {
            "type": "function",
            "function": {"name": "plan_least_story"}
        } if force_tool_call else "auto"

    print("📦 Payload enviado a Deepseek:")
    print(json.dumps(payload, indent=2))

    response = requests.post(DEEPSEEK_API_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

with open("tool.json") as f:
    tools = json.load(f)["tools"]

messages = [
    {"role": "system", "content": "Eres un asistente que resuelve tareas de desarrollo usando herramientas."},
    {"role": "user",   "content": "Necesito el diff para la historia más pequeña del sprint actual, para ello utiliza la tool plan_least_story"}
]

response = deepseek_chat(messages, tools=tools, force_tool_call=True)

message = response["choices"][0]["message"]
messages.append(message)
tool_calls = message.get("tool_calls", [])

if not tool_calls:
    log.warning("El modelo no hizo ninguna llamada a tools.")
    print(message["content"])
    exit(0)

for call in tool_calls:
    if call["function"]["name"] == "plan_least_story":
        args = json.loads(call["function"]["arguments"])
        log.info("Ejecutando plan_least_story con argumentos: %s", args)

        tool_result = plan_least_story(
            jira_url=JIRA_URL,
            jira_user=JIRA_USER,
            jira_token=JIRA_TOKEN,
            jira_board_id=JIRA_BOARD_ID,
            github_token=GITHUB_TOKEN,
            owner=OWNER,
            repo_name=REPO,
        )

        messages.append({
            "role": "tool",
            "tool_call_id": call["id"],
            "content": json.dumps(tool_result)
        })

MAX_RETRIES = 3
retry = 0
diff_content = None

while retry < MAX_RETRIES:
    final = deepseek_chat(messages)
    content = final["choices"][0]["message"]["content"]

    if "--- " in content and "+++" in content and "@@ " in content:
        diff_content = content
        break
    else:
        log.warning("Respuesta no es un diff válido, reintentando...")
        messages.append({
            "role": "user",
            "content": "Por favor, genera un diff unificado que implemente la historia anterior."
        })
        retry += 1

if not diff_content:
    log.error("No se pudo obtener un diff válido después de varios intentos.")
    exit(1)

patch_dir = os.path.join(os.getcwd(), "patch")
os.makedirs(patch_dir, exist_ok=True)

patch_path = os.path.join(patch_dir, f"{tool_result['story_key']}.patch")
with open(patch_path, "w", encoding="utf-8") as f:
    f.write(diff_content)

log.info("✅ Patch guardado en: %s", patch_path)
print(diff_content)
