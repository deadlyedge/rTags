from typing import List
import srt
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from googletrans import Translator  # Import Google Translate API
from openai import OpenAI

from utils.ai_utils import get_perplexity_client  # Import Perplexity API


router = APIRouter()
translator = Translator()  # Initialize the Google Translate API client


async def translate_subtitle_part_google(
    text_to_translate: str, target_language: str
) -> List[str]:
    """使用 Google Translate API 翻译字幕文本的一部分。"""
    try:
        translated = await translator.translate(text_to_translate, dest=target_language)
        return translated.text.split("\n")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"与 Google Translate API 通信时出错: {e}"
        )


async def translate_subtitle_part_perplexity(
    perplexity_client: OpenAI,
    text_to_translate: str,
    target_language: str = "chinese",
) -> List[str]:
    """使用 Perplexity API 翻译字幕文本的一部分。"""
    prompt = f"请将以下字幕文本翻译成{target_language}，注意保持上下文的连贯性和情绪的准确性。\n\n{text_to_translate}"
    try:
        response = perplexity_client.chat.completions.create(
            model="sonar",  # 或其他你喜欢的模型
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )
        translated_text = response.choices[0].message.content or ""
        return translated_text.split("\n")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"与 Perplexity API 通信时出错: {e}"
        )


@router.post("", summary="翻译字幕文件")
async def translate_subtitle(
    file: UploadFile = File(...),
    target_language: str = "zh-cn",  # Default to Chinese
    split_threshold: int = 200,
    perplexity_client: OpenAI = Depends(get_perplexity_client),
):
    """
    将字幕文件 (.srt 或 .ass) 翻译成目标语言。
    """
    # 1. 验证文件类型
    if not file.filename or not file.filename.endswith((".srt")):
        raise HTTPException(status_code=400, detail="仅支持 .srt 文件")

    # 2. 解析字幕文件
    try:
        subs = list(srt.parse(file.file.read().decode("utf-8")))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析 SRT 文件时出错: {e}")

    # 3. 检查是否需要拆分
    if len(subs) > split_threshold:
        parts = [
            subs[i : i + split_threshold] for i in range(0, len(subs), split_threshold)
        ]
    else:
        parts = [subs]

    # 4. 翻译每个部分
    translated_parts = []
    for part in parts:
        # 提取文本内容
        text_to_translate = "\n".join([sub.content for sub in part])
        # translated_part = await translate_subtitle_part_perplexity(
        #     perplexity_client, text_to_translate, target_language
        # )
        translated_part = await translate_subtitle_part_google(
            text_to_translate, target_language
        )
        translated_parts.append(translated_part)

    # 5. 重新组合翻译后的字幕
    translated_subs = [
        srt.Subtitle(
            index=global_idx + 1,
            start=subs[global_idx].start,
            end=subs[global_idx].end,
            content=translated_line,
        )
        for part_idx, part in enumerate(translated_parts)
        for i, translated_line in enumerate(part)
        for global_idx in [part_idx * split_threshold + i]
    ]

    # 6. 生成翻译后的字幕文件并返回
    output = io.StringIO()
    output.write(srt.compose(translated_subs))
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=translated.srt"},
    )
