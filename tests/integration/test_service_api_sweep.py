
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask

# Target modules
from backend.regulatory_api import regulatory_api
from backend.time_api import time_api
from backend.graphql_schema import register_graphql

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['AXIS_SYSTEM'] = MagicMock()
    app.config['DB_MANAGER'] = MagicMock()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.register_blueprint(regulatory_api, url_prefix='/regulatory')
    app.register_blueprint(time_api)
    register_graphql(app)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def mock_auth():
    # Mock current_user and check_api_auth to bypass decorators
    with patch("backend.auth.api_decorators.current_user") as mock_user:
        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_user.is_admin = True
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.role = "admin"
        
        # Also patch it in graphql_schema because it imports it directly
        with patch("backend.graphql_schema.current_user", mock_user):
            with patch("backend.auth.api_decorators.check_api_auth", return_value=(True, mock_user)):
                yield mock_user

class TestRegulatoryAPI:
    def test_get_frameworks(self, client, app):
        db_manager = app.config['DB_MANAGER']
        db_manager.get_nodes_by_properties.return_value = [{'uid': 'f1', 'name': 'Framework 1'}]
        
        # Now current_user should be accessible and auth bypassed
        response = client.get('/regulatory/frameworks?node_level=mega')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['count'] == 1

    def test_create_framework(self, client, app):
        axis_system = app.config['AXIS_SYSTEM']
        regulatory_manager = MagicMock()
        axis_system.axis_managers = {6: regulatory_manager}
        regulatory_manager.create_mega_framework.return_value = {'status': 'success', 'uid': 'new-f1'}
        
        with patch("backend.regulatory_api.api_admin_required", lambda x: x):
            response = client.post('/regulatory/frameworks', json={
                'name': 'New Mega Framework',
                'node_level': 'mega'
            })
            assert response.status_code == 201
            data = response.get_json()
            assert data['status'] == 'success'
            assert data['uid'] == 'new-f1'

    def test_get_octopus_structure(self, client, app):
        axis_system = app.config['AXIS_SYSTEM']
        regulatory_manager = MagicMock()
        axis_system.axis_managers = {6: regulatory_manager}
        regulatory_manager.get_octopus_structure.return_value = {
            'status': 'success', 
            'structure': {'mega': 'f1', 'arms': []}
        }
        
        with patch("backend.regulatory_api.api_login_required", lambda x: x):
            response = client.get('/regulatory/octopus/f1')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'structure' in data

class TestTimeAPI:
    @patch("backend.time_api.TimeContext")
    @patch("backend.time_api.db")
    def test_get_time_contexts(self, mock_db, mock_tc_class, client):
        mock_query = mock_db.session.query.return_value
        mock_tc = MagicMock()
        mock_tc.to_dict.return_value = {'uid': 't1', 'name': '2024'}
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_tc]
        
        response = client.get('/api/time?type=fiscal_year')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['count'] == 1

    @patch("backend.time_api.db.session")
    @patch("backend.time_api.uuid.uuid4")
    def test_create_time_context(self, mock_uuid, mock_session, client):
        mock_uuid.return_value = "fixed-uuid"
        
        payload = {
            'name': 'Test Month',
            'time_type': 'month',
            'start_date': '2024-01-01T00:00:00'
        }
        
        # We need to mock the TimeContext constructor or the instance it returns
        with patch("backend.time_api.TimeContext") as mock_tc_class:
            mock_tc_instance = mock_tc_class.return_value
            mock_tc_instance.to_dict.return_value = {'uid': 'fixed-uuid', 'name': 'Test Month'}
            
            response = client.post('/api/time', json=payload)
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True
            assert data['time_context']['uid'] == 'fixed-uuid'
            
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

class TestGraphQLAPI:
    def test_graphql_view_basic(self, client):
        # Test GET (Browser access)
        response = client.get('/graphql')
        assert response.status_code == 200
        assert "GraphQL API is running" in response.get_data(as_text=True)

    @patch("backend.graphql_schema.current_user")
    def test_me_query(self, mock_user, client):
        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.role = "admin"
        mock_user.is_admin = True
        
        response = client.post('/graphql', json={'query': '{ me { username email role isAdmin } }'})
        assert response.status_code == 200
        data = response.get_json()
        if 'data' not in data:
            pytest.fail(f"GraphQL Error: {data}")
        assert data['data']['me']['username'] == 'testuser'
        assert data['data']['me']['isAdmin'] is True

    @patch("extensions.db.session")
    @patch("uuid.uuid4")
    def test_create_simulation_mutation(self, mock_uuid, mock_session, client):
        mock_uuid.return_value = "sim-uuid"
        
        mutation = """
        mutation {
            createSimulation(name: "Test Sim", mode: "standard") {
                success
                simulation {
                    uid
                    name
                }
            }
        }
        """
        
        # Mock SimulationSession constructor
        with patch("models.SimulationSession") as mock_sim_class:
            mock_sim_instance = mock_sim_class.return_value
            mock_sim_instance.session_id = "sim-uuid"
            mock_sim_instance.name = "Test Sim"
            mock_sim_instance.status = "active"
            
            response = client.post('/graphql', json={'query': mutation})
            assert response.status_code == 200
            data = response.get_json()
            assert data['data']['createSimulation']['success'] is True
            assert data['data']['createSimulation']['simulation']['uid'] == "sim-uuid"

    @patch("backend.graphql_schema.schema.execute")
    def test_graphql_error_handling(self, mock_execute, client):
        mock_execute.return_value = MagicMock(data=None, errors=[Exception("GraphQL Error")])
        
        query = "{ nonExistentField }"
        response = client.post('/graphql', json={'query': query})
        assert response.status_code == 200
        data = response.get_json()
        assert 'errors' in data
        assert data['errors'][0]['message'] == "GraphQL execution failed"
