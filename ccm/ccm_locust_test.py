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

class CanvasCourseManagerUser(HttpUser):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            with open(os.getenv("ENV_FILE", "env.hjson")) as f:
                ENV = hjson.load(f)
                logger.debug(ENV)
        except FileNotFoundError:
            raise RuntimeError("Default config file or one defined in environment variable ENV_FILE not found.")

        self.username = ENV.get("username")
        self.password = ENV.get("password")
        self.course_id = ENV.get("course_id")
        self.external_tool_id = ENV.get("external_tool") 
        self.lti_host = ENV.get("lti_host")
        self.lti = HttpSession(
            base_url=self.lti_host,
            request_event=self.environment.events.request,
            user=self
        ) 

        self.user_is_admin = ENV.get("user_is_admin", False)
        self.run_create_tasks = ENV.get("run_create_tasks", False)

        wait_time_values = ENV.get("wait_time", [1, 2])
        if len(wait_time_values) < 2:
            wait_time_values = [1, 2]
        self.wait_time = between(wait_time_values[0], wait_time_values[1])

    def on_start(self):
        self._canvas_login()
        self._lti_login()


    def _canvas_login(self):
        # login to the application
        response = self.client.get('login/canvas/')
        # Need to set this for Django
        self.client.headers['Referer'] = self.client.base_url

        # Get Authenticity token from the login page
        soup = BeautifulSoup(response.text, "html.parser")
        token_input = soup.find('input', {'name': 'authenticity_token'})
        if token_input is not None:
            token = token_input.get('value')
            # Post to the login form
            response = self.client.post('login/canvas/',
                                        {'pseudonym_session[unique_id]': self.username, 'pseudonym_session[password]': self.password,
                                         'authenticity_token': token})
        else:
            logger.error("Authenticity token input not found in login page.")
            raise RuntimeError("Authenticity token input not found in login page.")

    def _lti_login(self):
        # Access the LTI launch URL to start the LTI session
        response = self.lti.get(f"courses/{self.course_id}/external_tools/{self.external_tool_id}/", name="LTI Launch")
        if response.status_code != 200:
            logger.error(f"LTI launch failed with status code {response.status_code}")
            raise RuntimeError(f"LTI launch failed with status code {response.status_code}")

        if "sessionid" in response.cookies:
            self.lti.headers.update({"X-CSRFToken": response.cookies["sessionid"]})
            self.lti.cookies.set("csrftoken", response.cookies["sessionid"])
        else:
            logger.error("sessionid cookie not found after LTI launch.")
            raise RuntimeError("sessionid cookie not found after LTI launch.")

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
        self.lti.post("/api/admin/createExternalUsers", json=payload, name="createExternalUsers")

    @task(1)
    def get_admin_sections(self):
        """GET /api/admin/sections/"""
        if not self.user_is_admin:
            return
        params = {
            "term_id": random_term_id(),
            "course_name": "ENG101"
        }
        self.lti.get("/api/admin/sections/", params=params, name="get_admin_sections")

    # --- Course endpoints -----------------------------------------------------

    @task(2)
    def update_course(self):
        """PUT /api/course/{course_id}"""
        if not self.run_create_tasks:
            return
        course_id = random_course_id()
        payload = {"newName": f"UpdatedCourse-{course_id}"}
        self.lti.put(f"/api/course/{course_id}", json=payload, name="update_course")

    @task(2)
    def create_course_sections(self):
        """POST /api/course/{course_id}/sections"""
        if not self.run_create_tasks:
            return
        course_id = random_course_id()
        payload = {
            "sections": [f"Section-{i}" for i in range(random.randint(1, 3))]
        }
        self.lti.post(f"/api/course/{course_id}/sections", json=payload, name="create_course_sections")

    @task(2)
    def merge_sections(self):
        """POST /api/course/{course_id}/sections/merge"""
        if not self.run_create_tasks:
            return
        course_id = random_course_id()
        payload = {"sectionIds": [random_section_id() for _ in range(3)]}
        self.lti.post(f"/api/course/{course_id}/sections/merge", json=payload, name="merge_sections")

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
        self.lti.post(f"/api/course/{course_id}/sections/enroll", json=payload, name="enroll_in_multiple_sections")

    @task(1)
    def get_section_enrollments(self):
        """GET /api/sections/students"""
        ids = [random_section_id() for _ in range(3)]
        params = {"section_ids": ",".join(map(str, ids))}
        self.lti.get("/api/sections/students", params=params, name="get_section_enrollments")

    # --- Instructor endpoints -------------------------------------------------

    @task(1)
    def get_instructor_sections(self):
        """GET /api/instructor/sections"""
        params = {"term_id": random_term_id()}
        self.lti.get("/api/instructor/sections", params=params, name="get_instructor_sections")

    # --- General UI tasks ------------------------------------------------------
    @task(1)
    def view_ccm_home(self):
        response = self.client.get(f"courses/{self.course_id}/external_tools/{self.external_tool_id}/", name="view ccm home")
        fetch_static_assets(self, response)

    @task(1)
    def view_course(self):
        self.client.get(f"courses/{self.course_id}/", name="courses")