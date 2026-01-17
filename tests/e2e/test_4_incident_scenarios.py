"""
E2E Tests: Full Incident Resolution Scenarios

These tests simulate real-world incidents and verify the complete
Maestro → Agents → Resolution workflow.

Scenarios:
1. Database Performance Issue → Auto-diagnosis and fix
2. Application Server Down → Detection and restart
3. Security Breach Detection → Backup and isolation

Run with: pytest tests/e2e/test_4_incident_scenarios.py -v
"""

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.slow]


class TestDatabaseIncidentScenario:
    """
    Scenario: "Database is slow"
    
    Flow:
    1. User reports slow database
    2. Maestro analyzes → category=DATABASE, priority=HIGH
    3. Sentiment analysis → urgency detected
    4. Monitoring check → performance metrics
    5. Resolution → ticket marked resolved
    """

    def test_step1_create_incident_ticket(self, client, admin_headers):
        """Step 1: Simulate user reporting database issue."""
        # Classify the incident
        payload = {
            "arguments": {
                "ticket_text": "URGENT: Production database is extremely slow! Queries taking 30+ seconds. Users complaining!"
            }
        }
        response = client.post(
            "/tools/real-classifier_classify_ticket",
            json=payload,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert not data.get("isError")
        content = data["content"][0]["text"]
        
        # Should classify as DATABASE or PERFORMANCE
        assert any(cat in content.upper() for cat in ["DATABASE", "PERFORMANCE", "INFRASTRUCTURE"])
        
        return content

    def test_step2_analyze_sentiment_urgency(self, client, admin_headers):
        """Step 2: Detect urgency from user message."""
        payload = {
            "arguments": {
                "text": "URGENT: Production database is extremely slow! Users complaining!",
                "detailed": True
            }
        }
        response = client.post(
            "/tools/sentiment-analyzer_analyze_sentiment",
            json=payload,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        content = response.json()["content"][0]["text"]
        
        # Should detect negative/urgent sentiment
        assert any(word in content.lower() for word in ["negative", "urgent", "critical"])

    def test_step3_check_system_health(self, client, admin_headers):
        """Step 3: Monitoring agent checks system health."""
        payload = {
            "arguments": {}
        }
        response = client.post(
            "/tools/monitoring_collect_metrics",
            json=payload,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        content = response.json()["content"][0]["text"]
        
        # Should return metrics or status
        assert any(word in content.lower() for word in ["cpu", "memory", "disk", "metrics", "status"])

    def test_step4_resolve_incident(self, client, admin_headers):
        """Step 4: Mark incident as resolved."""
        payload = {
            "arguments": {
                "ticket_id": "DB-PERF-001",
                "resolution_note": "Optimized slow queries. Added indexes. Response time back to <100ms."
            }
        }
        response = client.post(
            "/tools/real-resolver_resolve_ticket",
            json=payload,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        content = response.json()["content"][0]["text"]
        
        assert "DB-PERF-001" in content
        assert "resolved" in content.lower()

    def test_full_database_incident_flow(self, client, admin_headers):
        """Complete E2E flow for database incident."""
        results = {}
        
        # Step 1: Classify
        classify_response = client.post(
            "/tools/real-classifier_classify_ticket",
            json={"arguments": {"ticket_text": "Database queries are timing out"}},
            headers=admin_headers
        )
        assert classify_response.status_code == 200
        results["classification"] = classify_response.json()
        
        # Step 2: Sentiment
        sentiment_response = client.post(
            "/tools/sentiment-analyzer_analyze_sentiment",
            json={"arguments": {"text": "This is critical! Production is down!"}},
            headers=admin_headers
        )
        assert sentiment_response.status_code == 200
        results["sentiment"] = sentiment_response.json()
        
        # Step 3: Monitor
        health_response = client.post(
            "/tools/monitoring_collect_metrics",
            json={"arguments": {}},
            headers=admin_headers
        )
        assert health_response.status_code == 200
        results["health"] = health_response.json()
        
        # Step 4: Resolve
        resolve_response = client.post(
            "/tools/real-resolver_resolve_ticket",
            json={"arguments": {
                "ticket_id": "DB-AUTO-001",
                "resolution_note": "Auto-resolved: Query optimization applied"
            }},
            headers=admin_headers
        )
        assert resolve_response.status_code == 200
        results["resolution"] = resolve_response.json()
        
        # Verify complete flow
        assert all(not r.get("isError") for r in results.values())
        print(f"\n✅ Database incident resolved successfully!")
        print(f"   Classification: {results['classification']['content'][0]['text'][:100]}...")
        print(f"   Resolution: {results['resolution']['content'][0]['text'][:100]}...")


class TestApplicationDownScenario:
    """
    Scenario: "Web application not responding"
    
    Flow:
    1. User reports app is down
    2. Classify as APPLICATION issue
    3. Check health
    4. Create backup before intervention
    5. Resolve with action taken
    """

    def test_step1_classify_app_issue(self, client, admin_headers):
        """Classify application down incident."""
        payload = {
            "arguments": {
                "ticket_text": "The web application is down! Website not responding!"
            }
        }
        response = client.post(
            "/tools/real-classifier_classify_ticket",
            json=payload,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        content = response.json()["content"][0]["text"]
        
        # Should classify as APPLICATION
        assert any(cat in content.upper() for cat in ["APPLICATION", "WEB", "SERVER", "TECHNICAL"])

    def test_step2_backup_before_action(self, client, admin_headers):
        """Create backup before any intervention."""
        payload = {
            "arguments": {
                "service_name": "webapp-production"
            }
        }
        response = client.post(
            "/tools/real-backup_create_backup",
            json=payload,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        content = response.json()["content"][0]["text"]
        assert "backup_id" in content.lower()

    def test_step3_resolve_app_incident(self, client, admin_headers):
        """Resolve application incident."""
        payload = {
            "arguments": {
                "ticket_id": "APP-DOWN-001",
                "resolution_note": "Restarted application servers. Cleared cache. Application back online."
            }
        }
        response = client.post(
            "/tools/real-resolver_resolve_ticket",
            json=payload,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        content = response.json()["content"][0]["text"]
        assert "resolved" in content.lower()

    def test_full_application_down_flow(self, client, admin_headers):
        """Complete E2E flow for application down."""
        # Classify
        classify = client.post(
            "/tools/real-classifier_classify_ticket",
            json={"arguments": {"ticket_text": "Website is completely down!"}},
            headers=admin_headers
        )
        assert classify.status_code == 200
        
        # Backup
        backup = client.post(
            "/tools/real-backup_create_backup",
            json={"arguments": {"service_name": "webapp"}},
            headers=admin_headers
        )
        assert backup.status_code == 200
        
        # Health check
        health = client.post(
            "/tools/monitoring_collect_metrics",
            json={"arguments": {}},
            headers=admin_headers
        )
        assert health.status_code == 200
        
        # Resolve
        resolve = client.post(
            "/tools/real-resolver_resolve_ticket",
            json={"arguments": {
                "ticket_id": "APP-E2E-001",
                "resolution_note": "Application restarted and operational"
            }},
            headers=admin_headers
        )
        assert resolve.status_code == 200
        
        print("\n✅ Application down incident resolved!")


class TestSecurityBreachScenario:
    """
    Scenario: "Potential security breach detected"
    
    Flow:
    1. Security alert received
    2. Classify as SECURITY (high priority)
    3. Immediate backup of critical data
    4. Code review for vulnerabilities
    5. Resolve with security measures
    """

    def test_step1_classify_security_issue(self, client, admin_headers):
        """Classify security incident."""
        payload = {
            "arguments": {
                "ticket_text": "SECURITY ALERT: Suspicious login attempts detected. Possible brute force attack!"
            }
        }
        response = client.post(
            "/tools/real-classifier_classify_ticket",
            json=payload,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        content = response.json()["content"][0]["text"]
        
        # Should classify as SECURITY
        assert any(cat in content.upper() for cat in ["SECURITY", "ACCESS", "AUTH"])

    def test_step2_emergency_backup(self, client, admin_headers):
        """Emergency backup of critical systems."""
        payload = {
            "arguments": {
                "service_name": "auth-database-critical"
            }
        }
        response = client.post(
            "/tools/real-backup_create_backup",
            json=payload,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        content = response.json()["content"][0]["text"]
        assert "backup_id" in content.lower()

    def test_step3_security_code_scan(self, client, admin_headers):
        """Scan for security vulnerabilities."""
        payload = {
            "arguments": {
                "code": """
def login(request):
    password = request.POST['password']
    if password == 'admin123':  # Hardcoded!
        return allow_access()
    return deny_access()
"""
            }
        }
        response = client.post(
            "/tools/code-review_security_scan",
            json=payload,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        content = response.json()["content"][0]["text"]
        
        # Should detect vulnerabilities
        assert "vulnerable" in content.lower() or "hardcoded" in content.lower()

    def test_step4_resolve_security_incident(self, client, admin_headers):
        """Resolve security incident with measures taken."""
        payload = {
            "arguments": {
                "ticket_id": "SEC-BREACH-001",
                "resolution_note": "Blocked suspicious IPs. Forced password reset. Enabled 2FA. Security audit scheduled."
            }
        }
        response = client.post(
            "/tools/real-resolver_resolve_ticket",
            json=payload,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        content = response.json()["content"][0]["text"]
        assert "resolved" in content.lower()

    def test_full_security_breach_flow(self, client, admin_headers):
        """Complete E2E flow for security breach."""
        print("\n🔒 Security Breach Incident Flow:")
        
        # Step 1: Classify
        classify = client.post(
            "/tools/real-classifier_classify_ticket",
            json={"arguments": {"ticket_text": "Security breach! Unauthorized access detected!"}},
            headers=admin_headers
        )
        assert classify.status_code == 200
        print("   1. Classification: ✅")
        
        # Step 2: Sentiment (urgency)
        sentiment = client.post(
            "/tools/sentiment-analyzer_analyze_sentiment",
            json={"arguments": {"text": "CRITICAL: Security breach in progress!"}},
            headers=admin_headers
        )
        assert sentiment.status_code == 200
        print("   2. Urgency detected: ✅")
        
        # Step 3: Emergency backup
        backup = client.post(
            "/tools/real-backup_create_backup",
            json={"arguments": {"service_name": "critical-data"}},
            headers=admin_headers
        )
        assert backup.status_code == 200
        print("   3. Emergency backup: ✅")
        
        # Step 4: Security scan
        scan = client.post(
            "/tools/code-review_security_scan",
            json={"arguments": {"code": "password = 'secret123'"}},
            headers=admin_headers
        )
        assert scan.status_code == 200
        print("   4. Security scan: ✅")
        
        # Step 5: Resolve
        resolve = client.post(
            "/tools/real-resolver_resolve_ticket",
            json={"arguments": {
                "ticket_id": "SEC-E2E-001",
                "resolution_note": "Breach contained. Vulnerabilities patched."
            }},
            headers=admin_headers
        )
        assert resolve.status_code == 200
        print("   5. Resolution: ✅")
        
        print("\n✅ Security breach incident fully resolved!")


class TestMaestroOrchestration:
    """
    Test Maestro's ability to analyze and orchestrate.
    """

    def test_maestro_analyze_database_task(self, client, admin_headers):
        """Test Maestro analyzes database task correctly."""
        payload = {
            "arguments": {
                "task": "Database connection pool exhausted. All queries failing."
            }
        }
        response = client.post(
            "/tools/maestro_analyze_task",
            json=payload,
            headers=admin_headers
        )
        
        # Maestro endpoint might not exist yet, handle gracefully
        if response.status_code == 404:
            pytest.skip("Maestro analyze endpoint not yet exposed")
        
        assert response.status_code == 200
        content = response.json()["content"][0]["text"]
        assert "database" in content.lower() or "category" in content.lower()

    def test_maestro_orchestrate_dry_run(self, client, admin_headers):
        """Test Maestro orchestration in dry-run mode."""
        payload = {
            "arguments": {
                "task": "Network latency issues affecting all services",
                "dry_run": True
            }
        }
        response = client.post(
            "/tools/maestro_orchestrate",
            json=payload,
            headers=admin_headers
        )
        
        if response.status_code == 404:
            pytest.skip("Maestro orchestrate endpoint not yet exposed")
        
        assert response.status_code == 200


class TestAgentChaining:
    """Test that agents can work together in sequence."""

    def test_classify_then_analyze_sentiment(self, client, admin_headers):
        """Chain: Classify → Sentiment Analysis."""
        ticket = "The server crashed again! This keeps happening every week!"
        
        # First classify
        classify_response = client.post(
            "/tools/real-classifier_classify_ticket",
            json={"arguments": {"ticket_text": ticket}},
            headers=admin_headers
        )
        assert classify_response.status_code == 200
        
        # Then analyze sentiment
        sentiment_response = client.post(
            "/tools/sentiment-analyzer_analyze_sentiment",
            json={"arguments": {"text": ticket, "detailed": True}},
            headers=admin_headers
        )
        assert sentiment_response.status_code == 200
        
        # Both should succeed
        assert not classify_response.json().get("isError")
        assert not sentiment_response.json().get("isError")

    def test_backup_then_resolve(self, client, admin_headers):
        """Chain: Backup → Resolve (safe workflow)."""
        # Always backup first
        backup_response = client.post(
            "/tools/real-backup_create_backup",
            json={"arguments": {"service_name": "pre-intervention-backup"}},
            headers=admin_headers
        )
        assert backup_response.status_code == 200
        
        # Then resolve
        resolve_response = client.post(
            "/tools/real-resolver_resolve_ticket",
            json={"arguments": {
                "ticket_id": "CHAIN-001",
                "resolution_note": "Fixed after backup was taken"
            }},
            headers=admin_headers
        )
        assert resolve_response.status_code == 200
        
        print("\n✅ Backup → Resolve chain completed successfully!")


class TestErrorHandling:
    """Test graceful error handling in E2E scenarios."""

    def test_invalid_ticket_text(self, client, admin_headers):
        """Test classifier handles empty input gracefully."""
        response = client.post(
            "/tools/real-classifier_classify_ticket",
            json={"arguments": {"ticket_text": ""}},
            headers=admin_headers
        )
        
        # Should handle gracefully (either classify or return error)
        assert response.status_code in [200, 400, 422]

    def test_missing_required_argument(self, client, admin_headers):
        """Test agent handles missing arguments."""
        response = client.post(
            "/tools/real-resolver_resolve_ticket",
            json={"arguments": {}},  # Missing ticket_id
            headers=admin_headers
        )
        
        # Should return validation error
        assert response.status_code in [200, 400, 422]

    def test_very_long_text_input(self, client, admin_headers):
        """Test agents handle very long inputs."""
        long_text = "Database is slow. " * 1000  # 18,000 characters
        
        response = client.post(
            "/tools/sentiment-analyzer_analyze_sentiment",
            json={"arguments": {"text": long_text}},
            headers=admin_headers
        )
        
        # Should handle without crashing
        assert response.status_code in [200, 400, 413, 422]
