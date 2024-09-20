from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, make_response, url_for
from flask_session import Session
from datetime import datetime
from datetime import timedelta
from helpers import login_required
from RecipeManager import RecipeManager
from user_auth import UserAuth
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
user_auth = UserAuth(db)



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
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        success, redirect_url = user_auth.login(username, password)
        if success:
            return redirect(url_for("index"))
        else:
            return render_template(redirect_url)
    return render_template("login.html")


@app.route("/logout")
def logout():
    user_auth.logout()
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        success, redirect_url = user_auth.register(username, email, password, confirmation)
        if success:
            return redirect(url_for("login"))
        else:
            return render_template(redirect_url)
    else:
        return render_template("register.html")


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