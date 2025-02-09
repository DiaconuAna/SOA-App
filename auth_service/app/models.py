from app.extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    # Role can either be user or librarian
    role = db.Column(db.String(50), default='user', nullable=True)

    def __repr__(self):
        return '<User %r>' % self.username
