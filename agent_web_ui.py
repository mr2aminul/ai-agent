# agent_web_ui.py
import os, time, threading, json, traceback, subprocess, sqlite3
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import requests  # <-- fixed missing import

# embeddings & vector DB
from langchain_community.embeddings import SentenceTransformerEmbeddings
try:
    from langchain.vectorstores import Chroma
except Exception:
    from langchain_community.vectorstores import Chroma

from git import Repo

# ---------------- CONFIG ----------------
LMSTUDIO_URL = os.environ.get("LMSTUDIO_URL", "http://localhost:1234/v1")
DEFAULT_GEN_MODEL = os.environ.get("GEN_MODEL", "gpt-oss-20b")
USE_LMSTUDIO_EMBEDDINGS = False
LMSTUDIO_EMBED_MODEL = os.environ.get("LMSTUDIO_EMBED_MODEL", "text-embedding-3-small")

DEFAULT_EMBED_MODEL = "all-MiniLM-L6-v2"
CHROMA_BASE = os.path.abspath(os.environ.get("CHROMA_DIR", "./chroma_db"))
BRANCH_PREFIX = "llm/changes-"
CHUNK_SIZE = 1000
CODE_EXTENSIONS_DEFAULT = [".php", ".js", ".html", ".css", ".json", ".py"]
IGNORE_DIRS_DEFAULT = ["node_modules", "vendor", ".git", "assets/images", "lib"]

DB_PATH = os.path.abspath(os.environ.get("AGENT_DB", "./agent_data.db"))
# ----------------------------------------

app = Flask(__name__)
CORS(app)

# In-memory state
STATE = {
    "project_path": None,
    "exclude_exts": [],
    "exclude_dirs": [],
    "indexing": False,
    "last_index_time": None,
    "watcher_running": False,
    "last_error": None,
    "indexed_files": 0,
    "selected_model": DEFAULT_GEN_MODEL
}

# Globals for runtime
embedder = SentenceTransformerEmbeddings(model_name=DEFAULT_EMBED_MODEL)
vectordb = None
repo = None
observer = None

# ---------------- SQLite helpers ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_path TEXT,
                    model TEXT,
                    title TEXT,
                    created_at TEXT
                 )""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conv_id INTEGER,
                    role TEXT,
                    content TEXT,
                    created_at TEXT,
                    FOREIGN KEY(conv_id) REFERENCES conversations(id)
                 )""")
    conn.commit()
    return conn

DB = init_db()

def create_conversation(project_path, model, title=None):
    now = datetime.utcnow().isoformat()
    cur = DB.cursor()
    cur.execute("INSERT INTO conversations (project_path, model, title, created_at) VALUES (?,?,?,?)",
                (project_path, model, title or "", now))
    DB.commit()
    return cur.lastrowid

def save_message(conv_id, role, content):
    now = datetime.utcnow().isoformat()
    cur = DB.cursor()
    cur.execute("INSERT INTO messages (conv_id, role, content, created_at) VALUES (?,?,?,?)",
                (conv_id, role, content, now))
    DB.commit()
    return cur.lastrowid

def get_conversations_for_project(project_path):
    cur = DB.cursor()
    cur.execute("SELECT id, model, title, created_at FROM conversations WHERE project_path=? ORDER BY id DESC", (project_path,))
    return [{"id": r[0], "model": r[1], "title": r[2], "created_at": r[3]} for r in cur.fetchall()]

def get_messages_for_conv(conv_id):
    cur = DB.cursor()
    cur.execute("SELECT id, role, content, created_at FROM messages WHERE conv_id=? ORDER BY id ASC", (conv_id,))
    return [{"id": r[0], "role": r[1], "content": r[2], "created_at": r[3]} for r in cur.fetchall()]

# ---------------- File utilities ----------------
def safe_join_project(p):
    return os.path.abspath(p)

def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""

def chunk_text(text, size=CHUNK_SIZE):
    lines = text.splitlines()
    cur, cur_len = [], 0
    for ln in lines:
        cur.append(ln)
        cur_len += len(ln)
        if cur_len > size:
            yield "\n".join(cur)
            cur, cur_len = [], 0
    if cur:
        yield "\n".join(cur)

# ---------------- Indexing ----------------
def init_vectordb_for_project(project_path):
    global vectordb
    key = project_path.replace(":", "").replace("\\", "_").replace("/", "_")
    persist_dir = os.path.join(CHROMA_BASE, key)
    os.makedirs(persist_dir, exist_ok=True)
    vectordb = Chroma(persist_directory=persist_dir, embedding_function=embedder)
    return vectordb

def index_project(project_path, exts, ignore_dirs):
    global STATE, vectordb, repo
    STATE["indexing"] = True
    STATE["last_error"] = None
    STATE["indexed_files"] = 0
    try:
        init_vectordb_for_project(project_path)
        if not os.path.exists(os.path.join(project_path, ".git")):
            repo = Repo.init(project_path)
        else:
            repo = Repo(project_path)

        total = 0
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for f in files:
                if any(f.endswith(ext) for ext in exts):
                    total += 1
                    path = os.path.join(root, f)
                    text = read_text(path)
                    if not text.strip(): continue
                    chunks = list(chunk_text(text))
                    ids = [f"{path}__{i}" for i in range(len(chunks))]
                    metadatas = [{"path": path, "chunk_index": i} for i in range(len(chunks))]
                    try:
                        vectordb.add_texts(texts=chunks, metadatas=metadatas, ids=ids)
                    except Exception:
                        client = vectordb._client
                        if "project_code" not in [c.name for c in client.list_collections()]:
                            client.create_collection("project_code")
                        col = client.get_collection("project_code")
                        col.add(ids=ids, documents=chunks, metadatas=metadatas)
                        client.persist()
                    STATE["indexed_files"] += 1
        vectordb.persist()
        STATE["last_index_time"] = datetime.utcnow().isoformat()
        STATE["indexing"] = False
        return {"ok": True, "indexed": STATE["indexed_files"], "total_files": total}
    except Exception as e:
        STATE["last_error"] = str(e) + "\n" + traceback.format_exc()
        STATE["indexing"] = False
        return {"ok": False, "error": STATE["last_error"]}

# ---------------- Watcher ----------------
class ProjectChangeHandler(FileSystemEventHandler):
    def __init__(self, exts, ignore_dirs):
        self.exts = exts
        self.ignore_dirs = ignore_dirs
    def on_modified(self, event):
        if event.is_directory: return
        if any(event.src_path.endswith(ext) for ext in self.exts):
            try:
                path = event.src_path
                text = read_text(path)
                if not text.strip(): return
                chunks = list(chunk_text(text))
                ids = [f"{path}__{i}" for i in range(len(chunks))]
                metadatas = [{"path": path, "chunk_index": i} for i in range(len(chunks))]
                vectordb.add_texts(texts=chunks, metadatas=metadatas, ids=ids)
                vectordb.persist()
            except Exception as e:
                print("[WATCHER ERR]", e)

def start_watcher(project_path, exts, ignore_dirs):
    global observer
    if observer:
        try:
            observer.stop()
        except:
            pass
    handler = ProjectChangeHandler(exts, ignore_dirs)
    observer = Observer()
    observer.schedule(handler, project_path, recursive=True)
    observer.start()
    STATE["watcher_running"] = True
    print("[WATCHER] started")

def stop_watcher():
    global observer
    if observer:
        observer.stop()
        observer.join(timeout=1)
    STATE["watcher_running"] = False

# ---------------- LLM helpers ----------------
def lmstudio_models():
    try:
        r = requests.get(f"{LMSTUDIO_URL}/models", timeout=30)
        r.raise_for_status()
        data = r.json()
        # try to normalize various shapes
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "models" in data:
            return data["models"]
        return data
    except Exception as e:
        return {"error": str(e)}

def lmstudio_chat(messages, model, max_tokens=2000, temperature=0):
    url = f"{LMSTUDIO_URL}/chat/completions"
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()

def lmstudio_completions(prompt, model, max_tokens=2000, temperature=0):
    url = f"{LMSTUDIO_URL}/completions"
    payload = {"model": model, "prompt": prompt, "max_tokens": max_tokens, "temperature": temperature}
    r = requests.post(url, json=payload, timeout=180)
    r.raise_for_status()
    return r.json()

def retrieve_context(query, k=6):
    try:
        docs = vectordb.similarity_search(query, k=k)
        texts = [d.page_content if hasattr(d, "page_content") else str(d) for d in docs]
        meta = [{"path": getattr(d, "metadata", {}).get("path", "")} for d in docs]
        return texts, meta
    except Exception:
        try:
            client = vectordb._client
            res = client.query(query_texts=[query], n_results=k)
            texts = res["documents"][0]
            return texts, [{"path": m.get("path","")} for m in res["metadatas"][0]]
        except Exception as e:
            return [], []

# ---------------- Patch apply utilities ----------------
def apply_git_patch(project_path, patch_text):
    try:
        r = Repo(project_path)
        branch = BRANCH_PREFIX + datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        r.git.checkout("-b", branch)
        proc = subprocess.Popen(["git", "apply", "-"], cwd=project_path, stdin=subprocess.PIPE, text=True)
        out, err = proc.communicate(patch_text)
        if proc.returncode != 0:
            return {"ok": False, "error": f"git apply failed: {out} {err}"}
        r.git.add(all=True)
        r.index.commit("LLM applied patch")
        return {"ok": True, "branch": branch}
    except Exception as e:
        return {"ok": False, "error": str(e) + "\n" + traceback.format_exc()}

# ---------------- Flask routes / UI ----------------
INDEX_HTML = """
<!doctype html>
<title>Local Project Agent</title>
<style>
body{font-family:Inter,Segoe UI,Arial;margin:18px}
.container{display:flex;gap:20px}
.panel{flex:1;padding:12px;border:1px solid #ddd;border-radius:8px}
textarea{width:100%;height:120px}
input[type=text]{width:100%}
.small{font-size:0.9em;color:#666}
button{padding:8px 12px;margin-top:6px}
.file-list{max-height:200px;overflow:auto;border:1px solid #eee;padding:6px}
.row{display:flex;gap:8px}
</style>
<h2>Local Project Agent UI</h2>
<div class="container">
  <div class="panel">
    <h3>Project</h3>
    <label>Project Path</label>
    <input id="project_path" type="text" value="{{project_path or ''}}" placeholder="C:\\xampp\\htdocs">
    <label>Model (select)</label>
    <select id="model_select"></select>
    <label>Exclude extensions (comma)</label>
    <input id="ex_ext" type="text" value="{{ex_ext or ''}}">
    <label>Exclude dirs (comma)</label>
    <input id="ex_dir" type="text" value="{{ex_dir or ''}}">
    <div class="row"><button onclick="loadProject()">Load project & index</button> <button onclick="reindex()">Reindex</button></div>
    <p class="small">Status: <span id="status">{{status}}</span></p>

    <h4>Chat / Conversations</h4>
    <div class="row">
      <input id="conv_title" placeholder="Conversation title (optional)"/>
      <button onclick="createChat()">Create Chat</button>
    </div>
    <div class="small">Active conv id: <span id="active_conv">none</span></div>
    <div id="conversations" class="small"></div>

    <h4>Actions</h4>
    <textarea id="instruction" placeholder="Instruction for change or plan..."></textarea>
    <div class="row"><button onclick="generatePlan()">Generate Work Plan</button> <button onclick="previewPatch()">Preview Patch</button> <button onclick="applyPatch()">Apply Patch</button></div>
  </div>

  <div class="panel">
    <h3>Chat (project-aware)</h3>
    <div id="chat" style="height:300px;overflow:auto;border:1px solid #eee;padding:8px"></div>
    <textarea id="chat_input" placeholder="Ask about the project or request code changes..."></textarea>
    <div class="row"><button onclick="sendChat()">Send</button> <button onclick="loadConversations()">Reload convs</button></div>

    <h4>Index & files</h4>
    <div class="small">Indexed files: <span id="idx_count">{{indexed}}</span></div>
    <div class="file-list" id="file_list"></div>
  </div>
</div>

<script>
let activeConv = null;
async function loadModels(){
  const res = await fetch('/api/models');
  const j = await res.json();
  const sel = document.getElementById('model_select');
  sel.innerHTML = '';
  if(j.error){ sel.innerHTML = '<option>Error</option>'; return; }
  const list = j.models || j;
  for(const m of list){
    const id = (typeof m == 'string') ? m : (m.id || m.model || m.name || JSON.stringify(m));
    const opt = document.createElement('option'); opt.value = id; opt.innerText = id;
    sel.appendChild(opt);
  }
  // set default
  sel.value = "{{selected_model}}";
}
async function loadProject(){
  const p = document.getElementById('project_path').value;
  const ex1 = document.getElementById('ex_ext').value;
  const ex2 = document.getElementById('ex_dir').value;
  const model = document.getElementById('model_select').value;
  const res = await fetch('/api/load_project', {method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({path:p,exclude_exts:ex1,exclude_dirs:ex2,model:model})});
  const j = await res.json();
  alert(JSON.stringify(j));
  getStatus();
  loadConversations();  
}
async function reindex(){
  const res = await fetch('/api/reindex',{method:'POST'});
  const j = await res.json();
  alert(JSON.stringify(j));
  getStatus();
}
async function getStatus(){
  const res = await fetch('/api/status');
  const j = await res.json();
  document.getElementById('status').innerText = JSON.stringify(j);
  document.getElementById('idx_count').innerText = j.indexed_files||0;
  const fl = await fetch('/api/files');
  const jf = await fl.json();
  document.getElementById('file_list').innerText = jf.files.join('\\n');
}
async function loadConversations(){
  const path = document.getElementById('project_path').value;
  if(!path) return;
  const res = await fetch('/api/conversations?path=' + encodeURIComponent(path));
  const j = await res.json();
  const container = document.getElementById('conversations');
  container.innerHTML = '';
  for(const c of j.conversations || []){
    const btn = document.createElement('button');
    btn.innerText = `#${c.id} ${c.title||''} (${c.model})`;
    btn.onclick = ()=>{ setActiveConv(c.id); };
    container.appendChild(btn);
    container.appendChild(document.createElement('br'));
  }
}
function setActiveConv(id){
  activeConv = id;
  document.getElementById('active_conv').innerText = id;
  loadMessages(id);
}
async function createChat(){
  const path = document.getElementById('project_path').value;
  const model = document.getElementById('model_select').value;
  const title = document.getElementById('conv_title').value;
  const res = await fetch('/api/create_chat', {method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({path, model, title})});
  const j = await res.json();
  if(j.ok){ loadConversations(); setActiveConv(j.conv_id); } else alert(JSON.stringify(j));
}
async function loadMessages(conv_id){
  const res = await fetch('/api/messages?conv_id=' + conv_id);
  const j = await res.json();
  const chat = document.getElementById('chat');
  chat.innerText = '';
  for(const m of j.messages || []){
    chat.innerText += `${m.created_at} ${m.role}:\\n${m.content}\\n\\n`;
  }
}
async function sendChat(){
  const q = document.getElementById('chat_input').value;
  if(!q) return alert('Type a message');
  if(!activeConv) {
    if(!confirm('No conversation selected — create one using "Create Chat"? Press OK to auto-create.')) {
      return;
    }
    await createChat();
  }
  const model = document.getElementById('model_select').value;
  const res = await fetch('/api/chat',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({q:q, conv_id: activeConv, model: model})});
  const j = await res.json();
  if(j.ok){
    loadMessages(activeConv);
    document.getElementById('chat_input').value = '';
  } else {
    alert(JSON.stringify(j));
  }
}
async function generatePlan(){
  const instr = document.getElementById('instruction').value;
  const model = document.getElementById('model_select').value;
  const res = await fetch('/api/plan',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({instruction:instr, model})});
  const j = await res.json();
  alert("Plan:\\n" + (j.plan||j.error));
}
async function previewPatch(){
  const instr = document.getElementById('instruction').value;
  const model = document.getElementById('model_select').value;
  const res = await fetch('/api/preview_patch',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({instruction:instr, model})});
  const j = await res.json();
  if(j.patch) {
    const win = window.open('', '_blank');
    win.document.write('<pre>' + j.patch.replace(/</g,'&lt;') + '</pre>');
  } else {
    alert('No patch returned: ' + JSON.stringify(j));
  }
}
async function applyPatch(){
  const instr = document.getElementById('instruction').value;
  const model = document.getElementById('model_select').value;
  if(!confirm('Apply patch generated by model? This will create a git branch and commit.')) return;
  const res = await fetch('/api/apply_patch',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({instruction:instr, model})});
  const j = await res.json();
  alert(JSON.stringify(j));
  getStatus();
}
window.onload = ()=>{ loadModels(); getStatus(); loadConversations(); };
</script>
"""

@app.route("/")
def index():
    return render_template_string(INDEX_HTML,
        project_path=STATE.get("project_path",""),
        ex_ext=",".join(STATE.get("exclude_exts", [])),
        ex_dir=",".join(STATE.get("exclude_dirs", [])),
        status=json.dumps(STATE),
        indexed=STATE.get("indexed_files",0),
        selected_model=STATE.get("selected_model", DEFAULT_GEN_MODEL)
    )

# API endpoints for models, conversations, files, chat, plan, preview, apply etc.

@app.route("/api/models")
def api_models():
    try:
        r = requests.get(f"{LMSTUDIO_URL}/models", timeout=30)
        r.raise_for_status()
        data = r.json()
        # LM Studio response has models under data[]
        models = []
        if isinstance(data, dict) and "data" in data:
            for m in data["data"]:
                mid = m.get("id") or m.get("model") or str(m)
                models.append(mid)
        elif isinstance(data, list):
            models = [str(m) for m in data]
        return jsonify({"models": models})
    except Exception as e:
        return jsonify({"error": str(e), "models":[]})

@app.route("/api/load_project", methods=["POST"])
def api_load_project():
    payload = request.json
    path = payload.get("path")
    if not path or not os.path.isdir(path):
        return jsonify({"ok": False, "error": "Invalid project path"}), 400
    ex_ext = payload.get("exclude_exts","")
    ex_dir = payload.get("exclude_dirs","")
    ex_exts = [e.strip() for e in ex_ext.split(",") if e.strip()] if ex_ext else CODE_EXTENSIONS_DEFAULT
    ex_dirs = [d.strip() for d in ex_dir.split(",") if d.strip()] if ex_dir else IGNORE_DIRS_DEFAULT
    model = payload.get("model") or DEFAULT_GEN_MODEL
    STATE["project_path"] = os.path.abspath(path)
    STATE["exclude_exts"] = ex_exts
    STATE["exclude_dirs"] = ex_dirs
    STATE["selected_model"] = model
    t = threading.Thread(target=index_project, args=(STATE["project_path"], ex_exts, ex_dirs), daemon=True)
    t.start()
    start_watcher(STATE["project_path"], ex_exts, ex_dirs)
    return jsonify({"ok": True, "project": STATE["project_path"], "exclude_exts": ex_exts, "exclude_dirs": ex_dirs, "model": model})

@app.route("/api/reindex", methods=["POST"])
def api_reindex():
    if not STATE.get("project_path"):
        return jsonify({"ok": False, "error": "Project not loaded"}), 400
    res = index_project(STATE["project_path"], STATE["exclude_exts"] or CODE_EXTENSIONS_DEFAULT, STATE["exclude_dirs"] or IGNORE_DIRS_DEFAULT)
    return jsonify(res)

@app.route("/api/status")
def api_status():
    return jsonify(STATE)

@app.route("/api/files")
def api_files():
    try:
        p = STATE.get("project_path")
        files = []
        for root, dirs, filenames in os.walk(p):
            dirs[:] = [d for d in dirs if d not in STATE.get("exclude_dirs",[])]
            for fn in filenames:
                if any(fn.endswith(ext) for ext in (STATE.get("exclude_exts") or CODE_EXTENSIONS_DEFAULT)):
                    files.append(os.path.join(root, fn))
        return jsonify({"files": files[:500]})
    except Exception:
        return jsonify({"files": []})

@app.route("/api/conversations")
def api_conversations():
    p = request.args.get("path") or STATE.get("project_path")
    if not p: return jsonify({"conversations": []})
    convs = get_conversations_for_project(p)
    return jsonify({"conversations": convs})

@app.route("/api/create_chat", methods=["POST"])
def api_create_chat():
    data = request.json or {}
    path = data.get("path") or STATE.get("project_path")
    model = data.get("model") or STATE.get("selected_model") or DEFAULT_GEN_MODEL
    title = data.get("title") or ""
    if not path: return jsonify({"ok": False, "error": "project path required"}), 400
    conv_id = create_conversation(path, model, title)
    return jsonify({"ok": True, "conv_id": conv_id})

@app.route("/api/messages")
def api_messages():
    conv_id = request.args.get("conv_id")
    if not conv_id: return jsonify({"messages": []})
    msgs = get_messages_for_conv(conv_id)
    return jsonify({"messages": msgs})

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.json or {}
    q = data.get("q","")
    conv_id = data.get("conv_id")
    model = data.get("model") or STATE.get("selected_model") or DEFAULT_GEN_MODEL
    if not q: return jsonify({"ok": False, "error": "empty query"})
    if not conv_id:
        conv_id = create_conversation(STATE.get("project_path") or "", model, title="auto")
    # save user message
    save_message(conv_id, "user", q)
    # get context
    ctx_texts, meta = retrieve_context(q, k=6)
    system = {"role":"system","content":"You are a helpful code assistant with full access to the project. Use the provided project context when answering."}
    user = {"role":"user","content": f"Query: {q}\n\nRelevant project files:\n" + "\n\n".join(ctx_texts)}
    try:
        resp = lmstudio_chat([system, user], model=model)
        ans = ""
        if "choices" in resp and len(resp["choices"])>0:
            c = resp["choices"][0]
            if "message" in c:
                ans = c["message"].get("content","")
            else:
                ans = c.get("text","")
        else:
            ans = str(resp)
        save_message(conv_id, "assistant", ans)
        return jsonify({"ok": True, "answer": ans, "conv_id": conv_id})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "trace": traceback.format_exc()})

@app.route("/api/plan", methods=["POST"])
def api_plan():
    data = request.json or {}
    instr = data.get("instruction","")
    model = data.get("model") or STATE.get("selected_model") or DEFAULT_GEN_MODEL
    if not instr: return jsonify({"ok": False, "error":"no instruction"}), 400
    ctx_texts, meta = retrieve_context(instr, k=8)
    prompt = f"""You are a senior engineer. The project root is {STATE.get('project_path')}. The instruction is:
{instr}

Here are relevant code snippets:
{''.join(['\\n---\\n'+t for t in ctx_texts])}

Produce a prioritized, step-by-step work plan to implement this instruction. Each step should be short and reference files or modules to edit. Output as numbered list."""
    try:
        resp = lmstudio_completions(prompt, model=model, max_tokens=800)
        text = ""
        if "choices" in resp and len(resp["choices"])>0:
            text = resp["choices"][0].get("text","")
        return jsonify({"ok": True, "plan": text})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "trace": traceback.format_exc()})

@app.route("/api/preview_patch", methods=["POST"])
def api_preview_patch():
    data = request.json or {}
    instr = data.get("instruction","")
    model = data.get("model") or STATE.get("selected_model") or DEFAULT_GEN_MODEL
    if not instr: return jsonify({"ok": False, "error":"no instruction"}), 400
    ctx_texts, meta = retrieve_context(instr, k=12)
    prompt = f"""You are a professional code assistant.
The file(s) to modify are in project root {STATE.get('project_path')}. Instruction:
{instr}

Project context (relevant chunks):
{''.join(['\\n---\\n'+t for t in ctx_texts])}

Return only a git unified diff patch (the output of `git diff -U3`) that applies to files under the project root. Do not include any other text."""
    try:
        resp = lmstudio_completions(prompt, model=model, max_tokens=2000)
        patch = ""
        if "choices" in resp and len(resp["choices"])>0:
            patch = resp["choices"][0].get("text","")
        return jsonify({"ok": True, "patch": patch})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "trace": traceback.format_exc()})

@app.route("/api/apply_patch", methods=["POST"])
def api_apply_patch():
    data = request.json or {}
    instr = data.get("instruction","")
    model = data.get("model") or STATE.get("selected_model") or DEFAULT_GEN_MODEL
    if not instr: return jsonify({"ok": False, "error":"no instruction"}), 400
    preview_resp = api_preview_patch()
    preview_j = preview_resp.get_json()
    if not preview_j.get("ok"):
        return jsonify({"ok": False, "error": "preview failed", "details": preview_j}), 400
    patch = preview_j.get("patch","")
    if not patch.strip():
        return jsonify({"ok": False, "error":"empty patch"}), 400
    res = apply_git_patch(STATE.get("project_path"), patch)
    return jsonify(res)

@app.route("/api/logs")
def api_logs():
    return jsonify({"state": STATE})

@app.route("/api/download_index")
def api_download_index():
    p = CHROMA_BASE
    zipname = os.path.join(".", "chroma_export.zip")
    try:
        import zipfile
        with zipfile.ZipFile(zipname, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(p):
                for f in files:
                    zf.write(os.path.join(root,f), arcname=os.path.relpath(os.path.join(root,f), p))
        return send_file(zipname, as_attachment=True)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

# ---------------- Run app ----------------
if __name__ == "__main__":
    os.makedirs(CHROMA_BASE, exist_ok=True)
    print("LM Studio:", LMSTUDIO_URL, "default-model:", DEFAULT_GEN_MODEL, "DB:", DB_PATH)
    app.run(host="0.0.0.0", port=5000, debug=True)
