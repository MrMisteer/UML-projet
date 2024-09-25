#Ceci est le code du serveur en python

from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)


# Modèle pour les utilisateurs
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)


# Modèle pour les recettes
class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.String(300), nullable=False)
    quantity = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)


@app.route('/')
def home():
    if 'user_id' in session:
        return render_template('home.html', username=session['username'])
    else:
        return redirect(url_for('login'))


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
            flash('Identifiant ou mot de passe incorrect.')

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Utilisation de l'algorithme 'pbkdf2:sha256'
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/show_users')
def show_users():
    users = User.query.all()
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Password Hash: {user.password}")
    return "Les utilisateurs ont été affichés dans le terminal."


@app.route('/show_recipes')
def show_recipes():
    recipes = Recipe.query.all()
    for recipe in recipes:
        print(f"ID: {recipe.id}, Name: {recipe.name}, Ingredients: {recipe.ingredients}, Quantity: {recipe.quantity}, Description: {recipe.description}")
    return "Les recettes ont été affichées dans le terminal."



if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(host='172.30.40.6', port=5000, debug=True, threaded=True)


