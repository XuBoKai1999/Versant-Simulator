import os
import re
import asyncio
import edge_tts

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BANK_DIR = os.path.join(BASE_DIR, "bank")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")

VOICE = "en-US-JennyNeural"

BANK_FILES = {
    "easy": "input_easy.txt",
    "medium": "input_medium.txt",
    "hard": "input_hard.txt",
}


def clean_line(line: str):
    line = line.strip()
    line = re.sub(r"^\d+\.\s*", "", line)
    return line


def parse_question_line(line: str):
    line = clean_line(line)

    if not line:
        return None

    if "|" not in line:
        raise ValueError(f"格式錯誤（缺少 |）：{line}")

    answer_part, chunk_part = line.split("|", 1)

    answer = answer_part.strip()

    chunks = [
        c.strip()
        for c in chunk_part.split("/")
        if c.strip()
    ]

    if len(chunks) < 2:
        raise ValueError(f"chunk 太少（至少2個）：{line}")

    return {
        "answer": answer,
        "chunks": chunks,
    }


def read_bank(file_path):
    questions = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            parsed = parse_question_line(line)
            if parsed:
                questions.append(parsed)

    return questions


def build_spoken_text(chunks):
    # chunk 間加入停頓（用 ...）
    return " ... ".join(chunks)


async def text_to_mp3(text, output_file):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_file)


async def build_level(level, filename):
    input_path = os.path.join(BANK_DIR, filename)
    output_dir = os.path.join(AUDIO_DIR, level)

    os.makedirs(output_dir, exist_ok=True)

    questions = read_bank(input_path)

    print(f"[{level}] 共 {len(questions)} 題")

    for i, q in enumerate(questions, start=1):
        output_file = os.path.join(output_dir, f"{level}_{i:04d}.mp3")

        spoken_text = build_spoken_text(q["chunks"])

        print(f"轉換 {level}_{i:04d}: {spoken_text}")

        await text_to_mp3(spoken_text, output_file)

    print(f"[{level}] 完成")


async def main():
    for level, filename in BANK_FILES.items():
        await build_level(level, filename)

    print("全部完成")


if __name__ == "__main__":
    asyncio.run(main())