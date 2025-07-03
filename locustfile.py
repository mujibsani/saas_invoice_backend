from locust import HttpUser, task, between
import random
import json

class AuthenticatedUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Log in and get JWT token before running tasks."""
        response = self.client.post("/api/token/", json={
            "username": "sojol",
            "password": "Sojol123456789"
        })
        if response.status_code == 200:
            self.token = response.json()["access"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task
    def list_expenses(self):
        self.client.get("/api/users/expenses/", headers=self.headers)

    @task
    def list_invoices(self):
        self.client.get('/api/users/invoices/', headers=self.headers)
        
    @task
    def get_invoices_detail(self):
        self.client.get('/api/users/invoices/1/', headers=self.headers)
        
    @task
    def update_invoice(self):
        data = {
            'Status': 'paid',
        }
        self.client.put('/api/users/invoices/1/', headers=self.headers, json=data)
        
    

    # @task, he
    # def create_expense(self):
    #     data = {
    #         "amount": round(random.uniform(10.0, 500.0), 2),
    #         "category": random.choice(["travel", "office", "marketing"]),
    #         "date": "2025-04-06"
    #     }
    #     self.client.post("/api/users/expenses/", headers=self.headers, json=data)

    # @task
    # def get_expense_detail(self):
    #     # Replace `1` with a valid expense ID in your DB or mock this
    #     self.client.get("/api/users/expenses/1/", headers=self.headers)

    # @task
    # def update_expense(self):
    #     data = {
    #         "amount": 199.99,
    #         "category": "updated-category",
    #     }
    #     self.client.put("/api/users/expenses/1/", headers=self.headers, json=data)

    # @task
    # def approve_expense(self):
    #     # Only works for admin accounts and valid expense_id
    #     data = {"approval_status": "approved"}
    #     self.client.post("/api/users/expenses/1/approve/", headers=self.headers, json=data)
