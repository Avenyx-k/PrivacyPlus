import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "privacy-plus-local-secret"
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "privacy_plus"),
        port=int(os.environ.get("DB_PORT", "3306"))
    )


# =========================================================
# HOME / LANDING PAGE
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        college = request.form["college"].strip()
        password = request.form["password"]

        if not name or not email or not college or not password:

            flash("Please fill in all fields.")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        db = get_db_connection()
        cursor = db.cursor()

        try:

            query = """
                INSERT INTO students
                (name, email, college, password_hash)
                VALUES (%s, %s, %s, %s)
            """

            cursor.execute(
                query,
                (name, email, college, password_hash)
            )

            db.commit()

            flash("Account created successfully. Please login.")

            return redirect(url_for("login"))

        except mysql.connector.Error as error:

            print("Database error:", error)

            flash("This email may already be registered.")

        finally:

            cursor.close()
            db.close()

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip()
        password = request.form["password"]

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM students WHERE email = %s",
            (email,)
        )

        student = cursor.fetchone()

        cursor.close()
        db.close()

        if student and check_password_hash(
            student["password_hash"],
            password
        ):

            session["student_id"] = student["student_id"]
            session["student_name"] = student["name"]

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "student_id" not in session:
        return redirect(url_for("login"))

    name = session.get("student_name", "Student")

    return render_template(
        "dashboard.html",
        name=name
    )


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "student_id" not in session:

        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        college = request.form["college"].strip()

        if not name or not email or not college:

            flash("All profile fields are required.")

        else:

            try:

                cursor.execute(
                    """
                    UPDATE students
                    SET name = %s,
                        email = %s,
                        college = %s
                    WHERE student_id = %s
                    """,
                    (
                        name,
                        email,
                        college,
                        session["student_id"]
                    )
                )

                db.commit()

                session["student_name"] = name

                flash("Profile updated successfully.")

            except mysql.connector.Error:

                flash("That email may already be in use.")

    cursor.execute(
        """
        SELECT student_id, name, email, college, created_at
        FROM students
        WHERE student_id = %s
        """,
        (session["student_id"],)
    )

    student = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template(
        "profile.html",
        student=student
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

# =========================================================
# PRIVACY CHECK
# =========================================================

@app.route("/privacy-check")
def privacy_check():

    if "student_id" not in session:
        return redirect(url_for("login"))

    return render_template("privacy_check.html")

# =========================================================
# SUBMIT PRIVACY CHECK
# =========================================================

@app.route("/submit-privacy-check", methods=["POST"])
def submit_privacy_check():

    if "student_id" not in session:
        return redirect(url_for("login"))

    import json

    try:

        answers = json.loads(
            request.form.get("answers", "[]")
        )

    except json.JSONDecodeError:

        flash("There was a problem processing your answers.")

        return redirect(url_for("privacy_check"))


    if len(answers) != 12:

        flash("Please complete all 12 questions.")

        return redirect(url_for("privacy_check"))


    score_values = {

        "Never": 25,

        "Sometimes": 50,

        "Often": 75,

        "Always": 100

    }


    scores = []

    for answer in answers:

        scores.append(
            score_values.get(answer, 0)
        )


    # -----------------------------------------------------
    # OVERALL SCORE
    # -----------------------------------------------------

    total_score = round(
        sum(scores) / len(scores)
    )


    # -----------------------------------------------------
    # AWARENESS + RISK
    # -----------------------------------------------------

    if total_score >= 80:

        awareness_level = "High Awareness"
        risk_level = "Low Risk"

    elif total_score >= 60:

        awareness_level = "Good Awareness"
        risk_level = "Moderate Risk"

    else:

        awareness_level = "Needs Improvement"
        risk_level = "High Risk"


    # -----------------------------------------------------
    # CATEGORIES
    # -----------------------------------------------------

    categories = [

        "Account Security",
        "Account Security",

        "App Permissions",
        "App Permissions",

        "Sharing Habits",
        "Sharing Habits",

        "Payment Safety",
        "Payment Safety",

        "Phishing Awareness",
        "Phishing Awareness",

        "Data Awareness",
        "Data Awareness"

    ]


    category_scores = {}


    for category, score in zip(
        categories,
        scores
    ):

        if category not in category_scores:

            category_scores[category] = []

        category_scores[category].append(score)


    for category in category_scores:

        category_scores[category] = round(
            sum(category_scores[category])
            / len(category_scores[category])
        )


    # -----------------------------------------------------
    # STRONGEST / WEAKEST
    # -----------------------------------------------------

    strongest_area = max(
        category_scores,
        key=category_scores.get
    )


    weakest_area = min(
        category_scores,
        key=category_scores.get
    )


    # -----------------------------------------------------
    # RECOMMENDATIONS
    # -----------------------------------------------------

    recommendations = []


    if category_scores["Account Security"] < 70:

        recommendations.append(
            "Use unique passwords for important accounts "
            "and enable two-factor authentication whenever possible."
        )


    if category_scores["App Permissions"] < 70:

        recommendations.append(
            "Review app permissions regularly and remove "
            "access that is not necessary."
        )


    if category_scores["Sharing Habits"] < 70:

        recommendations.append(
            "Avoid publicly sharing sensitive personal "
            "information such as your phone number or address."
        )


    if category_scores["Payment Safety"] < 70:

        recommendations.append(
            "Verify payment requests and links carefully "
            "before completing transactions."
        )


    if category_scores["Phishing Awareness"] < 70:

        recommendations.append(
            "Check unexpected messages, senders and links "
            "before clicking or responding."
        )


    if category_scores["Data Awareness"] < 70:

        recommendations.append(
            "Pay attention to the personal information "
            "websites and applications request."
        )


    if not recommendations:

        recommendations.append(
            "Your privacy habits are strong. Continue "
            "reviewing your digital security regularly."
        )

    # -----------------------------------------------------
    # SAVE RESULT TO MYSQL
    # -----------------------------------------------------

    db = get_db_connection()
    cursor = db.cursor()

    try:

        cursor.execute(
        """
        INSERT INTO progress
        (
            student_id,
            score,
            awareness_level,
            risk_level
        )
        VALUES (%s, %s, %s, %s)
        """,
        (
            session["student_id"],
            total_score,
            awareness_level,
            risk_level
        )
    )

        db.commit()

    except mysql.connector.Error as error:

        print("Progress database error:", error)

    finally:

        cursor.close()
        db.close()
    
    # -----------------------------------------------------
    # SAVE RESULT IN SESSION
    # -----------------------------------------------------

    session["privacy_result"] = {

        "score": total_score,

        "awareness_level": awareness_level,

        "risk_level": risk_level,

        "strongest_area": strongest_area,

        "weakest_area": weakest_area,

        "category_scores": category_scores,

        "recommendations": recommendations,

        "answers": answers

    }

    return redirect(
        url_for("privacy_result")
    )


# =========================================================
# PRIVACY RESULT
# =========================================================

@app.route("/privacy-result")
def privacy_result():

    if "student_id" not in session:

        return redirect(url_for("login"))


    result = session.get(
        "privacy_result"
    )


    if not result:

        return redirect(
            url_for("privacy_check")
        )


    return render_template(
        "result.html",
        result=result
    )

# =========================================================
# MODULE 3 — SCAM CHECKER
# =========================================================

@app.route("/scam-checker", methods=["GET", "POST"])
def scam_checker():

    if "student_id" not in session:
        return redirect(url_for("login"))

    result = None
    risk = None

    if request.method == "POST":

        message = request.form.get(
            "message",
            ""
        ).strip().lower()

        warning_words = [

            "urgent",
            "otp",
            "verify now",
            "click here",
            "winner",
            "prize",
            "blocked",
            "account suspended",
            "claim",
            "password",
            "bank",
            "refund",
            "kyc",
            "lottery",
            "reward"

        ]

        found = [
            word
            for word in warning_words
            if word in message
        ]

        if len(found) >= 3:

            risk = "High Risk"

            result = (
                "Several common scam warning signs were detected: "
                + ", ".join(found)
                + ". Do not click links or share sensitive information. "
                "Verify the sender through an official channel."
            )

        elif len(found) >= 1:

            risk = "Caution"

            result = (
                "Some warning signs were detected: "
                + ", ".join(found)
                + ". Be careful and independently verify the message."
            )

        else:

            risk = "No Common Warning Signs"

            result = (
                "No common scam phrases were detected. "
                "However, this does not guarantee that the message "
                "is safe. Always verify unexpected requests."
            )

    return render_template(
        "scam_checker.html",
        result=result,
        risk=risk
    )


# =========================================================
# MODULE 3 — APP PRIVACY EXPLORER
# =========================================================

@app.route("/app-explorer")
def app_explorer():

    if "student_id" not in session:
        return redirect(url_for("login"))

    apps = [

        {
            "name": "Social Media",
            "icon": "🌐",
            "category": "Social",
            "description":
                "Platforms used for communication, sharing and communities.",
            "privacy":
                "Review profile visibility, location sharing, contacts and personal information.",
            "tips": [
                "Review who can see your profile.",
                "Limit location sharing.",
                "Check contact access."
            ]
        },

        {
            "name": "Payment Apps",
            "icon": "💳",
            "category": "Finance",
            "description":
                "Applications used for digital payments and transactions.",
            "privacy":
                "Protect OTPs and PINs and verify payment requests.",
            "tips": [
                "Never share OTPs.",
                "Check payment requests.",
                "Use official applications."
            ]
        },

        {
            "name": "Shopping Apps",
            "icon": "🛍️",
            "category": "Shopping",
            "description":
                "Applications used for online shopping and delivery.",
            "privacy":
                "Review saved addresses, payment details and permissions.",
            "tips": [
                "Remove old addresses.",
                "Review saved payment methods.",
                "Check app permissions."
            ]
        },

        {
            "name": "Education Apps",
            "icon": "🎓",
            "category": "Education",
            "description":
                "Platforms used for learning and academic communication.",
            "privacy":
                "Check what academic, profile and device information is collected.",
            "tips": [
                "Check profile visibility.",
                "Review account permissions.",
                "Avoid unnecessary information."
            ]
        },

        {
            "name": "Entertainment Apps",
            "icon": "🎬",
            "category": "Entertainment",
            "description":
                "Applications for videos, music, games and entertainment.",
            "privacy":
                "Review tracking, permissions and account privacy settings.",
            "tips": [
                "Review tracking settings.",
                "Limit unnecessary permissions.",
                "Check personalised advertising settings."
            ]
        },

        {
            "name": "Fitness Apps",
            "icon": "🏃",
            "category": "Health & Fitness",
            "description":
                "Applications that track activity and fitness information.",
            "privacy":
                "Review location, activity and device-data permissions.",
            "tips": [
                "Limit precise location.",
                "Review activity tracking.",
                "Check third-party sharing."
            ]
        }

    ]

    search = request.args.get(
        "search",
        ""
    ).strip().lower()

    if search:

        apps = [

            app for app in apps

            if search in app["name"].lower()
            or search in app["category"].lower()

        ]

    return render_template(
        "app_explorer.html",
        apps=apps,
        search=search
    )


# =========================================================
# MODULE 3 — PROGRESS
# =========================================================

@app.route("/progress")
def progress():

    if "student_id" not in session:
        return redirect(url_for("login"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            score,
            awareness_level,
            risk_level,
            assessment_date
        FROM progress  
        WHERE student_id = %s
        ORDER BY assessment_date DESC
        """,
        (session["student_id"],)
    )

    history = cursor.fetchall()

    cursor.close()
    db.close()

    if history:

        latest = history[0]

        score = latest["score"]
        level = latest["awareness_level"]
        risk = latest["risk_level"]

    else:

        score = 0
        level = "Not assessed"
        risk = "Not assessed"

    return render_template(
        "progress.html",
        score=score,
        level=level,
        risk=risk,
        history=history
    )

# =========================================================
# MODULE 3 — PRIVACY HUB
# =========================================================

@app.route("/privacy-hub")
def privacy_hub():

    if "student_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "privacy_hub.html"
    )


# =========================================================
# MODULE 3 — AI ASSISTANT
# =========================================================

@app.route("/ai-assistant")
def ai_assistant():

    if "student_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "ai_assistant.html"
    )


# =========================================================
# AI ASSISTANT CHAT
# =========================================================

@app.route(
    "/ai-assistant/chat",
    methods=["POST"]
)
def ai_assistant_chat():

    if "student_id" not in session:
        return {
            "reply": "Please log in to use Privacy+ Assistant."
        }, 401

    data = request.get_json()

    question = data.get(
        "question",
        ""
    ).strip().lower()

    if not question:

        return {
            "reply": "Please type a privacy-related question."
        }


    # Basic Privacy+ knowledge engine.
    # We will connect a real AI model later.

    responses = {

        "password":
            "Use a unique, strong password for every important account. "
            "A password manager can help you avoid reusing passwords.",

        "otp":
            "Never share an OTP with another person, even if they claim "
            "to be from your bank, delivery service or another company.",

        "phishing":
            "Phishing is an attempt to trick you into revealing information "
            "through fake messages, websites or links. Check the sender, "
            "URL and context before responding.",

        "2fa":
            "Two-factor authentication adds another verification step "
            "after your password. Enable it whenever an important service "
            "supports it.",

        "privacy":
            "Digital privacy means controlling how your personal information "
            "is collected, used, shared and stored online.",

        "permission":
            "Only give an app permissions that are necessary for its purpose. "
            "Review permissions regularly.",

        "scam":
            "Common scam warning signs include urgency, unexpected prizes, "
            "requests for OTPs, suspicious links and threats of account closure.",

        "location":
            "Avoid giving precise location access unless an app genuinely "
            "needs it. You can often choose approximate location instead.",

        "data":
            "Personal data can include your name, email, phone number, "
            "location, identifiers, browsing activity and other information "
            "linked to you.",

        "social media":
            "Review profile visibility, tagged posts, location sharing, "
            "contact syncing and third-party application access.",

        "payment":
            "Before making a digital payment, verify the recipient and "
            "payment request. Never share your PIN or OTP.",

        "cookies":
            "Cookies are small pieces of data websites store in your browser. "
            "Some are necessary, while others may be used for analytics or "
            "personalised advertising."

    }


    # Find the most relevant built-in response.

    reply = None

    for keyword, answer in responses.items():

        if keyword in question:

            reply = answer

            break


    if reply is None:

        reply = (
            "That's a good privacy question. Privacy+ currently focuses "
            "on passwords, permissions, scams, phishing, payments, "
            "personal data and online privacy. Try asking about one of "
            "these topics."
        )


    return {
        "reply": reply
    }

# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(debug=True)