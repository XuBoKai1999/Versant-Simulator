import os
import re
import asyncio
import edge_tts

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BANK_DIR = os.path.join(BASE_DIR, "bank")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")

VOICE_MALE = "en-US-GuyNeural"
VOICE_FEMALE = "en-US-JennyNeural"
VOICE_QUESTION = "en-US-JennyNeural"

BANK_FILES = {
    "easy": "input_easy.txt",
    "medium": "input_medium.txt",
    "hard": "input_hard.txt",
}


def split_items(content: str):
    return [item.strip() for item in re.split(r"\n\s*\n", content) if item.strip()]


def parse_item(item: str):
    lines = [line.strip() for line in item.splitlines() if line.strip()]

    segments = []
    question = None
    answer = None

    for line in lines:
        if line.startswith("Male:"):
            text = line.replace("Male:", "", 1).strip()
            segments.append(("male", text))

        elif line.startswith("Female:"):
            text = line.replace("Female:", "", 1).strip()
            segments.append(("female", text))

        elif line.startswith("Q:"):
            question = line.replace("Q:", "", 1).strip()

        elif line.startswith("A:"):
            answer = line.replace("A:", "", 1).strip()

        else:
            raise ValueError(f"格式錯誤：{line}")

    if not segments:
        raise ValueError(f"缺少對話：\n{item}")

    if not question:
        raise ValueError(f"缺少 Q:：\n{item}")

    if not answer:
        raise ValueError(f"缺少 A:：\n{item}")

    return {
        "segments": segments,
        "question": question,
        "answer": answer,
    }


def read_bank(file_path: str):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到題庫檔案：{file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return [parse_item(item) for item in split_items(content)]


def ensure_sentence_end(text: str):
    text = text.strip()

    if not text:
        raise ValueError("TTS 文字不可為空")

    if text[-1] not in ".!?":
        text += "."

    return text


async def tts_bytes(text: str, voice: str):
    text = ensure_sentence_end(text)

    communicate = edge_tts.Communicate(text, voice)
    data = b""

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            data += chunk["data"]

    if not data:
        raise RuntimeError(f"沒有收到音訊：{text}")

    return data


def get_voice(speaker: str):
    if speaker == "male":
        return VOICE_MALE
    if speaker == "female":
        return VOICE_FEMALE
    return VOICE_QUESTION


async def build_audio(question_data, output_file: str):
    """
    不用 pydub / ffmpeg。
    作法：
    - 每一句各自用 edge-tts 生成 bytes
    - 直接把 mp3 bytes 串接寫入同一個檔案
    - 不會念出 Male/Female/Q/A 標籤
    """

    with open(output_file, "wb") as f:
        for speaker, text in question_data["segments"]:
            voice = get_voice(speaker)
            f.write(await tts_bytes(text, voice))

        question_text = "Question. " + question_data["question"]
        f.write(await tts_bytes(question_text, VOICE_QUESTION))


async def build_level(level: str, filename: str):
    input_path = os.path.join(BANK_DIR, filename)
    output_dir = os.path.join(AUDIO_DIR, level)

    os.makedirs(output_dir, exist_ok=True)

    questions = read_bank(input_path)

    print(f"\n[{level}] 共 {len(questions)} 題")

    for i, q in enumerate(questions, start=1):
        output_file = os.path.join(output_dir, f"{level}_{i:04d}.mp3")

        print(f"生成 {level}_{i:04d}")
        await build_audio(q, output_file)

    print(f"[{level}] 完成")


async def main():
    for level, filename in BANK_FILES.items():
        await build_level(level, filename)

    print("\n全部 Part C 音檔轉換完成")


if __name__ == "__main__":
    asyncio.run(main())