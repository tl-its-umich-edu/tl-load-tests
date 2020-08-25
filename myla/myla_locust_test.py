import logging, os, random

from bs4 import BeautifulSoup
import hjson
from locust import HttpUser, task, between

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
            print (f"Skipping: {url}")

    for url in set(resource_urls):
        #Note: If you are going to tag different static file paths differently,
        #this is where I would normally do that.
        session.client.get(url, name="(Static File)")

class UserActions(HttpUser):
    try:
        with open(os.getenv("ENV_FILE", "env.hjson")) as f:
            ENV = hjson.load(f)
            logger.debug(ENV)
    except FileNotFoundError:
        logger.info("Default config file or one defined in environment variable ENV_FILE not found. This is normal for the build, should define for operation.")
        # Default ENV to os.environ
        ENV = os.environ

    username= ENV.get("username")
    password = ENV.get("password")
    course = ENV.get("course")
    wait_time = between(ENV.get("wait_time")[0], ENV.get("wait_time")[1])

    @task
    def view_course_grades(self):
        self.client.get(f"courses/{self.course}/grades", name="grades")
        # Get the user default selection for resource
        self.client.get(f"api/v1/courses/{self.course}/get_user_default_selection/?default_type=grade")
        # Get the data for this view
        self.client.get(f"https://test-myla.tl.it.umich.edu/api/v1/courses/{self.course}/grade_distribution/")

    @task
    def view_course_resources(self):
        self.client.get(f"courses/{self.course}/resources", name="resources")
        # Get the user default selection for resource
        self.client.get(f"api/v1/courses/{self.course}/get_user_default_selection/?default_type=resource")
        # Get the data for this view
        self.client.get(f"api/v1/courses/{self.course}/resource_access_within_week/?week_num_start=1&week_num_end=17&grade=90-100&resource_type=Files")


    @task
    def view_course_assignmentsv1(self):
        self.client.get(f"courses/{self.course}/assignmentsv1", name="assignmentsv1")
        # Get the user default selection for assignment
        self.client.get(f"api/v1/courses/{self.course}/get_user_default_selection/?default_type=assignmentv1")
        # Get the data for this view
        self.client.get(f"api/v1/courses/{self.course}/assignments/?percent=10")

    @task
    def view_course(self):
        self.client.get(f"courses/{self.course}", name="courses")
    
    # Don't run this @task for now
    def view_course_assignments(self):
        self.client.get(f"courses/{self.course}/assignments", name="assignments")

    def on_start(self):
        self.login()

    def login(self):
        # login to the application
        response = self.client.get('accounts/login/')
        # Need to set this for Django
        self.client.headers['Referer'] = self.client.base_url
        response = self.client.post('accounts/login/',
                                    {'username': self.username, 'password': self.password,
                                     'csrfmiddlewaretoken': response.cookies['csrftoken']})
