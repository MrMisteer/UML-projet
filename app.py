import json
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

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
    type = db.Column(db.String(50), nullable=False)  # Type: entrée, plat, dessert
    is_vegan = db.Column(db.Boolean, default=False)  # Boolean to indicate if the recipe is vegan
    is_vegetarian = db.Column(db.Boolean, default=False)  # Boolean to indicate if the recipe is vegetarian
    # Ratings for different aspects (health, easy to make, cheap, eco-friendly)
    health_score = db.Column(db.Integer, nullable=False)  # Score for health
    easy_score = db.Column(db.Integer, nullable=False)  # Score for how easy it is to make
    cheap_score = db.Column(db.Integer, nullable=False)  # Score for cost
    eco_score = db.Column(db.Integer, nullable=False)  # Score for being eco-friendly
    allergens = db.Column(db.String(200), nullable=True)  # Information on allergens (e.g. gluten, dairy)

# Function to load recipes from the JSON file and insert them into the database
def load_recipes_from_json():
    if not os.path.exists('recipes.json'):
        print("File recipes.json not found.")
        return

    with open('recipes.json', 'r') as f:
        recipes_data = json.load(f)

    for recipe in recipes_data:
        existing_recipe = Recipe.query.filter_by(name=recipe['name']).first()
        if not existing_recipe:
            new_recipe = Recipe(
                name=recipe['name'],
                ingredients=recipe['ingredients'],
                quantity=recipe['quantity'],
                description=recipe['description'],
                type=recipe.get('type', 'plat'),  # Default to 'plat' if not specified
                is_vegan=recipe.get('is_vegan', False),
                is_vegetarian=recipe.get('is_vegetarian', False),
                health_score=recipe.get('health_score', 0),
                easy_score=recipe.get('easy_score', 0),
                cheap_score=recipe.get('cheap_score', 0),
                eco_score=recipe.get('eco_score', 0),
                allergens=recipe.get('allergens', '')
            )
            db.session.add(new_recipe)
    db.session.commit()
    print("All recipes loaded from JSON.")


# Home route - redirects to login if the user is not logged in, otherwise shows the home page
@app.route('/')
def home():
    if 'user_id' in session:
        recipes = Recipe.query.all()  # Get all recipes from the database
        return render_template('home.html', username=session['username'], recipes=recipes)
    else:
        return redirect(url_for('login'))

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
            flash('Invalid username or password.')

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



# Reset Password route - allows user to reset their password after answering security questions
@app.route('/reset_password/<username>', methods=['GET', 'POST'])
def reset_password(username):
    if 'reset_user' not in session or session['reset_user'] != username:
        flash('Unauthorized access.')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')

        user = User.query.filter_by(username=username).first()
        if user:
            user.password = hashed_password
            db.session.commit()
            session.pop('reset_user', None)  # Supprime l'utilisateur de la session après le reset
            flash('Password reset successfully!')
            return redirect(url_for('login'))

    # Passe uniquement 'username' au template
    return render_template('reset_password.html', username=username)




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
