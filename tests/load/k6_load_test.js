import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '10s', target: 50 },
    { duration: '20s', target: 200 },
    { duration: '10s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<50'], // 95% of requests under 50ms (including mock)
    http_req_failed: ['rate<0.01'],    // less than 1% failure rate
  },
};

export default function () {
  const url = 'http://localhost:8000/v1/chat/completions';
  const payload = JSON.stringify({
    model: 'auto/coding',
    messages: [
      { role: 'user', content: 'Benchmark test prompt' },
    ],
    stream: false,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer cr_live_demo1234567890abcdef',
    },
  };

  const res = http.post(url, payload, params);
  check(res, {
    'status is 200': (r) => r.status === 200,
    'has choices': (r) => JSON.parse(r.body).choices.length > 0,
  });

  sleep(0.01);
}
