from prometheus_client import Counter, Histogram
import time

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path", "status"],
)

class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        path = self.normalize_path(request.path)
        
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method, path=path, status=response.status_code
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method, path=path, status=response.status_code
        ).observe(duration)
        
        return response

    def normalize_path(self, path):
        # Normalize paths with IDs, e.g., /api/users/123 -> /api/users/{id}
        import re
        path = re.sub(r'/\d+', '/{id}', path)
        return path
