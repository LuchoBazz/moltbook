pip3 cache purge
python3 -m venv cache_venv
source cache_venv/bin/activate
pip install -r requirements.txt


pip freeze > requirements.txt
