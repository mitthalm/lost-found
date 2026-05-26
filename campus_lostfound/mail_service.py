from flask_mail import Mail, Message
from flask import current_app, render_template_string

mail = Mail()

# Email templates
NEW_ITEM_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>New Item Alert</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #7c3aed, #4f46e5); color: white; padding: 20px; border-radius: 8px 8px 0 0; margin: -30px -30px 30px -30px; text-align: center; }
        .btn { display: inline-block; padding: 12px 24px; background: #7c3aed; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px; }
        .info { background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 10px 0; }
        .label { font-weight: bold; color: #333; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>New Item Alert</h1>
        </div>
        
        <div class="info">
            <span class="label">Type:</span> {{ item_type.upper() }}<br>
            <span class="label">Title:</span> {{ title }}<br>
            <span class="label">Category:</span> {{ category }}<br>
            <span class="label">Location:</span> {{ location }}<br>
            <span class="label">Date:</span> {{ date }}<br>
            <span class="label">Posted by:</span> {{ user_name }} ({{ user_email }})
        </div>
        
        <div class="info">
            <span class="label">Description:</span><br>
            {{ description }}
        </div>
        
        <div style="text-align: center;">
            <a href="{{ item_url }}" class="btn">View Item</a>
        </div>
        
        <p style="text-align: center; color: #666; margin-top: 30px; font-size: 12px;">
            This is an automated notification from CampusFind.
        </p>
    </div>
</body>
</html>
"""

CLAIM_REQUEST_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Claim Request</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 20px; border-radius: 8px 8px 0 0; margin: -30px -30px 30px -30px; text-align: center; }
        .section { background: #f8f9fa; padding: 15px; border-radius: 6px; margin: 10px 0; }
        .label { font-weight: bold; color: #333; }
        .btn { display: inline-block; padding: 12px 24px; background: #10b981; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Claim Request Received</h1>
        </div>
        
        <div class="section">
            <span class="label">Item:</span> {{ item_title }}<br>
            <span class="label">Item Status:</span> {{ item_status.title() }}<br>
            <span class="label">Item Posted by:</span> {{ owner_name }}
        </div>
        
        <div class="section">
            <h3>── Claimant Details ──</h3>
            <span class="label">Name:</span> {{ claimant_name }}<br>
            <span class="label">Email:</span> {{ claimant_email }}<br>
            <span class="label">Phone:</span> {{ claimant_phone }}
        </div>
        
        <div class="section">
            <h3>── Their Reason ──</h3>
            {{ claim_message }}
        </div>
        
        {% if has_proof %}
        <div class="section">
            <h3>── Proof Photo ──</h3>
            <p>Proof photo has been uploaded and is available for review on the website.</p>
        </div>
        {% endif %}
        
        <div class="section">
            <h3>── Actions ──</h3>
            <a href="{{ admin_url }}" class="btn">View and Approve on Website</a>
        </div>
        
        <p style="text-align: center; color: #666; margin-top: 30px; font-size: 12px;">
            This is an automated notification from CampusFind.
        </p>
    </div>
</body>
</html>
"""

CLAIM_APPROVED_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Claim Approved</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 20px; border-radius: 8px 8px 0 0; margin: -30px -30px 30px -30px; text-align: center; }
        .contact-info { background: #e8f5e8; padding: 20px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #10b981; }
        .label { font-weight: bold; color: #333; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Claim Approved</h1>
            <p>Your claim was approved.</p>
        </div>
        
        <h3>Item: {{ item_title }}</h3>
        
        <div class="contact-info">
            <h3>── Item Owner Contact Details ──</h3>
            <p><span class="label">Name:</span> {{ owner_name }}</p>
            <p><span class="label">Email:</span> {{ owner_email }}</p>
            <p><span class="label">Phone:</span> {{ owner_phone }}</p>
        </div>
        
        <p>Please contact them directly to arrange collection of your item.</p>
        
        <p style="text-align: center; color: #666; margin-top: 30px; font-size: 12px;">
            — CampusFind Team
        </p>
    </div>
</body>
</html>
"""

OWNER_NOTIFICATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Item Claimed</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #7c3aed, #4f46e5); color: white; padding: 20px; border-radius: 8px 8px 0 0; margin: -30px -30px 30px -30px; text-align: center; }
        .contact-info { background: #f0f4ff; padding: 20px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #7c3aed; }
        .label { font-weight: bold; color: #333; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Claim Approved</h1>
        </div>
        
        <p>A claim on your item "{{ item_title }}" has been approved by the admin.</p>
        
        <div class="contact-info">
            <h3>── Claimant Contact Details ──</h3>
            <p><span class="label">Name:</span> {{ claimant_name }}</p>
            <p><span class="label">Email:</span> {{ claimant_email }}</p>
            <p><span class="label">Phone:</span> {{ claimant_phone }}</p>
        </div>
        
        <p>They will reach out to you soon. Please coordinate the handover.</p>
        
        <p style="text-align: center; color: #666; margin-top: 30px; font-size: 12px;">
            — CampusFind Team
        </p>
    </div>
</body>
</html>
"""

CLAIM_REJECTED_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Claim Not Approved</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; padding: 20px; border-radius: 8px 8px 0 0; margin: -30px -30px 30px -30px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Claim Not Approved</h1>
        </div>
        
        <p>Your claim for "{{ item_title }}" was not approved.</p>
        
        <p>You may submit a new claim with additional proof.</p>
        
        <p style="text-align: center; color: #666; margin-top: 30px; font-size: 12px;">
            — CampusFind Team
        </p>
    </div>
</body>
</html>
"""

OWNERSHIP_CLAIM_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Ownership Claim Submitted</title>
    <style>
        body { font-family: Georgia, serif; background: #F5F5F0; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; border: 1px solid #D0C9B8; border-radius: 8px; padding: 30px; }
        .header { background: #1B3A6B; color: white; padding: 20px; border-radius: 8px 8px 0 0; margin: -30px -30px 30px -30px; text-align: center; }
        .section { background: #F5F5F0; padding: 15px; border-radius: 6px; margin: 10px 0; }
        .label { font-weight: bold; color: #1A1A1A; }
        .btn { display: inline-block; padding: 12px 24px; background: #1B3A6B; color: white; text-decoration: none; border-radius: 6px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>New Ownership Claim</h1>
        </div>
        <div class="section">
            <span class="label">Item:</span> {{ item_title }} (ID: {{ item_id }})<br>
            <span class="label">Claimant:</span> {{ claimant_name }}<br>
            <span class="label">Submitted:</span> {{ submitted_at }}
        </div>
        <div class="section">
            <span class="label">Claim Message:</span><br>
            {{ claim_message }}
        </div>
        <div style="text-align: center;">
            <a href="{{ admin_url }}" class="btn">Review Claim in Admin Dashboard</a>
        </div>
    </div>
</body>
</html>
"""

def send_ownership_claim_submitted_notification(item_title, item_id, claimant_name, claim_message, submitted_at, admin_url):
    """Notify admin when an ownership claim is submitted."""
    try:
        msg = Message(
            f'New Ownership Claim Submitted — {item_title}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[current_app.config['ADMIN_EMAIL']]
        )
        msg.html = render_template_string(
            OWNERSHIP_CLAIM_TEMPLATE,
            item_title=item_title,
            item_id=item_id,
            claimant_name=claimant_name,
            claim_message=claim_message,
            submitted_at=submitted_at,
            admin_url=admin_url
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send ownership claim notification: {e}")
        return False

def send_new_item_notification(item_type, title, category, location, date, user_name, user_email, description, item_url):
    """Send email notification for new item posted"""
    try:
        msg = Message(
            f'New {item_type.title()} Item Posted — {title}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[current_app.config['ADMIN_EMAIL']]
        )
        msg.html = render_template_string(NEW_ITEM_TEMPLATE, 
            item_type=item_type,
            title=title,
            category=category,
            location=location,
            date=date,
            user_name=user_name,
            user_email=user_email,
            description=description,
            item_url=item_url
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send new item notification: {e}")
        return False

def send_claim_request_notification(item_title, item_status, owner_name, claimant_name, claimant_email, claimant_phone, claim_message, has_proof, admin_url):
    """Send email notification for claim request"""
    try:
        msg = Message(
            f'Claim Request — {item_title} by {claimant_name}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[current_app.config['ADMIN_EMAIL']]
        )
        msg.html = render_template_string(CLAIM_REQUEST_TEMPLATE,
            item_title=item_title,
            item_status=item_status,
            owner_name=owner_name,
            claimant_name=claimant_name,
            claimant_email=claimant_email,
            claimant_phone=claimant_phone,
            claim_message=claim_message,
            has_proof=has_proof,
            admin_url=admin_url
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send claim request notification: {e}")
        return False

def send_claim_approved_notification(item_title, owner_name, owner_email, owner_phone, claimant_email):
    """Send email to claimant when claim is approved"""
    try:
        msg = Message(
            f'Your Claim was Approved — {item_title}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[claimant_email]
        )
        msg.html = render_template_string(CLAIM_APPROVED_TEMPLATE,
            item_title=item_title,
            owner_name=owner_name,
            owner_email=owner_email,
            owner_phone=owner_phone
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send claim approved notification: {e}")
        return False

def send_owner_notification(item_title, claimant_name, claimant_email, claimant_phone, owner_email):
    """Send email to item owner when claim is approved"""
    try:
        msg = Message(
            f'Someone\'s Claim on Your Item was Approved',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[owner_email]
        )
        msg.html = render_template_string(OWNER_NOTIFICATION_TEMPLATE,
            item_title=item_title,
            claimant_name=claimant_name,
            claimant_email=claimant_email,
            claimant_phone=claimant_phone
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send owner notification: {e}")
        return False

def send_claim_rejected_notification(item_title, claimant_email):
    """Send email to claimant when claim is rejected"""
    try:
        msg = Message(
            f'Your Claim was Not Approved — {item_title}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[claimant_email]
        )
        msg.html = render_template_string(CLAIM_REJECTED_TEMPLATE,
            item_title=item_title
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send claim rejected notification: {e}")
        return False


def send_possible_match_notification(lost_owner_email, lost_owner_name, found_uploader_name, found_uploader_email, lost_item_title, found_item_title, match_url):
    try:
        msg = Message(
            f'Possible Match Found for "{lost_item_title}"',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[lost_owner_email]
        )
        body = f"Hi {lost_owner_name},\n\nWe found a possible match for your lost item '{lost_item_title}' posted by {found_uploader_name}.\n\nView the possible match: {match_url}\n\nPlease review and confirm if this is your item.\n\n— CampusFind Team"
        msg.body = body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send possible match notification: {e}")
        return False


def send_final_match_notification(user1_email, user1_name, user2_email, user2_name, item_title):
    try:
        msg = Message(
            f'Match Confirmed — {item_title}',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user1_email, user2_email]
        )
        body = (
            f"Hi,\n\nA match for '{item_title}' has been confirmed.\n\nContact details:\n{user1_name} — {user1_email}\n{user2_name} — {user2_email}\n\nPlease reach out to coordinate the handover.\n\n— CampusFind Team"
        )
        msg.body = body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send final match notification: {e}")
        return False
