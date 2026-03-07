
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from models import Base
    Base.metadata.create_all(bind=engine)
    print("✓ 数据库表结构已创建")

def reset_db():
    from models import Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("⚠️  数据库已重置（所有数据已清空）")

def check_db_connection():
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("✓ 数据库连接正常")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("数据库配置测试")
    print("=" * 50)

    print(f"\n数据库URL: {DATABASE_URL}")

    if check_db_connection():
        print("\n✅ 数据库配置正确！")
    else:
        print("\n❌ 数据库配置有误，请检查！")
