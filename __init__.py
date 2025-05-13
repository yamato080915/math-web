from flask import Blueprint, render_template

math = Blueprint(
	"math", 
	__name__, 
	static_folder="static",
	template_folder="./templates"
)

@math.route("/", methods=["GET", "POST"])
def index():
	return render_template("index.html")