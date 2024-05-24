from app import flask_app, init_scheduler, update_data
import os
from app.shared import data

if __name__ == '__main__':
    scheduler = init_scheduler(flask_app)
    print("Initial data:", data)  # Should print the populated data dictionary
    flask_app.run(debug=True)
