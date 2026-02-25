import sys
import os

# Ensure backend acts like a package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import models
from database import engine

print("Dropping all tables...")
models.Base.metadata.drop_all(bind=engine)
print("Creating all tables...")
models.Base.metadata.create_all(bind=engine)
print("Done!")
