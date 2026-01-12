from flask import Flask, request, render_template, redirect, url_for, session, flash
from functools import wraps
from flask import session, redirect, url_for, request
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from info import get_unified_problem_recommendations, get_unified_tag_distribution, get_full_codeforces_profile_stats, get_codechef_profile_stats, get_full_leetcode_profile_stats
from llm import get_ai_response
from flask import jsonify
from mdit_py_plugins.texmath import texmath_plugin
from markdown_it import MarkdownIt

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

conversation_history = []

def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        user_id = session.get('user_id')

        if not user_id:
            return redirect(url_for('login', next=request.path))

        return view_func(*args, **kwargs)

    return wrapped_view


app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY")

@app.route("/", endpoint="landing")
def landing():
    if request.method == 'GET':
        user_id = session.get("user_id")

        if not user_id:
            authenticated = False
            username = ""
        else:
            authenticated = True
            username = session.get("username")

        return render_template('landing.html', authenticated=authenticated, username=username)
    

@app.route("/login", endpoint="login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":

        email = request.form.get("email", None)
        password = request.form.get("password", None)

        if not email or not password:
            flash("All required fields must be filled.")
            return redirect(url_for("signup"))


        elif email and password:
            response = supabase.auth.sign_in_with_password(
                {
                    "email": "email@example.com",
                    "password": "example-password",
                }
            )
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password,
                })

                if response.user:
                    user_id = response.user.id

                    profile_response = supabase.table('profiles')\
                        .select('*')\
                        .eq('id', user_id)\
                        .single()\
                        .execute()
                    

                    profile = profile_response.data
                    

                    session["user_id"] = user_id
                    session["username"] = profile.get("username")
                    session["leetcode_username"] = profile.get("leetcode_username")
                    session["codeforces_username"] = profile.get("codeforces_username")
                    session["codechef_username"] = profile.get("codechef_username")

                    flash("Login successful!")
                    return redirect(url_for("landing"))
            
            except Exception as e:
                flash(f"Login failed: {str(e)}")
                return redirect(url_for("login"))

    


@app.route("/signup", endpoint="signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    elif request.method == "POST":
        print("Got the post request!")
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        leetcode = request.form.get("leetcode", "").strip()
        codeforces = request.form.get("codeforces", "").strip()
        codechef = request.form.get("codechef", "").strip()

        print("got all the info")

       
        if not username or not email or not password:
            flash("All required fields must be filled.")
            return redirect(url_for("signup"))

        if not any([leetcode, codeforces, codechef]):
            flash("Please provide at least one coding profile.")
            return redirect(url_for("signup"))

        try:
            response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })

            user = response.user

            if not user:
                flash("Signup failed. Please try again.")
                return redirect(url_for("signup"))

        
            session["user_id"] = user.id
            session["username"] = username
            session["leetcode_username"] = leetcode
            session["codeforces_username"] = codeforces
            session["codechef_username"] = codechef

            return redirect(url_for("landing"))

        except Exception as e:
            flash(str(e))
            print(str(e))
            return redirect(url_for("signup"))


@app.route("/logout", endpoint="logout", methods=["GET", "POST"])
def logout():
    session.clear()
    supabase.auth.sign_out()
    return redirect(url_for("landing"))


@app.route("/contact", endpoint="contact")
def contact():

    if request.method == "GET":
        return render_template("contact.html")


@login_required
@app.route("/dashboard", endpoint="dashboard", methods=["GET"])
def dashboard():
    leetcode_user = session.get("leetcode_username")
    codeforces_user = session.get("codeforces_username")
    codechef_user = session.get("codechef_username")

    if leetcode_user:
        leetcode_data = get_full_leetcode_profile_stats(leetcode_user)
    if codechef_user:
        codechef_data = get_codechef_profile_stats(codechef_user)
    if codeforces_user:
        codeforces_data = get_full_codeforces_profile_stats(codeforces_user)
    if leetcode_user or codeforces_user:
        tag_distributions = get_unified_tag_distribution(leetcode_user, codeforces_user)

   
    platforms = {
        "leetcode": {
            "connected": bool(leetcode_user),
            "data": leetcode_data if leetcode_user else None,
        },
        "codeforces": {
            "connected": bool(codeforces_user),
            "data": codeforces_data if codeforces_user else None,
        },
        "codechef": {
            "connected": bool(codechef_user),
            "data": codechef_data if codechef_user else None,
        },
    }

    if not any(p["connected"] for p in platforms.values()):
        flash("Please connect at least one platform to continue.")
        return redirect(url_for("landing"))  
    
    return render_template(
        "dashboard.html",
        username=session.get("username"),
        platforms=platforms,
        tag_distribution=tag_distributions
    )

@login_required
@app.route("/chat", endpoint="chat", methods=["GET", "POST"])
def chat():
    
    if request.method == "GET":
        return render_template("chat.html")
    
    elif request.method == "POST":
        try:
            data = request.json
            doubt = data.get("doubt", "")
            
            if not doubt:
                return jsonify({
                    "success": False,
                    "error": "No doubt provided"
                }), 400
            
            context = []

            if len(conversation_history) == 1:
                context = conversation_history[0]
            elif len(conversation_history) > 2:
                context = conversation_history[-2]

            
            ai_response = get_ai_response(doubt, context)
            conversation_history.append({"user" : ai_response, "ai_response": ai_response})
            
            md = MarkdownIt("gfm-like", {"linkify": False}).use(texmath_plugin)
            ai_response = md.render(ai_response)

            if len(conversation_history) > 2:
                conversation_history.pop(0)

            return jsonify({
                "success": True,
                "response": ai_response
            })
            
        except Exception as e:
            print(f"Error in chat endpoint: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


@login_required
@app.route("/problem_recommendation", endpoint="problem_recommendation")
def problem_recommendation():
    if request.method == "GET":
        leetcode_username = session.get("leetcode_username")
        codeforces_username = session.get("codeforces_username")
        
        tag_distribution = get_unified_tag_distribution(
            leetcode_username=leetcode_username if leetcode_username else None,
            codeforces_handle=codeforces_username if codeforces_username else None
        )
        
        weak_tags = []
        if tag_distribution:
            sorted_tags = sorted(tag_distribution.items(), key=lambda x: x[1])
            
            weak_count = max(3, len(sorted_tags) // 3)
            weak_tags = [tag for tag, count in sorted_tags[:weak_count]]
            

        if not weak_tags:
            weak_tags = ['dp', 'greedy', 'graphs']

        
        recommendations = get_unified_problem_recommendations(
            tags=weak_tags,
            limit_per_platform=15,
            include_contests=True,
            platforms=['leetcode', 'codeforces', 'codechef']
        )

        
        return render_template(
            "problems.html",
            recommendations=recommendations,
            weak_areas=weak_tags,
            tag_distribution=tag_distribution
        )



if __name__ == '__main__':
    app.run(debug=True)