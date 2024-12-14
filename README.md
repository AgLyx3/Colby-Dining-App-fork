# Colby Dining App 🍽️

⭐ Currently deployed on Heroku: [Colby Dining](https://colby-dining-a5fb6bcb774e.herokuapp.com/)

## Overview
The Colby Dining App is a comprehensive dining management system designed for Colby College's dining services. It provides real-time menu information, wait times, and personalized dining experiences for students and staff.
<p align="center">
  <img src="website/static/img/readme.png" alt="Screenshot of Landing Page">
</p>

## Features
- 📱 Real-time wait time predictions for dining halls
- 🍳 Daily menu updates with dietary information
- ⭐ Personalized favorite dish tracking
- 📊 User feedback system
- 🔐 Google OAuth authentication
- 📱 Mobile-responsive design
- 💌 Email notifications for favorite dishes
- 👥 Admin dashboard for management

## Tech Stack
- **Backend**: Python/Flask
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLAlchemy with MySQL
- **Authentication**: Google OAuth
- **APIs**: 
  - Bon Appétit API for menu data
  - Custom ML models for wait time predictions
- **Libraries**:
  - Flask-Login for session management
  - Flask-SQLAlchemy for ORM
  - APScheduler for background tasks
  - Bootstrap for UI components

## Getting Started

### Prerequisites
- Python 3.10+
- MySQL
- pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/AgLyx3/Colby-Dining-App-fork.git
cd Colby-Dining-App-fork
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`:
```env
SECRET_KEY=your_secret_key
SQLALCHEMY_DATABASE_URI=mysql://username:password@localhost/dbname
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
MENU_API_USERNAME=your_api_username
MENU_API_PASSWORD=your_api_password
GEMINI_API=your-api-key
```

5. Initialize the database:
```bash
flask db upgrade
```

6. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:8000`

## Project Structure
```
colby-dining-app/
├── website/
│   ├── static/          # Static files (CSS, JS, images)
│   ├── templates/       # HTML templates
│   ├── models.py        # Database models
│   ├── views.py         # Route handlers
│   └── __init__.py      # App initialization
├── tests/               # Test files
├── requirements.txt     # Project dependencies
└── app.py              # Application entry point
```

## Key Features

### Wait Time Predictions
- ML-based system for predicting dining hall wait times
- Real-time updates based on historical data
- Visual indicators for busy periods

### Menu Management
- Daily menu updates from Bon Appétit API
- Dietary restriction filtering
- Nutritional information display
- Favorite dish tracking

### For Students
- 🕒 Real-time wait times
- 🍜 Today's menu at a glance
- ⭐ Save your favorite dishes
- 📱 Mobile-friendly interface
- 📧 Get notified when your favorites are served

### For Administrators
- 📊 Analytics dashboard
- 💭 Feedback management
- 📋 Menu customization
- 📈 Traffic monitoring
- 📑 Survey creation tools

## Testing
Run the test suite:
```bash
pytest
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- Colby College Dining Services
- Professor Naser Al Madi
- Bon Appétit Management Company
- Flask and SQLAlchemy communities
- Bootstrap team

## Contact
For questions or support, please contact us at colbydining.feedback@gmail.com

---
⚡ Built with ❤️ for Colby College students and staff


