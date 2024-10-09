import json
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Association table for User and Recipe favorites (Many-to-Many)
favorites = db.Table('favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('recipe_id', db.Integer, db.ForeignKey('recipe.id'), primary_key=True)
)

# Model for storing user information (username, password, security questions, and favorite recipes)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)  # Username should be unique
    password = db.Column(db.String(150), nullable=False)  # Password will be stored as a hash
    answer1 = db.Column(db.String(150), nullable=False)  # Answer to the first security question
    answer2 = db.Column(db.String(150), nullable=False)  # Answer to the second security question
    answer3 = db.Column(db.String(150), nullable=False)  # Answer to the third security question
    # Many-to-Many relationship with Recipe for storing favorite recipes
    favorite_recipes = db.relationship('Recipe', secondary=favorites, backref='users')

# Model for storing recipe information
class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Name of the recipe
    ingredients = db.Column(db.String(300), nullable=False)  # List of ingredients
    quantity = db.Column(db.String(100), nullable=False)  # Quantities for the ingredients
    description = db.Column(db.String(500), nullable=False)  # Description of how to prepare the dish
    type = db.Column(db.String(50), nullable=False)  # Type: starter, main, dessert
    is_vegan = db.Column(db.Boolean, default=False)  # Boolean to indicate if the recipe is vegan
    is_vegetarian = db.Column(db.Boolean, default=False)  # Boolean to indicate if the recipe is vegetarian
    health_score = db.Column(db.Integer, nullable=False)  # Score for health
    easy_score = db.Column(db.Integer, nullable=False)  # Score for how easy it is to make
    cheap_score = db.Column(db.Integer, nullable=False)  # Score for cost
    eco_score = db.Column(db.Integer, nullable=False)  # Score for being eco-friendly
    allergens = db.Column(db.String(200), nullable=True)  # Information on allergens
    image = db.Column(db.String(200), nullable=False)  # URL to the recipe image

# Function to load recipes from the JSON file and insert them into the database
def load_recipes_from_json():
    if not os.path.exists('recipes.json'):
        print("File recipes.json not found.")
        return

    with open('recipes.json', 'r') as f:
        recipes_data = json.load(f)

    for recipe in recipes_data:
        image_name = recipe['name'].lower().replace(" ", "_") + ".jpg"
        image_path = f"img/{image_name}"

        existing_recipe = Recipe.query.filter_by(name=recipe['name']).first()
        if not existing_recipe:
            new_recipe = Recipe(
                name=recipe['name'],
                ingredients=recipe['ingredients'],
                quantity=recipe['quantity'],
                description=recipe['description'],
                type=recipe.get('type', 'plat'),
                is_vegan=recipe.get('is_vegan', False),
                is_vegetarian=recipe.get('is_vegetarian', False),
                health_score=recipe.get('health_score', 0),
                easy_score=recipe.get('easy_score', 0),
                cheap_score=recipe.get('cheap_score', 0),
                eco_score=recipe.get('eco_score', 0),
                allergens=recipe.get('allergens', ''),
                image=image_path  # Add image path
            )
            db.session.add(new_recipe)
    db.session.commit()
    print("All recipes loaded from JSON.")

def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True



# Home route - redirects to login if the user is not logged in, otherwise shows the home page
@app.route('/', methods=['GET'])
def home():
    # Récupérer les paramètres de la requête
    search_query = request.args.get('search', '')
    is_vegan = request.args.get('is_vegan')
    is_vegetarian = request.args.get('is_vegetarian')
    types = request.args.getlist('type')  # Récupérer tous les types sélectionnés
    health_score_min = request.args.get('health_score_min', 1, type=int)
    health_score_max = request.args.get('health_score_max', 5, type=int)
    easy_score_min = request.args.get('easy_score_min', 1, type=int)
    easy_score_max = request.args.get('easy_score_max', 5, type=int)
    cheap_score_min = request.args.get('cheap_score_min', 1, type=int)
    cheap_score_max = request.args.get('cheap_score_max', 5, type=int)
    eco_score_min = request.args.get('eco_score_min', 1, type=int)
    eco_score_max = request.args.get('eco_score_max', 5, type=int)

    # Construire la requête de base
    query = Recipe.query

    # Appliquer la recherche par nom ou ingrédient
    if search_query:
        query = query.filter(
            (Recipe.name.ilike(f'%{search_query}%')) |
            (Recipe.ingredients.ilike(f'%{search_query}%'))
        )

    # Filtrer pour les recettes vegan et/ou végétariennes
    if is_vegan:
        query = query.filter_by(is_vegan=True)
    if is_vegetarian:
        query = query.filter_by(is_vegetarian=True)

    # Filtrer par types de recettes (starter, main, dessert)
    if types:
        query = query.filter(Recipe.type.in_(types))

    # Filtrer par scores
    query = query.filter(
        Recipe.health_score.between(health_score_min, health_score_max),
        Recipe.easy_score.between(easy_score_min, easy_score_max),
        Recipe.cheap_score.between(cheap_score_min, cheap_score_max),
        Recipe.eco_score.between(eco_score_min, eco_score_max)
    )

    # Exécuter la requête
    recipes = query.all()

    # Rendre le template avec les résultats filtrés
    return render_template('home.html', recipes=recipes)

# Route to display details of a recipe
@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)  # Retrieve the recipe by ID
    return render_template('recipe_detail.html', recipe=recipe)


# Login route - handles both GET (show form) and POST (process login) requests
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
        else:
            flash('Something is wrong.')

    return render_template('login.html')


# Signup route - handles both GET (show form) and POST (create new user) requests
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        answer1 = request.form['answer1']
        answer2 = request.form['answer2']
        answer3 = request.form['answer3']

        if not is_valid_password(password):
            flash('Password must be at least 8 characters, include one uppercase letter, one lowercase letter, one number, and one special character.')
            return render_template('signup.html')

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        user = User(
            username=username,
            password=hashed_password,
            answer1=answer1,
            answer2=answer2,
            answer3=answer3
        )
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')


# Forgot Password route - displays security questions and verifies answers
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        answer1 = request.form['answer1']
        answer2 = request.form['answer2']
        answer3 = request.form['answer3']

        user = User.query.filter_by(username=username).first()

        if user and user.answer1 == answer1 and user.answer2 == answer2 and user.answer3 == answer3:
            session['reset_user'] = user.username  # Stocke le nom d'utilisateur dans la session
            return redirect(url_for('reset_password', username=user.username))  # Redirige vers la page de réinitialisation
        else:
            flash('Incorrect answers to security questions.')

    return render_template('forgot_password.html')



@app.route('/reset_password/<username>', methods=['GET', 'POST'])
def reset_password(username):
    if 'reset_user' not in session or session['reset_user'] != username:
        flash('Unauthorized access.')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        # Assuming you have a password validation function
        if not is_valid_password(new_password):
            flash('Password must be at least 8 characters, include one uppercase letter, one lowercase letter, one number, and one special character.')
            return render_template('reset_password.html', username=username)

        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')

        user = User.query.filter_by(username=username).first()
        if user:
            user.password = hashed_password
            db.session.commit()
            session.pop('reset_user', None)  # Remove the reset user from session after password reset
            flash('Password reset successfully!')  # Flash message indicating success
            return redirect(url_for('login'))

    return render_template('reset_password.html', username=username)

@app.route('/add_to_favorites/<int:recipe_id>', methods=['POST'])
def add_to_favorites(recipe_id):
    if 'user_id' not in session:
        flash('You need to log in first.')
        return redirect(url_for('login'))

    recipe = Recipe.query.get_or_404(recipe_id)
    user = User.query.get(session['user_id'])

    if recipe in user.favorite_recipes:
        flash('Recipe already in favorites.')
    else:
        user.favorite_recipes.append(recipe)
        db.session.commit()
        flash('Recipe added to favorites successfully!')

    return redirect(url_for('recipe_detail', recipe_id=recipe_id))

@app.route('/favorites')
def favorites():
    if 'user_id' not in session:
        flash('You need to log in first.')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    favorites = user.favorite_recipes
    return render_template('favorites.html', favorites=favorites)

@app.route('/remove_from_favorites/<int:recipe_id>', methods=['POST'])
def remove_from_favorites(recipe_id):
    if 'user_id' not in session:
        flash('You need to log in first.')
        return redirect(url_for('login'))

    recipe = Recipe.query.get_or_404(recipe_id)
    user = User.query.get(session['user_id'])

    if recipe in user.favorite_recipes:
        user.favorite_recipes.remove(recipe)
        db.session.commit()
        flash('Recipe removed from favorites successfully!')
    else:
        flash('Recipe not in your favorites.')

    return redirect(url_for('favorites'))


# Logout route - clears the session and redirects to login
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


# Route to display users in the terminal (for debugging purposes)
@app.route('/show_users')
def show_users():
    users = User.query.all()
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Password Hash: {user.password}")
    return "Users have been printed in the terminal."


# Route to display recipes in the terminal (for debugging purposes)
@app.route('/show_recipes')
def show_recipes():
    recipes = Recipe.query.all()
    print("\n--- Recipes ---")
    for recipe in recipes:
        print('5')
        print(
            f"ID: {recipe.id}, Name: {recipe.name}, "
            f"Ingredients: {recipe.ingredients}, Quantity: {recipe.quantity}, "
            f"Description: {recipe.description}, Course: {recipe.course}, "
            f"Diet: {recipe.diet}, Notes: {recipe.notes}, Allergies: {recipe.allergies}"
        )
    return "Recipes have been printed in the terminal."




if __name__ == '__main__':
    with app.app_context():
        #db.drop_all()  # Supprime toutes les tables
        db.create_all()  # Recrée toutes les tables avec le nouveau schéma
        load_recipes_from_json()

    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
