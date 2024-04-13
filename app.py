from flask import Flask, request, render_template, Response, jsonify, send_file
import mysql.connector
from datetime import datetime

app = Flask(__name__)

tAvailable = False
rAvailable = False
kMatch = False
clubExists = False
submit = 'add'

@app.route('/')
def index():
    database = mysql.connector.connect(host='localhost', database='database', user='root', password='Database')

    cursor = database.cursor(dictionary=True)

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    schedules = {}
    for day in days:
        query = "SELECT * FROM schedules WHERE day = %s"
        cursor.execute(query, (day,))
        schedules[day] = cursor.fetchall()

    cursor.close()
    database.close()

    return render_template('home.html', data=schedules)


@app.route('/logo')
def logo():
    return send_file("templates/cs.png", mimetype='image/png')

@app.route('/addPage')
def addPage():
    return render_template('add.html')

@app.route('/homePage')
def homePage():
    database = mysql.connector.connect(host='localhost', database='database', user='root', password='Database')

    cursor = database.cursor(dictionary=True)

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    schedules = {}
    for day in days:
        query = "SELECT * FROM schedules WHERE day = %s"
        cursor.execute(query, (day,))
        schedules[day] = cursor.fetchall()

    cursor.close()
    database.close()

    return render_template('home.html', data=schedules, scroll='true')


@app.route('/processInput', methods=['POST'])
def processInput():

    connection = mysql.connector.connect(host='localhost', database='database', user='root', password='Database')
    cursor = connection.cursor(buffered=True)

    global tAvailable, rAvailable, kMatch, clubExists, submit

    club = request.form['club']
    room = request.form['room']
    supervisor = request.form['teacher']
    sTime = datetime.strptime(request.form['sTime'], "%H:%M").strftime("%I:%M %p")
    eTime = datetime.strptime(request.form['eTime'], "%H:%M").strftime("%I:%M %p")
    day = request.form['day']
    key = request.form['key']
    submit = request.form['submit']


    tAvailable = teacherAvailable(cursor, supervisor, sTime, eTime, day)
    rAvailable = roomAvailable(cursor, room, sTime, eTime, day)
    kMatch = keyMatch(cursor, key)
    clubExists = clubExist(cursor, club, supervisor, room, sTime, eTime, day)

    print(tAvailable, "teacher available")
    print(rAvailable, "room not available ")
    print(kMatch)


    if submit == 'add':
        if clubExists == False and (tAvailable and rAvailable and kMatch):
            query = """INSERT INTO schedules (club, supervisor, room, startTime, endTime, day) VALUES (%s, %s, %s, %s, %s, %s)"""
            values = (club, supervisor, room, sTime, eTime, day)
            cursor.execute(query, values)
            connection.commit()
    elif submit == 'remove':
        if clubExists:
                query = """DELETE FROM schedules WHERE club = %s AND supervisor = %s AND room = %s AND startTime = %s AND endTime = %s AND day = %s"""                
                values = (club, supervisor, room, sTime, eTime, day)
                cursor.execute(query, values)
                connection.commit()


    cursor.close()
    connection.close()
    return Response(status=204)

def teacherAvailable(cursor, supervisor, sTime, eTime, day):
    query = ("SELECT * FROM schedules "
             "WHERE supervisor = %s AND day = %s AND startTime <= %s AND endTime >= %s")
    cursor.execute(query, (supervisor, day, sTime, eTime))

    conflict = cursor.fetchone()

    if conflict:
        return False
    else:
        return True
    
def roomAvailable(cursor, room, sTime, eTime, day):
    query = ("SELECT * FROM schedules "
             "WHERE room = %s AND day = %s AND startTime <= %s AND endTime >= %s")
    cursor.execute(query, (room, day, sTime, eTime))

    conflict = cursor.fetchone()

    if conflict:
        return False
    else:
        return True
    
def keyMatch(cursor, key):
    query = """SELECT * FROM `keys` WHERE `key` = %s"""

    value = tuple(key.split(None))
    cursor.execute(query, value)

    conflict = cursor.fetchone()

    print(conflict)

    if conflict:
        return True
    else:
        return False
    
def clubExist(cursor, club, supervisor, room, sTime, eTime, day):
    query = ("SELECT * FROM schedules "
             "WHERE club = %s AND supervisor = %s AND room = %s AND startTime = %s AND endTime = %s AND day = %s")
    cursor.execute(query, (club, supervisor, room, sTime, eTime, day))

    conflict = cursor.fetchone()

    print(conflict)

    if conflict:
        return True
    else:
        return False


@app.route('/message')
def message():
    global tAvailable, rAvailable, kMatch, clubExists
    data = ""


    if clubExists and submit == 'add':
        data = "Club Routine already present in schedule!"
    elif clubExists and submit == 'remove':
        data = "Club Routine removed from schedule!"
    elif not clubExists and submit == 'remove':
        data = "Club Routine does not exist"
    
    elif not clubExists and submit == 'add':
        if tAvailable == False and rAvailable == False:
            data = "Teacher and Room not Available at that time of day. Please verify with teacher."
        elif tAvailable == False and rAvailable == True:
            data = "Teacher is not available at that time. Please verify."
        elif tAvailable == True and rAvailable == False:
            data = "Room is not available at that time. Please verify with teacher."
        elif tAvailable and rAvailable:
            data = "Club Routine added to the schedule!"


    if kMatch == False:
        data = data = "Access Code Incorrect. Please verify."

    return jsonify(data=data)


if __name__ == '__main__':
    app.run(debug=True)