import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from locust import HttpUser, task, between

class PaymentAPIUser(HttpUser):
    wait_time = between(0.5, 2.0)
    def on_start(self):
        self.token = None
        self.client.verify = False
        resp = self.client.post("/api/v1/login", json={"username":"testuser","password":"testpass123","device_id":"LOAD-TEST"}, name="/api/v1/login")
        if resp.status_code == 200: self.token = resp.json().get("token","")

    @task(3)
    def check_balance(self):
        self.client.post("/api/v1/balance", json={"account_id":"1234567890123456","token":self.token or "x"}, name="/api/v1/balance")

    @task(2)
    def get_exchange_rates(self):
        self.client.get("/api/v1/exchange-rates", name="/api/v1/exchange-rates")

    @task(1)
    def make_transfer(self):
        self.client.post("/api/v1/transfer", json={"from_account":"1234567890123456","to_account":"9876543210987654","amount":500000,"currency":"VND","otp":"123456"}, name="/api/v1/transfer")

    @task(1)
    def health_check(self):
        self.client.get("/health", name="/health")
