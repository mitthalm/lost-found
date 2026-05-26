"""One-time fix: store only filenames in Item.image (strip path prefixes)."""
import os

from app import app
from db import db, Item

with app.app_context():
    items = Item.query.filter(Item.image.isnot(None), Item.image != '').all()
    fixed = 0
    for item in items:
        if item.image and ('/' in item.image or '\\' in item.image):
            item.image = os.path.basename(item.image.replace('\\', '/'))
            fixed += 1
    db.session.commit()
    print(f'Fixed {fixed} records.')
