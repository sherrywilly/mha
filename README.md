# AI-Powered Mental Health Platform

A comprehensive mental health support platform offering virtual therapy sessions, mood tracking tools, personalized self-care plans, and AI-powered insights.

## Overview

This platform addresses the growing need for accessible and personalized mental health resources. It provides:

- **Virtual Therapy Sessions**: Schedule and manage therapy appointments with licensed therapists
- **Mood Tracking**: Track daily moods, emotions, activities, and triggers
- **AI-Powered Recommendations**: Receive personalized mental health insights based on your data
- **Self-Care Plans**: Get customized self-care plans tailored to your needs
- **Secure Data Storage**: All data is securely stored and managed

## Market Opportunity

The mental health software market is projected to reach **$5.9 billion by 2027**, indicating a significant opportunity for innovation in this space.

## Features

### User Management
- User registration and authentication (JWT-based)
- User profiles for individuals, therapists, and administrators
- Secure password hashing

### Mood Tracking
- Log daily mood scores (1-10 scale)
- Track emotions, activities, and triggers
- View mood history and patterns

### Virtual Therapy
- Schedule therapy sessions (virtual, in-person, chat)
- Manage appointments and session notes
- Connect with licensed therapists

### AI-Powered Insights
- Mood pattern analysis
- Personalized recommendations
- AI-generated insights
- Trend detection (improving, stable, declining)

### Self-Care Plans
- Personalized self-care recommendations
- Goal setting and tracking
- Evidence-based strategies

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLAlchemy (PostgreSQL/SQLite)
- **Authentication**: JWT (Flask-JWT-Extended)
- **AI/ML**: OpenAI GPT, NumPy, scikit-learn
- **API**: RESTful architecture

## Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL (optional, SQLite for development)
- Virtual environment (recommended)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/sherrywilly/mha.git
cd mha
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Set up the database:
```bash
# The database will be automatically created when you run the application
python main.py
```

## Configuration

Edit the `.env` file with your settings:

```env
FLASK_APP=main.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/mental_health_db
OPENAI_API_KEY=your-openai-api-key-here  # Optional
```

**Note**: OpenAI API key is optional. Without it, the platform will use rule-based recommendations.

## Running the Application

### Development Mode

```bash
python main.py
```

The API will be available at `http://localhost:5000`

### Production Mode

```bash
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

## API Endpoints

### Authentication (`/api/auth`)

- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - User login
- `GET /api/auth/profile` - Get user profile (requires auth)
- `PUT /api/auth/profile` - Update user profile (requires auth)

### Mood Tracking (`/api/mood`)

- `POST /api/mood/entries` - Create mood entry (requires auth)
- `GET /api/mood/entries` - Get mood entries (requires auth)
- `GET /api/mood/entries/<id>` - Get specific entry (requires auth)
- `PUT /api/mood/entries/<id>` - Update mood entry (requires auth)
- `DELETE /api/mood/entries/<id>` - Delete mood entry (requires auth)

### Therapy Sessions (`/api/therapy`)

- `POST /api/therapy/sessions` - Schedule session (requires auth)
- `GET /api/therapy/sessions` - Get all sessions (requires auth)
- `GET /api/therapy/sessions/<id>` - Get specific session (requires auth)
- `PUT /api/therapy/sessions/<id>` - Update session (requires auth)
- `DELETE /api/therapy/sessions/<id>` - Cancel session (requires auth)
- `GET /api/therapy/therapists` - List available therapists (requires auth)

### AI & Insights (`/api/ai`)

- `GET /api/ai/analyze-mood` - Analyze mood patterns (requires auth)
- `GET /api/ai/recommendations` - Get AI recommendations (requires auth)
- `POST /api/ai/self-care-plan` - Create self-care plan (requires auth)
- `GET /api/ai/self-care-plans` - Get self-care plans (requires auth)
- `GET /api/ai/insights` - Get AI insights (requires auth)
- `POST /api/ai/insights` - Generate new insight (requires auth)
- `PUT /api/ai/insights/<id>/read` - Mark insight as read (requires auth)

## Usage Examples

### Register a User

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Create a Mood Entry

```bash
curl -X POST http://localhost:5000/api/mood/entries \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -d '{
    "mood_score": 7,
    "emotions": ["happy", "calm"],
    "notes": "Had a good day at work",
    "activities": ["exercise", "meditation"],
    "triggers": []
  }'
```

### Get AI Recommendations

```bash
curl -X GET http://localhost:5000/api/ai/recommendations \
  -H "Authorization: Bearer <your-jwt-token>"
```

## Testing

Run the test suite:

```bash
pytest test_app.py -v
```

Run tests with coverage:

```bash
pytest test_app.py --cov=. --cov-report=html
```

## Database Schema

### Users
- Stores user information, credentials, and user type
- Relationships: mood_entries, therapy_sessions, self_care_plans

### MoodEntry
- Tracks daily mood scores and associated data
- Fields: mood_score (1-10), emotions, notes, activities, triggers

### TherapySession
- Manages therapy appointments and sessions
- Fields: session_type, scheduled_at, duration, status, notes

### SelfCarePlan
- Stores personalized self-care plans
- Fields: title, description, recommendations, goals, duration

### AIInsight
- Stores AI-generated insights and recommendations
- Fields: insight_type, content, confidence_score, metadata

## Security Considerations

- Passwords are hashed using Werkzeug's secure password hashing
- JWT tokens for authentication with configurable expiration
- CORS enabled for cross-origin requests
- Environment variables for sensitive configuration
- Database session rollback on errors

## Deployment

### Cloud Deployment Options

1. **Heroku**
```bash
# Add Procfile
echo "web: gunicorn main:app" > Procfile
git push heroku main
```

2. **AWS/Azure/GCP**
- Use the provided Docker configuration (if needed)
- Set environment variables in cloud console
- Configure PostgreSQL database
- Deploy using container services or app services

### Environment Configuration

For production:
- Use PostgreSQL instead of SQLite
- Set strong SECRET_KEY and JWT_SECRET_KEY
- Enable HTTPS
- Configure proper CORS settings
- Set up monitoring and logging

## Business Model

### B2C (Business to Consumer)
- Individual subscriptions for mental health support
- Access to AI insights and self-care tools
- Virtual therapy sessions

### B2B (Business to Business)
- Enterprise solutions for healthcare providers
- Integration with existing healthcare systems
- White-label options

## Future Enhancements

- Mobile applications (iOS/Android)
- Real-time chat with therapists
- Group therapy sessions
- Integration with wearables for biometric data
- Enhanced AI models for better predictions
- Multi-language support
- Telehealth video conferencing
- Insurance integration
- Crisis intervention features

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please contact:
- Email: support@mentalhealthplatform.com
- Issues: GitHub Issues page

## Acknowledgments

- Built with Flask and Python
- AI powered by OpenAI
- Inspired by the need for accessible mental health support

## Disclaimer

This platform is designed to support mental health but is not a replacement for professional medical advice, diagnosis, or treatment. Always seek the advice of qualified health providers with questions regarding medical conditions.
