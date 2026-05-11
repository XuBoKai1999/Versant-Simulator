import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
import pygame


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WELCOME_AUDIO_PATH = os.path.join(BASE_DIR, "sound/welcome.mp3")

PART_FILES = {
    "Part A": "PartA/PartA.py",
    "Part B": "PartB/PartB.py",
    "Part C": "PartC/PartC.py",
    "Part D": "PartD/PartD.py",
    "Part E": "PartE/PartE.py",
    "Part F": "PartF/PartF.py",
}


def open_part(part_name):
    filename = PART_FILES[part_name]
    file_path = os.path.join(BASE_DIR, filename)

    if not os.path.exists(file_path):
        messagebox.showerror(
            "找不到程式",
            f"找不到 {filename}\n\n請確認它和 main.py 放在同一個資料夾。"
        )
        return

    try:
        subprocess.Popen([sys.executable, file_path], cwd=BASE_DIR)
    except Exception as e:
        messagebox.showerror("啟動失敗", str(e))

def play_welcome(welcome_path):
    path = os.path.join(BASE_DIR, welcome_path)

    if not os.path.exists(path):
        return

    try:
        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
    except Exception as e:
        print("播放失敗:", e)

class MainMenuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Versant 練習器入口")
        self.root.geometry("520x620")
        self.root.option_add("*Font", ("Arial", 16))
        self.root.after(300, play_welcome(WELCOME_AUDIO_PATH))

        title = tk.Label(
            root,
            text="Versant Practice Launcher",
            font=("Arial", 22, "bold")
        )
        title.pack(pady=(20, 8))

        # ===== 動畫區 =====
        self.canvas = tk.Canvas(root, width=420, height=95, bg="#f0f0f0", highlightthickness=0)
        self.canvas.pack(pady=2)

        self.phrases = [
            "Listen carefully.",
            "Repeat the sentence.",
            "Type what you hear.",
            "Practice every day.",
            "Stay calm and answer clearly.",
        ]

        self.phrase_index = 0
        self.char_index = 0
        self.current_text = ""

        self.draw_character()
        self.animate_speech()

        subtitle = tk.Label(
            root,
            text="請選擇要練習的 Part",
            font=("Arial", 15)
        )
        subtitle.pack(pady=5)

        button_frame = tk.Frame(root)
        button_frame.pack(pady=18)

        parts = ["Part A", "Part B", "Part C", "Part D", "Part E", "Part F"]

        for i, part in enumerate(parts):
            btn = tk.Button(
                button_frame,
                text=part,
                width=14,
                height=2,
                command=lambda p=part: open_part(p)
            )
            btn.grid(row=i // 2, column=i % 2, padx=10, pady=10)

        quit_button = tk.Button(
            root,
            text="離開",
            width=12,
            command=root.destroy
        )
        quit_button.pack(pady=5)

    def draw_character(self):
        c = self.canvas

        # 小人頭
        c.create_oval(30, 20, 60, 50, fill="white", outline="black", width=2)

        # 身體
        c.create_line(45, 50, 45, 78, width=2)

        # 手
        c.create_line(45, 58, 25, 68, width=2)
        c.create_line(45, 58, 65, 68, width=2)

        # 腳
        c.create_line(45, 78, 30, 92, width=2)
        c.create_line(45, 78, 60, 92, width=2)

        # 眼睛
        c.create_oval(38, 31, 41, 34, fill="black")
        c.create_oval(49, 31, 52, 34, fill="black")

        # 嘴
        c.create_arc(38, 34, 53, 45, start=200, extent=140, style=tk.ARC, width=2)

    def animate_speech(self):
        c = self.canvas

        c.delete("bubble")

        phrase = self.phrases[self.phrase_index]

        if self.char_index <= len(phrase):
            self.current_text = phrase[:self.char_index]
            self.char_index += 1

            text_width = max(90, min(280, 18 + len(self.current_text) * 11))
            x1, y1 = 85, 18
            x2, y2 = x1 + text_width, 62

            # 對話框
            c.create_rectangle(
                x1, y1, x2, y2,
                fill="white",
                outline="black",
                width=2,
                tags="bubble"
            )

            # 對話框尖角
            c.create_polygon(
                85, 46,
                68, 55,
                85, 56,
                fill="white",
                outline="black",
                tags="bubble"
            )

            # 文字
            c.create_text(
                x1 + 12,
                y1 + 22,
                text=self.current_text,
                anchor="w",
                font=("Arial", 13),
                tags="bubble"
            )

            self.root.after(90, self.animate_speech)

        else:
            # 停一下，然後清掉重來
            self.root.after(50, self.reset_speech)

    def reset_speech(self):
        self.canvas.delete("bubble")

        self.phrase_index = (self.phrase_index + 1) % len(self.phrases)
        self.char_index = 0
        self.current_text = ""

        self.root.after(250, self.animate_speech)


if __name__ == "__main__":
    root = tk.Tk()
    app = MainMenuApp(root)
    root.mainloop()