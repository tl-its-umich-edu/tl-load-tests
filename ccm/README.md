## CCM Load Test

### Pre-setup
This is the basic start of load tests for CCM. This has a few pre-setup requirements. 

1. The CCM Server that you'll want to test on needs to be setup on Canvas and added to a specific course id. This course and sections in the course need to be added to a env.hjson based on the env_sample.hjson.

2. A user needs to be created on the Canvas Server where this tool will be launched from. This load test currently uses a backdoor login to avoid going through the LTI workflow, but the user needs to get a token into the system.

So you need to create a local user in Canvas Then login or act as them, enroll them in the course and launch/authorize the development CCM tool to get them into the CCM database. 

Alternatively they can be created with the [load-testing-users](https://github.com/tl-its-umich-edu/load-testing-users) script.

3. Once this is done you'll need to change the password for this user in the CCM database. This is easiest done with an admin user in the Django UI.

4. Then fill in the rest of the env.hjson with the user name and password

5. Once this is done continue on to install the dependencies for this and continue.

TODOs:
* Support more than one unique login user. Probably reading users from a CSV style similar to load-testing-users.
* Fix all tests that are currently disabled (all create tasks are disabled)

### Run in venv
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
# or
venv\Scripts\activate      # Windows

### Install dependencies
pip install -r requirements.txt

### Create env
cp env_sample.hjson env.hjson

### Edit env
Open the env.hjson and edit as needed

### Start Load Test
./start_load_test.sh