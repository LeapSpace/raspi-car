#! /usr/bin/python
# -*- coding:utf-8 -*-

#import control
from flask import Flask, session, redirect, url_for, request, render_template
app = Flask(__name__)
import signal

@app.route("/")
@app.route("/index")
def index():
	if not session.has_key("username") or session["username"]!="admin":
		return redirect(url_for("login"))
	return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		if request.form['key']=='123456':
			session['username'] = 'admin'
			return redirect(url_for('index'))
	return render_template("login.html")

@app.route("/video")
def video():
	if not session.has_key("username") or session["username"]!="admin":
		return redirect(url_for("login"))
	return render_template("video.html")

@app.route("/control")
def control():
	if not session.has_key("username") or session["username"]!="admin":
		return redirect(url_for("login"))
	x=y=0
	x=get_val(request.args.get("x"))
	y=get_val(request.args.get("y"))

	coordinate = (x,y)
	print coordinate
	#control.forward(coordinate)
	return "ok"

def get_val(s):
	i=0
	try:
		i=float(s)
	except Exception, e:
		pass
	return i



# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__ == "__main__":
	app.run(host='0.0.0.0',debug=False,threaded=True)