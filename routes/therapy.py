from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, TherapySession, User
from datetime import datetime

therapy_bp = Blueprint('therapy', __name__, url_prefix='/api/therapy')


@therapy_bp.route('/sessions', methods=['POST'])
@jwt_required()
def create_session():
    """Schedule a new therapy session."""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    session_type = data.get('session_type')
    scheduled_at_str = data.get('scheduled_at')

    if not all([session_type, scheduled_at_str]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        scheduled_at = datetime.fromisoformat(scheduled_at_str.replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    therapy_session = TherapySession(
        user_id=user_id,
        therapist_id=data.get('therapist_id'),
        session_type=session_type,
        scheduled_at=scheduled_at,
        duration_minutes=data.get('duration_minutes', 60),
        notes=data.get('notes')
    )

    db.session.add(therapy_session)
    db.session.commit()

    return jsonify({
        'message': 'Therapy session scheduled successfully',
        'session': therapy_session.to_dict()
    }), 201


@therapy_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_sessions():
    """Get all therapy sessions for the current user."""
    user_id = int(get_jwt_identity())
    status = request.args.get('status')

    query = TherapySession.query.filter_by(user_id=user_id)

    if status:
        query = query.filter_by(status=status)

    sessions = query.order_by(TherapySession.scheduled_at.desc()).all()

    return jsonify({
        'sessions': [session.to_dict() for session in sessions],
        'count': len(sessions)
    }), 200


@therapy_bp.route('/sessions/<int:session_id>', methods=['GET'])
@jwt_required()
def get_session(session_id):
    """Get a specific therapy session."""
    user_id = int(get_jwt_identity())
    session = TherapySession.query.filter_by(id=session_id, user_id=user_id).first()

    if not session:
        return jsonify({'error': 'Therapy session not found'}), 404

    return jsonify({'session': session.to_dict()}), 200


@therapy_bp.route('/sessions/<int:session_id>', methods=['PUT'])
@jwt_required()
def update_session(session_id):
    """Update a therapy session."""
    user_id = int(get_jwt_identity())
    session = TherapySession.query.filter_by(id=session_id, user_id=user_id).first()

    if not session:
        return jsonify({'error': 'Therapy session not found'}), 404

    data = request.get_json()

    if 'status' in data:
        session.status = data['status']
    if 'notes' in data:
        session.notes = data['notes']
    if 'session_summary' in data:
        session.session_summary = data['session_summary']
    if 'scheduled_at' in data:
        try:
            session.scheduled_at = datetime.fromisoformat(data['scheduled_at'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

    db.session.commit()

    return jsonify({
        'message': 'Therapy session updated successfully',
        'session': session.to_dict()
    }), 200


@therapy_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@jwt_required()
def delete_session(session_id):
    """Cancel/delete a therapy session."""
    user_id = int(get_jwt_identity())
    session = TherapySession.query.filter_by(id=session_id, user_id=user_id).first()

    if not session:
        return jsonify({'error': 'Therapy session not found'}), 404

    db.session.delete(session)
    db.session.commit()

    return jsonify({'message': 'Therapy session cancelled successfully'}), 200


@therapy_bp.route('/therapists', methods=['GET'])
@jwt_required()
def get_therapists():
    """Get list of available therapists."""
    therapists = User.query.filter_by(user_type='therapist', is_active=True).all()

    return jsonify({
        'therapists': [therapist.to_dict() for therapist in therapists],
        'count': len(therapists)
    }), 200
