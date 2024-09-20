from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, make_response, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from datetime import timedelta
from helpers import login_required
from RecipeManager import RecipeManager
import os


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
# na:
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "recipes.db")
db = SQL(f"sqlite:///{db_path}")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route('/')
@app.route('/index')
def index():
    return render_template("/index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()
    error = None
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            error = "must provide username"
            flash('Must provide username')
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "must provide password"
            flash('Must provide password')
            return render_template("login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            error = "invalid username or password"
            flash('Invalid username or password')
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash('You were successfully Signed in!')
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")

def password_validation(password):
    symbols = ['!', '#', '?', '%', '$', '&']
    if len(password) < 8:
        flash("password must provide min. 8 characters")
        return False
    elif len(password) > 20:
        flash("password must provide max 20 characters")
        return False
    if not any(char.isdigit() for char in password):
        flash("password should contain at least one number")
        return False
    if not any(char.isupper() for char in password):
        flash("password should contain at least one uppercase letter")
        return False
    if not any(char.islower() for char in password):
        flash("password should contain at least one lowercase letter")
        return False
    if not any(char in symbols for char in password):
        flash('Password should contain at least one of the symbols !#?%$&')
        return False
    else:
        return True

@app.route("/register", methods=["GET", "POST"])
def register():
    # User reached route via POST (as by submitting a form via POST)
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        usernames = db.execute(
            "SELECT * FROM users WHERE username = ?", username)
        hashed = generate_password_hash(password)

        # Ensure username was submitted
        if not username:
            error = "must provide username"
            flash('Must provide username')
            return render_template("register.html")

        # Ensure password was submitted
        elif not password:
            error = "must provide password"
            flash('Must provide password')
            return render_template("register.html")
        elif not email:
            error = "must provide an e-mail"
            flash('Must provide an e-mail')
            return render_template("register.html")

        elif password != confirmation:
            error = "Password does not match"
            flash('Password does not match')
            return render_template("register.html")

        if usernames:
            error = "username is already taken"
            flash('username is already taken')
            return render_template("register.html")

        existing_email = db.execute("SELECT * FROM users WHERE email = ?", email)
        if existing_email:
            error = "email is already taken"
            flash('E-mail is already taken')
            return render_template("register.html")

         # checking password validation
        val = password_validation(password)
        if not val:
            error = "Invalid password."
            flash('Invalid password')
            return render_template("register.html")


        # Query database for username

        db.execute("INSERT INTO users (username, email, hash) VALUES(?, ?, ?)",
                  username, email, hashed)

        # Redirect user to home page
        flash('You were successfully registered in. Sign in to start!')
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html", error=error)


@app.route("/recipes", methods=["GET", "POST"])
def recipes():
    if request.method == "POST":
        mealName = request.form.get("mealName")
        mealType = request.form.get("mealType")
        ingredients = request.form.get("ingredients")
        instructions = request.form.get("instructions")
        if not request.form.get("mealName"):
            flash('Must provide a meal name.')
            return render_template("recipes.html")
        user = session["user_id"]
        recipe_manager = RecipeManager(db, user)
        recipeList = recipe_manager.get_recipes()
        if not recipeList:
            recipe_manager.add_recipe(user, mealName, mealType, ingredients, instructions)
            return redirect("/ListOfRecipes")
        elif mealName not in recipeList[0]["mealName"]:
            recipe_manager.add_recipe(mealName, mealType, ingredients, instructions)
            return redirect("/ListOfRecipes")
    else:
        return render_template("recipes.html")


@app.route("/ListOfRecipes")
@login_required
def ListOfRecipes():
    user_id = session["user_id"]
    recipe_manager = RecipeManager(db, user_id)
    items = recipe_manager.get_recepes_list()
    
    return render_template("ListOfRecipes.html", items=items)


@app.route("/displayRecipe/<int:recipe_id>", methods=["GET", "POST"])
@login_required
def displayRecipe(recipe_id):
    user_id = session["user_id"]
    recipe_manager = RecipeManager(db, user_id)
    recipe = recipe_manager.get_recipe_by_id(recipe_id, db)
    if not recipe:
        flash("Invalid recipe id", "warning")
    ingredients = [ing.strip() for ing in recipe['ingredients'].split('\n')]
    recipe['ingredients'] = ingredients
    instructions = [ing.strip() for ing in recipe['instructions'].split('\n')]
    recipe['instructions'] = instructions
    if request.method == "POST" and request.form.get("deleteRecipe"):
        recipe_manager.delete_recipe(recipe_id)
        return redirect("/ListOfRecipes")
    return render_template("displayRecipe.html", recipe=recipe)


@app.route("/editRecipe/<int:recipe_id>", methods=["GET", "POST"])
@login_required
def editRecipe(recipe_id):
    user_id = session["user_id"]
    recipe_manager = RecipeManager(db, user_id)
    recipe = recipe_manager.get_recipe_by_id(recipe_id, db)
    if not recipe:
        flash("Invalid recipe id", "warning")

    if request.method == "POST":
        ed_mealName = request.form.get("mealName")
        ed_mealType = request.form.get("mealType")
        ed_ingredients = request.form.get('ingredients')
        ed_instructions = request.form.get("instructions")
        recipe_manager.update_recipe(recipe_id, ed_mealName, ed_mealType, ed_ingredients, ed_instructions)
        return redirect(url_for("displayRecipe", recipe_id=recipe_id))

    ingredients = [ing.strip() for ing in recipe[0]['ingredients'].split('\n')]
    instructions = [ing.strip()
                              for ing in recipe[0]['instructions'].split('\n')]
    return render_template("editRecipe.html", recipe=recipe[0], ingredients=ingredients, instructions=instructions)

@app.route("/schedule", methods=["GET", "POST"])
@login_required
def schedule():
    if request.method == "POST":
        date = request.form.get("date")
        user_id = session["user_id"]
        selected_date = request.form.get('selected_date')
        if selected_date:
            db.execute("UPDATE userPlan SET breakfast = :breakfast, lunch = :lunch, dinner = :dinner WHERE user_id = :user_id AND date = :selected_date", breakfast=breakfast, lunch=lunch, dinner=dinner, user_id=user_id, selected_date=selected_date)
            return redirect(url_for('schedule', date=selected_date))
        else:
            userPlans = db.execute("SELECT * FROM userPlan WHERE user_id = :user_id AND date = :date", user_id=user_id, date=date)
    else:
        now = datetime.now()
        date = request.args.get('date')
        if not date:
            date = now.strftime("%A %d %B %Y")
        user_id = session["user_id"]
        userPlans = db.execute("SELECT * FROM userPlan WHERE user_id = :user_id AND date = :date", user_id=user_id, date=date)
    return render_template("schedule.html", current_date=date, userPlans=userPlans, selected_date=date)

@app.route("/deleteMeal/<string:mealName>", methods=["POST"])
def deleteMeal(mealName):
    user_id = session["user_id"]
    selected_date = request.form.get('selected_date')
    db.execute("UPDATE userPlan SET {}=NULL WHERE user_id=:user_id AND date=:date".format(mealName), user_id=user_id, date=selected_date)
    flash("The recipe for {} was removed from your plan".format(mealName), "success")
    return "", 204


@app.route('/chooseMeal', methods=["GET", "POST"])
@login_required
def chooseMeal():
    user_id = session["user_id"]
    recipe_manager = RecipeManager(db, user_id)
    items = recipe_manager.get_recipes_ordered_by_meal_type()
    selected_date = request.form.get('selected_date')
    if request.method == "POST":
        userPlan = request.form["userPlan"]
        mealName = request.form.get("mealName")
        userPlans = db.execute("SELECT * FROM userPlan WHERE user_id = :user_id AND date = :selected_date", user_id=user_id, selected_date=selected_date)
        if not userPlans:
            db.execute("INSERT INTO userPlan (user_id, date) VALUES (:user_id, :date)", user_id=user_id, date=selected_date)
            if userPlan == 'breakfast':
                db.execute("UPDATE userPlan SET breakfast = :mealName WHERE user_id = :user_id AND date = :date", mealName = mealName, user_id=user_id, date=selected_date)
            elif userPlan == "lunch":
                db.execute("UPDATE userPlan SET lunch = :mealName WHERE user_id = :user_id AND date = :date", mealName = mealName, user_id=user_id, date=selected_date)
            elif userPlan == "dinner":
                db.execute("UPDATE userPlan SET dinner = :mealName WHERE user_id = :user_id AND date = :date", mealName=mealName, user_id=user_id, date=selected_date)
            elif userPlan == "dessert":
                db.execute("UPDATE userPlan SET dessert = :mealName WHERE user_id = :user_id AND date = :date", mealName=mealName, user_id=user_id, date=selected_date)
        else:
            if userPlan == 'breakfast':
                db.execute("UPDATE userPlan SET breakfast = :mealName WHERE user_id = :user_id AND date = :date", mealName = mealName, user_id=user_id, date=selected_date)
            elif userPlan == "lunch":
                db.execute("UPDATE userPlan SET lunch = :mealName WHERE user_id = :user_id AND date = :date", mealName = mealName, user_id=user_id, date=selected_date)
            elif userPlan == "dinner":
                db.execute("UPDATE userPlan SET dinner = :mealName WHERE user_id = :user_id AND date = :date", mealName=mealName, user_id=user_id, date=selected_date)
            elif userPlan == "dessert":
                db.execute("UPDATE userPlan SET dessert = :mealName WHERE user_id = :user_id AND date = :date", mealName=mealName, user_id=user_id, date=selected_date)
        return redirect(url_for("schedule", date=selected_date))
    else:
        return render_template('chooseMeal.html', items=items, date=selected_date)


@app.route('/shoppingList', methods=["GET", "POST"])
@login_required
def shoppingList():
    user_id = session['user_id']
    ingredients = []
    recipe_manager = RecipeManager(db, user_id)
    mealNames_recipes1 = recipe_manager.get_meal_names()
    recipes1Names = []
    for item in mealNames_recipes1:
        recipes1Names.append(item['mealName'])
    if request.method == "POST":
        date_range = request.form.get("date_range")
        if not date_range:
            flash("You must choose a date range.", "warning")
            return redirect(url_for("shoppingList"))
        start_date, end_date = date_range.split(" to ")
        start_date = datetime.strptime(start_date, "%A %d %B %Y")
        end_date = datetime.strptime(end_date, "%A %d %B %Y")
        date_list = []
        while start_date <= end_date:
            date_list.append(start_date.strftime("%A %d %B %Y"))
            start_date += timedelta(days=1)
        for date in date_list:
            userPlans = db.execute("SELECT breakfast, lunch, dinner, dessert FROM userPlan WHERE user_id = :user_id AND date = :date", user_id=user_id, date=date)
            if userPlans:
                mealNam = list(userPlans[0].values())
            else:
                mealNam = []
            for meal in mealNam:
                if meal in recipes1Names:
                    recipe_manager = RecipeManager(db, user_id)
                    result = recipe_manager.get_ingredients_by_meal_name(meal)
                    for row in result:
                        ingredients += [ing.strip() for ing in result.split("\n") if ing.strip()]
        ingredients = list(set(ingredients))
        if not ingredients:
            flash("You didn't set any meal plan for this date. Check your schedule.", "warning")
        return render_template("shoppingList.html", date_range = date_range, ingredients=ingredients)
    else:
        now = datetime.now()
        current_date = now.strftime("%A %d %B %Y")
        userPlans = db.execute("SELECT breakfast, lunch, dinner, dessert FROM userPlan WHERE user_id = :user_id AND date = :current_date", user_id=user_id, current_date=current_date)
        if userPlans:
            mealNam = list(userPlans[0].values())
        else:
            mealNam = []

        for meal in mealNam:
            if meal in recipes1Names:
                result = recipe_manager.get_ingredients_by_meal_name(meal)
                for row in result:
                    ingredients += [ing.strip() for ing in row["ingredients"].split("\n") if ing.strip()]
    ingredients = list(set(ingredients))
    return render_template("shoppingList.html", current_date=current_date, ingredients=ingredients)


if __name__ == "__main__":
    app.run(debug=True)