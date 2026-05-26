"""Google OAuth, Apple OAuth, and phone OTP authentication."""
import json
import random
import time
from datetime import datetime, timedelta

from authlib.integrations.flask_client import OAuth
from flask import flash, redirect, render_template, request, session, url_for, current_app

from db import db, User
from auth_session import login_user_session, redirect_after_login, store_oauth_next, pop_oauth_next

oauth = OAuth()


def _google_enabled():
    return bool(current_app.config.get('GOOGLE_CLIENT_ID') and current_app.config.get('GOOGLE_CLIENT_SECRET'))


def _apple_enabled():
    return bool(
        current_app.config.get('APPLE_CLIENT_ID')
        and current_app.config.get('APPLE_TEAM_ID')
        and current_app.config.get('APPLE_KEY_ID')
        and current_app.config.get('APPLE_PRIVATE_KEY')
    )


def _twilio_enabled():
    return bool(
        current_app.config.get('TWILIO_ACCOUNT_SID')
        and current_app.config.get('TWILIO_AUTH_TOKEN')
        and current_app.config.get('TWILIO_PHONE_NUMBER')
    )


def generate_apple_client_secret():
    import jwt
    private_key = current_app.config['APPLE_PRIVATE_KEY']
    if '\\n' in private_key and '\n' not in private_key:
        private_key = private_key.replace('\\n', '\n')
    headers = {'kid': current_app.config['APPLE_KEY_ID'], 'alg': 'ES256'}
    payload = {
        'iss': current_app.config['APPLE_TEAM_ID'],
        'iat': int(time.time()),
        'exp': int(time.time()) + 86400 * 180,
        'aud': 'https://appleid.apple.com',
        'sub': current_app.config['APPLE_CLIENT_ID'],
    }
    return jwt.encode(payload, private_key, algorithm='ES256', headers=headers)


def send_otp(phone_number, otp):
    if _twilio_enabled():
        from twilio.rest import Client as TwilioClient
        client = TwilioClient(
            current_app.config['TWILIO_ACCOUNT_SID'],
            current_app.config['TWILIO_AUTH_TOKEN'],
        )
        client.messages.create(
            body=f'Your Campus Lost & Found OTP is: {otp}. Valid for 5 minutes.',
            from_=current_app.config['TWILIO_PHONE_NUMBER'],
            to=phone_number,
        )
    else:
        current_app.logger.warning('[DEV OTP] %s -> %s (configure Twilio in .env for SMS)', phone_number, otp)
        print(f'[DEV OTP] Phone {phone_number}: {otp}')


def _find_or_create_google_user(userinfo):
    google_id = userinfo.get('sub')
    email = userinfo.get('email')
    name = userinfo.get('name') or (email.split('@')[0] if email else 'User')
    avatar = userinfo.get('picture')

    user = User.query.filter_by(google_id=google_id).first()
    if not user and email:
        user = User.query.filter_by(email=email).first()
        if user:
            user.google_id = google_id
            user.auth_provider = 'google'
            if avatar:
                user.avatar_url = avatar
    if not user:
        if not email:
            email = f'{google_id}@google.oauth.local'
        user = User(
            name=name,
            email=email,
            google_id=google_id,
            avatar_url=avatar,
            auth_provider='google',
            role='user',
        )
        db.session.add(user)
    db.session.commit()
    return user


def _find_or_create_apple_user(claims, display_name='User'):
    apple_id = claims.get('sub')
    email = claims.get('email')

    user = User.query.filter_by(apple_id=apple_id).first()
    if not user and email:
        user = User.query.filter_by(email=email).first()
        if user:
            user.apple_id = apple_id
            user.auth_provider = 'apple'
    if not user:
        user = User(
            name=display_name,
            email=email,
            apple_id=apple_id,
            auth_provider='apple',
            role='user',
        )
        db.session.add(user)
    db.session.commit()
    return user


def register_auth_routes(app):
    oauth.init_app(app)

    google = None
    apple_oauth = None

    if app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'):
        google = oauth.register(
            name='google',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'},
        )

    if (
        app.config.get('APPLE_CLIENT_ID')
        and app.config.get('APPLE_TEAM_ID')
        and app.config.get('APPLE_KEY_ID')
        and app.config.get('APPLE_PRIVATE_KEY')
    ):
        apple_oauth = oauth.register(
            name='apple',
            client_id=app.config['APPLE_CLIENT_ID'],
            client_secret=generate_apple_client_secret,
            api_base_url='https://appleid.apple.com',
            access_token_url='https://appleid.apple.com/auth/token',
            authorize_url='https://appleid.apple.com/auth/authorize',
            client_kwargs={
                'scope': 'name email',
                'response_mode': 'form_post',
            },
            jwks_uri='https://appleid.apple.com/auth/keys',
        )

    @app.route('/auth/google')
    def google_login():
        if not google:
            flash('Google sign-in is not configured.', 'error')
            return redirect(url_for('login'))
        store_oauth_next(request.args.get('next'))
        redirect_uri = url_for('google_callback', _external=True)
        return google.authorize_redirect(redirect_uri)

    @app.route('/auth/google/callback')
    def google_callback():
        if not google:
            flash('Google sign-in is not configured.', 'error')
            return redirect(url_for('login'))
        try:
            token = google.authorize_access_token()
            userinfo = token.get('userinfo')
            if not userinfo:
                userinfo = google.parse_id_token(token, nonce=None)
            if not userinfo:
                flash('Google login failed. Please try again.', 'error')
                return redirect(url_for('login'))
            user = _find_or_create_google_user(userinfo)
            login_user_session(user)
            flash('Logged in with Google.', 'success')
            return redirect_after_login(user, pop_oauth_next())
        except Exception as exc:
            current_app.logger.exception('Google OAuth error: %s', exc)
            flash('Google login failed. Please try again.', 'error')
            return redirect(url_for('login'))

    @app.route('/auth/apple')
    def apple_login():
        if not apple_oauth:
            flash('Apple sign-in is not configured.', 'error')
            return redirect(url_for('login'))
        store_oauth_next(request.args.get('next'))
        redirect_uri = url_for('apple_callback', _external=True)
        return apple_oauth.authorize_redirect(redirect_uri)

    @app.route('/auth/apple/callback', methods=['GET', 'POST'])
    def apple_callback():
        if not apple_oauth:
            flash('Apple sign-in is not configured.', 'error')
            return redirect(url_for('login'))
        try:
            token = apple_oauth.authorize_access_token()
            claims = apple_oauth.parse_id_token(token, nonce=None)
            name = 'User'
            user_data = request.form.get('user')
            if user_data:
                info = json.loads(user_data)
                fn = info.get('name', {}).get('firstName', '')
                ln = info.get('name', {}).get('lastName', '')
                name = f'{fn} {ln}'.strip() or 'User'
            user = _find_or_create_apple_user(claims, name)
            login_user_session(user)
            flash('Logged in with Apple.', 'success')
            return redirect_after_login(user, pop_oauth_next())
        except Exception as exc:
            current_app.logger.exception('Apple OAuth error: %s', exc)
            flash('Apple login failed. Please try again.', 'error')
            return redirect(url_for('login'))

    @app.route('/auth/phone', methods=['GET', 'POST'])
    def phone_login():
        if request.method == 'POST':
            phone = request.form.get('phone_number', '').strip().replace(' ', '')
            if not phone.startswith('+') or len(phone) < 10:
                flash('Enter a valid phone number with country code (e.g. +91...).', 'error')
                return redirect(url_for('phone_login'))

            otp = str(random.randint(100000, 999999))
            expiry = datetime.utcnow() + timedelta(seconds=app.config['OTP_EXPIRY_SECONDS'])

            user = User.query.filter_by(phone=phone).first()
            if not user:
                user = User(
                    phone=phone,
                    name=f'user_{phone[-4:]}',
                    auth_provider='phone',
                    role='user',
                )
                db.session.add(user)

            user.phone_otp = otp
            user.otp_expiry = expiry
            db.session.commit()

            try:
                send_otp(phone, otp)
                session['otp_phone'] = phone
                if not _twilio_enabled():
                    flash(f'OTP sent (dev mode). Code: {otp}', 'info')
                else:
                    flash('OTP sent to your phone number.', 'success')
                return redirect(url_for('phone_verify'))
            except Exception as exc:
                current_app.logger.exception('OTP send failed: %s', exc)
                flash('Could not send OTP. Check the phone number and try again.', 'error')
                return redirect(url_for('phone_login'))

        return render_template('auth/phone_login.html')

    @app.route('/auth/phone/verify', methods=['GET', 'POST'])
    def phone_verify():
        phone = session.get('otp_phone')
        if not phone:
            return redirect(url_for('phone_login'))

        if request.method == 'POST':
            entered_otp = request.form.get('otp', '').strip()
            user = User.query.filter_by(phone=phone).first()

            if not user:
                flash('Session expired. Please try again.', 'error')
                return redirect(url_for('phone_login'))

            if not user.otp_expiry or datetime.utcnow() > user.otp_expiry:
                flash('OTP has expired. Please request a new one.', 'error')
                return redirect(url_for('phone_login'))

            if user.phone_otp != entered_otp:
                flash('Incorrect OTP. Please try again.', 'error')
                return redirect(url_for('phone_verify'))

            user.phone_verified = True
            user.phone_otp = None
            user.otp_expiry = None
            db.session.commit()
            session.pop('otp_phone', None)
            login_user_session(user)
            flash('Phone login successful.', 'success')
            return redirect_after_login(user, pop_oauth_next())

        return render_template('auth/phone_verify.html', phone=phone)

    @app.route('/auth/phone/resend')
    def phone_resend():
        phone = session.get('otp_phone')
        if not phone:
            return redirect(url_for('phone_login'))
        user = User.query.filter_by(phone=phone).first()
        if user:
            otp = str(random.randint(100000, 999999))
            user.phone_otp = otp
            user.otp_expiry = datetime.utcnow() + timedelta(
                seconds=app.config['OTP_EXPIRY_SECONDS']
            )
            db.session.commit()
            try:
                send_otp(phone, otp)
                if not _twilio_enabled():
                    flash(f'New OTP sent (dev mode). Code: {otp}', 'info')
                else:
                    flash('New OTP sent.', 'success')
            except Exception:
                flash('Failed to resend OTP.', 'error')
        return redirect(url_for('phone_verify'))
