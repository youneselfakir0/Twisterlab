import pytest

class TestRealAgents:

    def test_sentiment_analyzer(self, client, viewer_headers):
        """Test Sentiment Analysis (Viewer allowed)."""
        payload = {"arguments": {"text": "I love TwisterLab! It is the best."}}
        response = client.post("/tools/sentiment-analyzer_analyze_sentiment", json=payload, headers=viewer_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert not data.get("isError")
        
        # Verify result logic
        content = data["content"][0]["text"]
        assert "positive" in content.lower()

    def test_classifier_agent(self, client, viewer_headers):
        """Test Classification (Viewer allowed)."""
        payload = {"arguments": {"ticket_text": "I cannot login to the portal."}}
        response = client.post("/tools/real-classifier_classify_ticket", json=payload, headers=viewer_headers)
        
        assert response.status_code == 200
        content = response.json()["content"][0]["text"]
        assert "ACCESS" in content # Expecting ACCESS category

    def test_desktop_commander_agent(self, client, admin_headers):
        """Test Desktop Commander - list allowed commands (Admin required)."""
        payload = {
            "arguments": {}
        }
        response = client.post("/tools/real-desktop-commander_get_allowed_commands", json=payload, headers=admin_headers)
        
        assert response.status_code == 200
        content = response.json()["content"][0]["text"]
        
        # Should return list of allowed commands
        assert "commands" in content.lower() or "allowed" in content.lower() or "[" in content

    def test_resolver_agent(self, client, admin_headers):
        """Test Resolver (Admin required)."""
        payload = {
            "arguments": {
                "ticket_id": "T-999",
                "resolution_note": "Rebooted the server manually."
            }
        }
        response = client.post("/tools/real-resolver_resolve_ticket", json=payload, headers=admin_headers)
        
        assert response.status_code == 200
        content = response.json()["content"][0]["text"]
        assert "T-999" in content
        assert "resolved" in content.lower()

    def test_backup_agent(self, client, admin_headers):
        """Test Backup (Admin required)."""
        payload = {
            "arguments": {
                "service_name": "postgres_test_db"
            }
        }
        response = client.post("/tools/real-backup_create_backup", json=payload, headers=admin_headers)
        
        assert response.status_code == 200
        content = response.json()["content"][0]["text"]
        assert "backup_id" in content
