

import firebase_admin
from firebase_admin import credentials, firestore, auth
from firebase_admin.exceptions import FirebaseError
from config import Config
import os
from datetime import datetime
from difflib import SequenceMatcher    # for simple text similarity

db = None

def initialize_firebase():
    global db
    try:
        if not firebase_admin._apps:
            cred_path = Config.FIREBASE_CREDENTIALS
            
            if not os.path.isabs(cred_path):
                base_dir = os.path.abspath(os.path.dirname(__file__))
                cred_path = os.path.join(base_dir, '..', cred_path)
                
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("Firebase initialized successfully!")
    except Exception as e:
        print(f"Firebase initialization failed: {e}")
        raise e

def get_users():
    users = []
    try:
        for user in auth.list_users().iterate_all():
            created = datetime.fromtimestamp(user.user_metadata.creation_timestamp / 1000) if hasattr(user.user_metadata, 'creation_timestamp') and user.user_metadata.creation_timestamp else None
            last_login = datetime.fromtimestamp(user.user_metadata.last_sign_in_timestamp / 1000) if hasattr(user.user_metadata, 'last_sign_in_timestamp') and user.user_metadata.last_sign_in_timestamp else None
            
            users.append({
                'uid': user.uid,
                'email': user.email,
                'created': created,
                'last_login': last_login,
                'disabled': user.disabled
            })
    except FirebaseError as e:
        print(f"Error fetching users: {e}")
    return users
def set_user_status(uid: str, disabled: bool) -> bool:
    """
    Enable or disable a Firebase Auth user.

    Args
    ────
    uid       : Firebase Auth UID
    disabled  : True → disable (block sign‑in)
                False → enable  (allow sign‑in)

    Returns
    ───────
    bool : True on success, False otherwise
    """
    try:
        auth.update_user(uid, disabled=disabled)
        return True
    except FirebaseError as e:
        print(f"Error updating user status: {e}")
        return False

def get_items(collection_name):
    items = []
    try:
        docs = db.collection(collection_name).stream()
        for doc in docs:
            item = doc.to_dict()
            item['id'] = doc.id
            items.append(item)
    except FirebaseError as e:
        print(f"Error fetching items: {e}")
    return items

def delete_item(collection_name, item_id, image_public_id=None):
    try:
        doc_ref = db.collection(collection_name).document(item_id)
        doc_ref.delete()
        if image_public_id:
            from .cloudinary_service import delete_image
            delete_image(image_public_id)
        return True
    except FirebaseError as e:
        print(f"Error deleting item: {e}")
        return False

def get_matches():
    matches = []
    try:
        docs = db.collection('matches').stream()
        for doc in docs:
            match = doc.to_dict()
            match['id'] = doc.id
            matches.append(match)
    except FirebaseError as e:
        print(f"Error fetching matches: {e}")
    return matches

def get_dashboard_stats():
    stats = {
        'total_users': 0,
        'active_today': 0,
        'lost_items': 0,
        'found_items': 0,
        'successful_matches': 0
    }
    matches = compute_matches()
    match_count = len(matches)
    try:
        stats['total_users'] = len(get_users())
        stats['lost_items'] = len(get_items('lost_items'))
        stats['found_items'] = len(get_items('found_items'))
        stats['successful_matches'] = match_count
    except:
        pass
    
    return stats

# Search functions
def search_users(query):
    all_users = get_users()
    if not query:
        return all_users
        
    query = query.lower()
    results = []
    
    for user in all_users:
        if (query in user['email'].lower() or
            query in user['uid'].lower() or
            query in ("active" if not user['disabled'] else "disabled") or
            (user.get('created') and query in user['created'].strftime('%Y-%m-%d').lower())):
            results.append(user)
            
    return results

def search_items(collection_name, query):
    all_items = get_items(collection_name)
    if not query:
        return all_items
        
    query = query.lower()
    results = []
    
    for item in all_items:
        if (query in item.get('name', '').lower() or
            query in item.get('description', '').lower() or
            query in item.get('location', '').lower() or
            query in item.get('status', '').lower() or
            query in item.get('id', '').lower() or
            (item.get('date') and query in item['date'].lower())):
            results.append(item)
            
    return results

def search_matches(query):
    all_matches = get_matches()
    if not query:
        return all_matches
        
    query = query.lower()
    results = []
    
    for match in all_matches:
        if (query in match.get('lost_item_name', '').lower() or
            query in match.get('found_item_name', '').lower() or
            query in match.get('status', '').lower() or
            query in match.get('id', '').lower() or
            query in str(match.get('confidence', '')).lower() or
            (match.get('match_date') and query in match['match_date'].lower())):
            results.append(match)
            
    return results


# --- Pattern B: compute on-the-fly --------------------------------
def compute_matches(threshold: float = 0.55) -> list[dict]:
    lost_docs  = list(db.collection("lost_items").stream())
    found_docs = list(db.collection("found_items").stream())
    matches = []

    for lost_doc in lost_docs:
        lost = lost_doc.to_dict() | {"id": lost_doc.id}
        text_l = f"{lost.get('item','')} {lost.get('description','')} {lost.get('location','')}".lower()

        for found_doc in found_docs:
            found = found_doc.to_dict() | {"id": found_doc.id}
            text_f = f"{found.get('item','')} {found.get('description','')} {found.get('location','')}".lower()

            score = SequenceMatcher(None, text_l, text_f).ratio()
            if score >= threshold:
                matches.append({
                    "id": f"{lost['id']}_{found['id']}",
                    "score": round(score, 2),
                    "created": lost.get("created_at", datetime.utcnow()),
                    "lost": lost,
                    "found": found
                })
    return sorted(matches, key=lambda m: m["score"], reverse=True)
# --- End of pattern B ---------------------------------------------