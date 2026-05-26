import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)

    google_id = db.Column(db.String(128), unique=True, nullable=True)
    apple_id = db.Column(db.String(128), unique=True, nullable=True)

    phone_otp = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    phone_verified = db.Column(db.Boolean, default=False)

    avatar_url = db.Column(db.String(500), nullable=True)
    auth_provider = db.Column(db.String(20), default='email')

    role = db.Column(db.Enum('user', 'moderator', 'admin', name='user_role'), default='user')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('Item', backref='user', lazy=True)
    claims_made = db.relationship('Claim', foreign_keys='Claim.claimer_user_id', backref='claimer', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

class Item(db.Model):
    __tablename__ = 'items'
    
    item_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)
    keywords = db.Column(db.String(255))
    location = db.Column(db.String(100), nullable=False)
    date_reported = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.Enum('lost', 'found', 'claimed', name='item_status'), nullable=False)
    image = db.Column(db.String(255))
    # Optional stored image features for fast matching (JSON or base64-encoded)
    image_phash = db.Column(db.String(64), nullable=True)
    image_embedding = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)

    @property
    def photo(self):
        """Filename-only alias for templates (stored in image column)."""
        if not self.image:
            return None
        return os.path.basename(self.image.replace('\\', '/'))
    
    # Relationships
    claims = db.relationship('Claim', backref='item', lazy=True)
    lost_matches = db.relationship('Match', foreign_keys='Match.lost_item_id', backref='lost_item', lazy=True)
    found_matches = db.relationship('Match', foreign_keys='Match.found_item_id', backref='found_item', lazy=True)

class Claim(db.Model):
    __tablename__ = 'claims'
    
    claim_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.item_id'), nullable=False)
    claimer_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    message = db.Column(db.Text)
    proof_image = db.Column(db.String(255))
    ownership_confirmed = db.Column(db.Boolean, default=False)
    status = db.Column(db.Enum('pending', 'approved', 'rejected', name='claim_status'), default='pending')
    claimed_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

class Match(db.Model):
    __tablename__ = 'matches'
    
    match_id = db.Column(db.Integer, primary_key=True)
    lost_item_id = db.Column(db.Integer, db.ForeignKey('items.item_id'), nullable=False)
    found_item_id = db.Column(db.Integer, db.ForeignKey('items.item_id'), nullable=False)
    match_score = db.Column(db.Float, nullable=False)
    found_confirmed = db.Column(db.Boolean, default=False)
    lost_confirmed = db.Column(db.Boolean, default=False)
    resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    notif_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='notifications')

def ensure_schema_updates():
    """Add new columns to existing SQLite databases without Alembic."""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)

    if 'claims' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('claims')]
        if 'ownership_confirmed' not in columns:
            with db.engine.begin() as conn:
                conn.execute(text(
                    'ALTER TABLE claims ADD COLUMN ownership_confirmed BOOLEAN DEFAULT 0'
                ))

    if 'users' in inspector.get_table_names():
        user_columns = {col['name'] for col in inspector.get_columns('users')}
        user_additions = [
            ('google_id', 'VARCHAR(128)'),
            ('apple_id', 'VARCHAR(128)'),
            ('phone_otp', 'VARCHAR(6)'),
            ('otp_expiry', 'DATETIME'),
            ('phone_verified', 'BOOLEAN DEFAULT 0'),
            ('avatar_url', 'VARCHAR(500)'),
            ('auth_provider', "VARCHAR(20) DEFAULT 'email'"),
            ('role', "VARCHAR(20) DEFAULT 'user'"),
            ('is_active', 'BOOLEAN DEFAULT 1'),
        ]
        # Add item-level columns if they don't exist
        item_columns = {col['name'] for col in inspector.get_columns('items')} if 'items' in inspector.get_table_names() else set()
        item_additions = [
            ('image_phash', 'VARCHAR(64)'),
            ('image_embedding', 'TEXT'),
        ]
        with db.engine.begin() as conn:
            for col_name, col_type in user_additions:
                if col_name not in user_columns:
                    conn.execute(text(f'ALTER TABLE users ADD COLUMN {col_name} {col_type}'))
            for col_name, col_type in item_additions:
                if col_name not in item_columns:
                    conn.execute(text(f'ALTER TABLE items ADD COLUMN {col_name} {col_type}'))
        
        # Add match-related columns (in separate connection context)
        if 'matches' in inspector.get_table_names():
            match_columns = {col['name'] for col in inspector.get_columns('matches')}
            match_additions = [
                ('found_confirmed', 'BOOLEAN DEFAULT 0'),
                ('lost_confirmed', 'BOOLEAN DEFAULT 0'),
                ('resolved', 'BOOLEAN DEFAULT 0'),
            ]
            with db.engine.begin() as conn:
                for col_name, col_type in match_additions:
                    if col_name not in match_columns:
                        conn.execute(text(f'ALTER TABLE matches ADD COLUMN {col_name} {col_type}'))

def init_db():
    """Initialize the database with tables"""
    db.create_all()
    ensure_schema_updates()
    
    # Create default admin user if not exists
    admin_email = 'mitthalm2006@gmail.com'
    admin_password = 'Mitthal#12&34'
    # Try to find by phone (since phone is unique and likely already exists)
    admin = User.query.filter_by(phone='0000000000').first()
    if admin:
        admin.email = admin_email
        admin.set_password(admin_password)
        admin.role = 'admin'
        db.session.commit()
        print(f"Admin user updated: {admin_email} / {admin_password}")
    else:
        admin = User(
            name='System Admin',
            email=admin_email,
            phone='0000000000',
            role='admin',
            auth_provider='email',
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print(f"Default admin user created: {admin_email} / {admin_password}")
