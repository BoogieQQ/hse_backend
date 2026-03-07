import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '1m', target: 50 },
    { duration: '30s', target: 100 },
    { duration: '1m', target: 50 },
    { duration: '30s', target: 0 },
  ]
};

const BASE_URL = 'http://localhost:8003';

const testCases = [
  { item_id: 1 },
  { item_id: 100 },
  { item_id: 1000 },      
  { item_id: 1_000_000 }
];

export default function () {
  const testCase = testCases[Math.floor(Math.random() * testCases.length)];
  
  const payload = JSON.stringify({
    item_id: testCase.item_id,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const simplePredictRes = http.post(`${BASE_URL}/simple_predict`, payload, params);
  
  const simpleCheckSuccess = check(simplePredictRes, {
    'simple_predict status is 200': (r) => r.status === 200,
    'simple_predict has valid response structure': (r) => {
      const body = JSON.parse(r.body);
      return body.hasOwnProperty('is_violation') && 
             body.hasOwnProperty('probability') &&
             body.probability >= 0 && 
             body.probability <= 1;
    },
  });

  sleep(0.1);

  // Несуществующая ручка
  if (Math.random() < 0.1) {
    const badPath =  http.get(`${BASE_URL}/simple_predict123`);
    
    const randomCheckSuccess = check(badPath, {
      'random endpoint returns 404': (r) => r.status === 404,
    });
    
    if (!randomCheckSuccess) {
      errorRate.add(1);
    }
    
    sleep(0.1);
  }

  // Несуществующий id
  if (Math.random() < 0.1) {
    const payload = JSON.stringify({
        item_id: -1,
    });

    const simplePredictRes = http.post(`${BASE_URL}/simple_predict`, payload, params);

    const simpleCheckSuccess = check(simplePredictRes, {
        'simple_predict status is 400': (r) => r.status === 400
      });
    
    sleep(0.1);
  }

  // Плохой тип
  if (Math.random() < 0.1) {
    const payload = JSON.stringify({
        item_id: 'asdasdasd',
    });

    const simplePredictRes = http.post(`${BASE_URL}/simple_predict`, payload, params);

    const simpleCheckSuccess = check(simplePredictRes, {
        'simple_predict returns 422 for invalid type': (r) => r.status === 422
      });
    
    sleep(0.1);
  }

  sleep(Math.random() * 2 + 1);
}