from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, SelfCarePlan, AIInsight
from ai_service import AIRecommendationEngine
from config import Config

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')


@ai_bp.route('/analyze-mood', methods=['GET'])
@jwt_required()
def analyze_mood():
    """Analyze mood patterns for the current user."""
    user_id = int(get_jwt_identity())
    days = request.args.get('days', 30, type=int)

    ai_engine = AIRecommendationEngine(
        api_key=Config.OPENAI_API_KEY,
        model=Config.AI_MODEL
    )

    analysis = ai_engine.analyze_mood_patterns(user_id, days)

    return jsonify({
        'analysis': analysis,
        'period_days': days
    }), 200


@ai_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """Get AI-powered recommendations for the current user."""
    user_id = int(get_jwt_identity())

    ai_engine = AIRecommendationEngine(
        api_key=Config.OPENAI_API_KEY,
        model=Config.AI_MODEL
    )

    mood_analysis = ai_engine.analyze_mood_patterns(user_id)
    recommendations = ai_engine.generate_recommendations(user_id, mood_analysis)

    return jsonify({
        'recommendations': recommendations,
        'mood_analysis': mood_analysis
    }), 200


@ai_bp.route('/self-care-plan', methods=['POST'])
@jwt_required()
def create_self_care_plan():
    """Create a personalized self-care plan."""
    user_id = int(get_jwt_identity())

    ai_engine = AIRecommendationEngine(
        api_key=Config.OPENAI_API_KEY,
        model=Config.AI_MODEL
    )

    plan_data = ai_engine.create_self_care_plan(user_id)

    # Deactivate existing active plans
    SelfCarePlan.query.filter_by(user_id=user_id, is_active=True).update({'is_active': False})

    self_care_plan = SelfCarePlan(
        user_id=user_id,
        title=plan_data['title'],
        description=plan_data['description'],
        recommendations=plan_data['recommendations'],
        goals=plan_data['goals'],
        duration_weeks=plan_data['duration_weeks']
    )

    db.session.add(self_care_plan)
    db.session.commit()

    return jsonify({
        'message': 'Self-care plan created successfully',
        'plan': self_care_plan.to_dict()
    }), 201


@ai_bp.route('/self-care-plans', methods=['GET'])
@jwt_required()
def get_self_care_plans():
    """Get all self-care plans for the current user."""
    user_id = int(get_jwt_identity())
    active_only = request.args.get('active_only', 'false').lower() == 'true'

    query = SelfCarePlan.query.filter_by(user_id=user_id)

    if active_only:
        query = query.filter_by(is_active=True)

    plans = query.order_by(SelfCarePlan.created_at.desc()).all()

    return jsonify({
        'plans': [plan.to_dict() for plan in plans],
        'count': len(plans)
    }), 200


@ai_bp.route('/insights', methods=['GET'])
@jwt_required()
def get_insights():
    """Get AI insights for the current user."""
    user_id = int(get_jwt_identity())
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'

    query = AIInsight.query.filter_by(user_id=user_id)

    if unread_only:
        query = query.filter_by(is_read=False)

    insights = query.order_by(AIInsight.created_at.desc()).limit(20).all()

    return jsonify({
        'insights': [insight.to_dict() for insight in insights],
        'count': len(insights)
    }), 200


@ai_bp.route('/insights', methods=['POST'])
@jwt_required()
def generate_insight():
    """Generate a new AI insight for the current user."""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    insight_type = data.get('insight_type', 'mood_pattern') if data else 'mood_pattern'

    ai_engine = AIRecommendationEngine(
        api_key=Config.OPENAI_API_KEY,
        model=Config.AI_MODEL
    )

    insight_data = ai_engine.generate_insight(user_id, insight_type)

    insight = AIInsight(**insight_data)
    db.session.add(insight)
    db.session.commit()

    return jsonify({
        'message': 'Insight generated successfully',
        'insight': insight.to_dict()
    }), 201


@ai_bp.route('/insights/<int:insight_id>/read', methods=['PUT'])
@jwt_required()
def mark_insight_read(insight_id):
    """Mark an insight as read."""
    user_id = int(get_jwt_identity())
    insight = AIInsight.query.filter_by(id=insight_id, user_id=user_id).first()

    if not insight:
        return jsonify({'error': 'Insight not found'}), 404

    insight.is_read = True
    db.session.commit()

    return jsonify({
        'message': 'Insight marked as read',
        'insight': insight.to_dict()
    }), 200
