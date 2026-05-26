"""Session helpers shared by email, OAuth, and phone auth."""
from flask import session, redirect, url_for
from urllib.parse import urlparse, urljoin
from flask import request


def is_safe_url(target):
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def login_user_session(user):
    session.permanent = True
    session['user_id'] = user.user_id
    session['user_name'] = user.name
    session['user_role'] = user.role


def redirect_after_login(user, next_page=None):
    if next_page and is_safe_url(next_page):
        return redirect(next_page)
    if user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('dashboard'))


def store_oauth_next(next_page):
    if next_page and is_safe_url(next_page):
        session['oauth_next'] = next_page


def pop_oauth_next():
    return session.pop('oauth_next', None)
