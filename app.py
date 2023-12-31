from flask import Flask, render_template, request, jsonify
import mysql.connector
import json

app = Flask(__name__)

# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'net',
    'password': 'net123',
    'database': 'example_db'
}

# Función para conectar a la base de datos
def connect_to_database():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print("Error al conectar a la base de datos:", err)
        return None

# Función para crear la tabla "posts" en la base de datos si no existe
def create_tables():
    conn = connect_to_database()
    if conn is not None:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                data_json JSON NOT NULL
            )
        """)
        conn.commit()
        #cursor.close()
        conn.close()

@app.before_first_request
def setup():
    print('Ejecutando la función create_tables')
    create_tables()

# Función para obtener el usuario de la base de datos por su correo electrónico
def get_user_by_email(email):
    conn = connect_to_database()
    if conn is not None:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM posts WHERE JSON_EXTRACT(data_json, '$.user.email') = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        #cursor.close()
        conn.close()
        return user
    else:
        return None

# Ruta para crear un nuevo post
@app.route('/posts', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        user_name = request.form['user_name']
        user_email = request.form['user_email']

        user = get_user_by_email(user_email)
        print("Contenido de user", user)
        if user:
            # Usuario ya existe, actualizamos su registro con el nuevo post
            data_json = json.loads(user['data_json'])
            posts = data_json.get('posts', [])
            print("data_json = ",data_json)
            print("posts = ",posts)
            new_post = {
                "title": title,
                "content": content
            }
            posts.append(new_post)
            data_json['posts'] = posts
            print("data_json = ",data_json)
            conn = connect_to_database()
            if conn is not None:
                cursor = conn.cursor()
                print("data_json = ",data_json)
                query = "UPDATE posts SET data_json = %s WHERE JSON_EXTRACT(data_json, '$.user.email') = %s"
                cursor.execute(query, (json.dumps(data_json), user_email))
                conn.commit()
                #cursor.close()
                conn.close()
                return jsonify({"message": "Post creado exitosamente"}), 201
            else:
                return jsonify({"message": "Error al conectar a la base de datos"}), 500
        else:
            # Usuario no existe, creamos un nuevo registro con el usuario y su post
            post_data = {
                "user": {
                    "name": user_name,
                    "email": user_email
                },
                "posts": [
                    {
                        "title": title,
                        "content": content
                    }
                ]
            }

            conn = connect_to_database()
            if conn is not None:
                cursor = conn.cursor()
                query = "INSERT INTO posts (data_json) VALUES (%s)"
                cursor.execute(query, (json.dumps(post_data),))
                conn.commit()
                #cursor.close()
                conn.close()
                return jsonify({"message": "Post creado exitosamente"}), 201
            else:
                return jsonify({"message": "Error al conectar a la base de datos"}), 500

    return render_template('create_post.html')

# Función para eliminar un usuario por su correo electrónico
# Ruta para eliminar un usuario
@app.route('/del_user', methods=['GET', 'POST'])
def delete_user_by_email():
    if request.method == 'POST':
        user_email = request.form['user_email']

        user = get_user_by_email(user_email)
        conn = connect_to_database()
        if conn is not None:
            cursor = conn.cursor()

            # Construir la consulta SQL para eliminar el usuario
            query = "DELETE FROM posts WHERE JSON_EXTRACT(data_json, '$.user.email') = %s"
            cursor.execute(query, (user_email,))

            # Hacer efectivos los cambios en la base de datos
            conn.commit()

            cursor.close()
            conn.close()
            return jsonify({"message": "Usuario borrado exitosamente"}), 201
        else:
            return jsonify({"message": "Error al conectar a la base de datos"}), 500

    return render_template('create_post.html')   

if __name__ == "__main__":
    create_tables()
    app.run()
