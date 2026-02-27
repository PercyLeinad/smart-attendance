# Alembic Migration Guide (FastAPI + SQLAlchemy + MySQL)

## 1️⃣ Initial Setup

### Install dependencies

``` bash
pip install alembic sqlalchemy pymysql python-dotenv
```

### Initialize Alembic

``` bash
alembic init alembic
```

This creates:

    alembic/
    alembic.ini

------------------------------------------------------------------------

## 2️⃣ Configure Database URL

### Option A --- Directly in `alembic.ini`

``` ini
sqlalchemy.url = mysql+pymysql://user:password@host/dbname
```

⚠️ Do NOT use quotes.

------------------------------------------------------------------------

### Option B --- Using `.env` (Recommended)

Create `.env` in project root:

    DATABASE_URL=mysql+pymysql://user:password@host/dbname

Then configure `alembic/env.py`:

``` python
import os
from pathlib import Path
from dotenv import load_dotenv
from alembic import context
from sqlalchemy import engine_from_config, pool

# Load .env from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

config = context.config

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env")

config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Import your Base
from app.models import Base  # Adjust to your project structure

target_metadata = Base.metadata
```

------------------------------------------------------------------------

## 3️⃣ Generate Initial Migration

``` bash
alembic revision --autogenerate -m "initial migration"
```

Then apply:

``` bash
alembic upgrade head
```

------------------------------------------------------------------------

## 4️⃣ Adding a New Column in Future

### Step 1 --- Modify your model

Example:

``` python
class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)  # NEW COLUMN
```

------------------------------------------------------------------------

### Step 2 --- Generate Migration

``` bash
alembic revision --autogenerate -m "add phone column to employees"
```

Alembic will detect:

    Detected added column 'employees.phone'

------------------------------------------------------------------------

### Step 3 --- Apply Migration

``` bash
alembic upgrade head
```

------------------------------------------------------------------------

## 5️⃣ Common Commands

### Show current version

``` bash
alembic current
```

### Show migration history

``` bash
alembic history
```

### Downgrade one revision

``` bash
alembic downgrade -1
```

### Downgrade to base

``` bash
alembic downgrade base
```

------------------------------------------------------------------------

## 6️⃣ Production Tips

-   Never delete migration files
-   Always commit migrations to Git
-   Use constraints (`UniqueConstraint`, `ForeignKey`) in models
-   Add `index=True` for frequently queried columns
-   Test migrations on staging before production

------------------------------------------------------------------------

## 7️⃣ Summary Workflow

### First Time

    alembic revision --autogenerate -m "initial"
    alembic upgrade head

### After Model Changes

    1. Modify models
    2. alembic revision --autogenerate -m "describe change"
    3. alembic upgrade head

------------------------------------------------------------------------

You now have a clean, repeatable Alembic migration workflow.
