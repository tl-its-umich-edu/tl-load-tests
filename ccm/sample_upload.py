from locust import HttpUser, task, between
import io
import csv
import random
import string

def generate_random_csv(num_rows=10):
    """
    Generate a CSV in memory with random data.
    Returns a BytesIO object ready for upload.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header row
    writer.writerow(["id", "name", "score"])

    # Write random rows
    for i in range(num_rows):
        random_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        random_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        random_score = random.randint(0, 100)
        writer.writerow([random_id, random_name, random_score])

    # Reset cursor and return as file-like object
    output.seek(0)
    return io.BytesIO(output.getvalue().encode("utf-8"))

class LtiUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        """
        Called when a simulated user starts.
        Here you could do LTI login / auth if needed.
        """
        # Example: do login or simulate LTI launch
        # self.client.post("/lti/launch", data={...})
        pass

    @task
    def upload_csv(self):
        """
        Generate and upload a random CSV.
        """
        csv_file = generate_random_csv(num_rows=20)
        files = {"file": ("random.csv", csv_file, "text/csv")}
        response = self.client.post("/upload_csv/", files=files)

        if response.status_code != 200:
            print(f"Upload failed: {response.status_code} {response.text[:200]}")

