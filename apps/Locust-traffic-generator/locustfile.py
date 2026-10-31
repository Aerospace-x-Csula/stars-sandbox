from locust import HttpUser, task, between

class NormalUser(HttpUser):
    """Steady, human-paced traffic. No errors."""
    wait_time = between(1, 3)

    @task(3)
    def homepage(self):
        self.client.get("/", name="homepage")

    @task(2)
    def list_items(self):
        self.client.get("/get", name="list_items")

class HighTrafficUser(HttpUser):
    """Same requests as NormalUser, but nearly back to back.
    Run this with a high user count."""
    wait_time = between(0.05, 0.3)

    @task(3)
    def homepage(self):
        self.client.get("/", name="homepage")

    @task(2)
    def list_items(self):
        self.client.get("/get", name="list_items")

class FailingUser(HttpUser):
    """Generates errors."""
    wait_time = between(0.5, 2)

    @task(2)
    def server_error(self):
        self.client.get("/status/500", name="server_error")

    @task(1)
    def missing_page(self):
        self.client.get("/does-not-exist", name="missing_page")