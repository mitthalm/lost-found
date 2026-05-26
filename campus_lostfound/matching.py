import re
from typing import List, Tuple
from db import Item, Match, db
from config import Config
import os
import base64
import numpy as np

def tokenize_keywords(keywords: str) -> set:
    """Tokenize keywords string into a set of normalized words"""
    if not keywords:
        return set()
    # Split by comma and clean up
    words = [word.strip().lower() for word in keywords.split(',')]
    # Remove empty strings and single characters
    return {word for word in words if len(word) > 1}

def calculate_jaccard_similarity(keywords1: str, keywords2: str) -> float:
    """Calculate Jaccard similarity between two keyword strings"""
    set1 = tokenize_keywords(keywords1)
    set2 = tokenize_keywords(keywords2)
    
    if not set1 or not set2:
        return 0.0
    
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    
    return len(intersection) / len(union) if union else 0.0

def calculate_image_similarity(image1_path: str, image2_path: str) -> float:
    """Calculate perceptual image hash similarity"""
    try:
        import imagehash
        from PIL import Image
        
        # Calculate perceptual hashes
        hash1 = imagehash.phash(Image.open(image1_path))
        hash2 = imagehash.phash(Image.open(image2_path))
        
        # Calculate hash difference (0 = identical, higher = more different)
        hash_diff = hash1 - hash2
        
        # Convert to similarity score (1 = identical, 0 = completely different)
        if hash_diff <= Config.IMAGE_HASH_THRESHOLD:
            return 1.0 - (hash_diff / Config.IMAGE_HASH_THRESHOLD)
        else:
            return 0.0
            
    except Exception as e:
        print(f"Image similarity calculation failed: {e}")
        return 0.0


def compute_image_phash(image_path: str) -> str:
    try:
        import imagehash
        from PIL import Image
        return str(imagehash.phash(Image.open(image_path)))
    except Exception:
        return None


def compute_orb_embedding(image_path: str):
    """Compute a compact ORB-based embedding (mean descriptor) as a list of floats."""
    try:
        import cv2
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None
        orb = cv2.ORB_create(nfeatures=500)
        kps, des = orb.detectAndCompute(img, None)
        if des is None or len(des) == 0:
            return None
        # Compute mean descriptor (shape 32)
        mean_desc = np.mean(des.astype(np.float32), axis=0)
        # Normalize
        norm = np.linalg.norm(mean_desc)
        if norm > 0:
            mean_desc = mean_desc / norm
        return mean_desc.tolist()
    except Exception as e:
        print(f"ORB embedding failed: {e}")
        return None


def cosine_similarity_vec(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    if a.size == 0 or b.size == 0:
        return 0.0
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)

def calculate_match_score(item1: Item, item2: Item) -> float:
    """Calculate overall match score between two items"""
    score = 0.0
    
    # Keyword similarity (main component)
    keyword_score = calculate_jaccard_similarity(item1.keywords, item2.keywords)
    score += keyword_score
    
    # Category bonus
    if item1.category.lower() == item2.category.lower():
        score += Config.CATEGORY_BONUS
    
    # Image similarity bonus (if both have images)
    if item1.image and item2.image:
        try:
            from flask import current_app
            import os
            upload_dir = current_app.config['UPLOAD_FOLDER']
            image1_path = os.path.join(upload_dir, os.path.basename(item1.image))
            image2_path = os.path.join(upload_dir, os.path.basename(item2.image))
            image_similarity = calculate_image_similarity(image1_path, image2_path)
            score += image_similarity * Config.IMAGE_BONUS
        except Exception as e:
            print(f"Image bonus calculation failed: {e}")
    
    # Cap the score at 1.0
    return min(score, 1.0)

def find_matches_for_item(new_item: Item) -> List[Tuple[Item, float]]:
    """Find matching items for a newly posted item"""
    matches = []
    # Find items with opposite status
    opposite_status = 'found' if new_item.status == 'lost' else 'lost'
    candidate_items = Item.query.filter_by(status=opposite_status).all()
    print(f"[MATCHING] Checking {len(candidate_items)} candidate items for new item {new_item.item_id} ({new_item.title})")
    for candidate in candidate_items:
        # Category match (exact)
        category_match = (new_item.category or '').strip().lower() == (candidate.category or '').strip().lower()
        # Title fuzzy match (substring or token overlap)
        title1 = (new_item.title or '').lower()
        title2 = (candidate.title or '').lower()
        title_match = (title1 in title2) or (title2 in title1) or (len(set(title1.split()) & set(title2.split())) > 0)
        # Keyword similarity
        keyword_score = calculate_jaccard_similarity(new_item.keywords, candidate.keywords)
        # Image similarity (ORB embedding)
        img_sim = 0.0
        try:
            if new_item.image_embedding and candidate.image_embedding:
                import json
                emb1 = json.loads(new_item.image_embedding)
                emb2 = json.loads(candidate.image_embedding)
                img_sim = cosine_similarity_vec(emb1, emb2)
        except Exception as e:
            print(f"[MATCHING] ORB sim error: {e}")
        # Weighted score
        score = 0.0
        if category_match:
            score += 0.3
        if title_match:
            score += 0.3
        score += min(keyword_score, 0.3)
        score += min(img_sim, 0.4)
        print(f"[MATCHING] Candidate {candidate.item_id} | Cat: {category_match} | Title: {title_match} | Key: {keyword_score:.2f} | Img: {img_sim:.2f} | Score: {score:.2f}")
        if score >= 0.7:
            matches.append((candidate, score))
    matches.sort(key=lambda x: x[1], reverse=True)
    print(f"[MATCHING] {len(matches)} matches found above threshold for item {new_item.item_id}")
    return matches

def save_matches(new_item: Item):
    """Save matches to database"""
    # Remove existing matches for this item
    Match.query.filter(
        (Match.lost_item_id == new_item.item_id) | 
        (Match.found_item_id == new_item.item_id)
    ).delete()
    
    # Ensure image features are computed for the new item and candidates
    from flask import current_app
    upload_dir = current_app.config['UPLOAD_FOLDER']

    def ensure_features(item):
        if item.image and (not item.image_embedding or not item.image_phash):
            try:
                image_path = os.path.join(upload_dir, os.path.basename(item.image))
                phash = compute_image_phash(image_path)
                emb = compute_orb_embedding(image_path)
                if phash:
                    item.image_phash = phash
                if emb is not None:
                    import json
                    item.image_embedding = json.dumps(emb)
                db.session.add(item)
                db.session.commit()
            except Exception as e:
                print(f"Failed to compute features for item {item.item_id}: {e}")

    ensure_features(new_item)

    # Find and save new matches
    matches = find_matches_for_item(new_item)
    
    for matched_item, score in matches:
        if new_item.status == 'lost':
            match = Match(lost_item_id=new_item.item_id, found_item_id=matched_item.item_id, match_score=score)
        else:
            match = Match(lost_item_id=matched_item.item_id, found_item_id=new_item.item_id, match_score=score)
        
        db.session.add(match)
    
    db.session.commit()
    return matches

def get_top_matches_for_item(item: Item, limit: int = 3) -> List[Tuple[Item, float]]:
    """Get top matches for an item from the database"""
    if item.status == 'lost':
        matches = Match.query.filter_by(lost_item_id=item.item_id)\
                           .join(Item, Match.found_item_id == Item.item_id)\
                           .order_by(Match.match_score.desc())\
                           .limit(limit)\
                           .all()
        return [(match.found_item, match.match_score) for match in matches]
    else:
        matches = Match.query.filter_by(found_item_id=item.item_id)\
                           .join(Item, Match.lost_item_id == Item.item_id)\
                           .order_by(Match.match_score.desc())\
                           .limit(limit)\
                           .all()
        return [(match.lost_item, match.match_score) for match in matches]

def recompute_all_matches():
    """Recompute all matches in the database (useful for testing)"""
    # Clear existing matches
    Match.query.delete()
    
    # Get all items
    all_items = Item.query.all()
    
    # Compute matches for each item
    for item in all_items:
        save_matches(item)
    
    print(f"Recomputed matches for {len(all_items)} items")
