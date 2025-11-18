import os
import json
import time
import threading
import traceback
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests

from langchain_community.embeddings import SentenceTransformerEmbeddings
try:
    from langchain.vectorstores import Chroma
except Exception:
    from langchain_community.vectorstores import Chroma

from git import Repo

app = Flask(__name__)
CORS(app)

LMSTUDIO_URL = os.environ.get("PYTHON_LMSTUDIO_URL", "http://localhost:1234/v1")
DEFAULT_MODEL = os.environ.get("PYTHON_DEFAULT_MODEL", "gpt-oss-20b")
CHROMA_DIR = os.environ.get("PYTHON_CHROMA_DIR", "./chroma_db")
WEB_SEARCH_API = os.environ.get("WEB_SEARCH_API", "duckduckgo")

embedder = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
vectordb = None
repo = None


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

    if not instruction:
        return jsonify({"error": "Missing instruction"}), 400

    try:
        if not vectordb:
            init_vectordb(project_path)

        context_texts = retrieve_context(instruction, k=8)
        workplan = generate_workplan(instruction, context_texts)

        return jsonify({"ok": True, "workplan": workplan})
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
        "vectordb_loaded": vectordb is not None
    })


if __name__ == "__main__":
    os.makedirs(CHROMA_DIR, exist_ok=True)
    print(f"LM Studio: {LMSTUDIO_URL}")
    print(f"Default Model: {DEFAULT_MODEL}")
    print(f"Chroma DB: {CHROMA_DIR}")
    print(f"Web Search: {WEB_SEARCH_API}")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)

