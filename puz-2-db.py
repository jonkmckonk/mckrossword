import puz
import sqlite3
import sys

def main():

    if len(sys.argv) != 2:
        print("Usage: python3 puz-2-db.py {.puz file}")
        sys.exit(1)
    # open puzzle

    p = puz.read(sys.argv[1])

    # read clues into across and down dicts

    numbering = p.clue_numbering()
    
    # insert dicts into database

    with sqlite3.connect("minicrossword.db") as con:
        cur = con.cursor()

        # delete puzzle info
        cur.execute('DELETE FROM clues')

        cur.execute('DELETE FROM solution')

        cur.execute('DELETE FROM dimensions')

        # insert new info
        cur.execute('INSERT INTO solution (string) VALUES (?)', (p.solution,))

        cur.execute('INSERT INTO dimensions (width, height) VALUES (?, ?)', ((p.width), (p.height)))

        for clue in numbering.across:    
            cur.execute(
                'INSERT INTO clues (direction, clue_id, clue, answer) VALUES (?, ?, ?, ?)', (
                    'across',
                    clue['num'],
                    clue['clue'],
                    ''.join(
                    p.solution[clue['cell'] + i]
                    for i in range(clue['len']))
                    )
                )
        for clue in numbering.down:
            cur.execute(
                'INSERT INTO clues (direction, clue_id, clue, answer) VALUES (?, ?, ?, ?)', (
                    'down',
                    clue['num'],
                    clue['clue'],
                    ''.join(
                    p.solution[clue['cell'] + i * numbering.width]
                    for i in range(clue['len']))
                    )
                )
    
                    

    return

main()
