from flask import Blueprint, render_template, request, redirect, jsonify, abort, flash
from myfunc import url_for, get_username
from flask_login import login_required, current_user

from models import User, MathProblems, Submissions
from app import db

from random import randint

math = Blueprint(
	"math", 
	__name__, 
	static_folder="./statics",
	template_folder="./templates",
	static_url_path="/statics"
)

def get_problem(id):
	p = db.session.query(MathProblems).get(id)
	score = list(map(int, p.score.split()))
	p = {"id":p.id, "userid":int(p.user), "user":get_username(p.user), "title":p.title, "content":p.content, "explanation":p.explanation, "category":p.category, "unit":p.unit, "score":[score, sum(score), len(score)], "created_at":p.created_at}
	return p
def get_problems(user=None, title=None, content=None, explanation=None, category=None, unit=None, score=None):
	query = db.session.query(MathProblems)
	if user is not None:query = query.filter_by(user=user)
	if title is not None:query = query.filter_by(title=title)
	if content is not None:query = query.filter_by(content=content)
	if explanation is not None:query = query.filter_by(explanation=explanation)
	if category is not None:query = query.filter_by(category=category)
	if unit is not None:query = query.filter_by(unit=unit)
	if score is not None:query = query.filter_by(score=score)
	return query.all()
def get_submission(id):
	s = db.session.query(Submissions).get(id)
	if s.score==None:
		score = []
	else:
		score = list(map(int, s.score.split()))
	s = {"id": s.id, "userid": int(s.user), "user": get_username(s.user), "content": s.content, "score": [score, sum(score), len(score)], "judged": s.judged, "created_at": s.created_at}
	return s
def get_submissions(problem, user=None, judged=None):
	query = db.session.query(Submissions).filter_by(problem=problem)
	if user is not None:query = query.filter_by(user=user)
	if judged is not None:query = query.filter_by(judged=judged)
	return query.all()

@math.route("/latex", methods=["GET", "POST"])
def latex():
	return render_template("math/latex.html")

@math.route("/problems", methods=["GET", "POST"])
def problems():
	if current_user.is_authenticated:
		data = {
			"my-problem": [get_problem(x.id) for x in get_problems(user=int(current_user.get_id()))],
			"new": [get_problem(x.id) for x in get_problems() if int(x.user)!=int(current_user.get_id())][-5:],
			"random": get_problem(randint(1, db.session.query(MathProblems).count()))
		}
	else:
		data = {
			"my-problem": [],
			"new": [],
			"random": get_problem(randint(1, db.session.query(MathProblems).count()))
		}
	return render_template("math/problems/index.html", data=data)

@math.route("/problems/all", methods=["GET", "POST"])
def problemsAll():
	return render_template("math/problems/all.html", data=[get_problem(x.id) for x in get_problems()])

@math.route("/problems/post", methods=["GET", "POST"])
@login_required
def post():
	if request.method == "GET":
		return render_template("math/problems/post.html")
	else:
		try:
			score = list(map(int, request.form["score"].split("\r\n")))
		except:
			flash("error.score")
			return redirect(url_for("math.post"))
		score = " ".join([str(x) for x in score])
		if get_problems(user=int(current_user.get_id()), content=request.form["content"])==[]:
			problem = MathProblems(user=int(current_user.get_id()), title=request.form["title"], content=request.form["content"], explanation=request.form["explanation"], category=request.form["category"], unit=request.form["unit"], score=score)
			db.session.add(problem)
			db.session.commit()
		p = get_problems(user=int(current_user.get_id()), content=request.form["content"])[0]
		return redirect(url_for("math.problem", id=p.id))

@math.route("/problems/problem/<id>", methods=["GET", "POST"])
def problem(id):
	p = get_problem(id)
	if p==None:
		return abort(404)
	else:
		p = get_problem(id)
		if current_user.is_authenticated:
			if int(current_user.get_id())==p["userid"]:
				s = [get_submission(x.id) for x in get_submissions(id, judged=False)] + [get_submission(x.id) for x in get_submissions(id, judged=True)]
			else:
				s = {
					"judged": [get_submission(x.id) for x in get_submissions(id, user=int(current_user.get_id()), judged=1)],
					"unjudged": [get_submission(x.id) for x in get_submissions(id, user=int(current_user.get_id()), judged=0)]
				}
		else:s = []
		if request.method=="GET":
			return render_template("math/problems/problem.html", data=p, submissions=s)
		else:
			if "answer" in request.form:
				submission = Submissions(problem=id, user=int(current_user.get_id()), content=request.form["answer"])
				db.session.add(submission)
				db.session.commit()
			elif "btn" in request.form:
				score = [request.form[f"score{request.form["btn"]}.{i}"] for i in range(p["score"][2])]
				print(score)
				s = db.session.query(Submissions).get(int(request.form["btn"]))
				s.score = " ".join(score)
				s.judged = True
				db.session.commit()
				print(s.score)
			return redirect(url_for("math.problem", id=id))

@math.route("/problems/problem/<id>/edit", methods=["GET", "POST"])
@login_required
def edit(id):
	p = get_problem(id)
	if request.method=="GET":
		if int(current_user.get_id()) == int(p["userid"]):
			p = get_problem(id)
			return render_template("math/problems/edit.html", data=p)
		else:
			return abort(403)
	elif request.method=="POST":
		query = db.session.query(MathProblems).get(int(id))
		if p["title"]!=request.form["title"]:query.title = request.form["title"]
		if p["content"]!=request.form["content"]:query.content = request.form["content"]
		if p["explanation"]!=request.form["explanation"]:query.explanation = request.form["explanation"]
		if p["category"]!=request.form["category"]:query.category = request.form["category"]
		if p["unit"]!=request.form["unit"]:query.unit = request.form["unit"]
		db.session.commit()
		return redirect(url_for("math.problem", id=id))