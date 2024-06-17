from flask import Flask, request, render_template, redirect, url_for
import pymysql
import bcrypt
import string
import random

app = Flask(__name__, template_folder='view')

# Database configuration
db_config = {
    'host': "localhost",
    'user': "root",
    'password': "",
    'db': "testpy",
    'port': 3306,
    'cursorclass': pymysql.cursors.DictCursor
}

def generate_unique_code(length=8):
    characters = string.ascii_uppercase
    return ''.join(random.choice(characters) for i in range(length))

def create_users_table():
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    referrer_id INT,
                    individual_code VARCHAR(8) NOT NULL UNIQUE
                );
            """)
            connection.commit()
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        connection.close()

def register_user(name, email, password, referrer_code):
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            check_query = "SELECT email FROM users WHERE email = %s;"
            cursor.execute(check_query, (email,))
            if cursor.fetchone():
                return 'Error: Email already exists'
            
            referrer_id = None
            if referrer_code:
                referrer_query = "SELECT id FROM users WHERE individual_code = %s;"
                cursor.execute(referrer_query, (referrer_code,))
                referrer = cursor.fetchone()
                if referrer:
                    referrer_id = referrer['id']
                else:
                    return 'Error: Invalid referrer code'
            
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            individual_code = generate_unique_code()
            
            insert_query = """
            INSERT INTO users (name, password, email, referrer_id, individual_code)
            VALUES (%s, %s, %s, %s, %s);
            """
            cursor.execute(insert_query, (name, hashed_password, email, referrer_id, individual_code))
            connection.commit()
            return 'User registered successfully'
    except Exception as e:
        return str(e)
    finally:
        connection.close()

def login_user(email, password):
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            select_query = "SELECT * FROM users WHERE email = %s;"
            cursor.execute(select_query, (email,))
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                return user
            else:
                return None
    except Exception as e:
        return None
    finally:
        connection.close()

# Создаем таблицы в базе данных
create_users_table()

@app.route('/')
def home():
    return render_template('main.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = login_user(email, password)
        if user:
            return redirect(url_for('dashboard', user_id=user['id']))
        else:
            return render_template('login.html', error="Invalid email or password")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        referrer_code = request.form.get('referrer_code', None)
        result = register_user(name, email, password, referrer_code)
        return render_template('register.html', result=result)
    return render_template('register.html')

@app.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    return f"Welcome to your dashboard, user {user_id}!"

if __name__ == "__main__":
    app.run(debug=True, port=8080)
