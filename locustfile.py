from locust import HttpUser, task, between
import json
import random


# Pre-registered test users (regular role)
# Make sure these exist in your test database before running
TEST_USERS = [
    {"email": "regular1@test.com", "password": "testpassword"},
    {"email": "regular2@test.com", "password": "testpassword"},
    {"email": "regular3@test.com", "password": "testpassword"},
]

TEST_MESSAGES = [
    "I've been feeling really anxious lately.",
    "I can't sleep and I'm stressed about work.",
    "Today was a good day, I felt happy.",
    "I'm feeling overwhelmed with everything.",
    "I just need someone to talk to.",
    "I've been having negative thoughts recently.",
    "Things are getting better slowly.",
    "I don't know how to cope with this situation.",
]


class ChatbotUser(HttpUser):
    wait_time = between(1, 3)  # seconds between tasks
    token: str = ""
    session_id: str = ""

    def on_start(self):
        """Login and create a chat session before running tasks."""
        user = random.choice(TEST_USERS)

        # Login
        with self.client.post(
            "/api/v1/auth/login",
            json={"email": user["email"], "password": user["password"]},
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                self.token = response.json()["access_token"]
            else:
                response.failure(f"Login failed: {response.status_code}")
                return

        # Create a chat session
        with self.client.post(
            "/api/v1/chat/sessions",
            headers=self._auth_headers(),
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                self.session_id = response.json()["id"]
            else:
                response.failure(f"Session creation failed: {response.status_code}")

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    @task(10)
    def send_message(self):
        """Main task: send a message and measure response time."""
        if not self.session_id:
            return

        message = random.choice(TEST_MESSAGES)

        with self.client.post(
            f"/api/v1/chat/sessions/{self.session_id}/messages",
            headers=self._auth_headers(),
            json={"content": message},
            catch_response=True,
            # LLM can be slow — set a generous timeout
            timeout=30,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "assistant_message" not in data:
                    response.failure("Response missing assistant_message")
            else:
                response.failure(f"Send message failed: {response.status_code} {response.text}")

    @task(1)
    def list_sessions(self):
        """Low-frequency task: list sessions (baseline comparison)."""
        self.client.get(
            "/api/v1/chat/sessions",
            headers=self._auth_headers(),
        )
