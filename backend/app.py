import os
import json
import time
import uuid
import traceback
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests

from database import SQLiteDB
from file_operations import FileOperations
from langchain_community.embeddings import SentenceTransformerEmbeddings
try:
    from langchain.vectorstores import Chroma
except Exception:
    from langchain_community.vectorstores import Chroma

from git import Repo

app = Flask(__name__)
CORS(app)

LMSTUDIO_URL = os.environ.get("PYTHON_LMSTUDIO_URL", "http://localhost:1234/v1")
DEFAULT_MODEL = os.environ.get("PYTHON_DEFAULT_MODEL", "qwen/qwen3-4b-2507")
CHROMA_DIR = os.environ.get("PYTHON_CHROMA_DIR", "./chroma_db")
WEB_SEARCH_API = os.environ.get("WEB_SEARCH_API", "duckduckgo")
DB_PATH = os.environ.get("PYTHON_DB_PATH", "./project_agent.db")

embedder = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
vectordb = None
repo = None
db = SQLiteDB(DB_PATH)
file_ops = {}


def get_file_ops(project_path: str) -> FileOperations:
    """Get file operations instance for project"""
    if project_path not in file_ops:
        file_ops[project_path] = FileOperations(project_path)
    return file_ops[project_path]


def init_vectordb(project_path):
    global vectordb
    key = project_path.replace(":", "").replace("\\", "_").replace("/", "_")
    persist_dir = os.path.join(CHROMA_DIR, key)
    os.makedirs(persist_dir, exist_ok=True)
    vectordb = Chroma(persist_directory=persist_dir, embedding_function=embedder)
    return vectordb


def stream_response(generator):
    @wraps(generator)
    def wrapper(*args, **kwargs):
        def event_stream():
            for data in generator(*args, **kwargs):
                yield f"data: {json.dumps(data)}\n\n"
        return Response(event_stream(), mimetype="text/event-stream")
    return wrapper


def retrieve_context(query, k=6):
    try:
        docs = vectordb.similarity_search(query, k=k)
        texts = [d.page_content if hasattr(d, "page_content") else str(d) for d in docs]
        return texts
    except Exception as e:
        print(f"[CONTEXT RETRIEVAL ERROR] {e}")
        return []


def chat_with_lmstudio(messages, model=DEFAULT_MODEL, max_tokens=2000):
    url = f"{LMSTUDIO_URL}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.3,
        "stream": True
    }

    try:
        response = requests.post(url, json=payload, timeout=120, stream=True)
        response.raise_for_status()
        return response
    except Exception as e:
        raise Exception(f"LM Studio connection failed: {str(e)}")


def web_search(query):
    try:
        if WEB_SEARCH_API == "duckduckgo":
            return web_search_duckduckgo(query)
        elif WEB_SEARCH_API == "google":
            return web_search_google(query)
        else:
            return []
    except Exception as e:
        print(f"[WEB SEARCH ERROR] {e}")
        return []


def web_search_duckduckgo(query):
    from duckduckgo_search import DDGS
    try:
        ddgs = DDGS()
        results = ddgs.text(query, max_results=5)
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
                "source": "duckduckgo"
            }
            for r in results
        ]
    except Exception as e:
        print(f"[DUCKDUCKGO ERROR] {e}")
        return []


def web_search_google(query):
    return []


def generate_workplan(instruction, context_texts):
    system_prompt = """You are a senior software engineer. Generate a comprehensive, step-by-step workplan for the given instruction.
Output as a JSON object with this structure:
{
  "title": "Plan Title",
  "description": "Brief description",
  "tasks": [
    {
      "title": "Task Title",
      "description": "Task description",
      "priority": 1-5,
      "assigned_agent": "coder|reviewer|tester|analyst"
    }
  ]
}"""

    user_content = f"""Instruction: {instruction}

Project Context:
{chr(10).join(['- ' + text[:200] for text in context_texts[:5]])}

Generate a detailed workplan:"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    try:
        response = chat_with_lmstudio(messages, max_tokens=1500)
        full_response = ""

        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line.decode().replace("data: ", ""))
                    if "choices" in chunk and len(chunk["choices"]) > 0:
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            full_response += delta["content"]
                except:
                    pass

        try:
            workplan = json.loads(full_response)
            return workplan
        except:
            return {
                "title": "Generated Plan",
                "description": "Auto-generated workplan",
                "tasks": [{"title": "Review and implement", "description": instruction, "priority": 3, "assigned_agent": "coder"}]
            }
    except Exception as e:
        raise Exception(f"Workplan generation failed: {str(e)}")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})


@app.route("/api/models", methods=["GET"])
def api_models():
    try:
        r = requests.get(f"{LMSTUDIO_URL}/models", timeout=10)
        r.raise_for_status()
        data = r.json()

        models = []
        if isinstance(data, dict) and "data" in data:
            models = [m.get("id") for m in data["data"]]
        elif isinstance(data, list):
            models = data

        return jsonify({"models": models})
    except Exception as e:
        return jsonify({"error": str(e), "models": []}), 500


@app.route("/api/chat/stream", methods=["GET"])
def api_chat_stream():
    conversation_id = request.args.get("conversation_id")
    query = request.args.get("query")
    project_path = request.args.get("project_path")
    model = request.args.get("model", DEFAULT_MODEL)

    if not query or not project_path:
        return jsonify({"error": "Missing parameters"}), 400

    def event_generator():
        try:
            yield {"type": "processing", "stage": "context_fetch", "message": "Fetching project context...", "progress": 10}
            time.sleep(0.1)

            if not vectordb:
                init_vectordb(project_path)

            context_texts = retrieve_context(query, k=6)

            yield {"type": "processing", "stage": "context_fetch", "message": f"Found {len(context_texts)} relevant files", "progress": 30}

            yield {"type": "processing", "stage": "search", "message": "Searching web for latest information...", "progress": 40}
            time.sleep(0.1)

            search_results = web_search(query)

            yield {"type": "processing", "stage": "search", "message": f"Found {len(search_results)} web results", "progress": 50}

            yield {"type": "processing", "stage": "generate", "message": "Generating response...", "progress": 60}
            time.sleep(0.1)

            system_prompt = "You are a helpful code assistant with full project context. Provide clear, concise answers."

            context_str = "\n\n".join([f"[Project Context]\n{text}" for text in context_texts[:3]])
            search_str = "\n\n".join([f"[Web Result] {r['title']}\n{r['snippet']}" for r in search_results[:2]])

            user_content = f"Query: {query}\n\n{context_str}\n\n{search_str}"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]

            response = chat_with_lmstudio(messages, model=model)

            yield {"type": "processing", "stage": "generate", "message": "Streaming response...", "progress": 70}

            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line.decode().replace("data: ", ""))
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield {"type": "chunk", "content": delta["content"]}
                    except:
                        pass

            yield {"type": "processing", "stage": "generate", "message": "Complete", "progress": 100}
            yield {"type": "complete", "message": "Response generated successfully"}

        except Exception as e:
            print(f"[STREAM ERROR] {traceback.format_exc()}")
            yield {"type": "error", "message": str(e)}

    return Response(event_generator(), mimetype="text/event-stream")


@app.route("/api/workplan/generate", methods=["POST"])
def api_generate_workplan():
    data = request.json or {}
    instruction = data.get("instruction", "")
    project_path = data.get("project_path", "")
    conversation_id = data.get("conversation_id", str(uuid.uuid4()))

    if not instruction:
        return jsonify({"error": "Missing instruction"}), 400

    try:
        if not vectordb:
            init_vectordb(project_path)

        context_texts = retrieve_context(instruction, k=8)
        workplan = generate_workplan(instruction, context_texts)

        workplan_id = str(uuid.uuid4())
        db.create_workplan(
            workplan_id,
            conversation_id,
            workplan.get("title", ""),
            workplan.get("description", ""),
            workplan.get("tasks", [])
        )

        return jsonify({"ok": True, "workplan": workplan, "workplan_id": workplan_id})
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/api/patch/generate", methods=["POST"])
def api_generate_patch():
    data = request.json or {}
    instruction = data.get("instruction", "")
    project_path = data.get("project_path", "")
    model = data.get("model", DEFAULT_MODEL)

    if not instruction:
        return jsonify({"error": "Missing instruction"}), 400

    try:
        if not vectordb:
            init_vectordb(project_path)

        context_texts = retrieve_context(instruction, k=12)

        system_prompt = """You are a professional code assistant. Generate ONLY a valid git unified diff patch.
Output format: git diff -U3 style patch that can be applied with `git apply`.
No explanations, no markdown, just the patch content."""

        context_str = "\n\n".join(context_texts[:5])
        user_content = f"Instruction: {instruction}\n\nProject root: {project_path}\n\nContext:\n{context_str}\n\nGenerate patch:"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        response = chat_with_lmstudio(messages, model=model, max_tokens=3000)

        patch_content = ""
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line.decode().replace("data: ", ""))
                    if "choices" in chunk and len(chunk["choices"]) > 0:
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            patch_content += delta["content"]
                except:
                    pass

        return jsonify({"ok": True, "patch": patch_content})
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/api/logs", methods=["GET"])
def api_logs():
    return jsonify({
        "lmstudio": LMSTUDIO_URL,
        "model": DEFAULT_MODEL,
        "chroma_dir": CHROMA_DIR,
        "vectordb_loaded": vectordb is not None,
        "database": DB_PATH
    })


@app.route("/api/files/read", methods=["POST"])
def api_read_file():
    data = request.json or {}
    project_path = data.get("project_path")
    file_path = data.get("file_path")

    if not project_path or not file_path:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        ops = get_file_ops(project_path)
        result = ops.read_file(file_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/files/write", methods=["POST"])
def api_write_file():
    data = request.json or {}
    project_path = data.get("project_path")
    file_path = data.get("file_path")
    content = data.get("content", "")
    overwrite = data.get("overwrite", True)

    if not project_path or not file_path:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        ops = get_file_ops(project_path)
        result = ops.write_file(file_path, content, overwrite)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/files/append", methods=["POST"])
def api_append_file():
    data = request.json or {}
    project_path = data.get("project_path")
    file_path = data.get("file_path")
    content = data.get("content", "")

    if not project_path or not file_path:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        ops = get_file_ops(project_path)
        result = ops.append_file(file_path, content)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/files/delete", methods=["POST"])
def api_delete_file():
    data = request.json or {}
    project_path = data.get("project_path")
    file_path = data.get("file_path")

    if not project_path or not file_path:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        ops = get_file_ops(project_path)
        result = ops.delete_file(file_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/files/list", methods=["POST"])
def api_list_directory():
    data = request.json or {}
    project_path = data.get("project_path")
    dir_path = data.get("dir_path", ".")

    if not project_path:
        return jsonify({"error": "Missing project_path"}), 400

    try:
        ops = get_file_ops(project_path)
        result = ops.list_directory(dir_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/files/mkdir", methods=["POST"])
def api_create_directory():
    data = request.json or {}
    project_path = data.get("project_path")
    dir_path = data.get("dir_path")

    if not project_path or not dir_path:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        ops = get_file_ops(project_path)
        result = ops.create_directory(dir_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/files/rmdir", methods=["POST"])
def api_delete_directory():
    data = request.json or {}
    project_path = data.get("project_path")
    dir_path = data.get("dir_path")

    if not project_path or not dir_path:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        ops = get_file_ops(project_path)
        result = ops.delete_directory(dir_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/files/rename", methods=["POST"])
def api_rename_file():
    data = request.json or {}
    project_path = data.get("project_path")
    old_path = data.get("old_path")
    new_path = data.get("new_path")

    if not project_path or not old_path or not new_path:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        ops = get_file_ops(project_path)
        result = ops.rename_file(old_path, new_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/files/copy", methods=["POST"])
def api_copy_file():
    data = request.json or {}
    project_path = data.get("project_path")
    source_path = data.get("source_path")
    dest_path = data.get("dest_path")

    if not project_path or not source_path or not dest_path:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        ops = get_file_ops(project_path)
        result = ops.copy_file(source_path, dest_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/files/info", methods=["POST"])
def api_file_info():
    data = request.json or {}
    project_path = data.get("project_path")
    file_path = data.get("file_path")

    if not project_path or not file_path:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        ops = get_file_ops(project_path)
        result = ops.get_file_info(file_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/files/search", methods=["POST"])
def api_search_files():
    data = request.json or {}
    project_path = data.get("project_path")
    pattern = data.get("pattern", "*")
    dir_path = data.get("dir_path", ".")

    if not project_path or not pattern:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        ops = get_file_ops(project_path)
        result = ops.search_files(pattern, dir_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/projects", methods=["GET"])
def api_get_projects():
    try:
        projects = db.get_projects()
        return jsonify({"ok": True, "projects": projects})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects", methods=["POST"])
def api_create_project():
    data = request.json or {}
    name = data.get("name")
    path = data.get("path")

    if not name or not path:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        project_id = str(uuid.uuid4())
        db.create_project(project_id, name, path)
        return jsonify({"ok": True, "project_id": project_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/conversations/<project_id>", methods=["GET"])
def api_get_conversations(project_id):
    try:
        conversations = db.get_conversations(project_id)
        return jsonify({"ok": True, "conversations": conversations})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/conversations", methods=["POST"])
def api_create_conversation():
    data = request.json or {}
    project_id = data.get("project_id")
    title = data.get("title")
    model = data.get("model", DEFAULT_MODEL)

    if not project_id:
        return jsonify({"error": "Missing project_id"}), 400

    try:
        conversation_id = str(uuid.uuid4())
        db.create_conversation(conversation_id, project_id, title or "New Conversation", model)
        return jsonify({"ok": True, "conversation_id": conversation_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/messages/<conversation_id>", methods=["GET"])
def api_get_messages(conversation_id):
    try:
        messages = db.get_messages(conversation_id)
        return jsonify({"ok": True, "messages": messages})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/messages", methods=["POST"])
def api_create_message():
    data = request.json or {}
    conversation_id = data.get("conversation_id")
    role = data.get("role")
    content = data.get("content")

    if not conversation_id or not role or not content:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        message_id = str(uuid.uuid4())
        db.create_message(message_id, conversation_id, role, content)
        return jsonify({"ok": True, "message_id": message_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    os.makedirs(CHROMA_DIR, exist_ok=True)
    print(f"LM Studio: {LMSTUDIO_URL}")
    print(f"Default Model: {DEFAULT_MODEL}")
    print(f"Chroma DB: {CHROMA_DIR}")
    print(f"Database: {DB_PATH}")
    print(f"Web Search: {WEB_SEARCH_API}")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
