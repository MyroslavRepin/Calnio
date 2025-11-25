import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Rate, Counter } from "k6/metrics";

// МЕТРИКИ
export const latency = new Trend("latency");
export const successRate = new Rate("success_rate");
export const failRate = new Rate("fail_rate");
export const requestCount = new Counter("request_count");

// НАСТРОЙКИ НАГРУЗКИ
export const options = {
    stages: [
        { duration: "10s", target: 5 },
        { duration: "20s", target: 20 },
        { duration: "30s", target: 50 },
        { duration: "20s", target: 20 },
        { duration: "10s", target: 0 },
    ],
    thresholds: {
        "success_rate": ["rate>0.95"],
        "latency": ["p(95)<400"],
    },
};

// ТЕСТИРУЕМЫЙ ЭНДПОИНТ
const API_URL = "https://calnio.com/";

// ОСНОВНОЙ ТЕСТ
export default function () {
    const res = http.get(API_URL);

    console.log(`Status: ${res.status}`);
    console.log(`Body length: ${res.body ? res.body.length : 0}`);

    const isSuccess = res.status === 200 || res.status === 201;
    successRate.add(isSuccess);
    failRate.add(!isSuccess);
    latency.add(res.timings.duration);
    requestCount.add(1);

    check(res, {
        "status is 200 or 201": (r) => r.status === 200 || r.status === 201,
        "body is not empty": (r) => r.body && r.body.length > 0,
    });

    sleep(0.01);
}