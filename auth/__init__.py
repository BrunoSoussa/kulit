from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from db import create_user, verify_user

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = verify_user(email, password)
        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("index"))
        flash("Credenciais inválidas", "error")
    return render_template("login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not name or not email or not password:
            flash("Preencha todos os campos", "error")
            return render_template("register.html")
        if password != confirm:
            flash("As senhas não coincidem", "error")
            return render_template("register.html")

        ok = create_user(name, email, password)
        if not ok:
            flash("E-mail já cadastrado", "error")
            return render_template("register.html")
        flash("Cadastro realizado! Faça login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@bp.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
