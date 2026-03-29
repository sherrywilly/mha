from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, MoodEntry
from datetime import datetime

mood_bp = Blueprint('mood', __name__, url_prefix='/api/mood')


@mood_bp.route('/entries', methods=['POST'])
@jwt_required()
def create_mood_entry():
    """Create a new mood entry."""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    mood_score = data.get('mood_score')
    if mood_score is None or not (1 <= mood_score <= 10):
        return jsonify({'error': 'Mood score must be between 1 and 10'}), 400

    mood_entry = MoodEntry(
        user_id=user_id,
        mood_score=mood_score,
        emotions=data.get('emotions', []),
        notes=data.get('notes'),
        activities=data.get('activities', []),
        triggers=data.get('triggers', [])
    )

    db.session.add(mood_entry)
    db.session.commit()

    return jsonify({
        'message': 'Mood entry created successfully',
        'entry': mood_entry.to_dict()
    }), 201


@mood_bp.route('/entries', methods=['GET'])
@jwt_required()
def get_mood_entries():
    """Get all mood entries for the current user."""
    user_id = int(get_jwt_identity())
    limit = request.args.get('limit', 30, type=int)

    mood_entries = MoodEntry.query.filter_by(user_id=user_id)\
        .order_by(MoodEntry.created_at.desc())\
        .limit(limit)\
        .all()

    return jsonify({
        'entries': [entry.to_dict() for entry in mood_entries],
        'count': len(mood_entries)
    }), 200


@mood_bp.route('/entries/<int:entry_id>', methods=['GET'])
@jwt_required()
def get_mood_entry(entry_id):
    """Get a specific mood entry."""
    user_id = int(get_jwt_identity())
    mood_entry = MoodEntry.query.filter_by(id=entry_id, user_id=user_id).first()

    if not mood_entry:
        return jsonify({'error': 'Mood entry not found'}), 404

    return jsonify({'entry': mood_entry.to_dict()}), 200


@mood_bp.route('/entries/<int:entry_id>', methods=['PUT'])
@jwt_required()
def update_mood_entry(entry_id):
    """Update a mood entry."""
    user_id = int(get_jwt_identity())
    mood_entry = MoodEntry.query.filter_by(id=entry_id, user_id=user_id).first()

    if not mood_entry:
        return jsonify({'error': 'Mood entry not found'}), 404

    data = request.get_json()

    if 'mood_score' in data:
        mood_score = data['mood_score']
        if not (1 <= mood_score <= 10):
            return jsonify({'error': 'Mood score must be between 1 and 10'}), 400
        mood_entry.mood_score = mood_score

    if 'emotions' in data:
        mood_entry.emotions = data['emotions']
    if 'notes' in data:
        mood_entry.notes = data['notes']
    if 'activities' in data:
        mood_entry.activities = data['activities']
    if 'triggers' in data:
        mood_entry.triggers = data['triggers']

    db.session.commit()

    return jsonify({
        'message': 'Mood entry updated successfully',
        'entry': mood_entry.to_dict()
    }), 200


@mood_bp.route('/entries/<int:entry_id>', methods=['DELETE'])
@jwt_required()
def delete_mood_entry(entry_id):
    """Delete a mood entry."""
    user_id = int(get_jwt_identity())
    mood_entry = MoodEntry.query.filter_by(id=entry_id, user_id=user_id).first()

    if not mood_entry:
        return jsonify({'error': 'Mood entry not found'}), 404

    db.session.delete(mood_entry)
    db.session.commit()

    return jsonify({'message': 'Mood entry deleted successfully'}), 200
