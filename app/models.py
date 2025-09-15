from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'employer', 'jobseeker'
    jobs = db.relationship('Job', back_populates='author', 
                         foreign_keys='Job.user_id')
    job_applications = db.relationship('Application', back_populates='applicant', lazy=True)
    applications = db.relationship('Application', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def has_applied(self, job):
        return Application.query.filter_by(
                user_id=self.id,
                job_id=job.id
            ).first() is not None
        
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    salary = db.Column(db.String(50))
    location = db.Column(db.String(100))
    company = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    applications = db.relationship('Application', back_populates='job', lazy=True)
    author = db.relationship('User', back_populates='jobs',
                           foreign_keys=[user_id])
    
    
class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    cover_letter = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date_applied = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    job = db.relationship('Job', back_populates='applications')
    applicant = db.relationship('User', back_populates='job_applications')

