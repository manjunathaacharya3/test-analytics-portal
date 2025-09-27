# test-analytics-portal

#### Command to start Dash frontend

`
python ui/dashboard.py
`

#### Command to start uvicorn backend

`python -m uvicorn service.main:app --reload --host 0.0.0.0 --port 8000
`