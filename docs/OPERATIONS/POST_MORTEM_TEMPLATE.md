# Incident Post-Mortem Template

**Incident ID**: [e.g., INC-2025-001]  
**Date**: [YYYY-MM-DD]  
**Severity**: [P0 / P1 / P2 / P3]  
**Status**: [Draft / Under Review / Published]  
**Author(s)**: [Name(s)]  
**Reviewers**: [Name(s)]

---

## Executive Summary

[2-3 sentence summary of what happened, impact, and resolution]

**Example**: On December 10, 2025, the TwisterLab API experienced complete downtime for 45 minutes (10:15-11:00 UTC) affecting all users. The root cause was PostgreSQL connection pool exhaustion due to a code change that leaked connections. The issue was resolved by rolling back the deployment and implementing proper connection handling.

---

## Impact Assessment

### User Impact
- **Users Affected**: [Number or percentage]
- **Duration**: [Start time - End time (Total: X minutes)]
- **Geographic Region**: [All / Specific regions]
- **Services Affected**: [List affected services]

### Business Impact
- **Revenue Loss**: [Estimated amount, if applicable]
- **SLA Breach**: [Yes/No - Details]
- **Customer Complaints**: [Number]
- **Reputational Impact**: [High / Medium / Low]

### Technical Impact
- **Data Loss**: [Yes/No - If yes, amount]
- **Data Corruption**: [Yes/No - Details]
- **Configuration Changes**: [Yes/No - Details]

---

## Timeline (UTC)

| Time | Event | Action Taken | By Whom |
|------|-------|--------------|---------|
| 10:15 | Alert fired: API health check failing | - | Monitoring |
| 10:16 | On-call engineer acknowledged alert | Checked Grafana dashboards | John Doe |
| 10:18 | Identified database connection errors | Checked API logs | John Doe |
| 10:20 | Escalated to senior SRE | Paged senior on-call | John Doe |
| 10:25 | Root cause identified: connection leak | Reviewed recent deployments | Jane Smith |
| 10:30 | Decision to rollback | Initiated rollback procedure | Jane Smith |
| 10:35 | Rollback completed | Verified health checks | Jane Smith |
| 10:40 | Services recovering | Monitored metrics | Team |
| 10:45 | Full recovery confirmed | All health checks passing | Team |
| 11:00 | Incident closed | Documented in post-mortem | Team |

---

## Root Cause Analysis

### What Happened?

[Detailed technical explanation of the root cause]

**Example**: 
A code change introduced in deployment v2.5.0 added a new database query in the `/agents/list` endpoint. The developer forgot to use a context manager (async with) when creating the database session, causing connections to never be properly closed. Under normal load, this wasn't immediately apparent, but when a scheduled job started polling this endpoint every second, connections accumulated rapidly until the pool was exhausted.

### Why Did It Happen?

**Contributing Factors**:
1. [Factor 1 - e.g., Insufficient code review]
2. [Factor 2 - e.g., Lack of integration tests]
3. [Factor 3 - e.g., No connection pool monitoring alerts]

**Code Example** (if applicable):
```python
# Bad code (caused the incident)
async def list_agents():
    session = AsyncSessionLocal()  # ❌ No context manager
    result = await session.execute(select(Agent))
    return result.scalars().all()
    # ❌ Session never closed

# Fixed code
async def list_agents():
    async with AsyncSessionLocal() as session:  # ✅ Proper cleanup
        result = await session.execute(select(Agent))
        return result.scalars().all()
    # ✅ Session automatically closed
```

---

## What Went Well

[Things that worked as expected during the incident]

- [+] Monitoring detected the issue within 1 minute
- [+] On-call engineer responded immediately
- [+] Rollback procedure was well-documented and executed smoothly
- [+] Communication was clear and timely

---

## What Went Wrong

[Things that didn't work or could have been better]

- [-] Code review didn't catch the connection leak
- [-] No integration tests for connection handling
- [-] Connection pool monitoring was in place but not alerting
- [-] Staging environment didn't simulate production load patterns

---

## Action Items

### Immediate (Within 24 hours)
- [ ] **[P0]** Enable connection pool alerts - Assigned: @john-doe - Due: 2025-12-11
- [ ] **[P0]** Document rollback procedure in runbook - Assigned: @jane-smith - Due: 2025-12-11
- [ ] **[P0]** Add connection leak detection to CI - Assigned: @dev-team - Due: 2025-12-11

### Short-term (Within 1 week)
- [ ] **[P1]** Add integration tests for all database endpoints - Assigned: @dev-team - Due: 2025-12-17
- [ ] **[P1]** Implement pre-commit hook for connection handling - Assigned: @john-doe - Due: 2025-12-17
- [ ] **[P1]** Create load testing suite mimicking production - Assigned: @sre-team - Due: 2025-12-17

### Medium-term (Within 1 month)
- [ ] **[P2]** Implement circuit breaker for database connections - Assigned: @dev-team - Due: 2026-01-10
- [ ] **[P2]** Add automatic connection leak detection tool - Assigned: @sre-team - Due: 2026-01-10
- [ ] **[P2]** Enhance staging environment to match production - Assigned: @sre-team - Due: 2026-01-10

### Long-term (Within 1 quarter)
- [ ] **[P3]** Implement chaos engineering for connection failures - Assigned: @sre-team - Due: 2026-03-10
- [ ] **[P3]** Create automated remediation for common failures - Assigned: @sre-team - Due: 2026-03-10

---

## Lessons Learned

### Technical Lessons
1. **Always use context managers for database sessions**  
   Context managers ensure resources are properly cleaned up even if exceptions occur.

2. **Load testing should simulate production patterns**  
   Staging environment should include scheduled jobs and background tasks.

3. **Monitor connection pool utilization actively**  
   Alert when pool utilization exceeds 70%, not just when exhausted.

### Process Lessons
1. **Code review checklist should include resource management**  
   Reviewers should specifically look for proper cleanup of connections, files, etc.

2. **Integration tests should cover resource cleanup**  
   Tests should verify connections are closed after operations.

3. **Runbook should be tested regularly**  
   Monthly drills to ensure procedures are up-to-date and team is familiar.

---

## Prevention Measures

### Code-Level Prevention
```python
# Add linter rule to detect missing context managers
# ruff.toml
[tool.ruff.lint]
select = ["ASYNC101"]  # Detect async resource leaks

# Add pre-commit hook
# .pre-commit-config.yaml
- id: check-async-resources
  name: Check for async resource leaks
  entry: python scripts/check_async_resources.py
```

### Infrastructure-Level Prevention
```yaml
# Add connection pool monitoring
# k8s/monitoring/prometheus/alerts.yaml
- alert: PostgreSQLConnectionPoolHigh
  expr: pg_stat_database_numbackends / pg_settings_max_connections > 0.7
  for: 5m
  annotations:
    summary: "PostgreSQL connection pool utilization > 70%"
```

### Process-Level Prevention
- Mandatory load testing before production deployment
- Code review checklist updated with resource management checks
- Monthly incident response drills

---

## Follow-up

### Review Meeting
- **Date**: [YYYY-MM-DD]
- **Attendees**: [List of attendees]
- **Action Items Reviewed**: [Yes/No]
- **Process Changes Approved**: [Yes/No]

### Tracking
- **JIRA Epic**: [LINK]
- **Action Items**: [Number completed / Total]
- **Target Completion**: [YYYY-MM-DD]

---

## Appendices

### Appendix A: Relevant Logs

```
[2025-12-10 10:15:23] ERROR: Database connection pool exhausted
[2025-12-10 10:15:24] ERROR: psycopg2.pool.PoolError: connection pool exhausted
[2025-12-10 10:15:25] ERROR: HTTPException: 503 Service Unavailable
```

### Appendix B: Metrics Screenshots

[Attach relevant Grafana/monitoring screenshots]

### Appendix C: Code Changes

**Problematic Code**:
- Commit: `abc123def`
- PR: `#456`
- Files: `src/twisterlab/api/routes/agents.py`

**Fix Code**:
- Commit: `xyz789ghi`
- PR: `#457`
- Files: `src/twisterlab/api/routes/agents.py`

---

## References

- [TwisterLab Runbook](./RUNBOOK.md)
- [Incident Response Procedure](./INCIDENT_RESPONSE.md)
- [Database Session Management Best Practices](../../.github/copilot-instructions.md#database--async-patterns)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-10 | Jane Smith | Initial draft |
| 1.1 | 2025-12-11 | John Doe | Added code examples |
| 2.0 | 2025-12-12 | Team | Final review and approval |

---

**Status**: [Draft / Under Review / Published]  
**Next Review**: [YYYY-MM-DD]  
**Approvers**: [Name, Name]

---

## Template Usage Instructions

1. **Create new post-mortem**: Copy this template immediately after incident resolution
2. **Draft within 24 hours**: Complete initial draft with timeline and root cause
3. **Review within 48 hours**: Team review and action item assignment
4. **Publish within 72 hours**: Final approved version shared with stakeholders
5. **Follow-up monthly**: Track action item completion

**Principles**:
- **Blameless**: Focus on systems and processes, not individuals
- **Honest**: Be transparent about what went wrong
- **Actionable**: Every lesson should have a concrete action item
- **Timely**: Complete while incident is fresh in memory

---

**Template Version**: 1.0  
**Last Updated**: 2025-12-10  
**Maintained By**: SRE Team
