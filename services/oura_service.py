import requests
from datetime import datetime, timedelta
from flask import current_app
from models import db, HealthData

class OuraService:
    BASE_URL = 'https://api.ouraring.com'
    AUTH_URL = 'https://cloud.ouraring.com/oauth/authorize'
    TOKEN_URL = 'https://api.ouraring.com/oauth/token'
    
    def get_authorization_url(self, user_id):
        """Generate Oura OAuth authorization URL"""
        from flask import current_app
        params = {
            'response_type': 'code',
            'client_id': current_app.config['OURA_CLIENT_ID'],
            'redirect_uri': current_app.config['OURA_REDIRECT_URI'],
            'scope': 'daily',
            'state': str(user_id)
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.AUTH_URL}?{query_string}"
    
    def exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': current_app.config['OURA_REDIRECT_URI'],
            'client_id': current_app.config['OURA_CLIENT_ID'],
            'client_secret': current_app.config['OURA_CLIENT_SECRET']
        }
        
        response = requests.post(self.TOKEN_URL, data=data)
        response.raise_for_status()
        
        return response.json()
    
    def get_sleep_data(self, access_token, start_date, end_date):
        """Get sleep data from Oura"""
        headers = {'Authorization': f'Bearer {access_token}'}
        
        params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
        
        url = f'{self.BASE_URL}/v2/usercollection/sleep'
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_activity_data(self, access_token, start_date, end_date):
        """Get activity data from Oura"""
        headers = {'Authorization': f'Bearer {access_token}'}
        
        params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
        
        url = f'{self.BASE_URL}/v2/usercollection/daily_activity'
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_readiness_data(self, access_token, start_date, end_date):
        """Get readiness data from Oura"""
        headers = {'Authorization': f'Bearer {access_token}'}

        params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }

        url = f'{self.BASE_URL}/v2/usercollection/daily_readiness'
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        return response.json()

    def get_body_signals_data(self, access_token, start_date, end_date):
        """Get body signals data from Oura (temperature, etc.)"""
        headers = {'Authorization': f'Bearer {access_token}'}

        params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }

        url = f'{self.BASE_URL}/v2/usercollection/daily_body_signals'
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        return response.json()
    
    def sync_data(self, user_id, integration, days=30):
        """Sync Oura data for the specified number of days"""
        access_token = integration.access_token
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        synced_data = {
            'sleep': 0,
            'activity': 0,
            'readiness': 0,
            'body_signals': 0
        }
        
        try:
            # Sync sleep data
            sleep_data = self.get_sleep_data(access_token, start_date, end_date)
            if 'data' in sleep_data:
                for sleep_record in sleep_data['data']:
                    date = datetime.fromisoformat(sleep_record['day']).date()
                    
                    # Total sleep time
                    if 'total_sleep_duration' in sleep_record:
                        hours = sleep_record['total_sleep_duration'] / 3600
                        self._save_health_data(user_id, 'sleep_duration', date, hours, 'hours')
                    
                    # Sleep score
                    if 'score' in sleep_record:
                        self._save_health_data(user_id, 'sleep_score', date, sleep_record['score'], 'score')
                    
                    # REM sleep
                    if 'rem_sleep_duration' in sleep_record:
                        hours = sleep_record['rem_sleep_duration'] / 3600
                        self._save_health_data(user_id, 'rem_sleep', date, hours, 'hours')
                    
                    # Deep sleep
                    if 'deep_sleep_duration' in sleep_record:
                        hours = sleep_record['deep_sleep_duration'] / 3600
                        self._save_health_data(user_id, 'deep_sleep', date, hours, 'hours')

                    # Sleep efficiency
                    if 'efficiency' in sleep_record:
                        efficiency = sleep_record['efficiency']
                        if efficiency is not None:
                            self._save_health_data(user_id, 'sleep_efficiency', date, efficiency, '%')

                    # Sleep latency (time to fall asleep)
                    if 'latency' in sleep_record:
                        latency = sleep_record['latency'] / 60  # Convert to minutes
                        if latency is not None:
                            self._save_health_data(user_id, 'sleep_latency', date, latency, 'minutes')

                    # Number of wake-ups
                    if 'wakeups' in sleep_record:
                        wakeups = sleep_record['wakeups']
                        if wakeups is not None:
                            self._save_health_data(user_id, 'sleep_wakeups', date, wakeups, 'count')

                    # Light sleep duration
                    if 'light_sleep_duration' in sleep_record:
                        hours = sleep_record['light_sleep_duration'] / 3600
                        if hours > 0:
                            self._save_health_data(user_id, 'light_sleep', date, hours, 'hours')

                    synced_data['sleep'] += 1
            
            # Sync activity data
            activity_data = self.get_activity_data(access_token, start_date, end_date)
            if 'data' in activity_data:
                for activity in activity_data['data']:
                    date = datetime.fromisoformat(activity['day']).date()
                    
                    # Steps
                    if 'steps' in activity:
                        self._save_health_data(user_id, 'steps', date, activity['steps'], 'steps')
                    
                    # Active calories
                    if 'active_calories' in activity:
                        self._save_health_data(user_id, 'active_calories', date, activity['active_calories'], 'kcal')
                    
                    # Activity score
                    if 'score' in activity:
                        self._save_health_data(user_id, 'activity_score', date, activity['score'], 'score')

                    # Sedentary time
                    if 'sedentary_time' in activity:
                        sedentary_hours = activity['sedentary_time'] / 3600  # Convert to hours
                        if sedentary_hours is not None:
                            self._save_health_data(user_id, 'sedentary_time', date, sedentary_hours, 'hours')

                    # MET minutes
                    if 'met' in activity:
                        met_minutes = activity['met']
                        if met_minutes is not None:
                            self._save_health_data(user_id, 'met_minutes', date, met_minutes, 'minutes')

                    # Activity time breakdown
                    if 'low_activity_time' in activity:
                        low_activity_hours = activity['low_activity_time'] / 3600
                        if low_activity_hours is not None:
                            self._save_health_data(user_id, 'low_activity_time', date, low_activity_hours, 'hours')

                    if 'medium_activity_time' in activity:
                        medium_activity_hours = activity['medium_activity_time'] / 3600
                        if medium_activity_hours is not None:
                            self._save_health_data(user_id, 'medium_activity_time', date, medium_activity_hours, 'hours')

                    if 'high_activity_time' in activity:
                        high_activity_hours = activity['high_activity_time'] / 3600
                        if high_activity_hours is not None:
                            self._save_health_data(user_id, 'high_activity_time', date, high_activity_hours, 'hours')

                    # Target calories
                    if 'target_calories' in activity:
                        target_calories = activity['target_calories']
                        if target_calories is not None:
                            self._save_health_data(user_id, 'target_calories', date, target_calories, 'kcal')

                    synced_data['activity'] += 1
            
            # Sync readiness data
            readiness_data = self.get_readiness_data(access_token, start_date, end_date)
            if 'data' in readiness_data:
                for readiness in readiness_data['data']:
                    date = datetime.fromisoformat(readiness['day']).date()

                    # Readiness score
                    if 'score' in readiness:
                        self._save_health_data(user_id, 'readiness_score', date, readiness['score'], 'score')

                    # Resting heart rate
                    if 'resting_heart_rate' in readiness:
                        self._save_health_data(user_id, 'resting_heart_rate', date,
                                             readiness['resting_heart_rate'], 'bpm')

                    # HRV
                    if 'hrv_balance' in readiness:
                        self._save_health_data(user_id, 'hrv', date, readiness['hrv_balance'], 'ms')

                    # Previous day activity score
                    if 'previous_day_activity' in readiness:
                        prev_activity = readiness['previous_day_activity']
                        if prev_activity is not None:
                            self._save_health_data(user_id, 'previous_day_activity', date, prev_activity, 'score')

                    # Previous night sleep score
                    if 'previous_night_sleep' in readiness:
                        prev_sleep = readiness['previous_night_sleep']
                        if prev_sleep is not None:
                            self._save_health_data(user_id, 'previous_night_sleep', date, prev_sleep, 'score')

                    synced_data['readiness'] += 1

            # Sync body signals data (temperature, etc.)
            try:
                body_signals_data = self.get_body_signals_data(access_token, start_date, end_date)
                if 'data' in body_signals_data:
                    for signals in body_signals_data['data']:
                        date = datetime.fromisoformat(signals['day']).date()

                        # Body temperature (if not already captured in readiness)
                        if 'body_temperature' in signals:
                            temp = signals['body_temperature']
                            if temp and temp > 30:  # Valid temperature range check
                                self._save_health_data(user_id, 'body_temperature', date, temp, '°C')

                        # Temperature deviation
                        if 'temperature_deviation' in signals:
                            temp_dev = signals['temperature_deviation']
                            if temp_dev is not None:
                                self._save_health_data(user_id, 'temperature_deviation', date, temp_dev, '°C')

                        synced_data['body_signals'] += 1
            except Exception as e:
                print(f"Body signals sync failed: {e}")
                # Continue with other data even if body signals fails
        
        except Exception as e:
            print(f"Error syncing Oura data: {str(e)}")
            raise
        
        return synced_data
    
    def _save_health_data(self, user_id, data_type, date, value, unit):
        """Save or update health data"""
        existing = HealthData.query.filter_by(
            user_id=user_id,
            provider='oura',
            data_type=data_type,
            date=date
        ).first()
        
        if existing:
            existing.value = value
            existing.unit = unit
        else:
            health_data = HealthData(
                user_id=user_id,
                provider='oura',
                data_type=data_type,
                date=date,
                value=value,
                unit=unit
            )
            db.session.add(health_data)
        
        db.session.commit()

