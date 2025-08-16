from flask import Blueprint, render_template, request, redirect, jsonify, abort, flash, make_response, session
from myfunc import url_for, get_username
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from models import User, MathProblems, Submissions
from app import db, app

from random import randint
import os, threading

from . import mathjax

def math_format(text):
	return text.replace("[終]", '<p style="text-align: right; padding-right: 10%;">(終)</p>')

app.jinja_env.globals["math_format"] = math_format

math = Blueprint(
	"math", 
	__name__, 
	static_folder="./statics",
	template_folder="./templates",
	static_url_path="/statics"
)

@math.route("/fonts/<font>")
def serve_fonts(font):
	if font in ["HaranoAjiMincho-Regular.otf"]:
		response = make_response(math.send_static_file(f"fonts/{font}"))
		response.headers["Cache-Control"] = 'public, max-age=86400'
		return response

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
	s = {"id": s.id, "userid": int(s.user), "user": get_username(s.user), "content": s.content, "score": [score, sum(score), len(score)], "judged": s.judged, "comment": s.comment, "created_at": s.created_at}
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
	if request.method == "GET":
		return render_template("math/problems/all.html", data=[get_problem(x.id) for x in get_problems()])
	else:
		data = request.get_json()
		return jsonify({"data": [get_problem(x.id) for x in get_problems() if [x.category, x.unit] in data["data"]]})

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

@math.route("/problems/post/image/processing", methods=["POST"])
def processing():
	try:
		if 'image' not in request.files:
			return jsonify({"success": False, "data": "ファイルがアップロードされていません。"})
		
		file = request.files['image']
		
		if file.filename == '':
			return jsonify({"success": False, "data": "ファイルが選択されていません。"})
		
		import os
		from werkzeug.utils import secure_filename
		import tempfile
		
		temp_dir = tempfile.gettempdir()
		filename = secure_filename(file.filename)
		filepath = os.path.join(temp_dir, filename)
		file.save(filepath)
		
		# 画像をmathjaxで処理
		res = mathjax.main(filepath)
		
		# 一時ファイルを削除
		try:
			os.remove(filepath)
		except:
			pass
			
		return jsonify({"success": True, "data": res})
	except Exception as e:
		app.logger.error(f"Image processing error: {str(e)}")
		return jsonify({"success": False, "data": "画像の処理中にエラーが発生しました。"})

@math.route("/problems/post/processing", methods=["POST"])
def post_processing():
	data = request.get_json()
	return jsonify({"success": True, "data": mathjax.solve(data["problem"])})

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
			elif get_submissions(id, user=int(current_user.get_id())):
				s = {
					"my_answer": get_submission(get_submissions(id, user=int(current_user.get_id()))[0].id),
					"all_answers": [get_submission(x.id) for x in get_submissions(id, judged=True) if x.user!=int(current_user.get_id())],
				}
			else:
				s = []
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
				s = db.session.query(Submissions).get(int(request.form["btn"]))
				s.score = " ".join(score)
				s.judged = True
				s.comment = request.form[f"comment{request.form['btn']}"]
				db.session.commit()
			elif "re-answer" in request.form:
				s = get_submissions(id, user=int(current_user.get_id()))[0]
				s.content = request.form["re-answer"]
				db.session.commit()
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

@math.route("/problems/problem/<id>/pdf")
def pdf(id):
	p = get_problem(id)
	if p==None:
		return abort(404)
	else:
		return render_template("math/problems/pdf.html", data=p)