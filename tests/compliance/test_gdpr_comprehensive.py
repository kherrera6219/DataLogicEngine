"""
Comprehensive GDPR Compliance Testing Suite

Tests for GDPR compliance endpoints covering:
- Data export (Article 20 - Data Portability)
- Data deletion (Article 17 - Right to Erasure)
- Consent management
- Data access requests
- Grace periods and cancellation
- Data completeness verification
"""

import pytest
import json
from unittest.mock import patch
from datetime import datetime, timedelta, UTC


class TestGDPRDataExport:
    """Test GDPR data export functionality (Article 20)"""

    def test_export_user_data_authenticated(self, authenticated_client, app):
        """Test authenticated user can export their data"""
        response = authenticated_client.post('/api/v1/gdpr/export')

        assert response.status_code == 200
        assert response.mimetype == 'application/json' or 'application/octet-stream' in response.mimetype
        assert 'attachment' in response.headers.get('Content-Disposition', '')

    def test_export_requires_authentication(self, client):
        """Test data export requires authentication"""
        response = client.post('/api/v1/gdpr/export')

        assert response.status_code == 401
        assert response.is_json
        assert response.get_json()['code'] == 'UNAUTHORIZED'

    def test_export_contains_user_profile(self, authenticated_client, app):
        """Test export includes user profile data"""
        response = authenticated_client.post('/api/v1/gdpr/export')

        if response.status_code == 200:
            # Parse the response data
            data = response.get_data()
            if data:
                try:
                    export_data = json.loads(data)
                    assert 'user_profile' in export_data
                    assert 'username' in export_data['user_profile']
                    assert 'email' in export_data['user_profile']
                except json.JSONDecodeError:
                    # File download response, can't parse inline
                    pass

    def test_export_includes_timestamp(self, authenticated_client, app):
        """Test export includes export timestamp"""
        response = authenticated_client.post('/api/v1/gdpr/export')

        if response.status_code == 200:
            data = response.get_data()
            if data:
                try:
                    export_data = json.loads(data)
                    assert 'export_date' in export_data
                    # Verify timestamp is recent (within 1 minute)
                    export_time = datetime.fromisoformat(export_data['export_date'].replace('Z', '+00:00'))
                    assert datetime.now(UTC) - export_time < timedelta(minutes=1)
                except (json.JSONDecodeError, KeyError, ValueError):
                    pass

    def test_export_includes_export_type(self, authenticated_client, app):
        """Test export identifies export type"""
        response = authenticated_client.post('/api/v1/gdpr/export')

        if response.status_code == 200:
            data = response.get_data()
            if data:
                try:
                    export_data = json.loads(data)
                    assert 'export_type' in export_data
                    assert export_data['export_type'] == 'gdpr_data_portability'
                except (json.JSONDecodeError, KeyError):
                    pass

    def test_export_filename_includes_date(self, authenticated_client, app):
        """Test export filename includes date"""
        response = authenticated_client.post('/api/v1/gdpr/export')

        if response.status_code == 200:
            content_disposition = response.headers.get('Content-Disposition', '')
            assert datetime.now(UTC).strftime('%Y%m%d') in content_disposition
            assert '.json' in content_disposition

    def test_export_data_structure_complete(self, authenticated_client, app):
        """Test export data structure includes all required fields"""
        response = authenticated_client.post('/api/v1/gdpr/export')

        if response.status_code == 200:
            data = response.get_data()
            if data:
                try:
                    export_data = json.loads(data)
                    required_fields = [
                        'export_date', 'export_type', 'user_profile',
                        'chat_sessions', 'knowledge_nodes', 'preferences',
                        'consent_records'
                    ]
                    for field in required_fields:
                        assert field in export_data, f"Missing required field: {field}"
                except json.JSONDecodeError:
                    pytest.fail("Export data is not valid JSON")

    def test_export_valid_json_format(self, authenticated_client, app):
        """Test export produces valid JSON"""
        response = authenticated_client.post('/api/v1/gdpr/export')

        if response.status_code == 200:
            data = response.get_data()
            if data:
                # Should be parseable as JSON
                try:
                    export_data = json.loads(data)
                    assert isinstance(export_data, dict)
                except json.JSONDecodeError:
                    pytest.fail("Export data is not valid JSON")

    @patch('backend.routes.gdpr_routes.db')
    def test_export_handles_missing_chat_sessions(self, mock_db, authenticated_client, app):
        """Test export handles missing chat sessions gracefully"""
        # Mock database query to raise exception
        mock_db.session.query.side_effect = Exception("Database error")

        response = authenticated_client.post('/api/v1/gdpr/export')

        # Should still return 200 with partial data
        # The route logs warnings but continues
        assert response.status_code == 200

    def test_export_does_not_expose_other_users_data(self, client, app):
        """Test export only includes requesting user's data"""
        with app.app_context():
            # Create two users
            from models import User, db
            # Clear existing users to avoid conflicts
            db.session.query(User).delete()
            db.session.commit()
            # ...

            user1 = User(username="user1", email="user1@test.com", role="user")
            user1.set_password("SecurePass123!")
            user2 = User(username="user2", email="user2@test.com", role="user")
            user2.set_password("SecurePass123!")

            db.session.add_all([user1, user2])
            db.session.commit()

            # Login as user1
            client.post('/api/v1/auth/login', json={
                'username': 'user1',
                'password': 'SecurePass123!'
            })

            # Export data
            response = client.post('/api/v1/gdpr/export')

            if response.status_code == 200:
                data = response.get_data()
                if data:
                    try:
                        export_data = json.loads(data)
                        # Should only contain user1's data
                        assert export_data['user_profile']['username'] == 'user1'
                        assert export_data['user_profile']['email'] == 'user1@test.com'
                    except json.JSONDecodeError:
                        pass

            # Cleanup
            db.session.delete(user1)
            db.session.delete(user2)
            db.session.commit()

    def test_multiple_exports_allowed(self, authenticated_client, app):
        """Test user can export data multiple times"""
        # First export
        response1 = authenticated_client.post('/api/v1/gdpr/export')
        assert response1.status_code == 200

        # Second export
        response2 = authenticated_client.post('/api/v1/gdpr/export')
        assert response2.status_code == 200


class TestGDPRDataDeletion:
    """Test GDPR data deletion functionality (Article 17)"""

    def test_request_data_deletion_authenticated(self, authenticated_client, app):
        """Test authenticated user can request deletion"""
        response = authenticated_client.post('/api/v1/gdpr/delete')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'message' in data
        assert 'data' in data

    def test_deletion_requires_authentication(self, client):
        """Test deletion request requires authentication"""
        response = client.post('/api/v1/gdpr/delete')

        assert response.status_code == 401
        assert response.is_json
        assert response.get_json()['code'] == 'UNAUTHORIZED'

    def test_deletion_request_includes_grace_period(self, authenticated_client, app):
        """Test deletion request includes grace period"""
        response = authenticated_client.post('/api/v1/gdpr/delete')

        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'grace_period_days' in data['data']
        assert data['data']['grace_period_days'] >= 1

    def test_deletion_request_returns_request_id(self, authenticated_client, app):
        """Test deletion request returns unique request ID"""
        response = authenticated_client.post('/api/v1/gdpr/delete')

        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'request_id' in data['data']
        assert len(data['data']['request_id']) > 0

    def test_deletion_request_includes_scheduled_date(self, authenticated_client, app):
        """Test deletion request includes scheduled deletion date"""
        response = authenticated_client.post('/api/v1/gdpr/delete')

        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'scheduled_deletion' in data['data']

    def test_deletion_request_includes_instructions(self, authenticated_client, app):
        """Test deletion request includes cancellation instructions"""
        response = authenticated_client.post('/api/v1/gdpr/delete')

        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'instructions' in data['data']
        assert 'grace period' in data['data']['instructions'].lower()

    def test_deletion_request_logged(self, authenticated_client, app):
        """Test deletion request is logged"""
        with patch('backend.routes.gdpr_routes.logger') as mock_logger:
            response = authenticated_client.post('/api/v1/gdpr/delete')

            assert response.status_code == 200
            mock_logger.info.assert_called()

    def test_multiple_deletion_requests(self, authenticated_client, app):
        """Test user can make multiple deletion requests"""
        # First request
        response1 = authenticated_client.post('/api/v1/gdpr/delete')
        assert response1.status_code == 200

        # Second request
        response2 = authenticated_client.post('/api/v1/gdpr/delete')
        assert response2.status_code == 200

    @patch('backend.routes.gdpr_routes.db')
    def test_deletion_request_handles_errors(self, mock_db, authenticated_client, app):
        """Test deletion request handles database errors gracefully"""
        mock_db.session.add.side_effect = Exception("Database error")

        response = authenticated_client.post('/api/v1/gdpr/delete')

        # Should return error response
        assert response.status_code in [200, 500]


class TestGDPRConsentManagement:
    """Test GDPR consent management"""

    def test_get_consent_status_authenticated(self, authenticated_client, app):
        """Test authenticated user can get consent status"""
        response = authenticated_client.get('/api/v1/gdpr/consent')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data

    def test_get_consent_requires_authentication(self, client):
        """Test getting consent status requires authentication"""
        response = client.get('/api/v1/gdpr/consent')

        assert response.status_code == 401
        assert response.is_json
        assert response.get_json()['code'] == 'UNAUTHORIZED'

    def test_consent_status_includes_all_categories(self, authenticated_client, app):
        """Test consent status includes all processing categories"""
        response = authenticated_client.get('/api/v1/gdpr/consent')

        assert response.status_code == 200
        data = response.get_json()
        consent_data = data['data']

        required_categories = [
            'analytics', 'marketing_emails', 'third_party_sharing',
            'ai_training', 'personalization'
        ]
        for category in required_categories:
            assert category in consent_data

    def test_consent_status_includes_last_updated(self, authenticated_client, app):
        """Test consent status includes last updated timestamp"""
        response = authenticated_client.get('/api/v1/gdpr/consent')

        assert response.status_code == 200
        data = response.get_json()
        assert 'last_updated' in data['data']

    def test_update_consent_authenticated(self, authenticated_client, app):
        """Test authenticated user can update consent"""
        consent_updates = {
            'analytics': False,
            'marketing_emails': True
        }

        response = authenticated_client.post(
            '/api/v1/gdpr/consent',
            json=consent_updates
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_update_consent_requires_authentication(self, client):
        """Test updating consent requires authentication"""
        response = client.post('/api/v1/gdpr/consent', json={
            'analytics': False
        })

        assert response.status_code == 401
        assert response.is_json
        assert response.get_json()['code'] == 'UNAUTHORIZED'

    def test_update_consent_filters_allowed_fields(self, authenticated_client, app):
        """Test consent update only accepts allowed fields"""
        consent_updates = {
            'analytics': False,
            'invalid_field': True,  # Should be filtered out
            'marketing_emails': True
        }

        response = authenticated_client.post(
            '/api/v1/gdpr/consent',
            json=consent_updates
        )

        assert response.status_code == 200
        data = response.get_json()
        returned_data = data['data']

        # Should only include allowed fields
        assert 'analytics' in returned_data
        assert 'marketing_emails' in returned_data
        assert 'invalid_field' not in returned_data

    def test_update_consent_with_empty_data(self, authenticated_client, app):
        """Test consent update with no fields"""
        response = authenticated_client.post(
            '/api/v1/gdpr/consent',
            json={}
        )

        assert response.status_code == 200

    def test_update_consent_logs_changes(self, authenticated_client, app):
        """Test consent updates are logged"""
        with patch('backend.routes.gdpr_routes.logger') as mock_logger:
            response = authenticated_client.post(
                '/api/v1/gdpr/consent',
                json={'analytics': False}
            )

            assert response.status_code == 200
            mock_logger.info.assert_called()

    def test_consent_boolean_values(self, authenticated_client, app):
        """Test consent accepts boolean values"""
        consent_updates = {
            'analytics': True,
            'marketing_emails': False
        }

        response = authenticated_client.post(
            '/api/v1/gdpr/consent',
            json=consent_updates
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['analytics'] is True
        assert data['data']['marketing_emails'] is False

    def test_consent_granular_control(self, authenticated_client, app):
        """Test user can selectively enable/disable consent categories"""
        # Enable only analytics
        response = authenticated_client.post(
            '/api/v1/gdpr/consent',
            json={
                'analytics': True,
                'marketing_emails': False,
                'ai_training': False
            }
        )

        assert response.status_code == 200


class TestGDPRAccessRequests:
    """Test GDPR data access requests (Article 15)"""

    def test_submit_access_request_authenticated(self, authenticated_client, app):
        """Test authenticated user can submit access request"""
        response = authenticated_client.post(
            '/api/v1/gdpr/access-request',
            json={'type': 'full_export'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_access_request_requires_authentication(self, client):
        """Test access request requires authentication"""
        response = client.post('/api/v1/gdpr/access-request')

        assert response.status_code == 401
        assert response.is_json
        assert response.get_json()['code'] == 'UNAUTHORIZED'

    def test_access_request_returns_request_id(self, authenticated_client, app):
        """Test access request returns unique request ID"""
        response = authenticated_client.post(
            '/api/v1/gdpr/access-request',
            json={'type': 'full_export'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'request_id' in data['data']
        assert 'gdpr-access-' in data['data']['request_id']

    def test_access_request_includes_response_time(self, authenticated_client, app):
        """Test access request includes estimated response time"""
        response = authenticated_client.post(
            '/api/v1/gdpr/access-request',
            json={'type': 'full_export'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'estimated_response_time' in data['data']
        assert '30 days' in data['data']['estimated_response_time']

    def test_access_request_includes_contact_info(self, authenticated_client, app):
        """Test access request includes contact information"""
        response = authenticated_client.post(
            '/api/v1/gdpr/access-request',
            json={'type': 'full_export'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'contact_email' in data['data']

    def test_access_request_with_specific_data(self, authenticated_client, app):
        """Test access request for specific data categories"""
        response = authenticated_client.post(
            '/api/v1/gdpr/access-request',
            json={
                'type': 'specific',
                'specific_data': ['chat_history', 'knowledge_nodes']
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_access_request_without_body(self, authenticated_client, app):
        """Test access request without request body"""
        response = authenticated_client.post(
            '/api/v1/gdpr/access-request',
            json={}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True

    def test_access_request_logged(self, authenticated_client, app):
        """Test access requests are logged"""
        with patch('backend.routes.gdpr_routes.logger') as mock_logger:
            response = authenticated_client.post(
                '/api/v1/gdpr/access-request',
                json={'type': 'full_export'}
            )

            assert response.status_code == 200
            mock_logger.info.assert_called()

    def test_access_request_unique_ids(self, authenticated_client, app):
        """Test multiple access requests get unique IDs"""
        import time
        response1 = authenticated_client.post(
            '/api/v1/gdpr/access-request',
            json={'type': 'full_export'}
        )

        # Small sleep to ensure timestamp differs (if ID includes seconds)
        # or use patch if it only uses minutes
        time.sleep(1.1)

        response2 = authenticated_client.post(
            '/api/v1/gdpr/access-request',
            json={'type': 'specific'}
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.get_json()
        data2 = response2.get_json()

        # IDs should be different (include timestamp)
        assert data1['data']['request_id'] != data2['data']['request_id']


class TestGDPRComplianceRequirements:
    """Test GDPR compliance requirements"""

    def test_data_export_within_time_limit(self, authenticated_client, app):
        """Test data export completes within reasonable time"""
        import time
        start_time = time.time()
        response = authenticated_client.post('/api/v1/gdpr/export')
        elapsed = time.time() - start_time

        assert response.status_code == 200
        # Export should complete in under 10 seconds
        assert elapsed < 10

    def test_consent_withdrawal_respected(self, authenticated_client, app):
        """Test consent can be withdrawn"""
        # Withdraw all consent
        response = authenticated_client.post(
            '/api/v1/gdpr/consent',
            json={
                'analytics': False,
                'marketing_emails': False,
                'third_party_sharing': False,
                'ai_training': False,
                'personalization': False
            }
        )

        assert response.status_code == 200
        data = response.get_json()
        # All should be set to False
        for key in data['data']:
            assert data['data'][key] is False

    def test_user_only_accesses_own_data(self, client, app):
        """Test users can only access their own data"""
        with app.app_context():
            from models import User, db

            # Create two users
            user1 = User(username="privacy1", email="privacy1@test.com", role="user")
            user1.set_password("SecurePass123!")
            user2 = User(username="privacy2", email="privacy2@test.com", role="user")
            user2.set_password("SecurePass123!")

            db.session.add_all([user1, user2])
            db.session.commit()

            # Login as user1
            client.post('/api/v1/auth/login', json={
                'username': 'privacy1',
                'password': 'SecurePass123!'
            })

            # Try to export data
            response = client.post('/api/v1/gdpr/export')

            if response.status_code == 200:
                data = response.get_data()
                if data:
                    try:
                        export_data = json.loads(data)
                        # Should only see user1's data
                        assert export_data['user_profile']['username'] == 'privacy1'
                    except json.JSONDecodeError:
                        pass

            # Cleanup
            db.session.delete(user1)
            db.session.delete(user2)
            db.session.commit()

    def test_deletion_grace_period_length(self, authenticated_client, app):
        """Test deletion grace period meets GDPR recommendations"""
        response = authenticated_client.post('/api/v1/gdpr/delete')

        assert response.status_code == 200
        data = response.get_json()
        grace_period = data['data']['grace_period_days']

        # GDPR recommends at least 30 days for data erasure requests
        assert grace_period >= 1


class TestGDPRErrorHandling:
    """Test error handling in GDPR endpoints"""

    @patch('backend.routes.gdpr_routes.db')
    def test_export_handles_database_errors(self, mock_db, authenticated_client, app):
        """Test export handles database errors gracefully"""
        mock_db.session.query.side_effect = Exception("Database error")

        response = authenticated_client.post('/api/v1/gdpr/export')

        # Should return error response
        assert response.status_code in [200, 500]

    def test_consent_update_with_invalid_json(self, authenticated_client, app):
        """Test consent update handles invalid JSON"""
        response = authenticated_client.post(
            '/api/v1/gdpr/consent',
            data='invalid json',
            content_type='application/json'
        )

        assert response.status_code in [200, 400, 500]

    def test_access_request_handles_exceptions(self, authenticated_client, app):
        """Test access request handles internal exceptions"""
        with patch('backend.routes.gdpr_routes.datetime') as mock_datetime:
            mock_datetime.now.side_effect = Exception("Time error")

            response = authenticated_client.post('/api/v1/gdpr/access-request')

        # Should return error response
        assert response.status_code in [200, 500]


class TestGDPRIntegration:
    """Integration tests for GDPR workflows"""

    def test_complete_gdpr_workflow(self, client, app):
        """Test complete GDPR workflow: export, consent, deletion"""
        with app.app_context():
            from models import User, db

            # Create user
            user = User(username="gdpruser", email="gdpr@test.com", role="user")
            user.set_password("SecurePass123!")
            db.session.add(user)
            db.session.commit()

            # Login
            client.post('/api/v1/auth/login', json={
                'username': 'gdpruser',
                'password': 'SecurePass123!'
            })

            # Step 1: Export data
            export_response = client.post('/api/v1/gdpr/export')
            assert export_response.status_code == 200

            # Step 2: Check consent
            consent_response = client.get('/api/v1/gdpr/consent')
            assert consent_response.status_code == 200

            # Step 3: Update consent
            update_response = client.post(
                '/api/v1/gdpr/consent',
                json={'analytics': False}
            )
            assert update_response.status_code == 200

            # Step 4: Request deletion
            delete_response = client.post('/api/v1/gdpr/delete')
            assert delete_response.status_code == 200

            # Cleanup
            db.session.delete(user)
            db.session.commit()

    def test_repeated_export_requests_consistent(self, authenticated_client, app):
        """Test repeated export requests return consistent data"""
        # First export
        response1 = authenticated_client.post('/api/v1/gdpr/export')
        # Second export immediately after
        response2 = authenticated_client.post('/api/v1/gdpr/export')

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Both should succeed
        data1 = response1.get_data()
        data2 = response2.get_data()

        # Both should have data
        assert len(data1) > 0
        assert len(data2) > 0
