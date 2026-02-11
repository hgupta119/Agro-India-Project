import sqlite3
import hashlib
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATABASE = 'users.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    print("Initializing database...")
    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Table for Users (Login/Register)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                full_name TEXT
            )
        ''')
        
        # --- NEW: Table for Products (Crops) ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price_text TEXT,
                price_num REAL,
                description TEXT,
                image TEXT,
                seller_name TEXT
            )
        ''')
        
        conn.commit()
        print("Database initialized (Users & Products tables ready).")
        conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# --- USER ROUTES (OLD CODE) ---

@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')

    if not email or not password or not full_name:
        return jsonify({"message": "Missing email, password, or name"}), 400

    hashed_password = hash_password(password)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, password, full_name) VALUES (?, ?, ?)",
            (email, hashed_password, full_name)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "User registered successfully!"}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"message": "This email is already registered"}), 400
    except Exception as e:
        conn.close()
        return jsonify({"message": str(e)}), 500

@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Missing email or password"}), 400

    hashed_password = hash_password(password)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE email = ? AND password = ?",
        (email, hashed_password)
    )
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"message": "Login successful!", "fullName": user['full_name']}), 200
    else:
        return jsonify({"message": "Invalid email or password"}), 401

# --- NEW: PRODUCT ROUTES (Data Save Karne Ke Liye) ---

@app.route('/products', methods=['GET'])
def get_products():
    """Fetch all products from database"""
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products ORDER BY id DESC').fetchall()
    conn.close()
    
    # Convert database rows to list of dictionaries
    products_list = [dict(row) for row in products]
    
    # If database is empty, return some default data so page isn't empty
    if not products_list:
        return jsonify([
            { "id": 1, "name": "Fresh Apples", "price_text": "₹200 / kg", "price_num": 200, "description": "Crisp, sweet apples.", "image": "https://tse2.mm.bing.net/th/id/OIP.k_tJy7YvcHY8yY3pi9gWkgHaFP?rs=1&pid=ImgDetMain&o=7&rm=3", "seller_name": "Default" },
            { "id": 2, "name": "Organic Carrots", "price_text": "₹80 / bunch", "price_num": 80, "description": "Farm-fresh organic carrots.", "image": "https://tse3.mm.bing.net/th/id/OIP.nFtUUisZP0u9AEMZ8BPkmQHaHa?rs=1&pid=ImgDetMain&o=7&rm=3", "seller_name": "Default" }
        ])
        
    return jsonify(products_list)

@app.route('/add_product', methods=['POST'])
def add_product():
    """Add a new product to database"""
    data = request.get_json()
    
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO products (name, price_text, price_num, description, image, seller_name) VALUES (?, ?, ?, ?, ?, ?)',
        (data['name'], data['priceText'], data['priceNum'], data['desc'], data['img'], data['seller'])
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Product added successfully"}), 201

@app.route('/delete_product/<int:id>', methods=['DELETE'])
def delete_product(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Deleted"}), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)