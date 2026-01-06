from flask import Flask, request, redirect
import json, os, uuid, datetime

app = Flask(__name__)
DATA_FILE = "data.json"

# ----------------- DATA -----------------

def load_data():
    if not os.path.exists(DATA_FILE):
        data = {
            "users": {
                "autor1": "passwort1",
                "autor2": "passwort2"
            },
            "projects": {}
        }
        save_data(data)
        return data

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Auto-Fix
    for pname, p in data.get("projects", {}).items():
        p.setdefault("chat", [])
        for key in ["characters","places","chapters","plots","times"]:
            p.setdefault(key, [])
            for i in p[key]:
                i.setdefault("id", str(uuid.uuid4()))
                i.setdefault("comments", [])

    save_data(data)
    return data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ----------------- LOGIN -----------------

SESSION = {"user": None}

def require_login():
    return SESSION["user"] is not None

@app.route("/login", methods=["GET","POST"])
def login():
    data = load_data()
    if request.method == "POST":
        u = request.form["user"]
        p = request.form["pass"]
        if u in data["users"] and data["users"][u] == p:
            SESSION["user"] = u
            return redirect("/")
    return """
    <h2>Login</h2>
    <form method="post">
    <input name="user" placeholder="Benutzer"><br>
    <input name="pass" type="password" placeholder="Passwort"><br>
    <button>Login</button>
    </form>
    """

@app.route("/logout")
def logout():
    SESSION["user"] = None
    return redirect("/login")

# ----------------- UI -----------------

def layout(title, content, sidebar=""):
    return f"""
    <html>
    <head>
    <title>{title}</title>
    <style>
    body {{ margin:0; font-family:Arial; background:#0f172a; color:#e5e7eb; }}
    a {{ color:#7dd3fc; text-decoration:none }}
    .app {{ display:flex; height:100vh }}
    .sidebar {{ width:240px; background:#020617; padding:20px }}
    .sidebar h2 {{ color:#38bdf8 }}
    .main {{ flex:1; padding:20px; overflow:auto }}
    .card {{ background:#020617; padding:15px; border-radius:12px; margin-bottom:15px }}
    .top {{ display:flex; justify-content:space-between; align-items:center }}
    input, textarea, button {{ width:100%; padding:10px; border-radius:8px; border:none; margin:5px 0 }}
    button {{ background:#38bdf8; color:#020617; font-weight:bold }}
    .chat {{ background:#000; padding:10px; border-radius:10px; max-height:300px; overflow:auto }}
    </style>
    </head>
    <body>
    <div class="app">
        <div class="sidebar">
            <h2>✍ AutorenTool</h2>
            {sidebar}
            <hr>
            <a href="/projects">📚 Projekte</a><br><br>
            <a href="/logout">🚪 Logout</a>
        </div>
        <div class="main">
            <div class="top">
                <h1>{title}</h1>
                <div>👤 {SESSION["user"]}</div>
            </div>
            {content}
        </div>
    </div>
    </body>
    </html>
    """

# ----------------- PROJECTS -----------------

@app.route("/", methods=["GET","POST"])
@app.route("/projects", methods=["GET","POST"])
def projects():
    if not require_login(): return redirect("/login")
    data = load_data()

    if request.method == "POST":
        name = request.form["name"]
        if name not in data["projects"]:
            data["projects"][name] = {
                "chat": [],
                "characters": [], "places": [], "chapters": [], "plots": [], "times": []
            }
            save_data(data)

    content = """
    <div class="card">
    <form method="post">
    <input name="name" placeholder="Neues Projekt">
    <button>Projekt erstellen</button>
    </form>
    </div>
    """

    for p in data["projects"]:
        content += f"""
        <div class="card">
            <a href="/project/{p}">📂 {p}</a><br><br>
            <a href="/delete_project/{p}">🗑 Löschen</a>
        </div>
        """

    return layout("Projekte", content)

@app.route("/delete_project/<project>")
def delete_project(project):
    if not require_login(): return redirect("/login")
    data = load_data()
    if project in data["projects"]:
        del data["projects"][project]
        save_data(data)
    return redirect("/projects")

# ----------------- PROJECT VIEW -----------------

@app.route("/project/<project>", methods=["GET","POST"])
def project(project):
    if not require_login(): return redirect("/login")
    data = load_data()
    p = data["projects"][project]

    if request.method == "POST":
        p["chat"].append({
            "user": SESSION["user"],
            "text": request.form["text"],
            "time": str(datetime.datetime.now())
        })
        save_data(data)

    chat = "<div class='chat'>"
    for m in p["chat"]:
        chat += f"<b>{m['user']}</b>: {m['text']}<br>"
    chat += "</div>"

    sidebar = f"""
    <b>📂 {project}</b><br><br>
    <a href="/list/{project}/chapters">📖 Kapitel</a><br>
    <a href="/list/{project}/characters">👤 Charaktere</a><br>
    <a href="/list/{project}/places">🏙 Orte</a><br>
    <a href="/list/{project}/plots">🧠 Plots</a><br>
    <a href="/list/{project}/times">⏳ Zeiten</a><br>
    """

    content = f"""
    <div class="card">
    <h3>💬 Projekt-Chat</h3>
    <form method="post">
    <textarea name="text"></textarea>
    <button>Senden</button>
    </form>
    {chat}
    </div>
    """

    return layout(project, content, sidebar)

# ----------------- GENERIC LIST -----------------

@app.route("/list/<project>/<key>", methods=["GET","POST"])
def list_items(project, key):
    if not require_login(): return redirect("/login")
    data = load_data()
    items = data["projects"][project][key]

    if request.method == "POST":
        items.append({
            "id": str(uuid.uuid4()),
            "name": request.form["name"],
            "desc": request.form["desc"],
            "comments": []
        })
        save_data(data)

    sidebar = f"""
    <b>📂 {project}</b><br><br>
    <a href="/project/{project}">⬅ Übersicht</a><br>
    <hr>
    <a href="/list/{project}/chapters">📖 Kapitel</a><br>
    <a href="/list/{project}/characters">👤 Charaktere</a><br>
    <a href="/list/{project}/places">🏙 Orte</a><br>
    <a href="/list/{project}/plots">🧠 Plots</a><br>
    <a href="/list/{project}/times">⏳ Zeiten</a><br>
    """

    content = f"""
    <div class="card">
    <form method="post">
    <input name="name" placeholder="Name">
    <textarea name="desc" placeholder="Beschreibung"></textarea>
    <button>Hinzufügen</button>
    </form>
    </div>
    """

    for i in items:
        content += f"""
        <div class="card">
        <b>{i['name']}</b><br>{i['desc']}<br><br>
        <a href="/edit/{project}/{key}/{i['id']}">✏ Bearbeiten</a> |
        <a href="/delete/{project}/{key}/{i['id']}">🗑 Löschen</a>
        </div>
        """

    return layout(key.capitalize(), content, sidebar)

# ----------------- EDIT -----------------

@app.route("/edit/<project>/<key>/<id>", methods=["GET","POST"])
def edit_item(project, key, id):
    if not require_login(): return redirect("/login")
    data = load_data()

    for i in data["projects"][project][key]:
        if i["id"] == id:
            if request.method == "POST":
                i["name"] = request.form["name"]
                i["desc"] = request.form["desc"]
                save_data(data)
                return redirect(f"/list/{project}/{key}")

            content = f"""
            <div class="card">
            <form method="post">
            <input name="name" value="{i['name']}">
            <textarea name="desc">{i['desc']}</textarea>
            <button>Speichern</button>
            </form>
            </div>
            """
            return layout("Bearbeiten", content)

    return "Nicht gefunden"

# ----------------- DELETE ITEM -----------------

@app.route("/delete/<project>/<key>/<id>")
def delete_item(project, key, id):
    if not require_login(): return redirect("/login")
    data = load_data()
    data["projects"][project][key] = [i for i in data["projects"][project][key] if i["id"] != id]
    save_data(data)
    return redirect(f"/list/{project}/{key}")

# ----------------- START -----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
