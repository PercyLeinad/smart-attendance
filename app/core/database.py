from sqlalchemy import create_engine

DATABASE_IP = "10.0.0.200"
DATABASE_USER = "attendance"
DATABASE_PASSWORD = "attendance"
DATABASE_NAME = "attendance"

DATABASE_URL = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_IP}/{DATABASE_NAME}?charset=utf8mb4"

# Create the engine (handles connection pooling automatically)
engine = create_engine(DATABASE_URL, 
                       pool_pre_ping=True,
                       pool_recycle=3600
                       )
     