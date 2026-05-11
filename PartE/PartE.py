import os
import re
import random
import difflib
import tkinter as tk
from tkinter import messagebox
import pygame


# ======================
# 基本設定
# ======================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BANK_DIR = os.path.join(BASE_DIR, "bank")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")

BANK_FILES = {
    "easy": "input_easy.txt",
    "medium": "input_medium.txt",
    "hard": "input_hard.txt",
}

DEFAULT_QUIZ_PLAN = {
    "easy": 2,
    "medium": 10,
    "hard": 4,
}


# ======================
# 題庫讀取
# ======================

def clean_question(text: str) -> str:
    text = text.strip()
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


def load_all_banks(quiz_plan):
    banks = {}

    for level, filename in BANK_FILES.items():
        file_path = os.path.join(BANK_DIR, filename)
        questions = read_questions_from_file(file_path)

        required = quiz_plan[level]

        if len(questions) < required:
            raise ValueError(
                f"{level} 題庫數量不足：需要 {required} 題，但只有 {len(questions)} 題"
            )

        banks[level] = questions

    return banks


# ======================
# 抽題與音檔
# ======================

def get_audio_path(level: str, index: int):
    number = index + 1
    filename = f"{level}_{number:04d}.mp3"
    return os.path.join(AUDIO_DIR, level, filename)


def build_quiz(banks, quiz_plan):
    quiz = []

    for level, count in quiz_plan.items():
        if count == 0:
            continue

        selected_indices = random.sample(range(len(banks[level])), count)

        for idx in selected_indices:
            audio_path = get_audio_path(level, idx)

            if not os.path.exists(audio_path):
                raise FileNotFoundError(
                    f"找不到音檔：{audio_path}\n"
                    f"請先執行 build_audio.py。"
                )

            quiz.append({
                "level": level,
                "index": idx,
                "question": banks[level][idx],
                "audio": audio_path,
            })

    return quiz


# ======================
# 答案比對
# ======================

def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[.,!?;:\"()\[\]{}]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def compare_answer(user_answer: str, correct_answer: str):
    user = normalize_text(user_answer)
    correct = normalize_text(correct_answer)

    ratio = difflib.SequenceMatcher(None, user, correct).ratio()
    return round(ratio * 100)


# ======================
# GUI
# ======================

class PartEApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Versant Part E 練習器")
        self.root.geometry("800x600")
        self.root.option_add("*Font", ("Arial", 16))

        pygame.mixer.init()

        self.banks = {}
        self.quiz = []
        self.current_index = 0

        # ===== 狀態 =====

        self.status_label = tk.Label(
            root,
            text="請設定題數，然後按「產生本次測驗」開始",
            font=("Arial", 14)
        )
        self.status_label.pack(pady=10)

        self.question_label = tk.Label(
            root,
            text="第 - 題 / 共 - 題",
            font=("Arial", 18)
        )
        self.question_label.pack(pady=5)

        self.level_label = tk.Label(
            root,
            text="難度：-",
            font=("Arial", 17)
        )
        self.level_label.pack(pady=5)

        # ===== 題數設定 =====

        plan_frame = tk.Frame(root)
        plan_frame.pack(pady=8)

        tk.Label(plan_frame, text="簡單").grid(row=0, column=0, padx=5)
        self.easy_count_var = tk.StringVar(value=str(DEFAULT_QUIZ_PLAN["easy"]))
        tk.Entry(plan_frame, textvariable=self.easy_count_var, width=5).grid(row=0, column=1, padx=5)

        tk.Label(plan_frame, text="中等").grid(row=0, column=2, padx=5)
        self.medium_count_var = tk.StringVar(value=str(DEFAULT_QUIZ_PLAN["medium"]))
        tk.Entry(plan_frame, textvariable=self.medium_count_var, width=5).grid(row=0, column=3, padx=5)

        tk.Label(plan_frame, text="困難").grid(row=0, column=4, padx=5)
        self.hard_count_var = tk.StringVar(value=str(DEFAULT_QUIZ_PLAN["hard"]))
        tk.Entry(plan_frame, textvariable=self.hard_count_var, width=5).grid(row=0, column=5, padx=5)

        # ===== 作答區 =====

        self.answer_box = tk.Text(
            root,
            height=5,
            width=82,
            font=("Arial", 17)
        )
        self.answer_box.pack(pady=10)

        # ===== 結果區 =====

        self.result_label = tk.Label(
            root,
            text="",
            font=("Arial", 17),
            justify="left",
            wraplength=740
        )
        self.result_label.pack(pady=10)

        # ===== 按鈕 =====

        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        self.new_quiz_button = tk.Button(
            button_frame,
            text="產生本次測驗",
            width=14,
            command=self.new_quiz
        )
        self.new_quiz_button.grid(row=0, column=0, padx=5)

        self.play_button = tk.Button(
            button_frame,
            text="播放本題",
            width=12,
            command=self.play_current,
            state=tk.DISABLED
        )
        self.play_button.grid(row=0, column=1, padx=5)

        self.replay_button = tk.Button(
            button_frame,
            text="再聽一次",
            width=12,
            command=self.play_current,
            state=tk.DISABLED
        )
        self.replay_button.grid(row=0, column=2, padx=5)

        self.check_button = tk.Button(
            button_frame,
            text="對答案",
            width=12,
            command=self.check_answer,
            state=tk.DISABLED
        )
        self.check_button.grid(row=0, column=3, padx=5)

        self.next_button = tk.Button(
            button_frame,
            text="下一題",
            width=12,
            command=self.next_question,
            state=tk.DISABLED
        )
        self.next_button.grid(row=0, column=4, padx=5)

    # ======================
    # 使用者題數設定
    # ======================

    def get_quiz_plan_from_ui(self):
        try:
            plan = {
                "easy": int(self.easy_count_var.get()),
                "medium": int(self.medium_count_var.get()),
                "hard": int(self.hard_count_var.get()),
            }
        except ValueError:
            raise ValueError("題數必須是整數")

        for level, count in plan.items():
            if count < 0:
                raise ValueError("題數不能是負數")

        if sum(plan.values()) == 0:
            raise ValueError("總題數不能是 0")

        return plan

    # ======================
    # 產生測驗
    # ======================

    def new_quiz(self):
        try:
            pygame.mixer.music.stop()

            quiz_plan = self.get_quiz_plan_from_ui()

            self.banks = load_all_banks(quiz_plan)
            self.quiz = build_quiz(self.banks, quiz_plan)
            self.current_index = 0

            self.answer_box.delete("1.0", tk.END)
            self.result_label.config(text="")

            self.update_question_display()

            self.play_button.config(state=tk.NORMAL)
            self.replay_button.config(state=tk.NORMAL)
            self.check_button.config(state=tk.NORMAL)
            self.next_button.config(state=tk.DISABLED)

            self.status_label.config(
                text="測驗已產生。請按「播放本題」開始。"
            )

        except Exception as e:
            messagebox.showerror("錯誤", str(e))

    # ======================
    # 顯示題目資訊
    # ======================

    def update_question_display(self):
        if not self.quiz:
            self.question_label.config(text="第 - 題 / 共 - 題")
            self.level_label.config(text="難度：-")
            return

        current = self.quiz[self.current_index]
        total = len(self.quiz)

        level_name = {
            "easy": "簡單",
            "medium": "中等",
            "hard": "困難",
        }.get(current["level"], current["level"])

        self.question_label.config(
            text=f"第 {self.current_index + 1} 題 / 共 {total} 題"
        )

        self.level_label.config(
            text=f"難度：{level_name}"
        )

    # ======================
    # 播放
    # ======================

    def play_current(self):
        if not self.quiz:
            return

        current = self.quiz[self.current_index]
        audio_file = current["audio"]

        try:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()

            self.status_label.config(
                text="播放中。播放完後請輸入你聽到的句子。"
            )

        except Exception as e:
            messagebox.showerror("播放錯誤", str(e))

    # ======================
    # 對答案
    # ======================

    def check_answer(self):
        if not self.quiz:
            return

        user_answer = self.answer_box.get("1.0", tk.END).strip()

        if not user_answer:
            messagebox.showwarning("提醒", "請先輸入答案")
            return

        correct_answer = self.quiz[self.current_index]["question"]
        score = compare_answer(user_answer, correct_answer)

        self.result_label.config(
            text=(
                f"相似度：{score}%\n\n"
                f"你的答案：\n{user_answer}\n\n"
                f"正確答案：\n{correct_answer}"
            )
        )

        self.next_button.config(state=tk.NORMAL)
        self.status_label.config(text="已對答案。可再聽一次，或進入下一題。")

    # ======================
    # 下一題
    # ======================

    def next_question(self):
        if not self.quiz:
            return

        if self.current_index + 1 >= len(self.quiz):
            messagebox.showinfo("完成", "全部題目完成")
            self.status_label.config(text="練習完成。可重新產生本次測驗。")
            self.next_button.config(state=tk.DISABLED)
            return

        self.current_index += 1

        self.answer_box.delete("1.0", tk.END)
        self.result_label.config(text="")
        self.next_button.config(state=tk.DISABLED)

        self.update_question_display()

        self.status_label.config(
            text="已切換到下一題。請按「播放本題」開始。"
        )


# ======================
# 啟動
# ======================

if __name__ == "__main__":
    root = tk.Tk()
    app = PartEApp(root)
    root.mainloop()