# Health Tracker

A comprehensive health tracking system that integrates with Fitbit, Oura Ring, and Clue to centralize your health data and blood test results.

## Features

- **Multiple API Integrations**: Connect Fitbit, Oura Ring, and Clue accounts
- **Automatic Data Sync**: Synchronize health metrics from all connected devices
- **Blood Test Management**: Upload and track blood test results with detailed markers
- **Data Visualization**: Interactive charts and graphs for health metrics over time
- **Historical Data**: Maintain complete history of all health data and lab results
- **Clean UI**: Minimal, professional design with pastel colors and smooth interactions

## Tech Stack

### Backend
- **Flask**: Python web framework
- **SQLAlchemy**: Database ORM
- **PostgreSQL/SQLite**: Database
- **OAuth 2.0**: Secure API integrations
- **Gunicorn**: Production WSGI server

### Frontend
- **React**: UI framework
- **Chart.js**: Data visualization
- **React Router**: Navigation
- **Axios**: HTTP client

## Project Structure

```
HealthTracker/
├── app.py                  # Flask application entry point
├── config.py              # Configuration settings
├── models.py              # Database models
├── requirements.txt       # Python dependencies
├── routes/               # API endpoints
│   ├── auth_routes.py    # OAuth authentication
│   ├── health_routes.py  # Health data endpoints
│   ├── blood_test_routes.py # Blood test endpoints
│   └── user_routes.py    # User management
├── services/             # External API integrations
│   ├── fitbit_service.py
│   ├── oura_service.py
│   └── clue_service.py
├── frontend/             # React application
│   ├── src/
│   │   ├── components/   # Reusable components
│   │   └── pages/       # Page components
│   └── public/
├── uploads/              # Uploaded files storage
└── migrations/           # Database migrations

```

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL (for production) or SQLite (for development)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd HealthTracker
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///health_tracker.db

# Fitbit OAuth
FITBIT_CLIENT_ID=your-fitbit-client-id
FITBIT_CLIENT_SECRET=your-fitbit-client-secret

# Oura OAuth
OURA_CLIENT_ID=your-oura-client-id
OURA_CLIENT_SECRET=your-oura-client-secret

# Clue OAuth (if available)
CLUE_CLIENT_ID=your-clue-client-id
CLUE_CLIENT_SECRET=your-clue-client-secret

PORT=5001
```

### 4. Get API Credentials

#### Fitbit
1. Go to https://dev.fitbit.com/
2. Register an application
3. Set OAuth 2.0 Application Type to "Personal"
4. Add redirect URL: `http://localhost:5001/api/auth/fitbit/callback`
5. Copy Client ID and Client Secret

#### Oura
1. Go to https://cloud.ouraring.com/oauth/applications
2. Create a new application
3. Add redirect URL: `http://localhost:5001/api/auth/oura/callback`
4. Copy Client ID and Client Secret

#### Clue
Note: Clue doesn't have a public API yet. The integration is prepared for future use.

### 5. Initialize Database

```bash
# Create database tables
python app.py
# The app will automatically create tables on first run
```

### 6. Set Up Frontend

```bash
cd frontend
npm install
```

### 7. Run the Application

#### Development Mode

Terminal 1 - Backend:
```bash
source venv/bin/activate
python app.py
```

Terminal 2 - Frontend:
```bash
cd frontend
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5001

#### Production Mode

```bash
# Build frontend
cd frontend
npm run build
cd ..

# Run with Gunicorn
gunicorn app:app --bind 0.0.0.0:5001
```

### 8. Using the Restart Script

```bash
chmod +x restart.sh
./restart.sh
```

## Deployment to Railway

### 1. Prepare for Deployment

Ensure your code is in a Git repository:

```bash
git init
git add .
git commit -m "Initial commit"
```

### 2. Deploy to Railway

1. Go to https://railway.app/
2. Create a new project
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will automatically detect the configuration

### 3. Add Environment Variables

In Railway dashboard, add the following environment variables:

```
SECRET_KEY=your-secret-key
DATABASE_URL=<automatically provided by Railway PostgreSQL>
FITBIT_CLIENT_ID=your-fitbit-client-id
FITBIT_CLIENT_SECRET=your-fitbit-client-secret
FITBIT_REDIRECT_URI=https://your-app.railway.app/api/auth/fitbit/callback
OURA_CLIENT_ID=your-oura-client-id
OURA_CLIENT_SECRET=your-oura-client-secret
OURA_REDIRECT_URI=https://your-app.railway.app/api/auth/oura/callback
PORT=5001
```

### 4. Add PostgreSQL Database

1. In Railway, click "New" → "Database" → "PostgreSQL"
2. Railway will automatically set DATABASE_URL

### 5. Update OAuth Redirect URLs

Update your Fitbit and Oura OAuth applications with the Railway URLs:
- `https://your-app.railway.app/api/auth/fitbit/callback`
- `https://your-app.railway.app/api/auth/oura/callback`

## Usage

### 1. Connect Your Devices

1. Navigate to "Integrations" page
2. Click "Connect" for each device you want to integrate
3. Authorize the application through OAuth
4. Click "Sync All Data" to fetch your health data

### 2. View Health Data

1. Go to "Health Data" page
2. Select a metric (steps, heart rate, sleep, etc.)
3. Choose a time range
4. View charts and statistics

### 3. Add Blood Tests

1. Navigate to "Blood Tests" page
2. Click "Add Blood Test"
3. Fill in the test date and lab name
4. Optionally upload test results file
5. Add individual markers with values and reference ranges

### 4. Dashboard Overview

The dashboard provides:
- Connected integrations status
- Recent health metrics summary
- Latest blood test results
- Quick statistics

## API Endpoints

### Authentication
- `GET /api/auth/{provider}/authorize` - Initiate OAuth flow
- `GET /api/auth/{provider}/callback` - OAuth callback
- `GET /api/auth/integrations/{user_id}` - Get user integrations
- `DELETE /api/auth/integrations/{id}` - Disconnect integration

### Health Data
- `POST /api/health/sync/{user_id}` - Sync data from all providers
- `GET /api/health/{user_id}` - Get health data with filters
- `GET /api/health/summary/{user_id}` - Get aggregated summary
- `GET /api/health/types` - Get available data types

### Blood Tests
- `POST /api/blood-tests/{user_id}` - Create blood test
- `GET /api/blood-tests/{user_id}` - Get all blood tests
- `GET /api/blood-tests/test/{test_id}` - Get specific test
- `PUT /api/blood-tests/test/{test_id}` - Update test
- `DELETE /api/blood-tests/test/{test_id}` - Delete test
- `POST /api/blood-tests/test/{test_id}/markers` - Add marker
- `GET /api/blood-tests/markers/{user_id}/trends` - Get marker trends

### Users
- `POST /api/users` - Create user
- `GET /api/users/{user_id}` - Get user
- `GET /api/users` - Get all users

## Database Schema

### Users
- id, email, created_at, updated_at

### Integrations
- id, user_id, provider, access_token, refresh_token, token_expires_at, is_active, last_sync

### HealthData
- id, user_id, provider, data_type, date, value, unit, metadata

### BloodTests
- id, user_id, test_date, lab_name, notes, file_path

### BloodMarkers
- id, blood_test_id, marker_name, value, unit, reference_range_low, reference_range_high, is_abnormal, notes

## Troubleshooting

### OAuth Issues
- Ensure redirect URLs match exactly in OAuth app settings
- Check that client IDs and secrets are correct
- Verify the app is running on the correct port

### Database Issues
- For SQLite: Delete `health_tracker.db` and restart
- For PostgreSQL: Check DATABASE_URL format

### Frontend Build Issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Port Already in Use
```bash
# Find process using port 5001
lsof -i :5001
# Kill the process
kill -9 <PID>
```

## Security Considerations

- Never commit `.env` file or credentials to Git
- Use strong SECRET_KEY in production
- Enable HTTPS in production
- Regularly update dependencies
- Implement proper authentication before production use
- Secure file uploads with validation

## Future Enhancements

- [ ] User authentication and multi-user support
- [ ] Apple Health integration
- [ ] Google Fit integration
- [ ] AI-powered insights and recommendations
- [ ] Export data to CSV/PDF
- [ ] Automated blood test result parsing (OCR)
- [ ] Mobile app
- [ ] Email notifications for abnormal results
- [ ] Doctor/healthcare provider sharing

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Key Technical Insights & Learnings

This project involved several complex integrations and deployment challenges. Here are the key technical insights gained during development:

### 🔐 OAuth Multi-Domain Support

**Challenge**: Supporting OAuth authentication from multiple domains (development, Railway subdomain, custom domain) while maintaining security.

**Solution**: Implemented dynamic redirect URI detection that automatically selects the correct OAuth callback URL based on the request origin:

```python
# Detect domain from request and choose appropriate redirect URI
base_url = request.host_url.rstrip('/')
if 'railway.app' in base_url:
    redirect_uri = 'https://[railway-subdomain]/api/auth/google/callback'
elif 'customdomain.com' in base_url:
    redirect_uri = 'https://customdomain.com/api/auth/google/callback'
```

**Key Benefits**:
- Seamless authentication from any domain
- No manual environment variable management
- Maintains OAuth security requirements

### 🚀 Railway Deployment Challenges

**Static File Serving Issues**:
- **Problem**: JavaScript files returning HTML instead of JS content
- **Root Cause**: Frontend build files not committed to Git repository
- **Solution**: Added `frontend/build/` directory to version control and implemented robust static file path resolution

**Database Configuration**:
- **Challenge**: Automatic PostgreSQL setup vs manual SQLite configuration
- **Solution**: Environment-aware database URI handling with proper PostgreSQL connection string formatting

**Port Management**:
- **Issue**: Railway's dynamic port assignment causing routing conflicts
- **Solution**: Proper PORT environment variable handling with fallback defaults

### 🌐 Custom Domain Setup

**DNS & SSL Propagation**:
- **Learning**: Custom domain setup can take 1-2 hours for DNS/SSL provisioning
- **Tip**: Use Railway subdomain during development and testing
- **Process**: Requires both DNS CNAME configuration and Railway SSL certificate provisioning

**Multi-Domain OAuth**: As mentioned above, implemented automatic domain detection for OAuth flows.

### 🔧 Development Workflow Improvements

**Frontend Build Process**:
- **Challenge**: Ensuring frontend build files are always deployed
- **Solution**: Integrated build verification in deployment scripts and proper Git tracking

**Environment Variable Management**:
- **Best Practice**: Use Railway's environment variable system for all sensitive configuration
- **Security**: Never commit credentials or API keys to version control

**Database Migrations**:
- **Learning**: Always run migrations in production deployment
- **Implementation**: Automated migration execution in deployment scripts

### 📊 API Design Patterns

**Health Data Aggregation**:
- **Challenge**: Efficiently querying and aggregating time-series health data
- **Solution**: Implemented summary endpoints with configurable date ranges and data type filtering

**OAuth State Management**:
- **Security**: Proper CSRF protection with OAuth state parameters
- **Error Handling**: Clear error messages for authentication failures

### 🐛 Debugging Techniques

**Railway Deployment Logs**:
- **Tip**: Use Railway's deployment logs extensively for debugging
- **Pattern**: Add detailed logging for OAuth flows, database connections, and static file serving

**Local vs Production Parity**:
- **Challenge**: Differences between local development and Railway deployment
- **Solution**: Implement environment-aware configuration and logging

### 📈 Performance Optimizations

**Database Queries**:
- **Learning**: Efficient indexing and query optimization for health data time series
- **Implementation**: Proper database schema design with appropriate indexes

**Static Asset Delivery**:
- **Challenge**: Reliable static file serving in production
- **Solution**: Flask's static file handling with proper cache headers

### 🔒 Security Considerations

**OAuth Implementation**:
- **Best Practice**: Always validate redirect URIs match exactly
- **Security**: Use HTTPS for all OAuth flows in production
- **State Protection**: Implement proper OAuth state parameter validation

**File Upload Security**:
- **Validation**: Implement file type and size validation for blood test uploads
- **Storage**: Secure file storage with proper permissions

### 🎯 Production Readiness Checklist

Based on our deployment experience:

- [x] Environment variable configuration
- [x] Database migration automation
- [x] Static file serving verification
- [x] OAuth callback URL configuration
- [x] HTTPS enforcement
- [x] Error logging and monitoring
- [x] Health check endpoints
- [x] Proper CORS configuration

## Support

For issues or questions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review API documentation
- Refer to the "Key Technical Insights" section for common deployment issues

---

Built with ❤️ for better health tracking

