# -*- encoding=utf8 -*-
__author__ = "Administrator"

from airtest.core.api import *
from airtest.aircv import *
from airtest.core.settings import Settings as ST
from paddleocr import PaddleOCR
import time
import win32gui
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QTextEdit, QLabel, QTabWidget, QLineEdit, QSpinBox, QFileDialog, QTimeEdit
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QTime
from PyQt5.QtGui import QFont
import json
import os



# 全局变量


Window_Title = 'EXILIUM'
Title_Bar_Height = 0
ocr = PaddleOCR(use_angle_cls=False)
dev = None

# 任务列表
TASKS = {
    'reusable_activity': '日常活动',
    'mailbox': '邮箱',
    'ally_area': '班组区域',
    'public_area': '公共区',
    'daily_battle': '每日战斗',
    'daily_task': '每日任务',
    'weekly_task': '每周任务',
    'frontline_activity': '前线活动',
    'temporary_activity': '临时活动',
    'period_task': '周期任务',
    'shopping': '购物'
}

class TaskThread(QThread):
    log_signal = pyqtSignal(str)
    task_status_signal = pyqtSignal(str, bool)  # 任务名, 是否成功

    def __init__(self, tasks, config):
        super().__init__()
        self.tasks = tasks
        self.config = config
        self.is_running = True

    def run(self):
        global dev
        try:
            # 在执行任务前先设置环境
            self.log_signal.emit("开始初始化环境...")
            setup_env(
                self.config.get('process_title', 'EXILIUM'),
                self.config.get('operation_delay', 2),
                self.config.get('log_path', './logs'),
                self.config.get('startup_path', '')
            )
            
            # 执行登录检查
            self.log_signal.emit("执行登录检查...")
            login_check()
            self.log_signal.emit("环境初始化完成")
            
        except Exception as e:
            self.log_signal.emit(f"环境初始化失败: {str(e)}")
            return
        
        for task_name in self.tasks:
            if not self.is_running:
                break
            try:
                self.log_signal.emit(f"开始执行: {TASKS[task_name]}")
                task_func = globals()[task_name]
                
                # 根据任务类型传递不同的配置参数
                if task_name == 'temporary_activity':
                    task_func(
                        activity_name=self.config.get('activity_name', ''),
                        sub_activity_name=self.config.get('activity_subname', '')
                    )
                elif task_name == 'shopping':
                    task_func(
                        activity_shop=self.config.get('activity_shop', ''),
                        sub_shop_name=self.config.get('activity_subshop', '')
                    )
                else:
                    task_func()
                
                self.task_status_signal.emit(task_name, True)
                self.log_signal.emit(f"执行成功: {TASKS[task_name]}")
            except Exception as e:
                self.task_status_signal.emit(task_name, False)
                self.log_signal.emit(f"执行失败: {TASKS[task_name]}, 错误: {str(e)}")
                break  # 当任务执行失败时，停止执行剩余任务
        self.log_signal.emit("所有任务执行完毕")

    def stop(self):
        self.is_running = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.task_thread = None
        self.schedule_timer = QTimer()
        self.schedule_timer.timeout.connect(self.execute_scheduled_tasks)
        self.init_ui()
        self.load_config()

    def init_ui(self):
        self.setWindowTitle('GF2自动化工具')
        self.setGeometry(100, 100, 1400, 800)  # 增加窗口宽度以适应两列布局

        # 设置大字体
        big_font = QFont()
        big_font.setPointSize(16)  # 设置字体大小为16
        self.setFont(big_font)

        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建任务执行标签页
        self.create_task_tab()
        
        # 创建全局配置标签页
        self.create_config_tab()

    def create_task_tab(self):
        """创建任务执行标签页"""
        task_tab = QWidget()
        self.tab_widget.addTab(task_tab, '任务执行')
        
        # 创建主要的水平布局（两列）
        main_layout = QHBoxLayout(task_tab)

        # === 左列：任务选择区域 ===
        left_column = QVBoxLayout()
        
        # 添加任务选择标题
        big_font = QFont()
        big_font.setPointSize(16)
        tasks_title = QLabel('任务选择')
        tasks_title.setFont(big_font)
        tasks_title.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        left_column.addWidget(tasks_title)
        
        # 创建任务选择区域
        self.task_checkboxes = {}
        for task_id, task_name in TASKS.items():
            checkbox = QCheckBox(task_name)
            checkbox.setFont(big_font)  # 设置复选框字体
            checkbox.setChecked(True)  # 默认选中
            checkbox.stateChanged.connect(self.update_select_all_button_text)  # 连接状态改变信号
            self.task_checkboxes[task_id] = checkbox
            left_column.addWidget(checkbox)
        
        # 创建全选/反全选按钮
        select_all_layout = QHBoxLayout()
        self.select_all_button = QPushButton('反全选')
        self.select_all_button.setFont(big_font)
        select_all_layout.addWidget(self.select_all_button)
        select_all_layout.addStretch()  # 添加弹簧，让按钮靠左对齐
        left_column.addLayout(select_all_layout)
        
        # 添加弹簧，让左列内容靠顶部对齐
        left_column.addStretch()

        # === 右列：配置和控制区域 ===
        right_column = QVBoxLayout()
        
        # 添加配置标题
        config_title = QLabel('配置设置')
        config_title.setFont(big_font)
        config_title.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        right_column.addWidget(config_title)
        
        # 创建配置区域（垂直布局）
        config_layout = QVBoxLayout()
        
        # 活动名称配置
        activity_layout = QHBoxLayout()
        activity_label = QLabel('活动名称:')
        activity_label.setFont(big_font)
        activity_label.setMinimumWidth(120)
        self.activity_input = QTextEdit()
        self.activity_input.setMaximumHeight(50)
        self.activity_input.setFont(big_font)
        activity_layout.addWidget(activity_label)
        activity_layout.addWidget(self.activity_input)
        config_layout.addLayout(activity_layout)
        
        # 子活动名称配置
        sub_activity_layout = QHBoxLayout()
        sub_activity_label = QLabel('子活动名称:')
        sub_activity_label.setFont(big_font)
        sub_activity_label.setMinimumWidth(120)
        self.sub_activity_input = QTextEdit()
        self.sub_activity_input.setMaximumHeight(50)
        self.sub_activity_input.setFont(big_font)
        sub_activity_layout.addWidget(sub_activity_label)
        sub_activity_layout.addWidget(self.sub_activity_input)
        config_layout.addLayout(sub_activity_layout)
        
        # 商店名称配置
        shop_layout = QHBoxLayout()
        shop_label = QLabel('商店名称:')
        shop_label.setFont(big_font)
        shop_label.setMinimumWidth(120)
        self.shop_input = QTextEdit()
        self.shop_input.setMaximumHeight(50)
        self.shop_input.setFont(big_font)
        shop_layout.addWidget(shop_label)
        shop_layout.addWidget(self.shop_input)
        config_layout.addLayout(shop_layout)
        
        # 子商店名称配置
        sub_shop_layout = QHBoxLayout()
        sub_shop_label = QLabel('子商店名称:')
        sub_shop_label.setFont(big_font)
        sub_shop_label.setMinimumWidth(120)
        self.sub_shop_input = QTextEdit()
        self.sub_shop_input.setMaximumHeight(50)
        self.sub_shop_input.setFont(big_font)
        sub_shop_layout.addWidget(sub_shop_label)
        sub_shop_layout.addWidget(self.sub_shop_input)
        config_layout.addLayout(sub_shop_layout)
        
        right_column.addLayout(config_layout)

        # 创建按钮区域
        button_layout = QHBoxLayout()
        self.start_button = QPushButton('开始执行')
        self.stop_button = QPushButton('停止执行')
        self.save_config_button = QPushButton('保存配置')
        self.start_button.setFont(big_font)  # 设置按钮字体
        self.stop_button.setFont(big_font)  # 设置按钮字体
        self.save_config_button.setFont(big_font)  # 设置按钮字体
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.save_config_button)
        right_column.addLayout(button_layout)

        # 创建日志区域
        log_title = QLabel('执行日志')
        log_title.setFont(big_font)
        log_title.setStyleSheet("font-weight: bold; margin-top: 20px; margin-bottom: 10px;")
        right_column.addWidget(log_title)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(big_font)  # 设置日志区域字体
        right_column.addWidget(self.log_text)

        # 将左右两列添加到主布局
        main_layout.addLayout(left_column, 1)  # 左列占1份
        main_layout.addLayout(right_column, 2)  # 右列占2份，给更多空间

        # 连接信号
        self.start_button.clicked.connect(self.start_tasks)
        self.stop_button.clicked.connect(self.stop_tasks)
        self.save_config_button.clicked.connect(self.save_config_with_feedback)
        self.select_all_button.clicked.connect(self.toggle_select_all)

    def create_config_tab(self):
        """创建全局配置标签页"""
        config_tab = QWidget()
        self.tab_widget.addTab(config_tab, '全局配置')
        
        # 设置字体
        big_font = QFont()
        big_font.setPointSize(16)
        
        # 创建主布局
        main_layout = QVBoxLayout(config_tab)
        
        # 创建配置表单
        form_layout = QVBoxLayout()
        
        # 启动路径配置
        startup_layout = QHBoxLayout()
        startup_label = QLabel('启动路径:')
        startup_label.setFont(big_font)
        startup_label.setMinimumWidth(120)
        self.startup_path_input = QLineEdit()
        self.startup_path_input.setFont(big_font)
        self.startup_path_input.setPlaceholderText('请选择或输入启动路径')
        startup_browse_btn = QPushButton('浏览')
        startup_browse_btn.setFont(big_font)
        startup_browse_btn.clicked.connect(self.browse_startup_path)
        startup_layout.addWidget(startup_label)
        startup_layout.addWidget(self.startup_path_input)
        startup_layout.addWidget(startup_browse_btn)
        form_layout.addLayout(startup_layout)
        
        # 日志路径配置
        log_layout = QHBoxLayout()
        log_label = QLabel('日志路径:')
        log_label.setFont(big_font)
        log_label.setMinimumWidth(120)
        self.log_path_input = QLineEdit()
        self.log_path_input.setFont(big_font)
        self.log_path_input.setPlaceholderText('请选择或输入日志路径')
        log_browse_btn = QPushButton('浏览')
        log_browse_btn.setFont(big_font)
        log_browse_btn.clicked.connect(self.browse_log_path)
        log_layout.addWidget(log_label)
        log_layout.addWidget(self.log_path_input)
        log_layout.addWidget(log_browse_btn)
        form_layout.addLayout(log_layout)
        
        # 目标进程标题配置
        process_layout = QHBoxLayout()
        process_label = QLabel('目标进程标题:')
        process_label.setFont(big_font)
        process_label.setMinimumWidth(120)
        self.process_title_input = QLineEdit()
        self.process_title_input.setFont(big_font)
        self.process_title_input.setPlaceholderText('请输入目标进程窗口标题')
        process_layout.addWidget(process_label)
        process_layout.addWidget(self.process_title_input)
        form_layout.addLayout(process_layout)
        
        # 操作延时配置
        delay_layout = QHBoxLayout()
        delay_label = QLabel('操作延时(秒):')
        delay_label.setFont(big_font)
        delay_label.setMinimumWidth(120)
        self.operation_delay_input = QSpinBox()
        self.operation_delay_input.setFont(big_font)
        self.operation_delay_input.setMinimum(1)
        self.operation_delay_input.setMaximum(10)
        self.operation_delay_input.setValue(2)
        self.operation_delay_input.setSuffix(' 秒')
        delay_layout.addWidget(delay_label)
        delay_layout.addWidget(self.operation_delay_input)
        delay_layout.addStretch()
        form_layout.addLayout(delay_layout)
        
        # 添加分隔线
        separator = QLabel()
        separator.setStyleSheet("border-top: 1px solid #ccc; margin: 20px 0;")
        form_layout.addWidget(separator)
        
        # 定时功能标题
        schedule_title = QLabel('定时功能')
        schedule_title.setFont(big_font)
        schedule_title.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        form_layout.addWidget(schedule_title)
        
        # 定时功能开关
        schedule_enable_layout = QHBoxLayout()
        self.schedule_enable_checkbox = QCheckBox('启用定时执行（勾选后自动启动定时器）')
        self.schedule_enable_checkbox.setFont(big_font)
        self.schedule_enable_checkbox.stateChanged.connect(self.on_schedule_enable_changed)
        schedule_enable_layout.addWidget(self.schedule_enable_checkbox)
        schedule_enable_layout.addStretch()
        form_layout.addLayout(schedule_enable_layout)
        
        # 定时时间设置
        time_layout = QHBoxLayout()
        time_label = QLabel('执行时间:')
        time_label.setFont(big_font)
        time_label.setMinimumWidth(120)
        self.schedule_time_input = QTimeEdit()
        self.schedule_time_input.setFont(big_font)
        self.schedule_time_input.setTime(QTime(9, 0))  # 默认09:00
        self.schedule_time_input.setDisplayFormat('HH:mm')
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.schedule_time_input)
        time_layout.addStretch()
        form_layout.addLayout(time_layout)
        
        # 定时器状态显示
        status_layout = QHBoxLayout()
        status_label = QLabel('定时器状态:')
        status_label.setFont(big_font)
        status_label.setMinimumWidth(120)
        self.schedule_status_label = QLabel('已停止')
        self.schedule_status_label.setFont(big_font)
        self.schedule_status_label.setStyleSheet("color: #666;")
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.schedule_status_label)
        status_layout.addStretch()
        form_layout.addLayout(status_layout)
        

        
        main_layout.addLayout(form_layout)
        
        # 添加保存按钮
        save_global_btn = QPushButton('保存全局配置')
        save_global_btn.setFont(big_font)
        save_global_btn.clicked.connect(self.save_global_config)
        main_layout.addWidget(save_global_btn)
        
        # 添加弹簧，让配置项靠顶部对齐
        main_layout.addStretch()
        
    def browse_startup_path(self):
        """浏览启动路径"""
        file_path, _ = QFileDialog.getOpenFileName(self, '选择启动程序', '', 'Executable Files (*.exe)')
        if file_path:
            self.startup_path_input.setText(file_path)
            
    def browse_log_path(self):
        """浏览日志路径"""
        dir_path = QFileDialog.getExistingDirectory(self, '选择日志目录')
        if dir_path:
            self.log_path_input.setText(dir_path)
            
    def save_global_config(self):
        """保存全局配置"""
        try:
            # 读取现有配置
            config = {}
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # 更新全局配置
            config.update({
                'startup_path': self.startup_path_input.text(),
                'log_path': self.log_path_input.text(),
                'process_title': self.process_title_input.text(),
                'operation_delay': self.operation_delay_input.value(),
                'schedule_enabled': self.schedule_enable_checkbox.isChecked(),
                'schedule_time': self.schedule_time_input.time().toString('HH:mm')
            })
            
            # 保存配置
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
                
            # 如果定时器正在运行，重新启动定时器以应用新的时间设置
            self.refresh_schedule_timer()
                
            self.log("全局配置保存成功")
        except Exception as e:
            self.log(f"全局配置保存失败: {str(e)}")
    
    def on_schedule_enable_changed(self, state):
        """处理定时功能开关状态变化"""
        enabled = state == Qt.Checked
        self.schedule_time_input.setEnabled(enabled)
        
        if enabled:
            self.start_schedule_timer()
        else:
            self.stop_schedule_timer()
    
    def refresh_schedule_timer(self):
        """刷新定时器状态，应用新的时间设置"""
        if self.schedule_enable_checkbox.isChecked():
            # 如果定时功能启用，重新启动定时器（不管之前是否运行）
            if self.schedule_timer.isActive():
                self.stop_schedule_timer()
            self.start_schedule_timer()
            self.log("定时器已根据新配置重新启动")
        else:
            # 如果定时功能禁用，停止定时器
            if self.schedule_timer.isActive():
                self.stop_schedule_timer()
    
    def start_schedule_timer(self):
        """启动定时器"""
        # 获取设置的时间
        schedule_time = self.schedule_time_input.time()
        current_time = QTime.currentTime()
        
        # 计算到目标时间的毫秒数
        if schedule_time > current_time:
            # 今天的目标时间还没到
            ms_until_target = current_time.msecsTo(schedule_time)
        else:
            # 今天的目标时间已过，设置为明天的这个时间
            ms_until_target = current_time.msecsTo(schedule_time) + 24 * 60 * 60 * 1000
        
        # 启动定时器
        self.schedule_timer.start(ms_until_target)
        self.schedule_status_label.setText(f"已启动 - 将在 {schedule_time.toString('HH:mm')} 执行")
        self.schedule_status_label.setStyleSheet("color: #0066cc;")
        self.log(f"定时器已启动，将在 {schedule_time.toString('HH:mm')} 执行任务")
    
    def stop_schedule_timer(self):
        """停止定时器"""
        self.schedule_timer.stop()
        self.schedule_status_label.setText("已停止")
        self.schedule_status_label.setStyleSheet("color: #666;")
        self.log("定时器已停止")
    
    def execute_scheduled_tasks(self):
        """执行定时任务"""
        self.log("定时器触发，开始执行任务...")
        
        # 检查是否有任务在执行
        if self.task_thread and self.task_thread.isRunning():
            self.log("任务正在执行中，跳过本次定时执行")
            # 重新设置定时器为明天的同一时间
            self.schedule_timer.start(24 * 60 * 60 * 1000)
            return
        
        # 检查定时功能是否仍然启用
        if not self.schedule_enable_checkbox.isChecked():
            self.log("定时功能已被禁用，停止定时执行")
            return
        
        # 执行任务
        self.start_tasks()
        
        # 重新设置定时器为明天的同一时间
        self.schedule_timer.start(24 * 60 * 60 * 1000)  # 24小时后再次触发
        schedule_time = self.schedule_time_input.time()
        self.schedule_status_label.setText(f"已启动 - 将在明天 {schedule_time.toString('HH:mm')} 执行")
        self.log("定时任务执行完成，定时器已重新设置为明天同一时间")

    def load_config(self):
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 加载任务配置
                    self.activity_input.setText(config.get('activity_name', ''))
                    self.sub_activity_input.setText(config.get('activity_subname', ''))
                    self.shop_input.setText(config.get('activity_shop', ''))
                    self.sub_shop_input.setText(config.get('activity_subshop', ''))
                    # 加载上次选择的任务
                    last_tasks = config.get('last_tasks', [])
                    for task_id in last_tasks:
                        if task_id in self.task_checkboxes:
                            self.task_checkboxes[task_id].setChecked(True)
                    
                    # 加载全局配置
                    self.startup_path_input.setText(config.get('startup_path', ''))
                    self.log_path_input.setText(config.get('log_path', ''))
                    self.process_title_input.setText(config.get('process_title', 'EXILIUM'))
                    self.operation_delay_input.setValue(config.get('operation_delay', 2))
                    
                    # 加载定时配置 - 先设置时间，再设置启用状态
                    schedule_time_str = config.get('schedule_time', '09:00')
                    schedule_time = QTime.fromString(schedule_time_str, 'HH:mm')
                    if schedule_time.isValid():
                        self.schedule_time_input.setTime(schedule_time)
                    else:
                        self.schedule_time_input.setTime(QTime(9, 0))
                    # 最后设置启用状态，这样会触发正确的时间
                    self.schedule_enable_checkbox.setChecked(config.get('schedule_enabled', False))
            else:
                # 如果配置文件不存在，尝试从last_tasks.json加载
                if os.path.exists('last_tasks.json'):
                    with open('last_tasks.json', 'r', encoding='utf-8') as f:
                        last_tasks = json.load(f)
                        for task_id in last_tasks:
                            if task_id in self.task_checkboxes:
                                self.task_checkboxes[task_id].setChecked(True)
                    # 迁移完成后删除旧文件
                    os.remove('last_tasks.json')
                # 设置默认的全局配置
                self.process_title_input.setText('EXILIUM')
                self.operation_delay_input.setValue(2)
                self.schedule_enable_checkbox.setChecked(False)
                self.schedule_time_input.setTime(QTime(9, 0))
        except Exception as e:
            self.log(f"加载配置失败: {str(e)}")
            self.activity_input.setText('拂晓的回响')
            self.sub_activity_input.setText('')
            self.shop_input.setText('营地小店')
            self.sub_shop_input.setText('')
            # 如果加载失败，默认选中所有任务
            for checkbox in self.task_checkboxes.values():
                checkbox.setChecked(True)
            # 设置默认的全局配置
            self.process_title_input.setText('EXILIUM')
            self.operation_delay_input.setValue(2)
            self.schedule_enable_checkbox.setChecked(False)
            self.schedule_time_input.setTime(QTime(9, 0))
        
        # 更新全选/反全选按钮文字
        self.update_select_all_button_text()

    def save_config(self):
        selected_tasks = [task_id for task_id, checkbox in self.task_checkboxes.items() 
                         if checkbox.isChecked()]
        config = {
            'activity_name': self.activity_input.toPlainText(),
            'activity_subname': self.sub_activity_input.toPlainText(),
            'activity_shop': self.shop_input.toPlainText(),
            'activity_subshop': self.sub_shop_input.toPlainText(),
            'last_tasks': selected_tasks,
            'startup_path': self.startup_path_input.text(),
            'log_path': self.log_path_input.text(),
            'process_title': self.process_title_input.text(),
            'operation_delay': self.operation_delay_input.value(),
            'schedule_enabled': self.schedule_enable_checkbox.isChecked(),
            'schedule_time': self.schedule_time_input.time().toString('HH:mm')
        }
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

    def save_config_with_feedback(self):
        """保存配置并提供用户反馈"""
        try:
            self.save_config()
            # 如果定时器正在运行，重新启动定时器以应用新的时间设置
            self.refresh_schedule_timer()
            self.log("配置保存成功")
        except Exception as e:
            self.log(f"配置保存失败: {str(e)}")

    def log(self, message):
        self.log_text.append(message)

    def start_tasks(self):
        self.save_config()  # 保存配置
        selected_tasks = [task_id for task_id, checkbox in self.task_checkboxes.items() 
                         if checkbox.isChecked()]
        if not selected_tasks:
            self.log("请至少选择一个任务")
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # 获取当前配置
        config = {
            'process_title': self.process_title_input.text(),
            'operation_delay': self.operation_delay_input.value(),
            'log_path': self.log_path_input.text(),
            'startup_path': self.startup_path_input.text(),
            'activity_name': self.activity_input.toPlainText(),
            'activity_subname': self.sub_activity_input.toPlainText(),
            'activity_shop': self.shop_input.toPlainText(),
            'activity_subshop': self.sub_shop_input.toPlainText()
        }
        
        self.task_thread = TaskThread(selected_tasks, config)
        self.task_thread.log_signal.connect(self.log)
        self.task_thread.task_status_signal.connect(self.update_task_status)
        self.task_thread.finished.connect(self.on_tasks_finished)
        self.task_thread.start()

    def stop_tasks(self):
        if self.task_thread:
            self.task_thread.stop()
            self.log("正在停止任务...")

    def on_tasks_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def update_task_status(self, task_id, success):
        checkbox = self.task_checkboxes[task_id]
        if success:
            checkbox.setStyleSheet("color: green")
        else:
            checkbox.setStyleSheet("color: red")
    
    def toggle_select_all(self):
        """切换全选/反全选状态"""
        # 检查当前是否所有复选框都被选中
        all_checked = all(checkbox.isChecked() for checkbox in self.task_checkboxes.values())
        
        # 如果全部选中，则反全选；否则全选
        new_state = not all_checked
        
        for checkbox in self.task_checkboxes.values():
            checkbox.setChecked(new_state)
        
        # 更新按钮文字
        self.update_select_all_button_text()
    
    def update_select_all_button_text(self):
        """更新全选/反全选按钮的文字"""
        all_checked = all(checkbox.isChecked() for checkbox in self.task_checkboxes.values())
        if all_checked:
            self.select_all_button.setText('反全选')
        else:
            self.select_all_button.setText('全选')
    
    def closeEvent(self, event):
        """程序关闭时的清理工作"""
        if self.schedule_timer.isActive():
            self.schedule_timer.stop()
        if self.task_thread and self.task_thread.isRunning():
            self.task_thread.stop()
            self.task_thread.wait()
        event.accept()

def get_window_title_bar_height():
    global Title_Bar_Height
    if Title_Bar_Height != 0:
        return Title_Bar_Height
    hwnd = win32gui.FindWindow(None, Window_Title)
    # 获取窗口矩形
    window_rect = win32gui.GetWindowRect(hwnd)
    # 获取客户端矩形
    client_rect = win32gui.GetClientRect(hwnd)
    # 计算边框和标题栏宽度
    border_width = (window_rect[2] - window_rect[0] - client_rect[2]) // 2
    Title_Bar_Height = window_rect[3] - window_rect[1] - client_rect[3] - border_width * 2
    
    return Title_Bar_Height

def w_touch(target_word, confidence_threshold = 0.8, is_isolating_word = False, region = None):
    """
    查找并点击指定文字
    :param target_word: 要查找的文字
    :param confidence_threshold: OCR识别置信度阈值，默认0.8
    :param is_isolating_word: 是否要求完全匹配，默认False
    :param region: 搜索区域，默认None表示全屏
    """
    match_rect = w_exists(target_word, confidence_threshold, is_isolating_word, region)
    if match_rect:
        w_click(match_rect)
    else:
        print('Cannot find word: ' + target_word)
        raise

def w_click(rect):
    """
    点击指定矩形区域的中心点
    :param rect: 矩形区域坐标
    """
    click(getcenter(rect))

def click_fixed_pos(x, y):
    click((x, y + get_window_title_bar_height()))

def w_exists(target_word, confidence_threshold = 0.8, is_isolating_word = False, region = None, retry = 3):
    """
    检查指定文字是否存在
    :param target_word: 要查找的文字
    :param confidence_threshold: OCR识别置信度阈值，默认0.8
    :param is_isolating_word: 是否要求完全匹配，默认False
    :param region: 搜索区域，默认None表示全屏
    :param retry: 重试次数，默认3
    :return: 如果找到文字返回其矩形区域，否则返回False
    """
    for i in range(retry + 1):
        res = find_word_by_ocr(target_word, confidence_threshold, is_isolating_word, region)
        if res:
            return res
        sleep(1)
    return False

def w_wait(target_word, confidence_threshold = 0.8, is_isolating_word = False, timeout = 60, interval = 0.5, region = None):
    """
    等待指定文字出现
    :param target_word: 要等待的文字
    :param confidence_threshold: OCR识别置信度阈值，默认0.8
    :param is_isolating_word: 是否要求完全匹配，默认False
    :param timeout: 超时时间（秒），默认60
    :param interval: 检查间隔（秒），默认0.5
    :param region: 搜索区域，默认None表示全屏
    :return: 找到文字时返回其矩形区域
    """
    sum_time = 0
    match_rect = None
    while sum_time < timeout:
        match_rect = w_exists(target_word, confidence_threshold, is_isolating_word, region)
        if match_rect:
            break
        sleep(interval)
        sum_time += interval
    if not match_rect:
        print(f'Cannot find word after {timeout}s: ' + target_word)
        raise
    return match_rect

def m_touch(*args):
    """
    触摸指定位置或模板
    :param args: 位置坐标或模板对象
    """
    return touch(*args)

def m_exists(*args):
    """
    检查指定位置或模板是否存在
    :param args: 位置坐标或模板对象
    """
    return exists(*args)

def m_wait(*args):
    """
    等待指定位置或模板出现
    :param args: 位置坐标或模板对象
    """
    return wait(*args)

def add_offset(rect, offset_x, offset_y):
    """
    为矩形区域添加偏移量
    :param rect: 原始矩形区域
    :param offset_x: X轴偏移量
    :param offset_y: Y轴偏移量
    :return: 新的矩形区域
    """
    new_rect = []
    for i in range(4):
        new_x = rect[i][0] + offset_x
        new_y = rect[i][1] + offset_y
        new_rect.append([new_x, new_y])
    return new_rect
    
def getcenter(rect):
    """
    获取矩形区域的中心点坐标
    :param rect: 矩形区域
    :return: 中心点坐标 [x, y]
    """
    x = (rect[0][0] + rect[2][0]) / 2
    y = (rect[0][1] + rect[2][1]) / 2
    return [x, y]

def get_ocr_result(region = None):
    """
    获取屏幕OCR识别结果
    :param region: 识别区域，默认None表示全屏
    :return: OCR识别结果列表
    """
    screen = G.DEVICE.snapshot()
    if region != None:
        abs_region = (region[0], region[1] + get_window_title_bar_height(), region[2], region[3] + get_window_title_bar_height())
        screen = crop_image(screen, abs_region)
    filename = try_log_screen(screen)['screen']
    img_dir = ST.LOG_DIR + '\\' + filename
    result = ocr.ocr(img_dir)[0]
    return result

def find_word_by_ocr(target_word, confidence_threshold = 0.8, is_isolating_word = False, region = None):
    """
    使用OCR查找指定文字
    :param target_word: 要查找的文字
    :param confidence_threshold: OCR识别置信度阈值，默认0.8
    :param is_isolating_word: 是否要求完全匹配，默认False
    :param region: 搜索区域，默认None表示全屏
    :return: 找到文字时返回其矩形区域，否则返回None
    """
    result = get_ocr_result(region)
    match_rect = None
    match_confidence = 0
    if result == None:
        print('No words in image')
        return match_rect
    for ocr_res in result:
        confidence = ocr_res[1][1]
        if confidence < confidence_threshold:
            continue
        if is_isolating_word:
            if ocr_res[1][0] != target_word:
                continue
        elif not target_word in ocr_res[1][0]:
            continue
        #文字匹配成功
        if confidence > match_confidence:
            match_rect = ocr_res[0]
    if match_rect:
        if region is not None:
            match_rect = add_offset(match_rect, region[0], region[1] + get_window_title_bar_height())
        print(f'find word:{target_word}, confidence:{confidence}')
        print(match_rect)
    else:
        print(result)
        print('fail to find word: ' + target_word)
    return match_rect

def get_stamia():
    """
    获取当前体力值
    :return: 当前体力值（整数）
    """
    region = (1415, 7, 1595, 63)
    result = get_ocr_result(region)
    full_text = result[0][1][0]
    print(f'Current stamia: {full_text}')
    stamia_num = int(full_text.split('/')[0])
    return stamia_num
            
def collect_reward():
    """
    收集奖励
    :return: 是否成功收集奖励
    """
    sleep(2)
    if w_exists('获得道具', retry = 2):
        backarrow_common()
        return True
    else:
        return False

def return_home():
    """
    返回主页
    """
    click_fixed_pos(125, 45)

def battle_common(esimated_time = 300, is_surrender = False):
    """
    通用战斗流程
    :param esimated_time: 预计战斗时间（秒），默认300
    :param is_surrender: 是否投降，默认False
    """
    #等待加载
    for i in range(5):
        sleep(10)
        if not m_exists(Template(r"tpl1724929193896.png", rgb=True, record_pos=(0.101, -0.056), resolution=(1404, 900))):
            break
    for i in range(3):
        sleep(5)
        if m_exists(Template(r"tpl1724037341185.png", record_pos=(0.01, 0.235), resolution=(1569, 900))):
            break
    if is_surrender:
        sleep(2)
        keyevent("{ESC}")
        m_touch(Template(r"tpl1728711100189.png", rgb=True, record_pos=(-0.401, 0.313), resolution=(1270, 900)))
        m_touch(Template(r"tpl1724931266467.png", record_pos=(0.107, 0.111), resolution=(1600, 900)))
        m_touch(Template(r"tpl1724037860299.png", record_pos=(0.33, 0.231), resolution=(1600, 900))) 
        sleep(10)
        #直接失败退出
        return
    m_touch(Template(r"tpl1724037341185.png", record_pos=(0.01, 0.235), resolution=(1569, 900)))
    #跳出场动画
    click_fixed_pos(800, 420)
    sleep(10)
    #自动战斗
    dev.key_press('o')
    dev.key_release('o')
    sleep(10)
    _timer_battle = 0
    while True:
        sleep(10)
        if _timer_battle > 5*60 + esimated_time:
            raise
        elif m_exists(Template(r"tpl1724037678163.png", record_pos=(0.331, -0.174), resolution=(1600, 792))):
            m_touch(Template(r"tpl1724037678163.png", record_pos=(0.331, -0.174), resolution=(1600, 792)))
            break
        elif m_exists(Template(r"tpl1724483714783.png", rgb=True, record_pos=(-0.001, -0.207), resolution=(1600, 900))):
            m_touch(Template(r"tpl1724483714783.png", rgb=True, record_pos=(-0.001, -0.207), resolution=(1600, 900)))
            break
        _timer_battle += 10
    #此处可能出现的页面： 段位晋升、
    click_fixed_pos(800, 420)
    sleep(2)
    click_fixed_pos(800, 420)
    m_touch(Template(r"tpl1724037860299.png", record_pos=(0.33, 0.231), resolution=(1600, 900)))
    sleep(10)

def backarrow_common():
    """
    点击返回按钮
    """
    # click_fixed_pos(55, 45)
    keyevent("{ESC}")

def has_ap_alert():
    """
    检查是否有体力不足提示
    :return: 是否有体力不足提示
    """
    if w_exists('情报拼图补充'):
        m_touch(Template(r"tpl1724226645988.png", record_pos=(-0.108, 0.114), resolution=(1610, 932)))
        return True
    else:
        return False
    
def touch_btn_plus(count):
    """
    点击加号按钮
    :param count: 点加号按钮的次数
    """
    btn_plus = m_exists(Template(r"tpl1749024786440.png", record_pos=(0.139, 0.019), resolution=(1610, 932)))
    for j in range(count):
        m_touch(btn_plus)

def buy_item(is_buyout = False, item_num = 0, item_list = []):
    """
    购买物品
    :param is_buyout: 是否清空商店，默认False
    :param item_num: 要购买的商品数量，默认0
    :param item_list: 要购买的商品列表，默认空列表
    """
    v_range = 0
    if is_buyout:
        v_range = item_num
    else:
        v_range = len(item_list)
    for i in range(v_range):
        if is_buyout:
            #点击第一个商品的固定位置
            click_fixed_pos(386, 215)
        else:
            btn_item = w_exists(item_list[i])
            if not btn_item:
                continue
            else:
                w_click(btn_item)
        btn_max = m_exists(Template(r"tpl1742209087579.png", rgb=True, record_pos=(0.209, 0.051), resolution=(1610, 932)))
        btn_buy = m_exists(Template(r"tpl1742209177011.png", rgb=True, record_pos=(0.12, 0.132), resolution=(1610, 932)))
        if btn_max:
            m_touch(btn_max)
        if btn_buy:
            m_touch(btn_buy)
            if m_exists(Template(r"tpl1742209177011.png", rgb=True, record_pos=(0.12, 0.132), resolution=(1610, 932))):
                #购买失败
                backarrow_common()
                break
            collect_reward()
        else:
            backarrow_common()
            if is_buyout:
                #已经卖空
                break 
def is_homepage():
    if w_exists('战役推进') and w_exists('限时开启') and w_exists('商城') and w_exists('委托'):
        return True
    
def login_check():
    if m_exists(Template(r"login_logo_1.png", resolution=(1600, 900))) and m_exists(Template(r"login_logo_2.png", resolution=(1600, 900))):
        for i in range(60):
            sleep(10)
            if w_exists('点击开始'):
                break
        w_touch('点击开始')
    for i in range(60):
        sleep(10)
        if is_homepage():
            break
        if collect_reward():
            if w_exists('每日出勤单'):
                backarrow_common()
                break
        if w_exists('每日出勤单'):
            backarrow_common()
    if w_exists('欢乐庆典'):
        backarrow_common()
    
def mailbox():
    if not m_exists(Template(r"tpl1737028627007.png", threshold=0.9000000000000001, record_pos=(-0.443, 0.125), resolution=(1610, 932))):
        return
    m_touch(Template(r"tpl1737028627007.png", threshold=0.9000000000000001, record_pos=(-0.443, 0.125), resolution=(1610, 932)))
    m_touch(Template(r"tpl1737028977397.png", threshold=0.9500000000000002, record_pos=(-0.283, 0.257), resolution=(1610, 932)))

    collect_reward()
    return_home()
    
def ally_area():
    w_touch('班组')
    m_touch(Template(r"tpl1724037004746.png", record_pos=(0.188, 0.237), resolution=(1600, 900)))
    try:
        w_touch('领取全部')
        collect_reward()
    except:
        pass
    finally:
        backarrow_common()
        sleep(5)

    m_touch(Template(r"tpl1724037196811.png", record_pos=(0.326, 0.264), resolution=(1467, 900)))
    if w_exists('每日要务已完成'):
        pass
    else:
        m_touch(Template(r"tpl1724037235890.png", record_pos=(0.31, 0.176), resolution=(1467, 900)))
        battle_common(300)
    backarrow_common()
    #公会本入口
    m_touch(Template(r"tpl1724927792450.png", record_pos=(0.384, 0.21), resolution=(1600, 900)))
    if m_exists(Template(r"tpl1724038051306.png", record_pos=(0.367, 0.236), resolution=(1600, 900))) and not m_exists(Template(r"tpl1724927792450.png", record_pos=(0.384, 0.21), resolution=(1600, 900))):
        for i in range(2):
            m_touch(Template(r"tpl1724038051306.png", record_pos=(0.367, 0.236), resolution=(1600, 900)))
            if not m_exists(Template(r"tpl1724927868702.png", record_pos=(0.294, 0.244), resolution=(1600, 900))):
                break
            m_touch(Template(r"tpl1724038855595.png", record_pos=(0.226, 0.25), resolution=(1564, 900)))
            # #重置后直接选最前面的4个
            click_fixed_pos(100, 400)
            click_fixed_pos(100+115, 400)
            click_fixed_pos(100+115*2, 400)
            click_fixed_pos(100+115*3, 400)
            m_touch(Template(r"tpl1724039182987.png", record_pos=(0.422, 0.193), resolution=(1600, 900)))
            zhuzhan_region = (260, 175, 1340, 900)
            w_touch('酸蚀', region = zhuzhan_region)
            w_touch('可露凯', region = zhuzhan_region)
            m_touch(Template(r"tpl1724039310900.png", record_pos=(0.32, 0.187), resolution=(1408, 900)))
            if m_exists(Template(r"tpl1724931239978.png", record_pos=(0.0, -0.126), resolution=(1600, 900))) and w_exists('队伍中有相同角色'):
                m_touch(Template(r"tpl1724931266467.png", record_pos=(0.107, 0.111), resolution=(1600, 900)))
                #补空位
                click_fixed_pos(100+115*4, 400)
            m_touch(Template(r"tpl1724038095179.png", record_pos=(0.384, 0.244), resolution=(1600, 900)))
            sleep(2)
            battle_common(360)
        w_touch('前线补给')
        try:
            m_touch(Template(r"tpl1739433596338.png", record_pos=(-0.002, 0.132), resolution=(1610, 932)))
            collect_reward()
        except:
            pass
        w_touch('班组表现', region = (400, 100, 1200, 800))
        try:
            m_touch(Template(r"tpl1739433596338.png", record_pos=(-0.002, 0.132), resolution=(1610, 932)))
            collect_reward()
        except:
            pass
        backarrow_common()
    #返回主页
    return_home()

def public_area():
    w_touch('公共区')
    w_touch('调度室')
    try:
        w_touch('键领取')
        w_touch('再次派遣')
    except:
        pass
    try:
        touch(Template(r"tpl1742922535723.png", record_pos=(-0.234, 0.18), resolution=(1610, 932)))
        if w_exists('本周派遣收益'):
            btn_collect = w_exists('领取')
            if btn_collect:
                w_click(btn_collect)
                collect_reward()
            backarrow_common()
        else:
            collect_reward()
    except:
        pass
    w_touch('调度收益')
    m_touch(Template(r"tpl1724042868258.png", record_pos=(0.106, 0.221), resolution=(1600, 900)))
    w_touch('资源生产')
    m_touch(Template(r"tpl1724042910758.png", record_pos=(0.308, 0.248), resolution=(1430, 900)))
    collect_reward()
    backarrow_common()
    #返回主页
    return_home()

def daily_battle():
    w_touch('战役推进')
    w_touch('模拟作战')
    #实兵演习
    w_touch('实兵演习')
    #每周的结算页面
    click_fixed_pos(800, 420)
    sleep(1)
    click_fixed_pos(800, 420)
    sleep(1)
    click_fixed_pos(800, 420)
    sleep(1)
    click_fixed_pos(800, 420)
    sleep(1)
    click_fixed_pos(800, 420)
    sleep(1)
    click_fixed_pos(800, 420)
    m_touch(Template(r"tpl1724040492694.png", record_pos=(0.38, 0.245), resolution=(1600, 900)))
    #每天3次 打1次退2次
    first_battle = True
    for i in range(3):
        m_touch(Template(r"tpl1724225312105.png", record_pos=(0.441, 0.249), resolution=(1600, 900)))
        #刷新次数用尽了
        if m_exists(Template(r"tpl1724236208525.png", record_pos=(0.001, -0.127), resolution=(1600, 900))):
            m_touch(Template(r"tpl1724236220728.png", record_pos=(-0.107, 0.113), resolution=(1600, 900)))
        #直接选中间的对手
        click_fixed_pos(300, 420)
        if w_exists('基础防守演习'):
            m_touch(Template(r"tpl1724224751372.png", record_pos=(0.261, 0.124), resolution=(1600, 900)))
            sleep(2)
            #检查次数是否用完
            if w_exists('基础防守演习'):
                backarrow_common()
                break
            else:
                battle_common(10)
#                 battle_common(10, not first_battle)
#                 first_battle = False
        else:
            pass
    #关闭选择对手页面
    backarrow_common()
    #返回模拟作战页面
    backarrow_common()

    w_touch('补给作战')
    #经验本
    m_touch(Template(r"tpl1724041440458.png", record_pos=(-0.327, -0.082), resolution=(1214, 900))) 
    def repeat_battle(battle_times, multi_factor = 1):
        if multi_factor < 1:
            return
        for i in range(battle_times):
            m_touch(Template(r"tpl1724040793103.png", record_pos=(0.261, 0.239), resolution=(1600, 900)))
            #检查体力
            if has_ap_alert():
                backarrow_common()
                break
            elif w_exists('自律准备'):
                if multi_factor > 1:
                    touch_btn_plus(multi_factor - 1)
                m_touch(Template(r"tpl1724040944534.png", record_pos=(0.107, 0.12), resolution=(1600, 900)))
                if has_ap_alert():
                    backarrow_common()
                    break
                sleep(3)
                collect_reward()
            else:
                raise
    cur_stamia = get_stamia()
    multi_ten, remainder = divmod(cur_stamia, 100)
    multi_single, remainder = divmod(remainder, 10)
    repeat_battle(multi_ten, 10)
    repeat_battle(1, multi_single)
    #返回主页
    return_home()

def daily_task():
    w_touch('委托')
    if w_exists('已全部领取'):
        pass
    else:
        try:
            m_touch(Template(r"tpl1724041727519.png", record_pos=(0.367, 0.232), resolution=(1600, 900)))
        except:
            pass
        finally:
            try:
                m_touch(Template(r"tpl1724041750798.png", record_pos=(-0.346, 0.152), resolution=(1219, 900)))
                collect_reward()
            except:
                pass
    return_home()
    
    if w_exists('巡录'):
        w_touch('巡录')
        w_touch('沿途行动')
        try:
            m_touch(Template(r"tpl1724042132942.png", record_pos=(0.367, 0.249), resolution=(1600, 900)))
        except:
            pass
        #等升级动画结束
        sleep(5)
        w_touch('远航巡录')
        if m_exists(Template(r"tpl1724228593870.png", record_pos=(0.411, 0.065), resolution=(1600, 900))):
            m_touch(Template(r"tpl1724228593870.png", record_pos=(0.411, 0.065), resolution=(1600, 900)))
            m_touch(Template(r"tpl1724228701339.png", record_pos=(0.107, 0.134), resolution=(1600, 900)))
            while select_bp_reward():
                pass
            collect_reward()
        return_home()

def select_bp_reward():
    if not m_exists(Template(r"tpl1724555019676.png", rgb=True, record_pos=(-0.071, 0.133), resolution=(1600, 900))):
        return False
    if w_exists('拂晓之光补给包'):
        touch(Template(r"tpl1742921042606.png", threshold=0.8, rgb=True, record_pos=(-0.237, -0.072), resolution=(1610, 932)))
        touch(Template(r"tpl1724237055401.png", record_pos=(0.107, 0.133), resolution=(1600, 900)))
        return True
    elif w_exists('标准武器自选礼箱'):
        w_touch('复仇女神')
        touch(Template(r"tpl1724237055401.png", record_pos=(0.107, 0.133), resolution=(1600, 900)))
        return True
    else:
        return False

def weekly_task():
    w_touch('战役推进')
    w_touch('模拟作战')
    m_touch(Template(r"tpl1724648488359.png", rgb=True, record_pos=(0.103, -0.147), resolution=(1600, 900)))
    if not w_exists('一键领取'):
        w_touch('周期报酬')

    if not w_exists('已领取本周期内全部报酬') and w_exists('一键领取'):
        w_touch('一键领取')
        collect_reward()
    backarrow_common()
    backarrow_common()
    #首领
    swipe((300,450), (1300, 450))
    w_touch('首领挑战')
    _v_btn_zilv = m_exists(Template(r"tpl1724648945638.png", rgb=True, record_pos=(0.345, 0.283), resolution=(1350, 900)))
    if not _v_btn_zilv:
        return_home()
        return
    m_touch(_v_btn_zilv)
    if w_exists('自律准备', is_isolating_word = True):
        touch_btn_plus(2)
        m_touch(Template(r"tpl1724649003384.png", rgb=True, record_pos=(0.219, 0.141), resolution=(1350, 900)))
        collect_reward()
    return_home()

def frontline_activity():
    w_touch('限时开启')
    w_touch('边界推进')
    w_touch('晶源采集')
    if w_exists('前往探索'):
        return_home()
        return
    try:
        touch(Template(r"tpl1742834854161.png", rgb=True, record_pos=(0.193, 0.256), resolution=(1620, 964)))
    except:
        pass
    try:
        w_touch('领取')
        w_touch('获得道具')
        sleep(2)
    except:
        pass
    return_home()

def reusable_activity():
    w_touch('活动')
    btn_zhanqianbuji = w_exists('战前补给')
    if btn_zhanqianbuji:
        w_click(btn_zhanqianbuji)
        btn_lingqu = w_exists('领取', is_isolating_word = True)
        if btn_lingqu:
            w_click(btn_lingqu)
            collect_reward()
    btn_qingbaobuji = w_exists('情报补给')
    if btn_qingbaobuji:
        w_click(btn_qingbaobuji)
        try:
            w_touch('领取', is_isolating_word = True)
            collect_reward()
        except:
            pass
        try:
            w_touch('领取', is_isolating_word = True)
            collect_reward()
        except:
            pass
    return_home()

def period_task():
    w_touch('战役推进')
    w_touch('模拟作战')
    swipe((1300, 450), (300,450))
    w_touch('兵棋推演')
    sleep(2)
    w_touch('奖励预览')
    w_touch('参与奖励')
    for i in range(3):
        try:
            w_touch('领取')
            collect_reward()
        except:
            break
    if not w_exists('未完成'):
        #奖励已领完 不需要继续
        backarrow_common()
        return_home()
        return
    backarrow_common()
    for i in range(5):
        w_touch('匹配', is_isolating_word = True)
        sleep(3)
        if w_exists('百炼荣光'):
            break
        sleep(30)
        dev.keyevent("{ESC}")
        w_wait('退出作战')
        w_touch('退出作战')
        w_touch('确认', is_isolating_word = True)
        w_wait('战斗失败')
        sleep(2)
        w_touch('战斗失败')
        w_wait('百炼荣光')
    w_touch('奖励预览')
    w_touch('参与奖励')
    for i in range(3):
        try:
            w_touch('领取')
            collect_reward()
        except:
            break
    backarrow_common()
    return_home()
    
def temporary_activity(activity_name='', sub_activity_name=''):
    w_touch('限时开启')
    if activity_name:
        w_touch(activity_name)
    if sub_activity_name:
        w_touch(sub_activity_name)
    w_touch('物资')
    w_touch('1-5')
    m_touch(Template(r"tpl1732055215502.png", record_pos=(0.291, 0.253), resolution=(1610, 932)))
    touch_btn_plus(5)
    m_touch(Template(r"tpl1732055268161.png", record_pos=(0.106, 0.12), resolution=(1610, 932)))
    if m_exists(Template(r"tpl1732055268161.png", record_pos=(0.106, 0.12), resolution=(1610, 932))):
        sleep(2)
        keyevent("{ESC}")
    else:
        collect_reward()
    backarrow_common()
    backarrow_common()
    return_home()
    
def shopping(activity_shop='', sub_shop_name=''):
    w_touch('商城')
    w_touch('品质甄选')
    w_touch('限时礼包')
    try:
        w_touch('周周乐补给箱')
        w_touch('购买', is_isolating_word = True)
        collect_reward()
    except:
        pass
    w_touch('周期礼包')
    w_touch('每日补给箱')
    if w_exists('购买', is_isolating_word = True):
        w_touch('购买', is_isolating_word = True)
        collect_reward()
    backarrow_common()
    sleep(2)
    w_touch('易物所')
    if activity_shop:
        w_touch(activity_shop)
    if sub_shop_name:
        w_touch(sub_shop_name)
    buy_item(True, 22)
    backarrow_common()
    w_touch('调度商店')
    buy_item(True, 14)
    # buy_item(item_list = ['访问许可', '紫色心意礼盒·一', '紫色心意礼盒·二', '紫色心意礼盒·三', '紫色心意礼盒·四', '紫色心意礼盒·五'])
    backarrow_common()
    w_touch('班组商店')
    buy_item(item_list = ['波波沙心智存档', '火控校准芯片'])
    backarrow_common()
    w_touch('讯段交易')
    buy_item(item_list = ['塞布丽娜心智存档', '访问许可', '基原信息核'])
    backarrow_common()
    w_touch('人形堆栈')
    buy_item(item_list = ['火控校准芯片', '访问许可', '专访许可', '大容量内存条'])
    backarrow_common()

def setup_env(title_name, OPDELAY, LOG_DIR, startup_path):
    global Window_Title, dev
    Window_Title = title_name
    ST.OPDELAY = OPDELAY
    ST.SNAPSHOT_QUALITY = 80
    if LOG_DIR:
        ST.LOG_DIR = LOG_DIR
    
    #检查目标Windows进程是否运行，如果未运行则启动
    gf2_window = win32gui.FindWindow(None, title_name)
    print(f"查找窗口 '{title_name}': {gf2_window}")
    
    if gf2_window == 0:  # FindWindow返回0表示未找到窗口
        print("目标窗口未运行，准备启动...")
        if startup_path:
            #根据配置中的startup_path，启动
            print(f"启动程序: {startup_path}")
            subprocess.Popen(startup_path)
            time.sleep(30)
            gf2_window = win32gui.FindWindow(None, title_name)
            print(f"重新查找窗口: {gf2_window}")
            if gf2_window == 0:
                raise Exception("目标窗口未运行")
            else:
                print("目标窗口已启动并运行")
        else:
            raise Exception("目标窗口未运行且未设置启动路径")
    else:
        print("目标窗口已运行")
    
    if dev is None:
        auto_setup(__file__, devices=["Windows:///?title_re=" + title_name])
        dev = device()



if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec_() 
