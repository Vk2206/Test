from flask import Flask, render_template, request, redirect, session
from db_config import get_connection
import hashlib

app = Flask(__name__)
app.secret_key = "secretkey"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = hash_password(request.form['password'])

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        conn.commit()
        cur.close()
        conn.close()
        return redirect('/')
    return render_template('signup.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = hash_password(request.form['password'])

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM users WHERE email=%s AND password=%s", (email, password))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        session['user_id'] = user[0]
        session['user_name'] = user[1]
        return redirect('/dashboard')
    return "Invalid credentials"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM stations")
    stations = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('dashboard.html', stations=stations)

@app.route('/book/<int:station_id>')
def book(station_id):
    if 'user_id' not in session:
        return redirect('/')
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO bookings (user_id, station_id) VALUES (%s, %s)", (session['user_id'], station_id))
    cur.execute("UPDATE stations SET available_batteries = available_batteries - 1 WHERE id = %s", (station_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/history')

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect('/')

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.name, s.location, b.booking_time FROM bookings b
        JOIN stations s ON b.station_id = s.id
        WHERE b.user_id = %s ORDER BY b.booking_time DESC
    """, (session['user_id'],))
    history = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('history.html', history=history)

if __name__ == "__main__":
    app.run(debug=True)

