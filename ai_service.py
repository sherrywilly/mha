import openai
from typing import List, Dict
import numpy as np
from datetime import datetime, timedelta
from models import MoodEntry, AIInsight, db


class AIRecommendationEngine:
    """AI-powered recommendation engine for mental health insights."""

    def __init__(self, api_key: str, model: str = 'gpt-3.5-turbo'):
        """Initialize the AI recommendation engine."""
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key

    def analyze_mood_patterns(self, user_id: int, days: int = 30) -> Dict:
        """Analyze mood patterns for a user over a specified period."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        mood_entries = MoodEntry.query.filter(
            MoodEntry.user_id == user_id,
            MoodEntry.created_at >= cutoff_date
        ).order_by(MoodEntry.created_at.desc()).all()

        if not mood_entries:
            return {
                'average_mood': None,
                'trend': 'insufficient_data',
                'patterns': []
            }

        mood_scores = [entry.mood_score for entry in mood_entries]
        average_mood = np.mean(mood_scores)
        std_dev = np.std(mood_scores)

        # Determine trend
        if len(mood_scores) >= 7:
            recent_avg = np.mean(mood_scores[:7])
            older_avg = np.mean(mood_scores[-7:])
            if recent_avg > older_avg + 1:
                trend = 'improving'
            elif recent_avg < older_avg - 1:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'stable'

        # Identify common emotions
        all_emotions = []
        for entry in mood_entries:
            if entry.emotions:
                all_emotions.extend(entry.emotions)

        emotion_counts = {}
        for emotion in all_emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        top_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            'average_mood': round(average_mood, 2),
            'mood_std_dev': round(std_dev, 2),
            'trend': trend,
            'total_entries': len(mood_entries),
            'top_emotions': [{'emotion': e[0], 'count': e[1]} for e in top_emotions],
            'lowest_mood': min(mood_scores),
            'highest_mood': max(mood_scores)
        }

    def generate_recommendations(self, user_id: int, mood_analysis: Dict) -> List[str]:
        """Generate AI-powered recommendations based on mood analysis."""
        if not self.api_key or self.api_key == '':
            return self._generate_rule_based_recommendations(mood_analysis)

        try:
            prompt = self._create_recommendation_prompt(mood_analysis)
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a compassionate mental health assistant providing evidence-based recommendations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )

            recommendations_text = response.choices[0].message.content
            recommendations = [rec.strip() for rec in recommendations_text.split('\n') if rec.strip()]

            return recommendations[:5]

        except Exception as e:
            print(f"Error generating AI recommendations: {e}")
            return self._generate_rule_based_recommendations(mood_analysis)

    def _create_recommendation_prompt(self, mood_analysis: Dict) -> str:
        """Create a prompt for AI recommendation generation."""
        trend = mood_analysis.get('trend', 'stable')
        avg_mood = mood_analysis.get('average_mood', 5)
        top_emotions = mood_analysis.get('top_emotions', [])

        emotions_text = ", ".join([e['emotion'] for e in top_emotions[:3]]) if top_emotions else "not specified"

        prompt = f"""Based on the following mental health data, provide 3-5 personalized, actionable recommendations:

Average mood score: {avg_mood}/10
Mood trend: {trend}
Common emotions: {emotions_text}

Please provide specific, evidence-based recommendations for improving mental well-being. Focus on practical actions the person can take."""

        return prompt

    def _generate_rule_based_recommendations(self, mood_analysis: Dict) -> List[str]:
        """Generate rule-based recommendations as fallback."""
        recommendations = []
        avg_mood = mood_analysis.get('average_mood', 5)
        trend = mood_analysis.get('trend', 'stable')

        if avg_mood < 4:
            recommendations.append("Consider reaching out to a mental health professional for support")
            recommendations.append("Practice daily mindfulness meditation for 10-15 minutes")
            recommendations.append("Maintain a regular sleep schedule of 7-9 hours")

        if trend == 'declining':
            recommendations.append("Track potential triggers in your daily mood journal")
            recommendations.append("Engage in regular physical activity, even a 20-minute walk can help")

        if avg_mood >= 7:
            recommendations.append("Continue your current self-care practices")
            recommendations.append("Consider sharing your positive strategies with others")

        recommendations.append("Stay connected with supportive friends and family")
        recommendations.append("Practice gratitude by noting three positive things each day")

        return recommendations[:5]

    def create_self_care_plan(self, user_id: int) -> Dict:
        """Create a personalized self-care plan based on user data."""
        mood_analysis = self.analyze_mood_patterns(user_id)
        recommendations = self.generate_recommendations(user_id, mood_analysis)

        plan = {
            'title': f"Personalized Self-Care Plan - {datetime.utcnow().strftime('%B %Y')}",
            'description': 'A personalized plan based on your recent mood patterns and mental health data',
            'recommendations': [
                {'activity': rec, 'frequency': 'daily', 'completed': False}
                for rec in recommendations
            ],
            'goals': [
                'Improve overall mood and well-being',
                'Develop consistent self-care habits',
                'Build resilience and coping strategies'
            ],
            'duration_weeks': 4
        }

        return plan

    def generate_insight(self, user_id: int, insight_type: str = 'mood_pattern') -> Dict:
        """Generate an AI insight for the user."""
        mood_analysis = self.analyze_mood_patterns(user_id)

        if insight_type == 'mood_pattern':
            content = self._generate_mood_pattern_insight(mood_analysis)
        else:
            content = "Continue tracking your mood to receive personalized insights"

        insight_data = {
            'user_id': user_id,
            'insight_type': insight_type,
            'content': content,
            'confidence_score': 0.8,
            'insight_metadata': mood_analysis
        }

        return insight_data

    def _generate_mood_pattern_insight(self, mood_analysis: Dict) -> str:
        """Generate a mood pattern insight message."""
        avg_mood = mood_analysis.get('average_mood')
        trend = mood_analysis.get('trend', 'stable')
        total_entries = mood_analysis.get('total_entries', 0)

        if total_entries < 3:
            return "Keep tracking your mood regularly to identify patterns and receive personalized insights."

        insight = f"Over the past {total_entries} entries, your average mood has been {avg_mood:.1f}/10. "

        if trend == 'improving':
            insight += "Your mood shows a positive trend, which is encouraging! Continue with your current self-care practices."
        elif trend == 'declining':
            insight += "Your mood shows a declining trend. Consider reaching out for professional support or trying new coping strategies."
        else:
            insight += "Your mood has been relatively stable. Maintaining consistency in self-care can help sustain your well-being."

        return insight
