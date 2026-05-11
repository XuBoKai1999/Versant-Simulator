import os
import re
import asyncio
import edge_tts

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BANK_DIR = os.path.join(BASE_DIR, "bank")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")

VOICE = "en-US-JennyNeural"

BANK_FILES = {
#    "easy": "input_easy.txt",
    "medium": "input_medium.txt",
#    "hard": "input_hard.txt",
}


def clean_question(text: str) -> str:
    text = text.strip()

    # 移除開頭題號：1. / 2. / 10.
    text = re.sub(r"^\d+\.\s*", "", text)

    return text.strip()


def read_questions_from_file(file_path: str):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到題庫檔案：{file_path}")

    questions = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            q = clean_question(line)

            if q:
                questions.append(q)

    return questions


async def text_to_mp3(text: str, output_file: str):
    # 前面加停頓，避免第一個字被吃掉
    tts_text = "... " + text

    communicate = edge_tts.Communicate(tts_text, VOICE)
    await communicate.save(output_file)


async def build_level(level: str, txt_filename: str):
    txt_path = os.path.join(BANK_DIR, txt_filename)
    output_dir = os.path.join(AUDIO_DIR, level)

    os.makedirs(output_dir, exist_ok=True)

    questions = read_questions_from_file(txt_path)

    print(f"\n[{level}] 讀到 {len(questions)} 題")

    for i, question in enumerate(questions, start=1):
        output_file = os.path.join(output_dir, f"{level}_{i:04d}.mp3")

        print(f"轉換 {level}_{i:04d}: {question}")

        await text_to_mp3(question, output_file)

    print(f"[{level}] 完成")


async def main():
    for level, txt_filename in BANK_FILES.items():
        await build_level(level, txt_filename)

    print("\n全部音檔轉換完成")


if __name__ == "__main__":
    asyncio.run(main())