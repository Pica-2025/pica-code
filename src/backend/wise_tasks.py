
import traceback
from typing import Optional
from sqlalchemy.orm import Session

async def generate_wise_suggestions_task(
    version_id: str,
    prompt: str,
    db_session: Optional[Session] = None
):
    from database import SessionLocal
    from crud import get_version_by_id

    if db_session is None:
        db = SessionLocal()
        should_close = True
    else:
        db = db_session
        should_close = False

    try:
        print(f"\n{'='*80}")
        print(f"[Wise分析任务开始]")
        print(f"  version_id: {version_id}")
        print(f"  prompt: {prompt[:100]}...")
        print(f"{'='*80}\n")

        version = get_version_by_id(db, version_id)
        if not version:
            print(f"❌ 版本不存在: {version_id}")
            return

        from wise.wise_client_v3 import analyze_prompt_with_wise_v3

        print(f"🤖 开始调用Wise分析...")
        result = await analyze_prompt_with_wise_v3(
            original_prompt=prompt,
            target_filename=None,
            verbose=True
        )

        suggestions = result.get("top_3_suggestions", [])

        print(f"\n✅ Wise分析完成")
        print(f"  建议数量: {len(suggestions)}")
        for i, sug in enumerate(suggestions, 1):
            print(f"  建议{i}: [{sug['type']}] {sug['dimension']} - {sug['suggestion'][:50]}...")

        version.wise_suggestions = suggestions
        version.wise_generated = True
        version.wise_error = None

        db.commit()
        print(f"\n💾 Wise建议已保存到数据库")
        print(f"{'='*80}\n")

    except Exception as e:
        error_msg = str(e)
        print(f"\n{'='*80}")
        print(f"[Wise分析失败]")
        print(f"  错误: {error_msg}")
        traceback.print_exc()
        print(f"{'='*80}\n")

        try:
            version = get_version_by_id(db, version_id)
            if version:
                version.wise_suggestions = None
                version.wise_generated = True
                version.wise_error = error_msg
                db.commit()
                print(f"💾 错误信息已保存到数据库")
        except:
            pass

    finally:
        if should_close:
            db.close()
