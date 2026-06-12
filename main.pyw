#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
待办事项程序 - 支持任务栏进度条、标记未完成、每日自动清空
依赖：PyQt5 (需安装：pip install PyQt5)
"""

import json
import os
import sys
from datetime import date
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLineEdit, QPushButton, QProgressBar,
    QLabel, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# 尝试导入任务栏进度条支持（仅 Windows）
try:
    from PyQt5.QtWinExtras import QWinTaskbarButton
    WINDOWS_TASKBAR = True
except ImportError:
    WINDOWS_TASKBAR = False

DATA_FILE = "todos.json"

class TodoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("每日待办事项")
        self.setMinimumSize(500, 500)

        # 加载数据
        self.data = self.load_data()
        self.todos = self.data["todos"]

        # 任务栏进度条对象（仅 Windows）
        self.taskbar_button = None
        if WINDOWS_TASKBAR:
            self.taskbar_button = QWinTaskbarButton(self)

        # 创建界面
        self.init_ui()

        # 刷新列表和进度
        self.refresh_todo_list()
        self.update_progress()

        # 窗口关闭时保存（修复参数传递错误）
        self.destroyed.connect(lambda: self.save_data())

    def showEvent(self, event):
        """重写窗口显示事件，在窗口句柄有效后再关联任务栏按钮"""
        super().showEvent(event)
        if WINDOWS_TASKBAR and self.taskbar_button is not None:
            # 确保窗口句柄已创建
            if self.windowHandle():
                self.taskbar_button.setWindow(self.windowHandle())
                # 确保任务栏进度条可见，并立即刷新一次
                taskbar_progress = self.taskbar_button.progress()
                taskbar_progress.setVisible(True)
                self.update_progress()

    def load_data(self):
        """加载数据，若日期不是今天则清空待办"""
        today = date.today().isoformat()
        default_data = {"date": today, "todos": []}

        if not os.path.exists(DATA_FILE):
            return default_data

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return default_data

        if data.get("date") != today:
            print("新的一天，自动清空昨日待办")
            data["date"] = today
            data["todos"] = []
            self.save_data(data)
        return data

    def save_data(self, data=None):
        """保存数据到文件"""
        if data is None:
            data = {"date": self.data["date"], "todos": self.todos}
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            QMessageBox.critical(self, "保存失败", f"无法保存数据：{e}")

    def init_ui(self):
        """构建界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 添加任务区域
        add_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("输入新任务...")
        self.task_input.returnPressed.connect(self.add_task)
        add_btn = QPushButton("添加任务")
        add_btn.clicked.connect(self.add_task)
        add_layout.addWidget(self.task_input)
        add_layout.addWidget(add_btn)
        main_layout.addLayout(add_layout)

        # 任务列表
        self.task_list = QListWidget()
        main_layout.addWidget(self.task_list)

        # 按钮区域
        btn_layout = QHBoxLayout()
        complete_btn = QPushButton("✅ 标记完成")
        complete_btn.clicked.connect(self.mark_complete)
        incomplete_btn = QPushButton("🔄 标记未完成")
        incomplete_btn.clicked.connect(self.mark_incomplete)
        edit_btn = QPushButton("✏️ 编辑任务")
        edit_btn.clicked.connect(self.edit_task)
        delete_btn = QPushButton("🗑 删除任务")
        delete_btn.clicked.connect(self.delete_task)
        btn_layout.addWidget(complete_btn)
        btn_layout.addWidget(incomplete_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        main_layout.addLayout(btn_layout)

        # 进度条和百分比
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        main_layout.addLayout(progress_layout)

        # 状态栏
        self.status_label = QLabel("就绪")
        self.status_label.setFrameStyle(QLabel.Shape.Box | QLabel.Shadow.Sunken)
        main_layout.addWidget(self.status_label)

    def refresh_todo_list(self):
        """刷新列表显示"""
        self.task_list.clear()
        for idx, task in enumerate(self.todos):
            prefix = "✅ " if task["completed"] else "□ "
            text = prefix + task["text"]
            item = QListWidgetItem(text)
            if task["completed"]:
                item.setForeground(Qt.GlobalColor.gray)
            self.task_list.addItem(item)

    def update_progress(self):
        """更新进度条和任务栏进度"""
        total = len(self.todos)
        if total == 0:
            percent = 0
        else:
            completed = sum(1 for t in self.todos if t["completed"])
            percent = int(completed / total * 100)

        self.progress_bar.setValue(percent)

        # 更新 Windows 任务栏进度条
        if WINDOWS_TASKBAR and self.taskbar_button is not None:
            # 如果尚未关联窗口（比如 showEvent 还没触发），则先尝试关联
            if not self.windowHandle() or self.taskbar_button.window() is None:
                # 延迟到 showEvent 中关联，这里不做重复关联
                pass
            else:
                taskbar_progress = self.taskbar_button.progress()
                taskbar_progress.setVisible(True)
                taskbar_progress.setValue(percent)
                # 可选：完成任务后隐藏进度条（取消下面注释）
                # if percent == 100:
                #     taskbar_progress.setVisible(False)

    def add_task(self):
        """添加新任务"""
        text = self.task_input.text().strip()
        if not text:
            QMessageBox.warning(self, "提示", "任务内容不能为空！")
            return
        self.todos.append({"text": text, "completed": False})
        self.task_input.clear()
        self.refresh_todo_list()
        self.update_progress()
        self.save_data()
        self.status_label.setText(f"已添加任务：{text}")

    def get_selected_index(self):
        """获取当前选中的任务索引"""
        selected = self.task_list.currentRow()
        if selected < 0:
            QMessageBox.information(self, "提示", "请先选择一个任务")
            return None
        return selected

    def mark_complete(self):
        """标记选中任务为已完成"""
        idx = self.get_selected_index()
        if idx is None:
            return
        if self.todos[idx]["completed"]:
            QMessageBox.information(self, "提示", "该任务已经是完成状态")
            return
        self.todos[idx]["completed"] = True
        self.refresh_todo_list()
        self.update_progress()
        self.save_data()
        self.status_label.setText(f"已完成：{self.todos[idx]['text']}")

    def mark_incomplete(self):
        """标记选中任务为未完成"""
        idx = self.get_selected_index()
        if idx is None:
            return
        if not self.todos[idx]["completed"]:
            QMessageBox.information(self, "提示", "该任务已经是未完成状态")
            return
        self.todos[idx]["completed"] = False
        self.refresh_todo_list()
        self.update_progress()
        self.save_data()
        self.status_label.setText(f"已恢复为未完成：{self.todos[idx]['text']}")

    def edit_task(self):
        """编辑任务内容"""
        idx = self.get_selected_index()
        if idx is None:
            return
        old_text = self.todos[idx]["text"]
        new_text, ok = QInputDialog.getText(self, "编辑任务", "修改任务内容：", text=old_text)
        if ok and new_text.strip():
            new_text = new_text.strip()
            self.todos[idx]["text"] = new_text
            self.refresh_todo_list()
            self.save_data()
            self.status_label.setText(f"已编辑：{old_text} -> {new_text}")

    def delete_task(self):
        """删除任务"""
        idx = self.get_selected_index()
        if idx is None:
            return
        task_text = self.todos[idx]["text"]
        reply = QMessageBox.question(self, "确认删除", f"确定要删除任务「{task_text}」吗？",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            del self.todos[idx]
            self.refresh_todo_list()
            self.update_progress()
            self.save_data()
            self.status_label.setText(f"已删除任务：{task_text}")

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("微软雅黑", 10))
    window = TodoApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
