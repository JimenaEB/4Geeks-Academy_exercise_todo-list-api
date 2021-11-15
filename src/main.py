"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os

from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from sqlalchemy import exc

from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Task

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/user', methods=['GET'])
def get_user():
    users = User.get_all()
    all_users = [user.to_dict() for user in users]
    return jsonify(all_users), 200


@app.route('/user/<int:id>', methods=['GET'])
def get_user_by_id(id):
    user = User.get_by_id(id)

    if user:
        return jsonify(user.to_dict()), 200
    
        return jsonify({'error': "User not found"}), 404


@app.route('/user', methods=['POST'])
def create_user():
    new_nick = request.json.get('nick', None)

    if not new_nick:
        return jsonify({'error': 'Missing parameters'}), 400

    user = User(nick=new_nick, _is_active=True)
    try:
        user.create()
        return jsonify(user_created.to_dict()), 201
    except exc.IntegrityError:
        return jsonify({'error': 'Fail in data'}), 400


@app.route('/user/<int:id>', methods=['PUT', 'PATCH'])
def update_user(id):
    new_nick = request.json.get('nick', None)

    if not new_nick:
        return jsonify({'error': 'Missing parameters'}), 400

    user = User.get_by_id(id)
    if user:
        user = user.update(new_nick)
        return jsonify(user.to_dict()), 200

    return jsonify({'error': 'User not found'}), 404



@app.route('/user/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.get_by_id(id)
    if user:
        user.soft_delete()
        return jsonify(user.to_dict()), 200

    return jsonify({'error': 'User not found'}), 404


@app.route('/user/<int:id>/task', methods=['GET'])
def get_user_tasks(id):
    user = User.get_by_id(id)

    if user:
        tasks = Task.get_by_user(id)
        tasks_dict = [task.to_dict() for task in tasks]
        
        return jsonify(tasks_dict), 200

    return jsonify({'error': 'User not found'}), 404


@app.route('/user/<int:id>/task', methods=['POST'])
def create_user_task(id):
    user = User.get_by_id(id)
    label = request.json.get('label', None)

    if user and label:
        task = Task(label=label, done=False, user_id=id)
        try:
            task.create()
            return jsonify(task.to_dict()), 201
        except exc.IntegrityError:
            return jsonify({'error': 'Fail in data'}), 400

    return jsonify({'error': 'User not found or label is missing'}), 404


@app.route('/user/<int:id_user>/task/<int:id_task>', methods=['DELETE'])
def delete_user_task(id_user, id_task):
    user = User.get_by_id(id_user)

    if user:
        task = Task.get_by_id(id_task)

        if task:
            try:
                task.delete()
                return jsonify(task.to_dict()), 200
            except exc.IntegrityError:
                return jsonify("Fail in operation"), 400
        
        return jsonify("Task nor found"), 404

    return jsonify("User not found"), 404



# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
