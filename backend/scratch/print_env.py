import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from config import settings
print("SETTINGS DATABASE_URL:", repr(settings.DATABASE_URL))
print("OS ENV DATABASE_URL:", repr(os.getenv("DATABASE_URL")))
