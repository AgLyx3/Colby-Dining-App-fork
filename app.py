from flask import Flask
from models import db
from flask_login import LoginManager
from views import main_blueprint

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'secret keyyyyy'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

#login_manager = LoginManager(app)

# Register blueprint for routes
app.register_blueprint(main_blueprint)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables (if not created)
    app.run(debug=True, port=8000)