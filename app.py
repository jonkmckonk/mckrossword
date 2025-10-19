import os


from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3

from helpers import login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

@app.after_request
def after_request(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Expires'] = 0
    response.headers['Pragma'] = 'no-cache'
    return response

@app.route("/")
def index():
        return render_template('index.html')
        


@app.route("/game", methods=["GET", "POST"])
@login_required
def game():
    # main puzzle page

    # initialise database
    with sqlite3.connect("minicrossword.db") as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT * FROM solution")
            solution = dict(cur.fetchone())
            cur.execute("SELECT * FROM dimensions")
            dimensions = dict(cur.fetchone())
            cur.execute("SELECT * FROM clues WHERE direction = 'across'")
            clues_across = [dict(row) for row in cur.fetchall()]
            cur.execute("SELECT * FROM clues WHERE direction = 'down'")
            clues_down = [dict(row) for row in cur.fetchall()]

    solution_string = solution['string']
    
    if request.method == "POST":
        
        height = dimensions['height']
        width = dimensions['width']

        # Checks solution with user input
        for row in range(height):
            for col in range(width):
                index = row * width + col
                correct_char = solution_string[index]
                user_char = request.form.get(f"cell_{row}_{col}", "").upper()

                if user_char != correct_char:
                    # log the attempt so people don't GAME IT
                    with sqlite3.connect("minicrossword.db") as con:
                        con.row_factory = sqlite3.Row
                        cur = con.cursor()
                        cur.execute("SELECT * FROM solves WHERE user_id = ? AND puzzle = ?", (session["user_id"], solution_string))
                        solves = [dict(row) for row in cur.fetchall()]
                    if not solves:
                        with sqlite3.connect("minicrossword.db") as con:
                            con.row_factory = sqlite3.Row
                            cur = con.cursor()
                            cur.execute("INSERT INTO solves (user_id, puzzle) VALUES (?, ?)", 
                                        (
                                        session["user_id"],
                                        solution_string,
                                        ))
                    
                    return redirect("/wrong")
        
        solve_time = request.form.get('elapsed')
        # input solve time into leaderboard data if there isn't one for this puzzle already
        with sqlite3.connect("minicrossword.db") as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT * FROM solves WHERE user_id = ? AND puzzle = ?", (session["user_id"], solution_string))
            solves = [dict(row) for row in cur.fetchall()]
        
        if not solves:
            # log the solve
            with sqlite3.connect("minicrossword.db") as con:
                # log whether the solve was sub 60 seconds
                if int(solve_time) < 60:
                    with sqlite3.connect("minicrossword.db") as con:
                        con.row_factory = sqlite3.Row
                        cur = con.cursor()
                        cur.execute("INSERT INTO solves (user_id, puzzle, solved, sub1) VALUES (?, ?, ?, ?)", 
                                (
                                session["user_id"],
                                solution_string,
                                1,
                                1
                                ))
                else:
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    cur.execute("INSERT INTO solves (user_id, puzzle, solved) VALUES (?, ?, ?)", 
                                (
                                session["user_id"],
                                solution_string,
                                1,
                                ))
            

        return render_template("solved.html", solve_time=solve_time)

    else:

        return render_template("game.html", clues_across=clues_across, clues_down=clues_down, dimensions=dimensions, solution=solution_string)
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    # login

    session.clear()

    if request.method == "POST":

        if not request.form.get('username'):
            return redirect('/')
        
        elif not request.form.get('password'):
            return redirect('/')
        
        with sqlite3.connect("minicrossword.db") as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE username = ?", (request.form.get('username'),))
            rows = [dict(row) for row in cur.fetchall()]
        
        # turn into hashed passwords
        if len(rows) != 1 or rows[0]['password'] != request.form.get('password'):
            return redirect('/')
        
        session["user_id"] = rows[0]['id']

        return redirect('/')
    
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

@app.route('/leaderboard')
def leaderboard():
    # get list of user_ids
    with sqlite3.connect("minicrossword.db") as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT DISTINCT id FROM users")
            users = [dict(row) for row in cur.fetchall()]
    # for user in user_id, count(puzzle), sum(solves), sum(sub1)
    leaderboard = {}

    with sqlite3.connect("minicrossword.db") as con:
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # Get all users (id + username)
        cur.execute("SELECT id, username FROM users")
        users = cur.fetchall()

        for user in users:
            user_id = user['id']
            username = user['username']

            # Get stats for this user
            cur.execute("""
                SELECT COUNT(puzzle) AS total_puzzles,
                    COALESCE(SUM(solved), 0) AS total_solved,
                    COALESCE(SUM(sub1), 0) AS total_sub1
                FROM solves
                WHERE user_id = ?
            """, (user_id,))
            stats = dict(cur.fetchone())

            # Store in leaderboard using username as the key
            leaderboard[username] = stats

    print(leaderboard)

    return render_template('leaderboard.html', leaderboard=leaderboard)

@app.route('/wrong')
@login_required
def wrong():

    return render_template('wrong.html')
