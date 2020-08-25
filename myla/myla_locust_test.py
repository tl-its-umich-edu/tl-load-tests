import json, logging, os, random
from locust import HttpUser, task, between
from bs4 import BeautifulSoup

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
            print (f"Skipping: {url}")

    for url in set(resource_urls):
        #Note: If you are going to tag different static file paths differently,
        #this is where I would normally do that.
        session.client.get(url, name="(Static File)")

class UserActions(HttpUser):
    try:
        with open(os.getenv("ENV_FILE", "env.hjson")) as f:
            ENV = json.load(f)
    except FileNotFoundError as fnfe:
        logger.info("Default config file or one defined in environment variable ENV_FILE not found. This is normal for the build, should define for operation.")
        # Default ENV to os.environ
        ENV = os.environ

    username= ENV.get("username")
    password = ENV.get("password")
    course = ENV.get("course")
    wait_time = between(ENV.get("wait")[0], ENV.get("wait")[1])

    @task
    def view_course_grades(self):
        self.client.get(f"/courses/{self.course}/grades", name="grades")

    @task
    def view_course_resources(self):
        self.client.get(f"/courses/{self.course}/resources", name="resources")

    @task
    def view_course_assignments(self):
        self.client.get(f"/courses/{self.course}/assignments", name="assignments")

    @task
    def view_course_assignmentsv1(self):
        self.client.get(f"/courses/{self.course}/assignmentsv1", name="assignmentsv1")

    @task
    def view_course(self):
        self.client.get(f"/courses/{self.course}", name="courses")

    def on_start(self):
        self.login()

    def login(self):
        # login to the application
        response = self.client.get('/accounts/login/')
        csrftoken = response.cookies['csrftoken']
        self.client.post('/accounts/login/',
                         {'username': self.username, 'password': self.password}, 
                         headers={'X-CSRFToken': csrftoken})