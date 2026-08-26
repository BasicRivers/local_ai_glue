import os
import itertools
import json
from html import escape

from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QLabel, QMenu, QTextEdit, QSlider
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self, status_flags, history_file="./conversation_history.json"):
        super().__init__()
        self.status_flags = status_flags
        self.history_file = history_file
        self.setWindowOpacity(0.01)
        self.deafen_mic_text = self._toggle_mic_button_text()
        self.images = self.update_current_emotion(status_flags["emotion"])
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)
        
        self.pic_label = QLabel(self)
        self.pic_label.setPixmap(next(self.images))
        
        layout.addWidget(self.pic_label)
        
        self.reset_animation()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.windowHandle():
                self.windowHandle().startSystemMove()
        
    def _toggle_base_animation(self):
        return "neutral" if self.status_flags["listening"] else "idle"
        
    def _toggle_mic_button_text(self):
        return "Unmute Mic." if self.status_flags["deafen"] else "Mute Mic."
    
    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        toggle_mic_action = context_menu.addAction(self.deafen_mic_text)
        open_logs_action = context_menu.addAction("Chat logs")
        change_mic_action = context_menu.addAction("Input method")
        context_menu.addSeparator()
        artist_credits_action = context_menu.addAction("Art created by: オギャ美") # This action does nothing, it's in place of the removed watermark that distracts from transparency
        artist_credits_action.setEnabled(False)
        context_menu.addSeparator()
        exit_action = context_menu.addAction("Exit")
        
        action = context_menu.exec(event.globalPos())
        if action == toggle_mic_action:
             self.deafen_button_toggle(self.status_flags)
        elif action == open_logs_action:
            self.show_chat_logs()
        elif action == change_mic_action:
            self.show_input_choice()
        elif action == exit_action:
            self.close()
    
    def deafen_button_toggle(self, status_flags):
        if status_flags["deafen"]:
            status_flags["deafen"] = False
        else:
            status_flags["deafen"] = True
        
        self.deafen_mic_text = self._toggle_mic_button_text()
        
    def update_current_emotion(self, emotion):
        animation_path = os.path.join("ANIMATIONS", emotion)
        images_list = [QPixmap(os.path.join(animation_path, image)) for image in os.listdir(animation_path)]
        return itertools.cycle(images_list)
    
    def toggle_animation(self):
        self.pic_label.setPixmap(next(self.images))

    def reset_animation(self):
        self.status_flags["emotion"] = self._toggle_base_animation()
        self.pic_label.setPixmap(QPixmap(f"ANIMATIONS/{self.status_flags["emotion"]}/1"))

    def show_chat_logs(self):
        self.viewer = JsonViewerWindow(self.history_file)
        self.viewer.show()

    def show_input_choice(self):
        self.viewer = MicControlsWindow(status_flags=self.status_flags)
        self.viewer.show()

    
class MicControlsWindow(QMainWindow):
    def __init__(self, status_flags):
        super().__init__()
        container = QWidget()
        self.setCentralWidget(container)
        self.status_flags = status_flags
        layout = QVBoxLayout(container)
        self.label = QLabel(f"{self.status_flags["silence_threshold"]} dB")
        self.slider = QSlider(orientation=Qt.Horizontal)
        self.slider.setRange(-60, 0)
        self.slider.setValue(status_flags["silence_threshold"])
        self.slider.valueChanged.connect(self.slider_moved)
        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        
    def slider_moved(self, value):
        self.status_flags["silence_threshold"] = value
        self.label.setText (f"{value} dB")
        
class JsonViewerWindow(QMainWindow):
    def __init__(self, json_file_path=None):
        super().__init__()
        
        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        # Load file if provided
        if json_file_path:
            self.load_json(json_file_path)
    
    # This function was vibe-coded because I don't care
    def load_json(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
    
            html = """
            <div style="
                font-family: Segoe UI, Arial;
                font-size: 14px;
                padding: 6px;
            ">
            """
    
            for item in data:
                role = escape(str(item.get("role", "unknown")))
                content = escape(str(item.get("content", "")))
    
                html += f"""
                <div style="margin-bottom: 8px;">
    
                    <span style="
                        font-weight: bold;
                        color: #4FC3F7;
                    ">
                        {role}:
                    </span>
    
                    <span style="
                        color: #000000;
                    ">
                        {content}
                    </span>
    
                    <hr style="
                        border: none;
                        border-top: 1px solid #444;
                        margin-top: 6px;
                    ">
                </div>
                """
    
            html += "</div>"
    
            self.text_edit.setHtml(html)
            self.setWindowTitle(f"JSON Viewer - {file_path}")
        except Exception as e:
            self.text_edit.setPlainText(f"Error: {str(e)}")
            
if __name__ == "__main__":
    from settings import status_flags
    app = QApplication()
    window = MainWindow(status_flags)
    window.show()
    app.exec()