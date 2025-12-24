from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from .firebase_service import (
    get_users,
    get_items,
    delete_item,
    get_matches,
    get_dashboard_stats,
    search_users,
    search_items,
    search_matches,
    set_user_status,
    compute_matches
)

bp = Blueprint('routes', __name__)
admin = Blueprint("admin", __name__, url_prefix="/admin")


# -------------------------------
# ADMIN LOGIN
# -------------------------------
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        admin_credentials = current_app.config.get("ADMIN_CREDENTIALS", {})

        if email in admin_credentials and password == admin_credentials[email]:
            user = User(email)
            login_user(user)
            flash("Login successful", "success")
            return redirect(url_for("routes.dashboard"))
        else:
            flash("Invalid email or password", "danger")

    return render_template("login.html")


# -------------------------------
# LOGOUT
# -------------------------------
@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("routes.login"))


# -------------------------------
# DASHBOARD
# -------------------------------
@bp.route("/")
@login_required
def dashboard():
    stats = get_dashboard_stats()
    return render_template("dashboard.html", stats=stats)


# -------------------------------
# USERS
# -------------------------------
@bp.route("/users")
@login_required
def users():
    query = request.args.get("q", "")
    users = search_users(query) if query else get_users()
    return render_template("users.html", users=users, search_query=query)


@admin.post("/users/<uid>")
def toggle_user(uid: str):
    disabled_flag = request.form.get("disabled", "true").lower() == "true"
    ok = set_user_status(uid, disabled_flag)

    flash(
        f"User {'disabled' if disabled_flag else 'enabled'} successfully!"
        if ok else
        "Something went wrong. Please try again.",
        "success" if ok else "danger"
    )
    return redirect(url_for("routes.users"))


# -------------------------------
# LOST / FOUND ITEMS
# -------------------------------
@bp.route("/items/<collection>")
@login_required
def items(collection):
    query = request.args.get("q", "")
    items = search_items(collection, query) if query else get_items(collection)
    return render_template("items.html", items=items, collection=collection, search_query=query)


@bp.route("/delete_item", methods=["POST"])
@login_required
def delete_item_route():
    data = request.get_json()
    success = delete_item(
        data["collection"],
        data["id"],
        data.get("image_public_id")
    )
    return jsonify(success=success)


# -------------------------------
# MATCHES
# -------------------------------
@bp.route("/matches")
@login_required
def matches():
    query = request.args.get("q", "").lower()
    all_matches = compute_matches()

    if query:
        def hit(m):
            return (
                query in m["lost"]["item"].lower()
                or query in m["found"]["item"].lower()
                or query in (
                    m["lost"].get("description", "")
                    + m["found"].get("description", "")
                ).lower()
            )

        all_matches = list(filter(hit, all_matches))

    return render_template(
        "matches.html",
        matches=all_matches,
        search_query=query
    )


# -------------------------------
# GLOBAL SEARCH
# -------------------------------
@bp.route("/search")
@login_required
def global_search():
    query = request.args.get("q", "")
    if not query:
        return redirect(url_for("routes.dashboard"))

    results = {
        "users": search_users(query),
        "lost_items": search_items("lost_items", query),
        "found_items": search_items("found_items", query),
        "matches": search_matches(query)
    }

    return render_template(
        "search_results.html",
        results=results,
        query=query
    )


# -------------------------------
# API STATS
# -------------------------------
@bp.route("/api/stats")
@login_required
def api_stats():
    stats = get_dashboard_stats()
    return jsonify(stats)
