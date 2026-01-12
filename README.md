# test-analytics-portal

`
git clone <url>
`
`
python -m venv venv
`
`
naviaget venv -> Scripts -> activate
`
`
pip install -r requirements.txt
`

#### Command to start Dash frontend

`
python ui/dashboard.py
`

#### Command to start uvicorn backend

`python -m uvicorn service.main:app --reload --host 0.0.0.0 --port 8000
`

![img.png](mockup/projects_page.png)

![img_1.png](mockup/execution_summary.png)

![img_2.png](mockup/trends.png)

![img_3.png](mockup/module_details.png)

![img_4.png](mockup/defect_management.png)

![img_5.png](mockup/ai_analysis.png)

![img_6.png](mockup/settings.png)
