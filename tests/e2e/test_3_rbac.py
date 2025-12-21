import pytest

class TestRBAC:

    def test_anonymous_access_denied(self, client, anonymous_headers):
        """Anonymous users should be blocked from sensitive tools."""
        payload = {"arguments": {}}
        response = client.post("/tools/real-backup_create_backup", json=payload, headers=anonymous_headers)
        
        # Expect 403 (Forbidden) or 401 (Unauthorized)
        assert response.status_code in [401, 403]

    def test_viewer_cannot_access_admin_tools(self, client, viewer_headers):
        """Viewers should NOT be able to access Admin tools like Backup."""
        payload = {"arguments": {"service_name": "redis"}}
        response = client.post("/tools/real-backup_create_backup", json=payload, headers=viewer_headers)
        
        # Expect 403 Forbidden specifically
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    def test_viewer_cannot_access_code_review(self, client, viewer_headers):
        """Viewers should NOT be able to access Code Review (Operator/Admin only)."""
        payload = {"arguments": {"code": "print('hi')"}}
        response = client.post("/tools/code-review_analyze_code", json=payload, headers=viewer_headers)
        
        assert response.status_code == 403

    def test_admin_can_access_everything(self, client, admin_headers):
        """Admins should be able to access restricted tools."""
        payload = {"arguments": {"service_name": "test_service"}}
        response = client.post("/tools/real-backup_create_backup", json=payload, headers=admin_headers)
        
        # Should be allowed (200 OK)
        assert response.status_code == 200
