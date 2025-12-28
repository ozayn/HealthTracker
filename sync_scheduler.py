#!/usr/bin/env python3
"""
Oura Data Sync Scheduler
Runs periodic syncs to keep user data up-to-date
Can be called by Railway cron jobs or manual execution
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def sync_recent_user_data():
    """Sync recent data for all active users"""
    from app import create_app
    from models import Integration, User
    from services.oura_service import OuraService
    from services.fitbit_service import FitbitService

    app = create_app()

    with app.app_context():
        print(f"=== SCHEDULED SYNC START: {datetime.utcnow()} ===")

        # Get all active integrations
        active_integrations = Integration.query.filter_by(is_active=True).all()
        print(f"Found {len(active_integrations)} active integrations")

        synced_users = 0
        total_synced = {'oura': 0, 'fitbit': 0, 'clue': 0}

        for integration in active_integrations:
            try:
                user = User.query.get(integration.user_id)
                if not user:
                    continue

                print(f"Syncing user {user.id} ({integration.provider})")

                if integration.provider == 'oura':
                    oura_service = OuraService()
                    result = oura_service.sync_recent_data(user.id, integration, hours=24)
                    total_synced['oura'] += sum(result.values()) if result else 0

                elif integration.provider == 'fitbit':
                    fitbit_service = FitbitService()
                    result = fitbit_service.sync_recent_data(user.id, integration, hours=24)
                    total_synced['fitbit'] += sum(result.values()) if result else 0

                # Update last sync timestamp
                integration.last_sync = datetime.utcnow()
                synced_users += 1

            except Exception as e:
                print(f"Error syncing {integration.provider} for user {integration.user_id}: {e}")

        # Commit all changes
        try:
            from app import db
            db.session.commit()
            print(f"✅ Synced {synced_users} users successfully")
            print(f"📊 Data synced: Oura={total_synced['oura']}, Fitbit={total_synced['fitbit']}, Clue={total_synced['clue']}")
        except Exception as e:
            print(f"❌ Database commit error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    sync_recent_user_data()
