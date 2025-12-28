import requests
from datetime import datetime, timedelta
from flask import current_app
from models import db, HealthData

class OuraService:
    BASE_URL = 'https://api.ouraring.com'
    AUTH_URL = 'https://cloud.ouraring.com/oauth/authorize'
    TOKEN_URL = 'https://api.ouraring.com/oauth/token'

    # Real-time sync configuration
    DEFAULT_SYNC_DAYS = 30  # How far back to sync initially
    RECENT_SYNC_HOURS = 24  # How recent data to sync for ongoing updates
    
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

        # Try multiple possible endpoints for temperature data
        possible_endpoints = [
            'daily_temperature',  # Primary temperature endpoint
            'daily_body_signals', # Alternative body signals endpoint
            'body_signals'         # Another possible name
        ]

        for endpoint in possible_endpoints:
            url = f'{self.BASE_URL}/v2/usercollection/{endpoint}'
            print(f"Trying temperature endpoint: {endpoint}")
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                print(f"Successfully found temperature data at endpoint: {endpoint}")
                break
            elif response.status_code == 404:
                print(f"Endpoint {endpoint} not found (404)")
                continue
            else:
                print(f"Endpoint {endpoint} returned status {response.status_code}")
                continue
        else:
            # If no endpoint works, return empty data
            print("No temperature endpoints available")
            return {'data': []}

        # If we found a working endpoint, return the response
        response.raise_for_status()
        return response.json()
    
    def sync_data(self, user_id, integration, days=30):
        """Sync Oura data for the specified number of days"""
        return self._sync_data_range(user_id, integration, days)

    def sync_recent_data(self, user_id, integration, hours=24):
        """Sync only recent Oura data (last N hours) - for real-time updates"""
        print(f"sync_recent_data called: user_id={user_id}, hours={hours}")
        days = max(1, hours / 24)  # Convert hours to days, minimum 1 day
        print(f"Calling _sync_data_range with days={days}")
        return self._sync_data_range(user_id, integration, days, is_recent_sync=True)

    def _sync_data_range(self, user_id, integration, days, is_recent_sync=False):
        """Sync Oura data for the specified number of days"""
        print(f"DEBUG: _sync_data_range called with integration={integration}, user_id={user_id}")
        if integration is None:
            print("ERROR: integration is None")
            return {'sleep': 0, 'activity': 0, 'readiness': 0, 'body_signals': 0}

        access_token = integration.access_token
        print(f"DEBUG: Got access token: {access_token[:10]}...")

        with open('/tmp/debug.log', 'a') as f:
            f.write("About to calculate dates\n")
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        sync_type = "RECENT" if is_recent_sync else "FULL"
        with open('/tmp/debug.log', 'a') as f:
            f.write(f"Dates calculated: {start_date} to {end_date}, sync_type: {sync_type}\n")

        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        sync_type = "RECENT" if is_recent_sync else "FULL"
        with open('/tmp/sync_debug.log', 'a') as f:
            f.write(f"=== OURA {sync_type} SYNC START ===\n")
            f.write(f"User {user_id}: Syncing {days} days from {start_date} to {end_date}\n")

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

                    # MET minutes - handle both simple values and complex objects
                    if 'met' in activity:
                        met_data = activity['met']
                        print(f"MET data for {date}: {type(met_data)} - {met_data}")
                        if met_data is not None:
                            # Handle complex MET data structure
                            if isinstance(met_data, dict):
                                print(f"Complex MET data structure detected")
                                # If it's a dict with 'items', sum them up
                                if 'items' in met_data and isinstance(met_data['items'], list):
                                    total_met = sum(float(item) for item in met_data['items'] if isinstance(item, (int, float)))
                                    print(f"Summed MET items: {total_met}")
                                    self._save_health_data(user_id, 'met_minutes', date, total_met, 'minutes')
                                else:
                                    print(f"Complex MET data but no 'items' field: {met_data.keys()}")
                                # Otherwise, skip complex data we can't handle
                            else:
                                # Simple numeric value
                                try:
                                    met_value = float(met_data)
                                    print(f"Simple MET value: {met_value}")
                                    self._save_health_data(user_id, 'met_minutes', date, met_value, 'minutes')
                                except (ValueError, TypeError) as e:
                                    print(f"Invalid MET data: {met_data} - {e}")
                                    pass  # Skip invalid data

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
            try:
                with open('/tmp/debug.log', 'a') as f:
                    f.write("About to call get_readiness_data\n")
                print("About to call get_readiness_data")
                readiness_data = self.get_readiness_data(access_token, start_date, end_date)
                import sys
                print(f"Readiness API response keys: {readiness_data.keys() if isinstance(readiness_data, dict) else 'Not dict'}", file=sys.stderr)
                if 'data' in readiness_data and readiness_data['data']:
                    print(f"Sample readiness record keys: {readiness_data['data'][0].keys()}", file=sys.stderr)
                    print(f"Sample readiness record: {readiness_data['data'][0]}", file=sys.stderr)
                if 'data' in readiness_data:
                    print(f"Found {len(readiness_data['data'])} readiness records", file=sys.stderr)
                    if len(readiness_data['data']) == 0:
                        print("No readiness records to process", file=sys.stderr)
                    for i, readiness in enumerate(readiness_data['data']):
                        print(f"DEBUG: Processing readiness record {i}", file=sys.stderr)
                        with open('/tmp/sync_debug.log', 'a') as f:
                            f.write(f"Processing readiness record {i}\n")
                        try:
                            if 'day' not in readiness:
                                with open('/tmp/sync_debug.log', 'a') as f:
                                    f.write(f"Readiness record {i} missing 'day' field: {readiness}\n")
                                continue
                            date = datetime.fromisoformat(readiness['day']).date()
                            with open('/tmp/sync_debug.log', 'a') as f:
                                f.write(f"Processing readiness record for date: {date}\n")
                                f.write(f"Readiness record has keys: {list(readiness.keys())}\n")
                        except Exception as e:
                            with open('/tmp/sync_debug.log', 'a') as f:
                                f.write(f"Error parsing date from readiness record: {e}\n")
                                f.write(f"Readiness record: {readiness}\n")
                            continue

                        with open('/tmp/sync_debug.log', 'a') as f:
                            f.write("About to process readiness_score\n")

                        # Readiness score
                        if 'score' in readiness:
                            print(f"Processing readiness_score: {readiness['score']}", file=sys.stderr)
                            self._save_health_data(user_id, 'readiness_score', date, readiness['score'], 'score')

                        # Resting heart rate
                        if 'resting_heart_rate' in readiness:
                            with open('/tmp/sync_debug.log', 'a') as f:
                                f.write(f"Processing resting_heart_rate: {readiness['resting_heart_rate']}\n")
                            self._save_health_data(user_id, 'resting_heart_rate', date,
                                                 readiness['resting_heart_rate'], 'bpm')

                        # HRV
                        if 'hrv_balance' in readiness:
                            self._save_health_data(user_id, 'hrv', date, readiness['hrv_balance'], 'ms')

                        # About to check temperature fields
                        with open('/tmp/sync_debug.log', 'a') as f:
                            f.write("About to check temperature fields\n")

                    # Temperature deviation (this is the main temperature metric from Oura)
                    if 'temperature_deviation' in readiness:
                        temp_dev = readiness['temperature_deviation']
                        print(f"Found temperature_deviation for {date}: {temp_dev}", file=sys.stderr)
                        if temp_dev is not None:
                            self._save_health_data(user_id, 'temperature_deviation', date, temp_dev, '°C')
                    else:
                        print(f"No temperature_deviation field for {date}", file=sys.stderr)

                    # Temperature trend deviation
                    if 'temperature_trend_deviation' in readiness:
                        temp_trend = readiness['temperature_trend_deviation']
                        print(f"Found temperature_trend_deviation in readiness: {temp_trend}")
                        if temp_trend is not None:
                            self._save_health_data(user_id, 'temperature_trend_deviation', date, temp_trend, '°C')

                    # Body temperature (from readiness)
                    if 'body_temperature' in readiness:
                        temp = readiness['body_temperature']
                        print(f"Found body_temperature in readiness: {temp}")
                        if temp and temp > 30:  # Valid temperature range check
                            self._save_health_data(user_id, 'body_temperature', date, temp, '°C')

                    # Check for temperature in other possible field names
                    temp_fields = ['temperature', 'body_temp', 'core_temperature', 'skin_temperature']
                    for field in temp_fields:
                        if field in readiness and readiness[field]:
                            temp = readiness[field]
                            print(f"Found temperature in {field}: {temp}")
                            if isinstance(temp, (int, float)) and temp > 30:  # Valid temperature range check
                                self._save_health_data(user_id, 'body_temperature', date, temp, '°C')
                                break

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
                        print(f"Readiness sync completed. Synced {synced_data['readiness']} records")
            except Exception as e:
                print(f"Readiness sync failed: {e}")
                import traceback
                traceback.print_exc()

            print("Readiness processing completed, now starting body signals")
            # About to start body signals sync
            print("About to start body signals sync")

            # Sync body signals data (temperature, etc.)
            print("=== STARTING BODY SIGNALS SYNC ===")
            try:
                print(f"Fetching body signals data from {start_date} to {end_date}")
                body_signals_data = self.get_body_signals_data(access_token, start_date, end_date)
                print(f"Body signals API response: {type(body_signals_data)}")
                print(f"Body signals response keys: {body_signals_data.keys() if isinstance(body_signals_data, dict) else 'Not dict'}")

                if 'data' in body_signals_data:
                    print(f"Found {len(body_signals_data['data'])} body signals records")
                    for signals in body_signals_data['data']:
                        print(f"Processing body signals for date: {signals.get('day')}")
                        date = datetime.fromisoformat(signals['day']).date()

                        # Body temperature (if not already captured in readiness)
                        if 'body_temperature' in signals:
                            temp = signals['body_temperature']
                            print(f"Found body temperature: {temp}")
                            if temp and temp > 30:  # Valid temperature range check
                                self._save_health_data(user_id, 'body_temperature', date, temp, '°C')
                                print(f"Saved body temperature: {temp}°C for {date}")
                        else:
                            print("No body_temperature field in signals data")

                        # Temperature deviation
                        if 'temperature_deviation' in signals:
                            temp_dev = signals['temperature_deviation']
                            print(f"Found temperature deviation: {temp_dev}")
                            if temp_dev is not None:
                                self._save_health_data(user_id, 'temperature_deviation', date, temp_dev, '°C')

                        synced_data['body_signals'] += 1
                else:
                    print(f"No 'data' key in body signals response. Keys: {body_signals_data.keys() if isinstance(body_signals_data, dict) else 'Not a dict'}")
            except Exception as e:
                print(f"Body signals sync failed: {e}")
                import traceback
                traceback.print_exc()
                # Continue with other data even if body signals fails
        
        except Exception as e:
            print(f"Error syncing Oura data: {str(e)}")
            raise
        
        return synced_data
    
    def _save_health_data(self, user_id, data_type, date, value, unit):
        """Save or update health data - PRESERVES ALL HISTORICAL DATA"""
        # Data Retention Policy: Never delete historical health data
        # Each data point represents a unique measurement at a specific time
        # Updates are allowed for the same date/type/provider combination

        existing = HealthData.query.filter_by(
            user_id=user_id,
            provider='oura',
            data_type=data_type,
            date=date
        ).first()

        if existing:
            # Update existing record (same date/type/provider)
            old_value = existing.value
            existing.value = value
            existing.unit = unit
            existing.updated_at = datetime.utcnow()
            print(f"Updated Oura data: {data_type} for {date} - {old_value} → {value}")
        else:
            # Create new record (preserves all historical data)
            health_data = HealthData(
                user_id=user_id,
                provider='oura',
                data_type=data_type,
                date=date,
                value=value,
                unit=unit
            )
            db.session.add(health_data)
            print(f"Saved new Oura data: {data_type} for {date} - {value} {unit}")

        try:
            db.session.commit()
        except Exception as e:
            print(f"Error saving health data: {e}")
            db.session.rollback()
            raise

