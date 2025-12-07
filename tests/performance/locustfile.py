try:  # pragma: no cover - optional dependency
    from locust import HttpUser, task, between
except ImportError:  # pragma: no cover - keep pytest happy without locust
    HttpUser = object

    def task(func):
        return func

    def between(*_args, **_kwargs):
        return lambda: None


class BasicUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def load_homepage(self):
        # This method is invoked by Locust when installed; placeholder for CI scaffolding
        if hasattr(self, "client"):
            self.client.get("/")
