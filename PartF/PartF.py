import os
import re
import random
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText


# ======================
# 基本設定
# ======================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BANK_DIR = os.path.join(BASE_DIR, "bank")

BANK_FILES = {
    "easy": "input_easy.txt",
    "medium": "input_medium.txt",
    "hard": "input_hard.txt",
}

DEFAULT_QUIZ_PLAN = {
    "easy": 1,
    "medium": 2,
    "hard": 1,
}

READING_SECONDS = 30
ANSWERING_SECONDS = 90


# ======================
# 題庫讀取
# ======================

def clean_passage(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def read_passages_from_file(file_path: str):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到題庫檔案：{file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    raw_passages = re.split(r"\n\s*\n", content)

    passages = []
    for p in raw_passages:
        p = clean_passage(p)
        if p:
            passages.append(p)

    return passages


def load_all_banks(quiz_plan):
    banks = {}

    for level, filename in BANK_FILES.items():
        file_path = os.path.join(BANK_DIR, filename)
        passages = read_passages_from_file(file_path)

        required = quiz_plan[level]

        if len(passages) < required:
            raise ValueError(
                f"{level} 題庫數量不足：需要 {required} 題，但只有 {len(passages)} 題"
            )

        banks[level] = passages

    return banks


def build_quiz(banks, quiz_plan):
    quiz = []

    for level, count in quiz_plan.items():
        if count == 0:
            continue

        selected_indices = random.sample(range(len(banks[level])), count)

        for idx in selected_indices:
            quiz.append({
                "level": level,
                "index": idx,
                "passage": banks[level][idx],
            })

    return quiz


# ======================
# GUI
# ======================

class PartFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Versant Part F 練習器")
        self.root.geometry("1000x680")
        self.root.option_add("*Font", ("Arial", 16))

        self.banks = {}
        self.quiz = []
        self.current_index = 0

        self.mode_var = tk.StringVar(value="practice")
        self.state = "IDLE"
        self.timer_id = None
        self.time_left = 0
        self.passage_visible = True

        # ===== 上方狀態 =====

        self.status_label = tk.Label(
            root,
            text="請設定題數與模式，然後按「產生本次測驗」",
            font=("Arial", 14)
        )
        self.status_label.pack(pady=8)

        self.question_label = tk.Label(
            root,
            text="第 - 題 / 共 - 題",
            font=("Arial", 18)
        )
        self.question_label.pack(pady=3)

        self.level_label = tk.Label(
            root,
            text="難度：-",
            font=("Arial", 12)
        )
        self.level_label.pack(pady=3)

        self.timer_label = tk.Label(
            root,
            text="時間：-",
            font=("Arial", 16)
        )
        self.timer_label.pack(pady=3)

        # ===== 模式與題數設定 =====

        control_frame = tk.Frame(root)
        control_frame.pack(pady=8)

        tk.Label(control_frame, text="模式：").grid(row=0, column=0, padx=5)

        tk.Radiobutton(
            control_frame,
            text="練習模式",
            variable=self.mode_var,
            value="practice",
            command=self.on_mode_change
        ).grid(row=0, column=1, padx=5)

        tk.Radiobutton(
            control_frame,
            text="實戰模式",
            variable=self.mode_var,
            value="exam",
            command=self.on_mode_change
        ).grid(row=0, column=2, padx=5)

        tk.Label(control_frame, text="簡單").grid(row=0, column=3, padx=5)
        self.easy_count_var = tk.StringVar(value=str(DEFAULT_QUIZ_PLAN["easy"]))
        tk.Entry(control_frame, textvariable=self.easy_count_var, width=5).grid(row=0, column=4, padx=5)

        tk.Label(control_frame, text="中等").grid(row=0, column=5, padx=5)
        self.medium_count_var = tk.StringVar(value=str(DEFAULT_QUIZ_PLAN["medium"]))
        tk.Entry(control_frame, textvariable=self.medium_count_var, width=5).grid(row=0, column=6, padx=5)

        tk.Label(control_frame, text="困難").grid(row=0, column=7, padx=5)
        self.hard_count_var = tk.StringVar(value=str(DEFAULT_QUIZ_PLAN["hard"]))
        tk.Entry(control_frame, textvariable=self.hard_count_var, width=5).grid(row=0, column=8, padx=5)

        # ===== 中間左右區 =====

        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(6, 0))

        tk.Label(left_frame, text="Passage / 原文", font=("Arial", 12)).pack(anchor="w")
        self.passage_box = ScrolledText(
            left_frame,
            height=20,
            width=55,
            font=("Arial", 17),
            wrap=tk.WORD
        )
        self.passage_box.pack(fill=tk.BOTH, expand=True)

        tk.Label(right_frame, text="Your retelling / 你的重述", font=("Arial", 12)).pack(anchor="w")
        self.answer_box = ScrolledText(
            right_frame,
            height=20,
            width=55,
            font=("Arial", 17),
            wrap=tk.WORD
        )
        self.answer_box.pack(fill=tk.BOTH, expand=True)

        # ===== 下方按鈕 =====

        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        self.new_quiz_button = tk.Button(
            button_frame,
            text="產生本次測驗",
            width=14,
            command=self.new_quiz
        )
        self.new_quiz_button.grid(row=0, column=0, padx=5)

        self.start_button = tk.Button(
            button_frame,
            text="開始本題",
            width=12,
            command=self.start_current,
            state=tk.DISABLED
        )
        self.start_button.grid(row=0, column=1, padx=5)

        self.toggle_button = tk.Button(
            button_frame,
            text="隱藏原文",
            width=12,
            command=self.toggle_passage,
            state=tk.DISABLED
        )
        self.toggle_button.grid(row=0, column=2, padx=5)

        self.show_answer_button = tk.Button(
            button_frame,
            text="對照原文",
            width=12,
            command=self.review_current,
            state=tk.DISABLED
        )
        self.show_answer_button.grid(row=0, column=3, padx=5)

        self.next_button = tk.Button(
            button_frame,
            text="下一題",
            width=12,
            command=self.next_question,
            state=tk.DISABLED
        )
        self.next_button.grid(row=0, column=4, padx=5)

        self.set_textbox_state(self.passage_box, tk.DISABLED)
        self.set_textbox_state(self.answer_box, tk.NORMAL)

    # ======================
    # 工具函數
    # ======================

    def cancel_timer(self):
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    def set_textbox_state(self, box, state):
        box.config(state=state)

    def set_passage_text(self, text):
        self.passage_box.config(state=tk.NORMAL)
        self.passage_box.delete("1.0", tk.END)
        self.passage_box.insert(tk.END, text)
        self.passage_box.config(state=tk.DISABLED)

    def clear_answer(self):
        self.answer_box.config(state=tk.NORMAL)
        self.answer_box.delete("1.0", tk.END)

    def get_current_passage(self):
        if not self.quiz:
            return ""
        return self.quiz[self.current_index]["passage"]

    def show_passage(self):
        self.set_passage_text(self.get_current_passage())
        self.passage_visible = True
        self.toggle_button.config(text="隱藏原文")

    def hide_passage(self):
        self.set_passage_text("[原文已隱藏]")
        self.passage_visible = False
        self.toggle_button.config(text="顯示原文")

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

        for count in plan.values():
            if count < 0:
                raise ValueError("題數不能是負數")

        if sum(plan.values()) == 0:
            raise ValueError("總題數不能是 0")

        return plan

    # ======================
    # 模式切換
    # ======================

    def on_mode_change(self):
        if self.state in ("READING", "ANSWERING"):
            messagebox.showwarning("提醒", "計時中不能切換模式")
            return

        mode = self.mode_var.get()

        if mode == "practice":
            self.status_label.config(text="練習模式：可自由顯示或隱藏原文。")
            self.toggle_button.config(state=tk.NORMAL if self.quiz else tk.DISABLED)
        else:
            self.status_label.config(text="實戰模式：30 秒閱讀，90 秒作答。")
            self.toggle_button.config(state=tk.DISABLED)

    # ======================
    # 產生測驗
    # ======================

    def new_quiz(self):
        try:
            self.cancel_timer()

            quiz_plan = self.get_quiz_plan_from_ui()
            self.banks = load_all_banks(quiz_plan)
            self.quiz = build_quiz(self.banks, quiz_plan)
            self.current_index = 0
            self.state = "IDLE"

            self.clear_answer()
            self.update_question_display()
            self.show_passage()

            self.timer_label.config(text="時間：-")

            self.start_button.config(state=tk.NORMAL)
            self.show_answer_button.config(state=tk.NORMAL)
            self.next_button.config(state=tk.DISABLED)

            if self.mode_var.get() == "practice":
                self.answer_box.config(state=tk.NORMAL)
                self.toggle_button.config(state=tk.NORMAL)
                self.status_label.config(text="測驗已產生。練習模式可直接作答，也可隱藏原文。")
            else:
                self.answer_box.config(state=tk.DISABLED)
                self.toggle_button.config(state=tk.DISABLED)
                self.status_label.config(text="測驗已產生。按「開始本題」進入 30 秒閱讀。")

        except Exception as e:
            messagebox.showerror("錯誤", str(e))

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

        self.question_label.config(text=f"第 {self.current_index + 1} 題 / 共 {total} 題")
        self.level_label.config(text=f"難度：{level_name}")

    # ======================
    # 開始本題
    # ======================

    def start_current(self):
        if not self.quiz:
            return

        self.cancel_timer()
        self.clear_answer()

        mode = self.mode_var.get()

        if mode == "practice":
            self.state = "PRACTICE"
            self.answer_box.config(state=tk.NORMAL)
            self.show_passage()
            self.timer_label.config(text="時間：不限")
            self.status_label.config(text="練習模式：可自由輸入，必要時隱藏原文。")
            self.toggle_button.config(state=tk.NORMAL)
            self.next_button.config(state=tk.NORMAL)
            self.show_answer_button.config(state=tk.NORMAL)

        else:
            self.state = "READING"
            self.show_passage()
            self.answer_box.config(state=tk.DISABLED)
            self.toggle_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
            self.show_answer_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.DISABLED)

            self.time_left = READING_SECONDS
            self.status_label.config(text="實戰模式：閱讀中，請記住內容。")
            self.run_reading_timer()

    # ======================
    # 實戰模式倒數
    # ======================

    def run_reading_timer(self):
        self.timer_label.config(text=f"閱讀時間：{self.time_left} 秒")

        if self.time_left <= 0:
            self.start_answering_phase()
            return

        self.time_left -= 1
        self.timer_id = self.root.after(1000, self.run_reading_timer)

    def start_answering_phase(self):
        self.cancel_timer()

        self.state = "ANSWERING"
        self.hide_passage()
        self.answer_box.config(state=tk.NORMAL)
        self.answer_box.focus_set()

        self.time_left = ANSWERING_SECONDS
        self.status_label.config(text="實戰模式：作答中，請在 90 秒內重述。")
        self.run_answering_timer()

    def run_answering_timer(self):
        self.timer_label.config(text=f"作答時間：{self.time_left} 秒")

        if self.time_left <= 0:
            self.finish_exam_question()
            return

        self.time_left -= 1
        self.timer_id = self.root.after(1000, self.run_answering_timer)

    def finish_exam_question(self):
        self.cancel_timer()

        self.state = "REVIEW"
        self.answer_box.config(state=tk.DISABLED)
        self.show_passage()

        self.timer_label.config(text="時間到")
        self.status_label.config(text="時間到。已顯示原文，可對照你的重述。")

        self.next_button.config(state=tk.NORMAL)
        self.show_answer_button.config(state=tk.NORMAL)
        self.start_button.config(state=tk.NORMAL)

    # ======================
    # 原文顯示/隱藏
    # ======================

    def toggle_passage(self):
        if self.mode_var.get() != "practice":
            return

        if self.passage_visible:
            self.hide_passage()
            self.status_label.config(text="原文已隱藏。請嘗試重述。")
        else:
            self.show_passage()
            self.status_label.config(text="原文已顯示。")

    def review_current(self):
        if not self.quiz:
            return

        self.show_passage()
        self.status_label.config(text="已顯示原文，可自行對照。")
        self.next_button.config(state=tk.NORMAL)

    # ======================
    # 下一題
    # ======================

    def next_question(self):
        if not self.quiz:
            return

        self.cancel_timer()

        if self.current_index + 1 >= len(self.quiz):
            messagebox.showinfo("完成", "全部題目完成")
            self.state = "IDLE"
            self.status_label.config(text="練習完成。可重新產生本次測驗。")
            self.next_button.config(state=tk.DISABLED)
            self.timer_label.config(text="時間：-")
            return

        self.current_index += 1
        self.state = "IDLE"

        self.clear_answer()
        self.update_question_display()
        self.show_passage()

        self.timer_label.config(text="時間：-")
        self.next_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)
        self.show_answer_button.config(state=tk.NORMAL)

        if self.mode_var.get() == "practice":
            self.answer_box.config(state=tk.NORMAL)
            self.toggle_button.config(state=tk.NORMAL)
            self.status_label.config(text="已切換到下一題。練習模式可直接作答，或按「開始本題」。")
        else:
            self.answer_box.config(state=tk.DISABLED)
            self.toggle_button.config(state=tk.DISABLED)
            self.status_label.config(text="已切換到下一題。請按「開始本題」進入 30 秒閱讀。")


# ======================
# 啟動
# ======================

if __name__ == "__main__":
    root = tk.Tk()
    app = PartFApp(root)
    root.mainloop()