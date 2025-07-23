from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'ipl_secret'

MATCHES = [
    {"teams": "MI vs CSK", "date": "2025-08-01", "time": "7:30 PM", "stadium": "Wankhede"},
    {"teams": "RCB vs KKR", "date": "2025-08-02", "time": "7:30 PM", "stadium": "Chinnaswamy"},
    {"teams": "GT vs RR", "date": "2025-08-03", "time": "7:30 PM", "stadium": "Narendra Modi Stadium"}
]

def init_db():
    with sqlite3.connect('db.sqlite3') as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        role TEXT DEFAULT 'user')""")
        c.execute("""CREATE TABLE IF NOT EXISTS bookings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        teams TEXT,
                        stadium TEXT,
                        date TEXT,
                        time TEXT,
                        seat TEXT,
                        status TEXT)""")
        conn.commit()

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        with sqlite3.connect('db.sqlite3') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
            user = c.fetchone()
            if user:
                session['user'] = u
                session['role'] = user[3]
                return redirect('/select_match')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        with sqlite3.connect('db.sqlite3') as conn:
            try:
                c = conn.cursor()
                c.execute("INSERT INTO users(username, password) VALUES (?, ?)", (u, p))
                conn.commit()
                return redirect('/login')
            except:
                return "User already exists"
    return render_template('register.html')

@app.route('/select_match')
def select_match():
    if 'user' not in session: return redirect('/login')
    return render_template('select_match.html', matches=MATCHES)

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if 'user' not in session: return redirect('/login')
    if request.method == 'GET':
        match_data = request.args.get('match').split('|')
        session['match'] = match_data
        with sqlite3.connect('db.sqlite3') as conn:
            c = conn.cursor()
            c.execute("SELECT seat FROM bookings WHERE teams=? AND date=? AND time=?", 
                      (match_data[0], match_data[1], match_data[2]))
            booked = [r[0] for r in c.fetchall()]
        return render_template('booking.html', teams=match_data[0], stadium=match_data[3], 
                               date=match_data[1], time=match_data[2], booked=booked)

    seat = request.form['seat']
    session['seat'] = seat
    return redirect('/payment')

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'user' not in session: return redirect('/login')
    teams, date, time, stadium = session['match']
    seat = session['seat']
    return render_template('payment.html', teams=teams, date=date, time=time, stadium=stadium, seat=seat)

@app.route('/confirm', methods=['POST'])
def confirm():
    if 'user' not in session: return redirect('/login')
    data = request.form
    with sqlite3.connect('db.sqlite3') as conn:
        c = conn.cursor()
        c.execute("INSERT INTO bookings(username, teams, stadium, date, time, seat, status) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  (session['user'], data['teams'], data['stadium'], data['date'], data['time'], data['seat'], 'Paid'))
        conn.commit()
    return render_template('confirm.html', **data)

@app.route('/admin')
def admin():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect('/login')
    with sqlite3.connect('db.sqlite3') as conn:
        c = conn.cursor()
        c.execute("SELECT username, teams, stadium, date, time, seat, status FROM bookings")
        bookings = c.fetchall()
    return render_template('admin.html', bookings=bookings)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)