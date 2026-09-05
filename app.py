from flask import Flask, request, render_template, render_template_string, redirect, session
import subprocess
import requests
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = "support-portal-secret"


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]

        db = get_db()

        try:
            db.execute(
                "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                (username, password, email)
            )
            db.commit()
            message = "Account created successfully."
        except Exception:
            message = "Unable to create account."

        db.close()

    return render_template("register.html", message=message)


@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()

        query = (
            "SELECT * FROM users "
            "WHERE username = '" + username +
            "' AND password = '" + password + "'"
        )

        user = db.execute(query).fetchone()
        db.close()

        if user:
            session["username"] = user["username"]
            return redirect("/dashboard")

        message = "Invalid username or password."

    return render_template("login.html", message=message)

@app.route("/change-email", methods=["GET", "POST"])
def change_email():
    if "username" not in session:
        return redirect("/login")

    message = ""

    if request.method == "POST":
        email = request.form["email"]

        db = get_db()
        db.execute(
            "UPDATE users SET email = ? WHERE username = ?",
            (email, session["username"])
        )
        db.commit()
        db.close()

        message = "Email changed successfully."

    return render_template(
        "change_email.html",
        message=message
    )

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/login")

    db = get_db()
    tickets = db.execute("SELECT * FROM tickets").fetchall()
    db.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        tickets=tickets
    )

@app.route("/download")
def download():
    filename = request.args.get("file", "")

    filepath = "files/" + filename

    with open(filepath, "r") as f:
        content = f.read()

    return content

@app.route("/debug-info")
def debug_info():
    return {
        "app": "Support Portal",
        "environment": "development",
        "debug": app.debug,
        "database": "SQLite",
        "internal_path": "/var/www/support-portal"
    }

@app.route("/search")
def search():
    search_term = request.args.get("q", "")

    db = get_db()


    query = (
        "SELECT * FROM tickets "
        "WHERE title LIKE '%" + search_term +
        "%' OR description LIKE '%" + search_term + "%'"
    )

    tickets = db.execute(query).fetchall()
    db.close()

    return render_template(
        "search.html",
        search_term=search_term,
        tickets=tickets
    )


@app.route("/ping")
def ping():
    host = request.args.get("host", "")

    result = subprocess.check_output(
        "ping -c 1 " + host,
        shell=True,
        text=True,
        stderr=subprocess.STDOUT
    )

    return result


@app.route("/csrf")
def csrf():
    return render_template("csrf.html")


@app.route("/fetch")
def fetch():
    url = request.args.get("url", "")

    if not url:
        return "Missing URL"

    response = requests.get(url, timeout=5)

    return response.text


@app.route('/ssti')
def ssti():
    name = request.args.get("name", "")
    return render_template_string("Hello " + name)


if __name__ == "__main__":
    init_db()
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
