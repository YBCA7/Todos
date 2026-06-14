#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
待办事项程序 - 支持任务栏进度条、标记未完成、清空所有任务、批量操作
依赖：PyQt5 (需安装：pip install PyQt5)
"""

import json
import os
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLineEdit, QPushButton, QProgressBar,
    QLabel, QMessageBox, QInputDialog, QAbstractItemView
)
from PyQt5.QtCore import Qt
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
        self.setWindowTitle("待办事项")
        self.setMinimumSize(500, 500)

        # 加载数据（直接是任务列表）
        self.todos = self.load_data()

        # 任务栏进度条对象（仅 Windows）
        self.taskbar_button = None
        if WINDOWS_TASKBAR:
            self.taskbar_button = QWinTaskbarButton(self)

        # 创建界面
        self.init_ui()

        # 刷新列表和进度
        self.refresh_todo_list()
        self.update_progress()

        # 窗口关闭时保存
        self.destroyed.connect(lambda: self.save_data())

    def showEvent(self, event):
        """重写窗口显示事件，在窗口句柄有效后再关联任务栏按钮"""
        super().showEvent(event)
        if WINDOWS_TASKBAR and self.taskbar_button is not None:
            if self.windowHandle():
                self.taskbar_button.setWindow(self.windowHandle())
                taskbar_progress = self.taskbar_button.progress()
                taskbar_progress.setVisible(True)
                self.update_progress()

    def load_data(self):
        """从 JSON 文件加载任务列表（直接返回列表）"""
        if not os.path.exists(DATA_FILE):
            return []

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 要求数据必须是一个列表
                if isinstance(data, list):
                    return data
                else:
                    # 如果格式不对，返回空列表（避免后续错误）
                    return []
        except (json.JSONDecodeError, IOError):
            return []

    def save_data(self):
        """保存任务列表到 JSON 文件"""
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.todos, f, ensure_ascii=False, indent=2)
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

        # 任务列表（支持多选）
        self.task_list = QListWidget()
        self.task_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
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
        clear_btn = QPushButton("🧹 清空所有")
        clear_btn.clicked.connect(self.clear_all)
        btn_layout.addWidget(complete_btn)
        btn_layout.addWidget(incomplete_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(clear_btn)
        main_layout.addLayout(btn_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)

        # 状态栏
        self.status_label = QLabel("就绪")
        self.status_label.setFrameStyle(QLabel.Shape.Box | QLabel.Shadow.Sunken)
        main_layout.addWidget(self.status_label)

    def refresh_todo_list(self):
        """刷新列表显示"""
        self.task_list.clear()
        for task in self.todos:
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

        if WINDOWS_TASKBAR and self.taskbar_button is not None:
            if self.windowHandle() and self.taskbar_button.window() is not None:
                taskbar_progress = self.taskbar_button.progress()
                taskbar_progress.setVisible(True)
                taskbar_progress.setValue(percent)

        total = len(self.todos)
        completed = sum(1 for t in self.todos if t["completed"])
        self.status_label.setText(f"总计 {total} 项，已完成 {completed} 项")

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

    def get_selected_indices(self):
        """获取当前选中的所有任务索引"""
        return [index.row() for index in self.task_list.selectedIndexes()]

    def mark_complete(self):
        """批量标记选中任务为已完成"""
        indices = self.get_selected_indices()
        if not indices:
            QMessageBox.information(self, "提示", "请先选择要标记的任务")
            return
        changed = 0
        for idx in indices:
            if not self.todos[idx]["completed"]:
                self.todos[idx]["completed"] = True
                changed += 1
        if changed == 0:
            QMessageBox.information(self, "提示", "所选任务都已经是完成状态")
        else:
            self.refresh_todo_list()
            self.update_progress()
            self.save_data()
            self.status_label.setText(f"已将 {changed} 个任务标记为完成")

    def mark_incomplete(self):
        """批量标记选中任务为未完成"""
        indices = self.get_selected_indices()
        if not indices:
            QMessageBox.information(self, "提示", "请先选择要标记的任务")
            return
        changed = 0
        for idx in indices:
            if self.todos[idx]["completed"]:
                self.todos[idx]["completed"] = False
                changed += 1
        if changed == 0:
            QMessageBox.information(self, "提示", "所选任务都已经是未完成状态")
        else:
            self.refresh_todo_list()
            self.update_progress()
            self.save_data()
            self.status_label.setText(f"已将 {changed} 个任务标记为未完成")

    def edit_task(self):
        """编辑单个任务（仅对当前焦点项操作）"""
        current_row = self.task_list.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "提示", "请先选择一个任务")
            return
        old_text = self.todos[current_row]["text"]
        new_text, ok = QInputDialog.getText(self, "编辑任务", "修改任务内容：", text=old_text)
        if ok and new_text.strip():
            new_text = new_text.strip()
            self.todos[current_row]["text"] = new_text
            self.refresh_todo_list()
            self.save_data()
            self.status_label.setText(f"已编辑：{old_text} -> {new_text}")

    def delete_task(self):
        """批量删除选中任务"""
        indices = self.get_selected_indices()
        if not indices:
            QMessageBox.information(self, "提示", "请先选择要删除的任务")
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除选中的 {len(indices)} 个任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for idx in sorted(indices, reverse=True):
                del self.todos[idx]
            self.refresh_todo_list()
            self.update_progress()
            self.save_data()
            self.status_label.setText(f"已删除 {len(indices)} 个任务")

    def clear_all(self):
        """清空所有任务"""
        if not self.todos:
            QMessageBox.information(self, "提示", "当前没有任务可清空")
            return
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要删除所有任务吗？此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.todos.clear()
            self.refresh_todo_list()
            self.update_progress()
            self.save_data()
            self.status_label.setText("已清空所有任务")

def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("微软雅黑", 10))
    window = TodoApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
