import logging
from datetime import datetime

# Create a logger object
logger = logging.getLogger(__name__)

# Set the logging level (you can adjust this as needed)
logger.setLevel(logging.INFO)

# Create a file handler to log to a file (optional)
file_handler = logging.FileHandler(f'odis_{datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}.log')
file_handler.setLevel(logging.INFO)

# Create a console handler to log to the console (optional)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Define a formatter for log messages
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)
