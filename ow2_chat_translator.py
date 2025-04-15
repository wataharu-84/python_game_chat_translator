import re
import mss
from PIL import Image
import pytesseract
from googletrans import Translator
import tkinter as tk
import threading
import keyboard
import time

# Tesseractのパス (必要なら指定)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 翻訳結果を表示するウィンドウ
root = tk.Tk()
root.title("OW2 チャット翻訳")
label = tk.Label(root, text="", font=("Meiryo", 11), wraplength=600, justify="left")
label.pack()

# サブモニターの座標を指定 (モニター設定に応じて調整)
root.geometry("600x500-2000+100")

class ChatTranslator:
    def __init__(self):
        self.last_text = None
        self.translator = Translator()

    def capture_and_translate(self):
        with mss.mss() as sct:
            # チャットボックスの座標を指定 (モニター解像度に応じて変更)
            monitor = {"top": 450, "left": 80, "width": 400, "height": 250}

            img = sct.grab(monitor)
            img_pil = Image.frombytes("RGB", img.size, img.rgb, "raw")

            # OCRでテキスト抽出
            text = pytesseract.image_to_string(img_pil, lang='eng+jpn+kor+chi_sim').strip()

            # 抽出したテキストが前回と同じか空白の場合は翻訳スキップ
            if text == "" or text == self.last_text:
                return ""

            # 正規表現でチャット形式を抽出
            pattern = r"\[(.*?)\]:\s*(.+)"
            matches = re.findall(pattern, text)

            if not matches:
                return ""

            output_lines = []

            for username, message in matches:
                message = message.strip()
                if not message:
                    continue

                # システムメッセージではなく本文が存在するかつ、日本語でない場合のみ翻訳
                output_lines.append(f"検出: [{username}]: {message}")
                if len(message) > 0 and not re.search(r'[ぁ-ん]+|[ァ-ヴー]+', message):
                    try:
                        result = self.translator.translate(message, dest='ja')
                        output_lines.append(f"翻訳: [{username}]: {result.text}")
                    except Exception as e:
                        output_lines.append(f"翻訳エラー: {e}")

            # テキストを記憶
            self.last_text = text
            return "\n".join(output_lines)

# 実行制御用フラグ
loop_running = False

translator = ChatTranslator()

# 定期監視ループ
def translation_loop():
    global loop_running

    while True:
        if loop_running:
            translated_text = translator.capture_and_translate()
            if translated_text:
                label.config(text=translated_text)
        time.sleep(1.0)  # 翻訳間隔

# キー監視
def keyboard_watcher():
    global loop_running

    while True:
        if keyboard.is_pressed('ctrl+f1'):
            loop_running = True
            label.config(text="翻訳ループ実行中...")

        elif keyboard.is_pressed('ctrl+f2'):
            loop_running = False
            label.config(text="翻訳停止中")

        elif keyboard.is_pressed('ctrl+shift+z'):
            translated_text = translator.capture_and_translate()
            if translated_text:
                label.config(text="ワンショット翻訳実行\n" + translated_text)
            else:
                label.config(text="ワンショット翻訳実行 (チャット未検出)")

        time.sleep(0.1)

# スレッドで開始
threading.Thread(target=translation_loop, daemon=True).start()
threading.Thread(target=keyboard_watcher, daemon=True).start()

root.mainloop()
