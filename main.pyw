#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
图形化待办事项程序 - 支持进度条显示与每日自动清空
依赖：Python 3 + tkinter (标准库)
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

DATA_FILE = "todos.json"

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("每日待办事项")
        self.root.geometry("500x500")
        self.root.resizable(True, True)

        # 加载数据（会自动处理每日清空）
        self.data = self.load_data()
        self.todos = self.data["todos"]

        # 创建界面组件
        self.create_widgets()

        # 刷新任务列表和进度条
        self.refresh_list()
        self.update_progress()

        # 窗口关闭时保存数据
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

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
            print("数据文件损坏，使用空数据")
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
            messagebox.showerror("保存失败", f"无法保存数据：{e}")

    def create_widgets(self):
        """创建所有界面组件"""
        # 顶部：添加任务区域
        add_frame = ttk.Frame(self.root, padding=5)
        add_frame.pack(fill=tk.X, pady=5)

        self.task_entry = ttk.Entry(add_frame)
        self.task_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.task_entry.bind("<Return>", lambda e: self.add_task())

        add_btn = ttk.Button(add_frame, text="添加任务", command=self.add_task)
        add_btn.pack(side=tk.RIGHT)

        # 中间：任务列表（Listbox + 滚动条）
        list_frame = ttk.Frame(self.root, padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.task_listbox = tk.Listbox(list_frame, height=15, font=("微软雅黑", 10))
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.task_listbox.yview)
        self.task_listbox.configure(yscrollcommand=scrollbar.set)

        self.task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 底部按钮区域
        btn_frame = ttk.Frame(self.root, padding=5)
        btn_frame.pack(fill=tk.X)

        complete_btn = ttk.Button(btn_frame, text="✅ 标记完成", command=self.complete_task)
        complete_btn.pack(side=tk.LEFT, padx=5)

        delete_btn = ttk.Button(btn_frame, text="🗑 删除任务", command=self.delete_task)
        delete_btn.pack(side=tk.LEFT, padx=5)

        # 进度条区域
        progress_frame = ttk.Frame(self.root, padding=5)
        progress_frame.pack(fill=tk.X, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100, length=300
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.percent_label = ttk.Label(progress_frame, text="0%")
        self.percent_label.pack(side=tk.RIGHT)

        # 底部状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def refresh_list(self):
        """刷新任务列表显示"""
        self.task_listbox.delete(0, tk.END)
        for task in self.todos:
            # 显示前缀：✅ 已完成，⭕ 未完成
            prefix = "✅ " if task["completed"] else "⭕ "
            display_text = prefix + task["text"]
            self.task_listbox.insert(tk.END, display_text)
            # 可选：为已完成任务设置不同颜色（仅对支持的环境有效）
            # 这里简单改变前景色（部分系统可能不支持）
            if task["completed"]:
                self.task_listbox.itemconfig(tk.END, fg="gray")

    def update_progress(self):
        """更新进度条和百分比显示"""
        total = len(self.todos)
        if total == 0:
            self.progress_var.set(0)
            self.percent_label.config(text="0%")
            return

        completed = sum(1 for t in self.todos if t["completed"])
        percent = (completed / total) * 100
        self.progress_var.set(percent)
        self.percent_label.config(text=f"{percent:.1f}%")

    def add_task(self):
        """添加新任务"""
        text = self.task_entry.get().strip()
        if not text:
            messagebox.showwarning("提示", "任务内容不能为空！")
            return
        self.todos.append({"text": text, "completed": False})
        self.task_entry.delete(0, tk.END)
        self.refresh_list()
        self.update_progress()
        self.save_data()
        self.status_var.set(f"已添加任务：{text}")

    def complete_task(self):
        """标记选中任务为已完成"""
        selection = self.task_listbox.curselection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个任务")
            return
        idx = selection[0]
        if self.todos[idx]["completed"]:
            messagebox.showinfo("提示", "该任务已经是完成状态")
            return
        self.todos[idx]["completed"] = True
        self.refresh_list()
        self.update_progress()
        self.save_data()
        self.status_var.set(f"已完成：{self.todos[idx]['text']}")

    def delete_task(self):
        """删除选中任务"""
        selection = self.task_listbox.curselection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个任务")
            return
        idx = selection[0]
        task_text = self.todos[idx]["text"]
        if messagebox.askyesno("确认删除", f"确定要删除任务「{task_text}」吗？"):
            del self.todos[idx]
            self.refresh_list()
            self.update_progress()
            self.save_data()
            self.status_var.set(f"已删除任务：{task_text}")

    def on_closing(self):
        """窗口关闭时保存数据并退出"""
        self.save_data()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
