
from repositories.schemas.schema import Base
from Database.database import Database

class Migration:
    def __init__(self):
        self.db = Database()
    
    def create_tables(self):
        try:
            Base.metadata.create_all(bind=self.db.engine)
            print("✓ Database tables created successfully")
        except Exception as e:
            print(f"✗ Error creating tables: {str(e)}")
            raise e
    
    def drop_tables(self):
        try:
            Base.metadata.drop_all(bind=self.db.engine)
            print("✓ All tables dropped successfully")
        except Exception as e:
            print(f"✗ Error dropping tables: {str(e)}")
            raise e

    def run_startup_migration(self):
        """Run migrations on FastAPI startup"""
        self.create_tables()

if __name__ == "__main__":
    migration = Migration()
    migration.create_tables()
    
 