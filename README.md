# otlp receiver

## setup

```bash
# run the fastapi receiver and the otel pipeline
docker-compose up -d --force-recreate --build

# start log triggering app (and visit endpoint)
source venv/bin/activate
pip install
python app.py
```
