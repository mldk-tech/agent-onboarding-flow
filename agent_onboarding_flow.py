# --- Agent Onboarding Flow with LLM Integration ---
import requests
import pandas as pd
import io
import datetime
import json

# --- Short-term Memory (Ephemeral) ---
conversation_buffer = []

# --- Long-term Memory (Persistent) ---
persistent_memory = {
    "user_id": None,
    "user_type": None,
    "csv_uploaded": False,
    "csv_validated": False,
    "last_tool_error": None,
    "completed_steps": [],
    "failed_attempts": [],
    "timestamps": {}
}

# --- Tools ---
def fetch_user_data(user_id: str) -> dict:
    response = requests.get(f"https://internal-api/users/{user_id}")
    if response.status_code == 200:
        return response.json()
    raise Exception(f"Failed to fetch user data: {response.status_code}")

def validate_csv(file_bytes: bytes) -> dict:
    df = pd.read_csv(io.BytesIO(file_bytes))
    required_columns = {"tenant_name", "email", "contract_start"}
    missing = required_columns - set(df.columns)
    return {
        "valid": len(missing) == 0,
        "missing_fields": list(missing)
    }

def route_to_module(task: str) -> str:
    routes = {
        "import_tenants": "/dashboard/tenants/import",
        "setup_payments": "/dashboard/payments/setup"
    }
    return routes.get(task, "/dashboard")

# --- LLM Integration (stubbed call) ---
def call_openai(prompt: str) -> str:
    # Placeholder for LLM API call
    return "prompt_user_to_upload_csv"

def recognize_intent(user_input: str, context: str = "") -> str:
    prompt = f"""
    Given the following user message: '{user_input}'
    And context: '{context}'
    Classify the intent as one of: ['import_tenants', 'setup_payments', 'unknown'].
    Return intent only.
    """
    return call_openai(prompt).strip()

def decision_by_llm(intent: str, memory: dict) -> str:
    system_prompt = (
        "You are an onboarding agent. Based on the user intent and memory, "
        "decide the next action from: ['prompt_user_to_upload_csv', 'validate_csv', "
        "'route_to_module', 'fallback_to_template']. Only return the action name."
    )
    user_prompt = f"""
    Intent: {intent}
    Memory: {json.dumps(memory)}
    """
    return call_openai(system_prompt + user_prompt).strip()

# --- Agent Monitoring Loop ---
def agent_main_loop(user_input: str, user_id: str, file_bytes: bytes = None):
    persistent_memory["user_id"] = user_id
    intent = recognize_intent(user_input)
    action = decision_by_llm(intent, persistent_memory)

    conversation_buffer.append({
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "intent": intent,
        "action": action
    })

    if action == "prompt_user_to_upload_csv":
        return "Please upload your tenant CSV file."

    if action == "validate_csv":
        if file_bytes:
            result = validate_csv(file_bytes)
            persistent_memory["csv_validated"] = result["valid"]
            if not result["valid"]:
                persistent_memory["last_tool_error"] = result["missing_fields"]
                persistent_memory["failed_attempts"].append("validate_csv")
                return f"Missing fields: {result['missing_fields']}"
            persistent_memory["completed_steps"].append("validate_csv")
            return "File validated successfully. Proceeding to import."
        else:
            return "No file uploaded. Please provide a CSV."

    if action == "handle_error":
        return f"There was an issue: {persistent_memory['last_tool_error']}"

    if action.startswith("/dashboard"):
        persistent_memory["completed_steps"].append(intent)
        return f"Redirecting to: {action}"

    if action == "fallback_to_template":
        return "I'm having trouble understanding. Let's go step-by-step. What would you like to do?"

    return "Unable to process your request. Please contact support."

# --- Example Run ---
# print(agent_main_loop("I want to upload tenant info", "user_123"))
