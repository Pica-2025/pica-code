
import os
import time
import json
from openai import AsyncOpenAI
from typing import Dict, Optional
from pathlib import Path

from .wise_knowledge_v3 import get_wise_system_prompt_v3, KNOWLEDGE_VERSION

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("⚠️ OPENAI_API_KEY 未设置！请设置环境变量")

DEFAULT_WISE_MODEL = "gpt-5.2"
WISE_TEMPERATURE = 0
WISE_MAX_TOKENS = 1500
WISE_SEED = 14159265

async def analyze_prompt_with_wise_v3(
    original_prompt: str,
    target_filename: Optional[str] = None,
    model: str = DEFAULT_WISE_MODEL,
    verbose: bool = True
) -> Dict:
    if verbose:
        print(f"\n{'='*80}")
        print(f"[Wise v{KNOWLEDGE_VERSION} 分析]")
        if target_filename:
            print(f"目标图: {target_filename}")
        print(f"{'='*80}")
        print(f"原始提示词 ({len(original_prompt)}字):")
        print(f"  {original_prompt[:200]}{'...' if len(original_prompt) > 200 else ''}")
        print(f"使用模型: {model}")
        print(f"{'='*80}\n")

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    system_prompt = get_wise_system_prompt_v3()

    user_message = f"请分析以下提示词，按照规则输出恰好3个建议：\n\n【首轮提示词】\n{original_prompt}"

    start_time = time.time()

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=WISE_TEMPERATURE,
            max_completion_tokens=WISE_MAX_TOKENS,
            seed=WISE_SEED,
            response_format={"type": "json_object"}
        )

        response_time = time.time() - start_time

        content = response.choices[0].message.content
        result = json.loads(content)

        result["metadata"] = {
            "model": model,
            "response_time": round(response_time, 2),
            "knowledge_version": KNOWLEDGE_VERSION,
            "tokens_used": response.usage.total_tokens,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        if verbose:
            print(f"✓ Wise分析完成 (耗时 {response_time:.2f}秒)")
            print(f"✓ Tokens使用: {response.usage.total_tokens}")
            print(f"\n【Top 3 建议】")
            for i, sug in enumerate(result.get("top_3_suggestions", []), 1):
                print(f"{i}. [{sug['dimension']}] {sug['type']}: {sug['suggestion'][:80]}...")
            print(f"{'='*80}\n")

        return result

    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        print(f"原始响应: {content[:500]}...")
        raise
    except Exception as e:
        print(f"❌ Wise分析失败: {e}")
        raise

class WiseClient:

    def __init__(self, model: str = DEFAULT_WISE_MODEL):
        self.model = model

    async def get_wise_suggestions(self, prompt: str) -> list:
        try:
            result = await analyze_prompt_with_wise_v3(
                original_prompt=prompt,
                target_filename=None,
                model=self.model,
                verbose=True
            )

            suggestions = result.get("top_3_suggestions", [])

            enhanced_suggestions = []
            for sug in suggestions:
                enhanced_sug = {
                    "dimension": sug.get("dimension", ""),
                    "type": sug.get("type", ""),
                    "suggestion": sug.get("suggestion", ""),
                    "example": sug.get("example", "")
                }
                enhanced_suggestions.append(enhanced_sug)

            return enhanced_suggestions

        except Exception as e:
            print(f"❌ Wise 分析失败: {e}")
            raise

if __name__ == "__main__":
    import asyncio

    async def test():
        print("="*80)
        print("Wise Client v3.0 测试（异步版本）")
        print("="*80)

        test_prompt = "一幅山水画，有山有水"

        print("\n【测试用例: 缺失多个维度】")
        result = await analyze_prompt_with_wise_v3(
            original_prompt=test_prompt,
            verbose=True
        )

        print("\n【测试 WiseClient 接口】")
        client = WiseClient()
        suggestions = await client.get_wise_suggestions(test_prompt)
        print(f"获得 {len(suggestions)} 个建议:")
        for i, sug in enumerate(suggestions, 1):
            print(f"{i}. [{sug['type']}] {sug['dimension']}: {sug['suggestion']}")

        print("\n" + "="*80)
        print("测试完成！")

    asyncio.run(test())
