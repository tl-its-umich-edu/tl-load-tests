import logging, os, random

from bs4 import BeautifulSoup
import hjson #type: ignore[import-untyped]
from locust import HttpUser, task, between
from locust.clients import HttpSession

import random
import string

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def is_static_file(f):
    if "/sites/default/files" in f:
        return True
    else:
        return False

def fetch_static_assets(session, response):
    resource_urls = set()
    soup = BeautifulSoup(response.text, "html.parser")
 
    for res in soup.find_all(src=True):
        url = res['src']
        if is_static_file(url):
            resource_urls.add(url)
        else:
            logger.debug (f"Skipping: {url}")

    for url in set(resource_urls):
        #Note: If you are going to tag different static file paths differently,
        #this is where I would normally do that.
        session.client.get(url, name="(Static File)")


# --- Helper functions ---------------------------------------------------------

def random_email():
    return f"{''.join(random.choices(string.ascii_lowercase, k=6))}@example.com"

def random_name():
    return ''.join(random.choices(string.ascii_letters, k=8))

def random_term_id():
    return str(random.randint(1000, 9999))

def random_course_id():
    return random.randint(10000, 99999)

def random_section_id():
    return random.randint(10000, 99999)

try:
    with open(os.getenv("ENV_FILE", "env.hjson")) as f:
        ENV = hjson.load(f)
        logger.debug(ENV)
except FileNotFoundError:
    raise RuntimeError("Default config file or one defined in environment variable ENV_FILE not found.")

wait_time_values = ENV.get("wait_time", [1, 2])
if len(wait_time_values) < 2:
    wait_time_values = [1, 2]
logger.info("Setting wait time between %s and %s seconds", wait_time_values[0], wait_time_values[1])
wait_time = between(wait_time_values[0], wait_time_values[1])

class CanvasCourseManagerUser(HttpUser):

    wait_time = between(wait_time_values[0], wait_time_values[1])
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
 
        self.username = ENV.get("username")
        self.password = ENV.get("password")
        self.course_id = ENV.get("course_id")
        self.section_ids = ENV.get("section_ids", [])
        self.external_tool_id = ENV.get("external_tool") 

        self.user_is_admin = ENV.get("user_is_admin", False)
        self.run_create_tasks = ENV.get("run_create_tasks", False)

    def on_start(self):
        self._ccm_login()

    def _ccm_login(self):
        # login to the application
        response = self.client.get('admin/')

        # Login to the Django Admin page, need to provide a referrer
        self.client.headers['Referer'] = self.client.base_url + 'admin/login/'
        # Also need to provide a CSRF token 
        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
        self.client.cookies.set('csrftoken', csrf_token)

        response = self.client.post('admin/login/?next=/admin/', {'username': self.username, 'password': self.password, 'csrfmiddlewaretoken': csrf_token})
        if response.status_code != 200:
            logger.error("Failed to log in to Django admin.")
            raise RuntimeError("Failed to log in to Django admin.")

    # --- Admin endpoints ------------------------------------------------------

    @task(2)
    def create_external_users(self):
        """POST /api/admin/createExternalUsers"""
        if not self.user_is_admin and not self.run_create_tasks:
            return
        users = [
            {
                "email": random_email(),
                "givenName": random_name(),
                "surname": random_name(),
            }
            for _ in range(random.randint(1, 3))
        ]
        payload = {"users": users}
        self.client.post("/api/admin/createExternalUsers", json=payload, name="createExternalUsers")

    @task(1)
    def get_admin_sections(self):
        """GET /api/admin/sections/"""
        if not self.user_is_admin:
            return
        params = {
            "term_id": random_term_id(),
            "course_name": "ENG101"
        }
        self.client.get("/api/admin/sections/", params=params, name="get_admin_sections")

    # --- Course endpoints -----------------------------------------------------

    @task(2)
    def update_course(self):
        """PUT /api/course/{course_id}"""
        if not self.run_create_tasks:
            return
        course_id = random_course_id()
        payload = {"newName": f"UpdatedCourse-{course_id}"}
        self.client.put(f"/api/course/{course_id}", json=payload, name="update_course")

    @task(2)
    def create_course_sections(self):
        """POST /api/course/{course_id}/sections"""
        if not self.run_create_tasks:
            return
        course_id = random_course_id()
        payload = {
            "sections": [f"Section-{i}" for i in range(random.randint(1, 3))]
        }
        self.client.post(f"/api/course/{course_id}/sections", json=payload, name="create_course_sections")

    @task(2)
    def merge_sections(self):
        """POST /api/course/{course_id}/sections/merge"""
        if not self.run_create_tasks:
            return
        course_id = random_course_id()
        payload = {"sectionIds": [random_section_id() for _ in range(3)]}
        self.client.post(f"/api/course/{course_id}/sections/merge", json=payload, name="merge_sections")

    # --- Enrollment endpoints -------------------------------------------------

    @task(2)
    def enroll_in_multiple_sections(self):
        """POST /api/course/{course_id}/sections/enroll"""
        if not self.run_create_tasks:
            return
        course_id = random_course_id()
        enrollments = [
            {
                "sectionId": random_section_id(),
                "loginId": random_email(),
                "role": random.choice(["Student", "Teacher"]),
            }
            for _ in range(random.randint(1, 3))
        ]
        payload = {"enrollments": enrollments}
        self.client.post(f"/api/course/{course_id}/sections/enroll", json=payload, name="enroll_in_multiple_sections")

    @task(1)
    def get_section_enrollments(self):
        """GET /api/sections/students"""
        params = {"section_ids": ",".join(map(str, self.section_ids))}
        self.client.get("/api/sections/students", params=params, name="get_section_enrollments")

    # --- Instructor endpoints -------------------------------------------------

    @task(1)
    def get_instructor_sections(self):
        """GET /api/instructor/sections"""
        params = {"term_id": random_term_id()}
        self.client.get("/api/instructor/sections", params=params, name="get_instructor_sections")

    # --- General UI tasks ------------------------------------------------------
    @task(1)
    def view_ccm_home(self):
        response = self.client.get(f"/", name="view ccm home")
        fetch_static_assets(self, response)