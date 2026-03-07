import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "src" / "backend"
sys.path.insert(0, str(backend_path))

from database import engine, Base, SessionLocal
from models import User, Session, Task, ImageVersion, Rating
from auth import hash_password

def init_database():
    print("正在创建数据库表...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✓ 数据库表创建完成")

def create_test_users():
    db = SessionLocal()
    try:
        print("\n正在创建测试用户...")

        admin = User(
            user_id="admin",
            password_hash=hash_password("admin123"),
            role="admin"
        )
        db.add(admin)

        for i in range(1, 11):
            user = User(
                user_id=f"test{i:03d}",
                password_hash=hash_password("password123"),
                role="tester"
            )
            db.add(user)

        db.commit()
        print("✓ 测试用户创建完成")
        print("\n可用账号：")
        print("  管理员: admin / admin123")
        print("  测试者: test001 ~ test010 / password123")

    except Exception as e:
        print(f"✗ 创建用户失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("="*60)
    print("Pica 数据库初始化")
    print("="*60)

    init_database()
    create_test_users()

    print("\n" + "="*60)
    print("初始化完成！")
    print("="*60)
