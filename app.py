import os


from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3

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

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        with sqlite3.connect("minicrossword.db") as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM solution")
            solution = cur.fetchall()[0][0]
            cur.execute("SELECT * FROM dimensions")
            dimensions = cur.fetchall()
        
        height = dimensions[0][0]
        width = dimensions[0][1]

        # Checks solution with user input
        for row in range(height):
            for col in range(width):
                index = row * width + col
                correct_char = solution[index]
                user_char = request.form.get(f"cell_{row}_{col}", "").upper()

                if user_char != correct_char:
                    print('Wrong solution')
                    return redirect("/")
        
        [print('Correct!')]
        return redirect("/")

    else:
        with sqlite3.connect("minicrossword.db") as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM clues WHERE direction = 'across'")
            clues_across = cur.fetchall()
            cur.execute("SELECT * FROM clues WHERE direction = 'down'")
            clues_down = cur.fetchall()
            cur.execute("SELECT * FROM dimensions")
            dimensions = cur.fetchall()
            cur.execute("SELECT * FROM solution")
            solution = cur.fetchall()

            solution = str(solution).strip(('[]()')).replace(',', '').replace('\'','')

        return render_template("index.html", clues_across=clues_across, clues_down=clues_down, dimensions=dimensions, solution=solution)

    


