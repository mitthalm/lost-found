# === ALL IMPORTS AT THE TOP ===
import os
import sys
import logging
import uuid
import json
import time
import threading
from datetime import datetime, date, timedelta
from functools import wraps
from urllib.parse import urlparse, urljoin
from sqlalchemy import and_, text

import click

# Flask and extensions
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    has_app_context,
    current_app,
)

# Flask extensions with fallback
try:
    from flask_wtf import FlaskForm
    from flask_wtf.csrf import CSRFProtect
    FLASK_WTF_AVAILABLE = True
except ImportError:
    FLASK_WTF_AVAILABLE = False
    FlaskForm = object
    CSRFProtect = None

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    FLASK_LIMITER_AVAILABLE = True
except ImportError:
    FLASK_LIMITER_AVAILABLE = False
    Limiter = None
    get_remote_address = None

try:
    from flask_socketio import SocketIO, emit
except Exception:
    SocketIO = None

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import configuration
from config import Config

# Import database models and utilities
from db import db, User, Item, Claim, Match, Notification, init_db, ensure_schema_updates

# Import matching logic
from matching import find_matches_for_item, save_matches, get_top_matches_for_item

# Import mail service
from mail_service import (
    mail,
    send_new_item_notification,
    send_claim_request_notification,
    send_ownership_claim_submitted_notification,
    send_claim_approved_notification,
    send_owner_notification,
    send_claim_rejected_notification,
)

# Import OAuth
from auth_oauth import register_auth_routes


# === APP INITIALIZATION ===
app = Flask(__name__)
app.config.from_object(Config)

# Secure secret key - prefer environment variable
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    import secrets
    app.secret_key = secrets.token_hex(32)
    logging.warning("WARNING: Using generated secret key. Set SECRET_KEY in environment for production.")

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# File upload configuration
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['MAX_FILE_SIZE'] = 4 * 1024 * 1024  # 4MB for item images

# Create required directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'claims'), exist_ok=True)

# Initialize extensions
db.init_app(app)
mail.init_app(app)
if FLASK_WTF_AVAILABLE and CSRFProtect:
    csrf = CSRFProtect(app)
else:
    csrf = None
register_auth_routes(app)

# SocketIO initialization
if SocketIO:
    socketio = SocketIO(app, cors_allowed_origins='*')
else:
    socketio = None

# Rate limiter
if FLASK_LIMITER_AVAILABLE and Limiter:
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=os.environ.get('REDIS_URL', "memory://"),
    )
else:
    limiter = None

# Track server start time
app_start_time = datetime.utcnow()


# === LOGGING CONFIGURATION ===
def setup_logging():
    """Configure application logging"""
    if not app.debug:
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(
            os.path.join(log_dir, 'campus_lostfound.log')
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # Log startup
        app.logger.info("Application started")


# === DATABASE CLI COMMANDS ===
@app.cli.command('delete-nonadmin-users')
def delete_nonadmin_users():
    """Delete all users except admin."""
    count = User.query.filter(User.role != 'admin').delete()
    db.session.commit()
    click.echo(f"Deleted {count} non-admin users.")
    sys.stdout.flush()


@app.cli.command('init-db')
def init_db_command():
    """Initialize the database."""
    db.create_all()
    ensure_schema_updates()
    init_db()
    click.echo("Database initialized successfully.")


# === WTForms ===
try:
    from wtforms import StringField, PasswordField, TextAreaField, SelectField, DateField, FileField, BooleanField
    from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, FileAllowed
    WTFORMS_AVAILABLE = True
except ImportError:
    WTFORMS_AVAILABLE = False

if WTFORMS_AVAILABLE:
    class LostItemForm(FlaskForm):
        """Form for posting a lost item"""
        title = StringField('Title', validators=[
            DataRequired(),
            Length(min=3, max=200, message='Title must be between 3 and 200 characters')
        ])
        description = TextAreaField('Description', validators=[
            Length(max=2000, message='Description cannot exceed 2000 characters')
        ])
        category = SelectField('Category', validators=[DataRequired()])
        keywords = StringField('Keywords', validators=[
            Length(max=500, message='Keywords cannot exceed 500 characters')
        ])
        location = StringField('Location', validators=[
            DataRequired(),
            Length(max=200, message='Location cannot exceed 200 characters')
        ])
        date_lost = DateField('Date Lost', validators=[DataRequired()])
        photo = FileField('Photo', validators=[
            FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
        ])


    class FoundItemForm(FlaskForm):
        """Form for posting a found item"""
        title = StringField('Title', validators=[
            DataRequired(),
            Length(min=3, max=200, message='Title must be between 3 and 200 characters')
        ])
        description = TextAreaField('Description', validators=[
            Length(max=2000, message='Description cannot exceed 2000 characters')
        ])
        category = SelectField('Category', validators=[DataRequired()])
        keywords = StringField('Keywords', validators=[
            Length(max=500, message='Keywords cannot exceed 500 characters')
        ])
        location = StringField('Location', validators=[
            DataRequired(),
            Length(max=200, message='Location cannot exceed 200 characters')
        ])
        date_found = DateField('Date Found', validators=[DataRequired()])
        photo = FileField('Photo', validators=[
            FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
        ])


    class ClaimForm(FlaskForm):
        """Form for submitting a claim"""
        message = TextAreaField('Ownership Message', validators=[
            DataRequired(message='Please describe why this item belongs to you.'),
            Length(min=20, max=1000, message='Message must be between 20 and 1000 characters')
        ])
        proof_image = FileField('Proof Image', validators=[
            FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
        ])
        ownership_confirmed = BooleanField('I confirm this item belongs to me')


    class LoginForm(FlaskForm):
        """Login form"""
        email = StringField('Email', validators=[
            DataRequired(),
            Email(message='Invalid email address')
        ])
        password = PasswordField('Password', validators=[DataRequired()])


    class SignupForm(FlaskForm):
        """Signup form"""
        name = StringField('Name', validators=[
            DataRequired(),
            Length(min=2, max=100, message='Name must be between 2 and 100 characters')
        ])
        email = StringField('Email', validators=[
            DataRequired(),
            Email(message='Invalid email address')
        ])
        phone = StringField('Phone', validators=[
            Regexp(r'^[\d\s\-\+\$\$]*$', message='Invalid phone number format'),
            Length(max=20, message='Phone number too long')
        ])
        password = PasswordField('Password', validators=[
            DataRequired(),
            Length(min=8, message='Password must be at least 8 characters')
        ])
        confirm_password = PasswordField('Confirm Password', validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match')
        ])
else:
    # Dummy forms if WTForms is not available
    class LostItemForm:
        pass
    class FoundItemForm:
        pass
    class ClaimForm:
        pass
    class LoginForm:
        pass
    class SignupForm:
        pass


# === HELPER FUNCTIONS ===

def create_notification(user_id, message):
    """Create a notification for a user"""
    try:
        notification = Notification(user_id=user_id, message=message)
        db.session.add(notification)
        db.session.commit()
        current_app.logger.info(f"Notification created for user {user_id}")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to create notification: {e}")


def get_unread_notification_count(user_id):
    """Get count of unread notifications for a user"""
    try:
        return Notification.query.filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        ).count()
    except Exception:
        return 0


def get_recent_notifications(user_id, limit=5):
    """Get recent notifications for a user"""
    try:
        return Notification.query.filter(
            Notification.user_id == user_id
        ).order_by(
            Notification.created_at.desc()
        ).limit(limit).all()
    except Exception:
        return []


def mark_notification_read(notif_id):
    """Mark a notification as read"""
    try:
        notification = Notification.query.get(notif_id)
        if notification:
            notification.is_read = True
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to mark notification read: {e}")


def mark_all_notifications_read(user_id):
    """Mark all notifications as read for a user"""
    try:
        Notification.query.filter(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        ).update({'is_read': True})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to mark all notifications read: {e}")


def allowed_file(filename):
    """Check if file has allowed extension"""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in app.config['ALLOWED_EXTENSIONS']


def save_item_photo(file_storage, subfolder=''):
    """Save item photo with validation"""
    if not file_storage or not file_storage.filename:
        return None
    
    if not allowed_file(file_storage.filename):
        current_app.logger.warning(f"File type not allowed: {file_storage.filename}")
        return None
    
    # Validate file size
    file_storage.seek(0, 2)  # Seek to end
    size = file_storage.tell()
    file_storage.seek(0)  # Reset to start
    
    if size > app.config.get('MAX_FILE_SIZE', 4 * 1024 * 1024):
        current_app.logger.warning(f"File too large: {size} bytes")
        return None
    
    if size == 0:
        return None
    
    try:
        ext = file_storage.filename.rsplit('.', 1)[1].lower()
        filename = f'{uuid.uuid4().hex}.{ext}'
        
        if subfolder:
            save_dir = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, filename)
        else:
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        file_storage.save(save_path)
        current_app.logger.info(f"File saved: {filename}")
        return filename
    except Exception as e:
        current_app.logger.error(f"File save error: {e}")
        return None


def is_safe_url(target):
    """Validate URL is safe (same domain)"""
    if not target:
        return False
    
    # Block relative URLs starting with //
    if target.startswith('//'):
        return False
    
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    
    return (
        test_url.scheme in ('http', 'https')
        and ref_url.netloc == test_url.netloc
    )


def notify_admins(message):
    """Notify all administrators"""
    try:
        admins = User.query.filter_by(role='admin').all()
        for admin in admins:
            create_notification(admin.user_id, message)
    except Exception as e:
        current_app.logger.error(f"Failed to notify admins: {e}")


def item_claimable(item, user_id=None):
    """Check if item can be claimed by user"""
    if item.status not in ('lost', 'found'):
        return False
    if user_id and item.user_id == user_id:
        return False
    if user_id:
        existing = Claim.query.filter_by(
            item_id=item.item_id,
            claimer_user_id=user_id
        ).first()
        if existing:
            return False
    return True


def login_required(f):
    """Decorator requiring login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator requiring admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login', next=request.url))
        
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# === BACKGROUND WORKER ===

def background_process_matches(item_id):
    """Background worker for match processing"""
    if not has_app_context():
        with app.app_context():
            _process_matches_internal(item_id)
    else:
        _process_matches_internal(item_id)


def _process_matches_internal(item_id):
    """Internal match processing logic"""
    try:
        item = Item.query.get(item_id)
        if not item:
            current_app.logger.warning(f"Item {item_id} not found for matching")
            return
        
        current_app.logger.info(f"Processing matches for item {item_id}")
        
        # Compute and persist matches
        matches = find_matches_for_item(item)
        save_matches(item)
        
        # Notify matched item owners if confidence > 0.75
        for matched_item, score in matches:
            if score >= 0.75:
                # Notify the owner
                match_url = url_for('item_detail', item_id=item.item_id, _external=True)
                create_notification(
                    matched_item.user_id,
                    f'Possible match found for your item "{matched_item.title}". Check {match_url}'
                )
                
                # Send email notification
                try:
                    from mail_service import send_possible_match_notification
                    send_possible_match_notification(
                        lost_owner_email=matched_item.user.email,
                        lost_owner_name=matched_item.user.name,
                        found_uploader_name=item.user.name,
                        found_uploader_email=item.user.email,
                        lost_item_title=matched_item.title,
                        found_item_title=item.title,
                        match_url=match_url
                    )
                except Exception as e:
                    current_app.logger.error(f"Email send failed: {e}")
                
                # Emit socket event
                if socketio:
                    payload = {
                        'to_user_id': matched_item.user_id,
                        'message': f'Possible match found for "{matched_item.title}"',
                        'found_item_id': item.item_id,
                        'found_item_title': item.title,
                        'score': score
                    }
                    try:
                        socketio.emit('new_match', payload)
                    except Exception as e:
                        current_app.logger.error(f"Socket emit failed: {e}")
        
        current_app.logger.info(f"Match processing complete for item {item_id}")
    except Exception as e:
        current_app.logger.error(f"Background matching error for item {item_id}: {e}")


def get_uploaded_item_photo():
    """Get uploaded photo from form"""
    photo = request.files.get('photo')
    if photo and photo.filename:
        return photo
    image = request.files.get('image')
    if image and image.filename:
        return image
    return None


# === VIEW ROUTES ===

@app.route('/')
def index():
    """Home page"""
    total_lost = Item.query.filter_by(status='lost').count()
    total_found = Item.query.filter_by(status='found').count()
    total_claimed = Item.query.filter_by(status='claimed').count()
    
    recent_items = Item.query.order_by(Item.date_reported.desc()).limit(6).all()
    
    return render_template('index.html',
                         total_lost=total_lost,
                         total_found=total_found,
                         total_claimed=total_claimed,
                         recent_items=recent_items)


@app.route('/browse')
def browse():
    """Browse items page"""
    status_filter = request.args.get('status', 'all')
    category_filter = request.args.get('category', '')
    location_filter = request.args.get('location', '')
    
    query = Item.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if category_filter:
        query = query.filter(Item.category.ilike(f'%{category_filter}%'))
    
    if location_filter:
        query = query.filter(Item.location.ilike(f'%{location_filter}%'))
    
    items = query.order_by(Item.date_reported.desc()).all()
    
    # Get unique categories and locations
    categories = db.session.query(Item.category).distinct().all()
    locations = db.session.query(Item.location).distinct().all()