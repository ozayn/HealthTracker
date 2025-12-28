import requests
from datetime import datetime, timedelta
from flask import current_app
from models import db, HealthData

class FitbitService:
    BASE_URL = 'https://api.fitbit.com'
    AUTH_URL = 'https://www.fitbit.com/oauth2/authorize'
    TOKEN_URL = 'https://api.fitbit.com/oauth2/token'
    
    def get_authorization_url(self, user_id):
        """Generate Fitbit OAuth authorization URL"""
        params = {
            'response_type': 'code',
            'client_id': current_app.config['FITBIT_CLIENT_ID'],
            'redirect_uri': current_app.config['FITBIT_REDIRECT_URI'],
            'scope': 'activity heartrate sleep profile nutrition weight',
            'state': str(user_id)
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.AUTH_URL}?{query_string}"
    
    def exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': current_app.config['FITBIT_REDIRECT_URI'],
            'client_id': current_app.config['FITBIT_CLIENT_ID'],
            'client_secret': current_app.config['FITBIT_CLIENT_SECRET']
        }
        
        response = requests.post(self.TOKEN_URL, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def refresh_access_token(self, refresh_token):
        """Refresh the access token"""
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': current_app.config['FITBIT_CLIENT_ID'],
            'client_secret': current_app.config['FITBIT_CLIENT_SECRET']
        }
        
        response = requests.post(self.TOKEN_URL, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_activities(self, access_token, date):
        """Get activity data for a specific date"""
        headers = {'Authorization': f'Bearer {access_token}'}
        date_str = date.strftime('%Y-%m-%d')
        
        url = f'{self.BASE_URL}/1/user/-/activities/date/{date_str}.json'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def get_heart_rate(self, access_token, date):
        """Get heart rate data for a specific date"""
        headers = {'Authorization': f'Bearer {access_token}'}
        date_str = date.strftime('%Y-%m-%d')
        
        url = f'{self.BASE_URL}/1/user/-/activities/heart/date/{date_str}/1d.json'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def get_sleep(self, access_token, date):
        """Get sleep data for a specific date"""
        headers = {'Authorization': f'Bearer {access_token}'}
        date_str = date.strftime('%Y-%m-%d')
        
        url = f'{self.BASE_URL}/1.2/user/-/sleep/date/{date_str}.json'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def sync_data(self, user_id, integration, days=30):
        """Sync Fitbit data for the specified number of days"""
        access_token = integration.access_token
        
        # Check if token needs refresh
        if integration.token_expires_at and datetime.utcnow() >= integration.token_expires_at:
            tokens = self.refresh_access_token(integration.refresh_token)
            access_token = tokens['access_token']
            integration.access_token = access_token
            integration.refresh_token = tokens['refresh_token']
            integration.token_expires_at = datetime.utcnow() + timedelta(seconds=tokens['expires_in'])
            db.session.commit()
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        synced_data = {
            'activities': 0,
            'heart_rate': 0,
            'sleep': 0
        }
        
        current_date = start_date
        while current_date <= end_date:
            try:
                # Sync activities
                activities = self.get_activities(access_token, current_date)
                if 'summary' in activities:
                    summary = activities['summary']
                    
                    # Steps
                    if 'steps' in summary:
                        self._save_health_data(user_id, 'steps', current_date, summary['steps'], 'steps')
                        synced_data['activities'] += 1
                    
                    # Distance
                    if 'distances' in summary and summary['distances']:
                        total_distance = sum([d.get('distance', 0) for d in summary['distances']])
                        self._save_health_data(user_id, 'distance', current_date, total_distance, 'km')
                    
                    # Calories
                    if 'caloriesOut' in summary:
                        self._save_health_data(user_id, 'calories', current_date, summary['caloriesOut'], 'kcal')
                
                # Sync heart rate
                heart_data = self.get_heart_rate(access_token, current_date)
                if 'activities-heart' in heart_data and heart_data['activities-heart']:
                    heart_info = heart_data['activities-heart'][0]
                    if 'value' in heart_info and 'restingHeartRate' in heart_info['value']:
                        self._save_health_data(user_id, 'resting_heart_rate', current_date, 
                                             heart_info['value']['restingHeartRate'], 'bpm')
                        synced_data['heart_rate'] += 1
                
                # Sync sleep
                sleep_data = self.get_sleep(access_token, current_date)
                if 'sleep' in sleep_data and sleep_data['sleep']:
                    for sleep_record in sleep_data['sleep']:
                        if sleep_record.get('isMainSleep'):
                            minutes = sleep_record.get('minutesAsleep', 0)
                            self._save_health_data(user_id, 'sleep_duration', current_date, 
                                                 minutes / 60, 'hours')
                            synced_data['sleep'] += 1
                            break
                
            except Exception as e:
                print(f"Error syncing Fitbit data for {current_date}: {str(e)}")
            
            current_date += timedelta(days=1)
        
        return synced_data
    
    def _save_health_data(self, user_id, data_type, date, value, unit):
        """Save or update health data"""
        existing = HealthData.query.filter_by(
            user_id=user_id,
            provider='fitbit',
            data_type=data_type,
            date=date
        ).first()
        
        if existing:
            existing.value = value
            existing.unit = unit
        else:
            health_data = HealthData(
                user_id=user_id,
                provider='fitbit',
                data_type=data_type,
                date=date,
                value=value,
                unit=unit
            )
            db.session.add(health_data)
        
        db.session.commit()

