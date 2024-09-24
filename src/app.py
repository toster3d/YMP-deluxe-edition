import os
from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from helpers.login_required_decorator import login_required
from services import ShoppingListService, UserAuth, UserPlanManager, RecipeManager

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "recipes.db")
db = SQL(f"sqlite:///{db_path}")

# Initialize services
user_auth = UserAuth(db)
user_plan_manager = UserPlanManager(db)
recipe_manager = RecipeManager(db)
shopping_list_service = ShoppingListService(user_plan_manager, recipe_manager)


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
        success, user_id = user_auth.login(username, password)
        if success:
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid credentials")
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
        if not mealName:
            flash('Must provide a meal name.')
            return render_template("recipes.html")
        user = session['user_id']
        recipeList = recipe_manager.get_recipes(user)
        if not recipeList or mealName not in recipeList[0]["mealName"]:
            recipe_manager.add_recipe(user, mealName, mealType, ingredients, instructions)
            return redirect("/ListOfRecipes")
    else:
        return render_template("recipes.html")


@app.route("/ListOfRecipes")
@login_required
def ListOfRecipes():
    user_id = session['user_id']
    items = recipe_manager.get_recepes_list(user_id)
    return render_template("ListOfRecipes.html", items=items)


@app.route("/displayRecipe/<int:recipe_id>", methods=["GET", "POST"])
@login_required
def displayRecipe(recipe_id):
    user_id = session["user_id"]
    recipe = recipe_manager.get_recipe_by_id(recipe_id, user_id)
    if not recipe:
        flash("Invalid recipe id", "warning")
    ingredients = [ing.strip() for ing in recipe['ingredients'].split('\n')]
    recipe['ingredients'] = ingredients
    instructions = [ing.strip() for ing in recipe['instructions'].split('\n')]
    recipe['instructions'] = instructions
    if request.method == "POST" and request.form.get("deleteRecipe"):
        recipe_manager.delete_recipe(recipe_id, user_id)
        return redirect("/ListOfRecipes")
    return render_template("displayRecipe.html", recipe=recipe)


@app.route("/editRecipe/<int:recipe_id>", methods=["GET", "POST"])
@login_required
def editRecipe(recipe_id):
    user_id = session["user_id"]
    recipe = recipe_manager.get_recipe_by_id(recipe_id, user_id)
    if not recipe:
        flash("Invalid recipe id", "warning")

    if request.method == "POST":
        ed_mealName = request.form.get("mealName")
        ed_mealType = request.form.get("mealType")
        ed_ingredients = request.form.get('ingredients')
        ed_instructions = request.form.get("instructions")
        recipe_manager.update_recipe(recipe_id, user_id, ed_mealName, ed_mealType, ed_ingredients, ed_instructions)
        return redirect(url_for("displayRecipe", recipe_id=recipe_id))

    ingredients = [ing.strip() for ing in recipe['ingredients'].split('\n')]
    instructions = [ing.strip() for ing in recipe['instructions'].split('\n')]
    return render_template("editRecipe.html", recipe=recipe, ingredients=ingredients, instructions=instructions)


@app.route("/schedule", methods=["GET", "POST"])
@login_required
def schedule():
    user_id = session["user_id"]
    if request.method == "POST":
        date = request.form.get("date")
        selected_date = request.form.get('selected_date')
        if selected_date:
            user_plan_manager.update_plan(user_id, selected_date)
            return redirect(url_for('schedule', date=selected_date))
        else:
            userPlans = user_plan_manager.get_plans(user_id, date)
    else:
        now = datetime.now()
        date = request.args.get('date')
        if not date:
            date = now.strftime("%A %d %B %Y")
        user_id = session["user_id"]
        userPlans = user_plan_manager.get_plans(user_id, date)
    return render_template("schedule.html", current_date=date, userPlans=userPlans, selected_date=date)


@app.route('/chooseMeal', methods=["GET", "POST"])
@login_required
def chooseMeal():
    user_id = session["user_id"]
    items = recipe_manager.get_recipes_ordered_by_meal_type(user_id)
    selected_date = request.form.get('selected_date')
    
    if request.method == "POST":
        userPlan = request.form["userPlan"]
        mealName = request.form.get("mealName")
        user_plan_manager.create_or_update_plan(user_id, selected_date, userPlan, mealName)
        return redirect(url_for("schedule", date=selected_date))
    else:
        return render_template('chooseMeal.html', items=items, date=selected_date)


@app.route('/shoppingList', methods=["GET", "POST"])
@login_required
def shoppingList():
    user_id = session['user_id']
    
    if request.method == "POST":
        date_range = request.form.get("date_range")
        if not date_range:
            flash("You must choose a date range.", "warning")
            return redirect(url_for("shoppingList"))
        
        start_date, end_date = date_range.split(" to ")
        start_date = datetime.strptime(start_date, "%A %d %B %Y")
        end_date = datetime.strptime(end_date, "%A %d %B %Y")
        
        ingredients = shopping_list_service.get_ingredients_for_date_range(user_id, (start_date, end_date))
        
        if not ingredients:
            flash("You didn't set any meal plan for this date range. Check your schedule.", "warning")
        
        return render_template("shoppingList.html", date_range=date_range, ingredients=ingredients)
    
    else:
        now = datetime.now()
        current_date = now.strftime("%A %d %B %Y")
        ingredients = shopping_list_service.get_ingredients_for_date_range(user_id, (now, now))
        
        if not ingredients:
            flash("You don't have any meal plan for today. Check your schedule.", "info")
        
        return render_template("shoppingList.html", current_date=current_date, ingredients=ingredients)


if __name__ == "__main__":
    app.run(debug=True)