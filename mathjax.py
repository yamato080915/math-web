from openai import OpenAI
from app import app
import base64

client = OpenAI(
	api_key=app.config["OPENAI_API_KEY"],
	base_url="https://openrouter.ai/api/v1"
)

prompt = """mathjaxでは、インラインの数式は\\(数式\\)が、別行立ての数式は\\[数式\\]が使用されます。
数式はLaTeXと同様ですが、インラインの'\\int', '\\sum', '\\lim'には、'\\displaystyle'を前に付け足してください。分数は'\\dfrac'を使用してください。
"""

def main(path):
	with open(path, "rb") as f:
		image_data = base64.b64encode(f.read()).decode("utf-8")
	res = client.chat.completions.create(
		model="qwen/qwen2.5-vl-32b-instruct:free",
		messages=[{"role": "user", "content": [
			{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}},
			{"type": "text", "text": "画像の数学の問題文を読み取り、mathjax形式で出力してください。" + prompt + "もし問題文が読み取れない場合は、'問題文を読み取れませんでした。'と出力してください。また、ほかの情報は一切出力しないでください。出力はコードブロックで囲まないでください。"}
		]}]
	)
	return str(res.choices[0].message.content).replace("\n\n", "\n")

def solve(problem):
	res = client.chat.completions.create(
		model="deepseek/deepseek-r1:free",
		messages=[{"role": "user", "content": f"問題: ```{problem}```" + """
問題を解いて、過程を含めて解答をmathjax形式で出力してください。""" + prompt + """証明終を示す場合は、'[終]'を使用してください。
また、ほかの情報は一切出力しないでください。出力はコードブロックで囲まないでください。
"""}]
	)
	print(res.choices[0].message.content, type(res.choices[0].message.content))
	return str(res.choices[0].message.content)