from datetime import datetime
from flask import Flask, render_template, redirect, url_for,request,redirect,url_for,session
from flask_socketio import SocketIO,send,join_room,send,emit
from flask_login import LoginManager,login_required, login_user, logout_user,current_user

import json
from bson.json_util import dumps
from flask import jsonify

from db import add_room_members, get_message, get_room, get_room_members, get_rooms_for_user, get_user, is_room_admin, is_room_member, remove_room_members, save_message, save_room, save_user, delete_room_messages, delete_room_and_members, is_valid_members
from user import User
from flask_session import Session


app=Flask(__name__)
app.secret_key = "Secret Key"
app.config['SECRET']="123456"
socketio=SocketIO(app, cors_allowed_origins="*") 
login_manager = LoginManager()
login_manager.login_view='login'
login_manager.init_app(app)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route('/')
def home():
    if not session.get("username"):
        return redirect("/login")
    else:
        rooms = get_rooms_for_user(session.get("username"))    
    return render_template("index.html", rooms=rooms)

@app.route('/login', methods=['GET', 'POST'])
def login():
    
    if 'username' in session:
        return redirect(url_for('home'))
    
    message = ''
    if request.method == 'POST':
        entered_username = request.form.get('username')
        entered_password = request.form.get('password')
        
        user = get_user(entered_username)
                
        if user and user.check_password(entered_password):
            login_user(user)
            session['username'] = entered_username
            return redirect(url_for('home'))
        else:
            message = 'Kullanıcı adı veya şifre yanlış'
    
    return render_template('login.html', message=message)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    
    if session.get("username"):
        return render_template('index.html')

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if is_valid_members([username]) or is_valid_members([email]):
            message = "Kullanıcı Adı ve E-posta Kullanılıyor."
            print(message)

        else:
            save_user(username, email, password)
            return redirect(url_for('login'))

    
    return render_template('signup.html', message=message)

@app.route("/logout")
def logout():
    session.clear()
    logout_user()
    return redirect(url_for('home'))

@app.route('/create_room', methods=['GET', 'POST'])
def create_room():
    if not session.get("username"):
        return redirect("/login")

    message = ""

    if request.method == 'POST':
        room_name = request.form.get('room_name')
        usernames = [username.strip() for username in request.form.get('members').split(',')]

        if is_valid_members(usernames):
            room_id = save_room(room_name, session.get("username"))
            if session.get("username") in usernames:
                usernames.remove(session.get("username"))
            add_room_members(room_id, room_name, usernames, session.get("username"))

            # Broadcast the room creation event to all clients
            socketio.emit('room_created', {'roomId': room_id, 'roomName': room_name})

            return redirect(url_for('view_room', room_id=room_id))
        else:
            message = "Kayıtlı Olmayan Kullanıcı"
            print(message)

    return render_template("create_room.html", server_ip="http://16.171.152.178:5000/")

@app.route('/rooms/<room_id>/delete', methods=['POST'])
def delete_room(room_id):
    if not session.get("username"):
        return redirect("/login")

    if is_room_admin(room_id, session.get("username")):
        # Yalnızca oda yöneticisi odayı silebilir
        delete_room_messages(room_id)
        delete_room_and_members(room_id)
        
        # Socket.io ile "room_deleted" mesajını istemcilere gönder
        socketio.emit('room_deleted', {'roomId': room_id})
        
        return jsonify({"message": "Oda başarıyla silindi."}), 200
    else:
        return jsonify({"error": "Bu işlemi gerçekleştirmek için yeterli izniniz yok."}), 403

def delete_room_and_members(room_id):
    # Odadaki tüm üyeleri kaldır
    room_members = get_room_members(room_id)
    usernames = [member[1] for member in room_members]
    remove_room_members(room_id, usernames)
    

@app.route('/rooms/<room_id>/')
def view_room(room_id):
    
    if not session.get("username"):
        return redirect("/login") 
    
    room=get_room(room_id)
    if room and is_room_member(room_id,session['username']):
        room_uye=get_room_members(room_id)
        message=get_message(room_id)
        return render_template('view_room.html',username =session.get("username") ,room=room,room_members=room_uye,messages=message)
    else:
        return redirect(url_for('home'))


@app.route('/rooms/<room_id>/messages/')
def get_older_messages(room_id):

    if not session.get("username"):
        return redirect("/login") 
    print("Get_older_mesaj")
    
    room=get_room(room_id)
    if room and is_room_member(room_id,session['username']):
        page = int(request.args.get('page', 0))
        messages=get_message(room_id,page) 
        
        message_dicts = [
        {
            "id": message[0],
            "room_id": message[1],
            "text": message[2],
            "username": message[3],
            "created_at": message[4]
        }
            for message in messages
            ]
        
        return jsonify(message_dicts)
    else:
        return "Oda bulunamadı",404
    

@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info("{},{} Numaralı Odaya Mesaj Gönderdi: {}".format(data['username'],data['room'],data['message']))
    
    data['created_at'] = datetime.now().strftime("%d %b, %H:%M")
    
    str= data['room']
    print(str)
    save_message(str,data['message'],data['username'])
    socketio.emit('receive_message', data, room=data['room'])

@socketio.on('join_room')
def handle_join_room_event(data):
    app.logger.info("{} Adlı Kullanıcısı {} Odasına Katıldı".format(data['username'],data['room']))
    join_room(data['room'])
    socketio.emit('join_room_announcement',data)

@login_manager.user_loader
def load_user(username):
    return get_user(username)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True, use_reloader=True, allow_unsafe_werkzeug=True)