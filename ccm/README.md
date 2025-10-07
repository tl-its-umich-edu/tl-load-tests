## CCM Load Test

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
