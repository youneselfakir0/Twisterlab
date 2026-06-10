#!/usr/bin/env python3
"""
TwisterLab Agent Audit Script
Validates all agents are functional
"""
import asyncio
import sys
sys.path.insert(0, 'src')


async def audit():
    results = []
    
    # 1. Classifier
    try:
        from twisterlab.agents.real.real_classifier_agent import RealClassifierAgent
        agent = RealClassifierAgent()
        r = await agent.handle_classify('Computer slow')
        results.append(('Classifier', r.success, r.data.get('category', 'N/A') if r.data else 'N/A'))
    except Exception as e:
        results.append(('Classifier', False, str(e)[:30]))
    
    # 2. Sentiment
    try:
        from twisterlab.agents.real.real_sentiment_analyzer_agent import SentimentAnalyzerAgent
        agent = SentimentAnalyzerAgent()
        r = await agent.handle_analyze_sentiment('Frustrated!', False)
        results.append(('Sentiment', r.success, r.data.get('sentiment', 'N/A') if r.data else 'N/A'))
    except Exception as e:
        results.append(('Sentiment', False, str(e)[:30]))
    
    # 3. Resolver
    try:
        from twisterlab.agents.real.real_resolver_agent import RealResolverAgent
        agent = RealResolverAgent()
        r = await agent.handle_resolve('T-001', 'Fixed')
        results.append(('Resolver', r.success, 'OK'))
    except Exception as e:
        results.append(('Resolver', False, str(e)[:30]))
    
    # 4. Backup
    try:
        from twisterlab.agents.real.real_backup_agent import RealBackupAgent
        agent = RealBackupAgent()
        r = await agent.handle_backup('test')
        bid = r.data.get('backup_id', 'N/A')[:15] if r.data else 'N/A'
        results.append(('Backup', r.success, bid))
    except Exception as e:
        results.append(('Backup', False, str(e)[:30]))
    
    # 5. Browser
    try:
        from twisterlab.agents.real.browser_agent import RealBrowserAgent
        agent = RealBrowserAgent()
        r = await agent.handle_status()
        results.append(('Browser', r.success, r.data.get('available_engine', 'N/A') if r.data else 'N/A'))
    except Exception as e:
        results.append(('Browser', False, str(e)[:30]))
    
    # 6. Monitoring
    try:
        from twisterlab.agents.real.real_monitoring_agent import RealMonitoringAgent
        agent = RealMonitoringAgent()
        r = await agent.handle_collect_metrics()
        results.append(('Monitoring', r.success, 'OK' if r.success else 'FAIL'))
    except Exception as e:
        results.append(('Monitoring', False, str(e)[:30]))
    
    # 7. Desktop Commander
    try:
        from twisterlab.agents.real.real_desktop_commander_agent import RealDesktopCommanderAgent
        agent = RealDesktopCommanderAgent()
        # Use a whitelisted command
        r = await agent.handle_get_allowed_commands()
        results.append(('DesktopCmd', r.success, 'OK' if r.success else 'FAIL'))
    except Exception as e:
        results.append(('DesktopCmd', False, str(e)[:30]))
    
    # 8. Maestro
    try:
        from twisterlab.agents.real.real_maestro_agent import RealMaestroAgent
        agent = RealMaestroAgent()
        r = await agent.handle_orchestrate('list agents')
        results.append(('Maestro', r.success, 'OK' if r.success else r.error[:20] if r.error else 'FAIL'))
    except Exception as e:
        results.append(('Maestro', False, str(e)[:30]))
    
    # 9. Code Review
    try:
        from twisterlab.agents.real.real_code_review_agent import RealCodeReviewAgent
        agent = RealCodeReviewAgent()
        r = await agent.handle_analyze('def foo(): pass')
        results.append(('CodeReview', r.success, 'OK' if r.success else 'FAIL'))
    except Exception as e:
        results.append(('CodeReview', False, str(e)[:30]))
    
    print('=' * 60)
    print('🔍 AUDIT AGENTS TWISTERLAB - 16 Jan 2026')
    print('=' * 60)
    passed = 0
    for name, success, info in results:
        icon = '✅' if success else '❌'
        print(f'{icon} {name:15} | {info}')
        if success:
            passed += 1
    print('=' * 60)
    print(f'📊 RESULTAT: {passed}/{len(results)} agents fonctionnels')
    
    if passed == len(results):
        print('🎉 Tous les agents sont opérationnels!')
    else:
        print(f'⚠️  {len(results) - passed} agent(s) nécessitent attention')
    
    return passed, len(results)


if __name__ == '__main__':
    passed, total = asyncio.run(audit())
    sys.exit(0 if passed == total else 1)
