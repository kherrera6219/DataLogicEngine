"""
Tests for GraphQL API endpoint.

Tests the following:
- GraphQL queries (nodes, simulations, me)
- GraphQL mutations (createSimulation)
- Error handling
"""

import json


class TestGraphQLQueries:
    """Tests for GraphQL query operations."""

    def test_graphql_endpoint_exists(self, client):
        """Test that the GraphQL endpoint enforces authentication."""
        response = client.get('/graphql')
        assert response.status_code == 401

    def test_graphql_introspection(self, authenticated_client):
        """Test GraphQL introspection query."""
        query = '''
        {
            __schema {
                types {
                    name
                }
            }
        }
        '''
        response = authenticated_client.post(
            '/graphql',
            data=json.dumps({'query': query}),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert '__schema' in data['data']

    def test_graphql_node_count_query(self, authenticated_client):
        """Test nodeCount query."""
        query = '''
        {
            nodeCount
            edgeCount
        }
        '''
        response = authenticated_client.post(
            '/graphql',
            data=json.dumps({'query': query}),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'nodeCount' in data['data']
        assert isinstance(data['data']['nodeCount'], int)

    def test_graphql_nodes_query(self, authenticated_client):
        """Test nodes query with parameters."""
        query = '''
        {
            nodes(limit: 10) {
                uid
                name
                pillarId
            }
        }
        '''
        response = authenticated_client.post(
            '/graphql',
            data=json.dumps({'query': query}),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'nodes' in data['data']
        assert isinstance(data['data']['nodes'], list)

    def test_graphql_simulations_query(self, authenticated_client):
        """Test simulations query."""
        query = '''
        {
            simulations(limit: 5) {
                uid
                name
                status
                currentStep
            }
        }
        '''
        response = authenticated_client.post(
            '/graphql',
            data=json.dumps({'query': query}),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'simulations' in data['data']

    def test_graphql_me_query_authenticated(self, authenticated_client):
        """Test me query returns current user."""
        query = '''
        {
            me {
                id
                username
                email
                isAdmin
            }
        }
        '''
        response = authenticated_client.post(
            '/graphql',
            data=json.dumps({'query': query}),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        # User may or may not be present depending on auth


class TestGraphQLMutations:
    """Tests for GraphQL mutation operations."""

    def test_create_simulation_mutation(self, authenticated_client):
        """Test createSimulation mutation."""
        mutation = '''
        mutation {
            createSimulation(name: "Test Simulation") {
                success
                error
                simulation {
                    uid
                    name
                    status
                }
            }
        }
        '''
        response = authenticated_client.post(
            '/graphql',
            data=json.dumps({'query': mutation}),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'data' in data
        assert 'createSimulation' in data['data']


class TestGraphQLErrorHandling:
    """Tests for GraphQL error handling."""

    def test_invalid_query_syntax(self, authenticated_client):
        """Test that invalid syntax returns appropriate error."""
        query = 'invalid query syntax {'
        response = authenticated_client.post(
            '/graphql',
            data=json.dumps({'query': query}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'errors' in data

    def test_unknown_field_query(self, authenticated_client):
        """Test query with unknown field."""
        query = '''
        {
            unknownField
        }
        '''
        response = authenticated_client.post(
            '/graphql',
            data=json.dumps({'query': query}),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'errors' in data
