from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user

from models import User, MathProblems
from app import db

math = Blueprint(
	"math", 
	__name__, 
	static_folder="static",
	template_folder="./templates"
)

@math.route("/latex", methods=["GET", "POST"])
def latex():
	return render_template("math/latex.html")

@math.route("/problems", methods=["GET", "POST"])
def problems():
	return render_template("math/problems/index.html")

@math.route("/problems/post", methods=["GET", "POST"])
@login_required
def post():
	if request.method == "GET":
		return render_template("math/problems/post.html")
	else:
		if not db.session.query(MathProblems).filter_by(user=int(current_user.get_id()), content=request.form["content"], category=request.form["category"], unit=request.form["unit"]).first():
			problem = MathProblems(user=int(current_user.get_id()), title=request.form["title"], content=request.form["content"], explanation=request.form["explanation"], category=request.form["category"], unit=request.form["unit"])
			db.session.add(problem)
			db.session.commit()
		p = db.session.query(MathProblems).filter_by(user=int(current_user.get_id()), title=request.form["title"], content=request.form["content"], explanation=request.form["explanation"], category=request.form["category"], unit=request.form["unit"]).first()
		return redirect(url_for("math.problem", id=p.id))

@math.route("/problems/problem/<id>", methods=["GET", "POST"])
@login_required
def problem(id):
	p = db.session.query(MathProblems).get(id)
	if p==None:
		return "404"
	else:
		p = {"id":p.id, "userid":int(p.user), "user":User.query.get(p.user).email.split("@")[0], "title":p.title, "content":p.content, "explanation":p.explanation, "category":p.category, "unit":p.unit, "created_at":p.created_at}
		return render_template("math/problems/problem.html", data=p)

@math.route("/problems/problem/<id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
	p = db.session.query(MathProblems).get(id)
	if current_user.id == int(p.user):
		return jsonify({"id":p.id, "userid":int(p.user), "user":User.query.get(p.user).email.split("@")[0], "title":p.title, "content":p.content, "explanation":p.explanation, "category":p.category, "unit":p.unit, "created_at":p.created_at})
	else:
		return "403"