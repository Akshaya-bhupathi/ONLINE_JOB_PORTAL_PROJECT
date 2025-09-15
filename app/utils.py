from app import db, create_app
from app.models import User

def create_admin():
    """Create an admin user if none exists"""
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('securepassword')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created!")
        else:
            print("Admin user already exists")