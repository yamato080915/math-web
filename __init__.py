from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort, flash
from flask_login import login_required, current_user

from models import User, MathProblems
from app import db

from random import randint

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
	data = {
		"my-problem": db.session.query(MathProblems).filter_by(user=int(current_user.get_id())).all(),
		"new": [x for x in db.session.query(MathProblems).all() if int(x.user)!=int(current_user.get_id())][-5:],
		"random": db.session.query(MathProblems).get(randint(1, db.session.query(MathProblems).count()))
	}
	return render_template("math/problems/index.html", data=data)

@math.route("/problems/all", methods=["GET", "POST"])
def problemsAll():
	return render_template("math/problems/all.html", data=db.session.query(MathProblems).all())

@math.route("/problems/post", methods=["GET", "POST"])
@login_required
def post():
	if request.method == "GET":
		return render_template("math/problems/post.html")
	else:
		try:
			score = list(map(int, request.form["score"].split("\r\n")))#例外処理
		except:
			flash("error.score")
			return redirect(url_for("math.post"))
		score = " ".join([str(x) for x in score])
		if not db.session.query(MathProblems).filter_by(user=int(current_user.get_id()), content=request.form["content"], category=request.form["category"], unit=request.form["unit"]).first():
			problem = MathProblems(user=int(current_user.get_id()), title=request.form["title"], content=request.form["content"], explanation=request.form["explanation"], category=request.form["category"], unit=request.form["unit"], score=score)
			db.session.add(problem)
			db.session.commit()
		p = db.session.query(MathProblems).filter_by(user=int(current_user.get_id()), title=request.form["title"], content=request.form["content"], explanation=request.form["explanation"], category=request.form["category"], unit=request.form["unit"], score=score).first()
		return redirect(url_for("math.problem", id=p.id).replace('index.cgi/', ''))

@math.route("/problems/problem/<id>", methods=["GET", "POST"])
def problem(id):
	p = db.session.query(MathProblems).get(id)
	if p==None:
		return "404"
	else:
		score = list(map(int, p.score.split()))
		if request.method=="GET":
			p = {"id":p.id, "userid":int(p.user), "user":User.query.get(p.user).email.split("@")[0], "title":p.title, "content":p.content, "explanation":p.explanation, "category":p.category, "unit":p.unit, "score":[score, sum(score), len(score)], "created_at":p.created_at}
			return render_template("math/problems/problem.html", data=p)
		else:
			p = {"id":p.id, "userid":int(p.user), "user":User.query.get(p.user).email.split("@")[0], "title":p.title, "content":p.content, "explanation":p.explanation, "category":p.category, "unit":p.unit, "score":[score, sum(score), len(score)], "created_at":p.created_at}
			return render_template("math/problems/problem.html", data=p)

@math.route("/problems/problem/<id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
	p = db.session.query(MathProblems).get(id)
	if request.method=="GET":
		if current_user.id == int(p.user):
			p = {"id":p.id, "userid":int(p.user), "user":User.query.get(p.user).email.split("@")[0], "title":p.title, "content":p.content, "explanation":p.explanation, "category":p.category, "unit":p.unit, "created_at":p.created_at}
			return render_template("math/problems/edit.html", data=p)
		else:
			return abort(403)
	elif request.method=="POST":
		if p.title!=request.form["title"]:p.title = request.form["title"]
		if p.content!=request.form["content"]:p.content = request.form["content"]
		if p.explanation!=request.form["explanation"]:p.explanation = request.form["explanation"]
		if p.category!=request.form["category"]:p.category = request.form["category"]
		if p.unit!=request.form["unit"]:p.unit = request.form["unit"]
		db.session.commit()
		return redirect(url_for("math.problem", id=id).replace('index.cgi/', ''))