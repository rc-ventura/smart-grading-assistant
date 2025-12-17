from .agent import root_agent, grading_app

# Expose `app` for ADK when loading this package as an App
app = grading_app
