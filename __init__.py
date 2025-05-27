from flask import Blueprint, render_template

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
	return render_template("math/problems.html")