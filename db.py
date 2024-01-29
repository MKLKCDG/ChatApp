from datetime import datetime
from flask import Flask
import mysql.connector
from werkzeug.security import generate_password_hash
from user import User
import mysql.connector
from contextlib import closing
import base64


mydb = mysql.connector.connect(
  host="db",
   user="root",
  password="12345",
  database="chat"
)

mycursor = mydb.cursor()
mycursor.execute("USE chat")

""""""
mycursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        password VARCHAR(255) NOT NULL
    )
""")

mycursor.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        created_by VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

mycursor.execute("""
    CREATE TABLE IF NOT EXISTS room_members (
    room_id INT,
    username VARCHAR(255) NOT NULL,
    room_name VARCHAR(255) NOT NULL,
    added_by VARCHAR(255) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_room_admin BOOLEAN,
    PRIMARY KEY (room_id, username),  
    FOREIGN KEY (room_id) REFERENCES rooms(id)    
    )
""")

mycursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INT AUTO_INCREMENT PRIMARY KEY,
        room_id INT NOT NULL,
        text TEXT NOT NULL,
        sender VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")




def save_user(username, email, password):
    
    try:
        # Şifreyi güvenli bir şekilde hashle
        pasword_hash = generate_password_hash(password)

        # Kullanıcıyı veritabanına ekle
        mycursor.execute("""
            INSERT INTO users (username, email, password)
            VALUES (%s, %s, %s)
        """, (username, email, pasword_hash))

        mydb.commit()
    except mysql.connector.IntegrityError as e:
        if e.errno==1062:
             raise ValueError("Bu kullanıcı adı veya e-posta adresi zaten kullanılıyor.")
        else:
            raise e
    
def get_user(username):
    user = None
    try:
        with closing(mydb.cursor()) as mycursor:
            mycursor.execute("""
                SELECT id, username, email, password FROM users
                WHERE username = %s
            """, (username,))
            
            user_data = mycursor.fetchone()
            print("USERDATA FETCHONE")
            
            if user_data:
                print("USERDATA İFİN İÇİ = ",user_data)
                
                user_id, username, email, password_hash = user_data
                
                print("VERİLER = ",user_id, username, email, password_hash)
                
                user = User(user_id, email, password_hash)
                
                mycursor.clear_attributes()
                print("USERE GİRDİ =",user)
                return User(user_id, email, password_hash)
    except Exception as e:
        print(f"HATA ? ? ******** =  {e}")
    return None

def save_room(room_name,created_by):
    
    room_id = None
    
    try:
        # Kullanıcı kontrolü
        user = get_user(created_by)
        if not user:
            raise ValueError("Kullanıcı bulunamadı veya geçersiz.")

        # Odayı veritabanına ekle
        created_at = datetime.now()
        mycursor.execute("""
            INSERT INTO rooms (name, created_by, created_at)
            VALUES (%s, %s, %s)
        """, (room_name, created_by, created_at))
        
        mycursor.execute("SELECT LAST_INSERT_ID()") 
        room_id = mycursor.fetchone()[0]

        mydb.commit()
    except Exception as e:
        print(f"HATA = {e}")
    
    add_room_member(room_id, room_name, created_by, created_by, is_room_admin=True)
    return room_id

def delete_room_and_members(room_id):
    try:
        # Odaya ait üyelerin silinmesi
        remove_room_members(room_id)

        # Odaya ait mesajların silinmesi
        delete_room_messages(room_id)

        # Odayı veritabanından silme
        mycursor.execute("""
            DELETE FROM rooms
            WHERE id = %s
        """, (room_id,))

        mydb.commit()
        print(f"Oda {room_id} Ve Üyeleri Başarıyla Silindi.")
    except mysql.connector.Error as e:
        print(f"Hata: {e}")
        mydb.rollback()  # Hata durumunda geri alma işlemi yapılır


def remove_room_members(room_id):
        delet_query = """
            DELETE FROM room_members
            WHERE room_id = %s
         """
        mycursor.execute(delet_query, (room_id,))

        mydb.commit()

def delete_room_messages(room_id):
    try:
        global mycursor, mydb  # Eğer global değişkenler değilse bu satırı çıkarın

        # Odaya ait mesajların silinmesi
        mycursor.execute("""
            DELETE FROM messages
            WHERE room_id = %s
        """, (room_id,))

        mydb.commit()
        print(f"{room_id} Odasının Mesajları Başarıyla Silindi")
    except mysql.connector.Error as e:
        print(f"Hata: {e}")             
        
def get_room(room_id):
    try:
        mycursor.execute("""
            SELECT * FROM rooms
            WHERE id = %s
        """, (room_id,))

        room_data = mycursor.fetchone()

        if room_data:
            room_id, name, created_by, created_at = room_data
            print(f"Oda Bulundu: id={room_id}, name={name}, created_by={created_by}, created_at={created_at}")
            return room_data
        else:
            print("Oda Bulunamadı")
            return None
    except mysql.connector.Error as e:
        print(f"Hata: {e}")
        return None

def add_room_member(room_id, room_name, username, added_by, is_room_admin=False):
    try:
        # Oda üyesini eklemek için INSERT sorgusu
        added_at = datetime.now()
        mycursor.execute("""
            INSERT INTO room_members (room_id, username, room_name, added_by, added_at, is_room_admin)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (room_id, username, room_name, added_by, added_at, is_room_admin))

        # Veritabanındaki değişiklikleri kaydetme
        mydb.commit()

        print("Oda üyesi başarıyla eklendi.")
    except mysql.connector.Error as e:
        print(f"Hata: {e}")

def add_room_members(room_id, room_name, usernames, added_by):
    try:
        # Oda üyelerini eklemek için INSERT sorgusu
        added_at = datetime.now()
        is_room_admin = False

        insert_query = """
            INSERT INTO room_members (room_id, username, room_name, added_by, added_at, is_room_admin)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        # Her kullanıcı için INSERT işlemi gerçekleştir
        for username in usernames:
            mycursor.execute(insert_query, (room_id, username, room_name, added_by, added_at, is_room_admin))

        # Veritabanındaki değişiklikleri kaydetme
        mydb.commit()

        print("Oda üyeleri başarıyla eklendi.")
    except mysql.connector.Error as e:
        print(f"Hata: {e}")

def remove_room_members(room_id, usernames):
    try:
        print("Oda Üyeleri Siliniyor")
        delet_query = """
            DELETE FROM room_members
            WHERE room_id = %s AND username = %s
         """
        for username in usernames:
            mycursor.execute(delet_query, (room_id, username))
            

        mydb.commit()
        print(f"Oda üyeleri başarıyla silindi.")
    except mysql.connector.Error as e:
        print(f"Hata: {e}")

def get_room_members(room_id):
    try:
        mycursor.execute("""
            SELECT * FROM room_members
            WHERE room_id = %s
        """, (room_id,))

        room_members_data = mycursor.fetchall()

        if room_members_data:
            print(f"room_id={room_id} içinde oda üyeleri bulundu.")
            return room_members_data
        else:
            print("Oda üyeleri bulunamadı.")
            return []
    except mysql.connector.Error as e:
        print(f"Hata: {e}")
        return []

def get_rooms_for_user(username):
    try:
        mycursor.execute("""
            SELECT * FROM room_members
            WHERE username = %s
        """, (username,))

        user_rooms_data = mycursor.fetchall()

        if user_rooms_data:
            print(f"{username} Kullanıcısı Odada Bulundu")
            return user_rooms_data
        else:
            print(f"{username} Kullanıcısı Odada Bulunamadı")
            return []
    except mysql.connector.Error as e:
        print(f"Hata: {e}")
        return []
    
def is_valid_members(usernames):
    try:
        with closing(mydb.cursor()) as mycursor:
            for username in usernames:
                mycursor.execute("""
                    SELECT COUNT(*) FROM users
                    WHERE username = %s
                """, (username,))

                count = mycursor.fetchone()[0]

                if count == 0:
                    return False

            return True
    except mysql.connector.Error as e:
        print(f"Hata: {e}")

def is_email_members(email):
    try:
        with closing(mydb.cursor()) as mycursor:
            for email in email:
                mycursor.execute("""
                    SELECT COUNT(*) FROM users
                    WHERE email = %s
                """, (email,))

                count = mycursor.fetchone()[0]

                if count == 0:
                    return False

            return True
    except mysql.connector.Error as e:
        print(f"Hata: {e}")

def is_room_member(room_id, username):
    try:
        mycursor.execute("""
            SELECT COUNT(*) FROM room_members
            WHERE room_id = %s AND username = %s
        """, (room_id, username))

        count = mycursor.fetchone()[0]

        if count > 0:
            print(f"{username} Kullanıcısı {room_id}  Odasına Üye")
            return True
        else:
            print(f"{username} Kullanıcısı {room_id}  Odasına Üye Değil")
            return False
    except mysql.connector.Error as e:
        print(f"Hata: {e}")
        return False

def is_room_admin(room_id, username):
    try:
        mycursor.execute("""
            SELECT COUNT(*) FROM room_members
            WHERE room_id = %s AND username = %s AND is_room_admin = 1
        """, (room_id, username))

        count = mycursor.fetchone()[0]

        if count > 0:
            print(f"{username} room_id={room_id} Odasının Admini ")
            return True
        else:
            print(f"{username} room_id={room_id} Odasının Admini Değil")
            return False
    except mysql.connector.Error as e:
        print(f"Hata: {e}")
        return False

def save_message(room_id, text, sender):
    try:
        date_time = datetime.now()

        # Mesajı Base64 ile şifrele
        encoded_message = base64.b64encode(text.encode()).decode()

        insert_query = """
            INSERT INTO messages (room_id, text, sender, created_at)
            VALUES (%s, %s, %s, %s)
        """

        mycursor.execute(insert_query, (room_id, encoded_message, sender, date_time))
        mydb.commit()
    except mysql.connector.Error as e:
        print(f"HATA: {e}")


message_fetch_limit=999999 # Sayfa başına gösterilecek mesaj sayısı

def get_message(room_id,page=0):
    try: 
        offset = page * message_fetch_limit
        with closing(mydb.cursor()) as mycursor:
            mycursor.execute("""
                SELECT * FROM messages
                WHERE room_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (room_id, message_fetch_limit, offset))

            messages_data = mycursor.fetchall()

            if messages_data:
                print(f"Mesaj bulundu, Oda={room_id}")
                messages_data = [list(message) for message in messages_data]
                # Mesajı Base64 şifresini çözümle
                for message in messages_data:
                    message[2] = base64.b64decode(message[2]).decode()

                for message in messages_data:
                    message[4] = message[4].strftime("%d %b, %H:%M")
                return messages_data[::-1]
            else:
                print(f"Mesaj Bulunamadı, Oda={room_id}")
                return []
    except mysql.connector.Error as e:
        print(f"Hata: {e}")