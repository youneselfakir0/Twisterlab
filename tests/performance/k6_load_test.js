import http from 'k6/http';
import { check, sleep } from 'k6';

// Options correspondant aux SLA de la Phase 3.4 du TODO.md
export const options = {
  stages: [
    { duration: '30s', target: 50 },  // Ramp-up à 50 utilisateurs
    { duration: '4m', target: 100 },  // Plateau à 100 VU pendant 4 minutes
    { duration: '30s', target: 0 },   // Cool-down
  ],
  thresholds: {
    // SLA Validation (p95 < 1s, error rate < 1%)
    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.01'],   
  },
};

export default function () {
  // On utilise host.docker.internal si k6 est exécuté sous docker
  // Si K6 est natif, utiliser localhost ou l'IP k8s (ex: 192.168.0.30:30000)
  const url = __ENV.TARGET_URL || 'http://127.0.0.1:8000/api/health';
  
  const res = http.get(url);
  
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
  
  // Pause de 1 seconde entre chaque itération (simulateur comportemental simple)
  sleep(1);
}
