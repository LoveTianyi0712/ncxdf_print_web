#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import os
import secrets
from utils import ProofPrintSimulator, TEMPLATE_MAPPING
import base64
from io import BytesIO
from config import config
import pymysql

# 安装PyMySQL作为MySQLdb的替代
pymysql.install_as_MySQLdb()

app = Flask(__name__)

# 从环境变量获取配置模式，默认为development
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config.get(config_name, config['default']))

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录才能访问此页面'

# 数据库模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin' or 'user'
    is_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    print_logs = db.relationship('PrintLog', backref='user', lazy=True)

class PrintLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student_code = db.Column(db.String(50), nullable=False)
    student_name = db.Column(db.String(100), nullable=False)
    biz_type = db.Column(db.Integer, nullable=False)
    biz_name = db.Column(db.String(50), nullable=False)
    print_time = db.Column(db.DateTime, default=datetime.utcnow)
    print_data = db.Column(db.Text, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 权限装饰器
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('需要管理员权限才能访问此页面', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# 路由
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            if not user.is_enabled:
                flash('账号已被禁用，请联系管理员', 'error')
                return render_template('login.html')
            
            login_user(user)
            flash(f'欢迎回来，{user.username}！', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已成功退出登录', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # 获取用户的打印记录统计
    user_print_count = PrintLog.query.filter_by(user_id=current_user.id).count()
    
    # 如果是管理员，获取更多统计信息
    stats = {}
    if current_user.role == 'admin':
        stats = {
            'total_users': User.query.count(),
            'active_users': User.query.filter_by(is_enabled=True).count(),
            'total_prints': PrintLog.query.count(),
            'recent_prints': PrintLog.query.order_by(PrintLog.print_time.desc()).limit(5).all()
        }
    
    return render_template('dashboard.html', user_print_count=user_print_count, stats=stats)

@app.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/create_user', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if request.method == 'POST':
        usernames = request.form.get('usernames', '').strip()
        passwords = request.form.get('passwords', '').strip()
        role = request.form.get('role', 'user')
        
        if not usernames:
            flash('请输入用户名', 'error')
            return render_template('create_user.html')
        
        # 处理批量创建
        username_list = [u.strip() for u in usernames.split('\n') if u.strip()]
        password_list = []
        
        if passwords:
            password_list = [p.strip() for p in passwords.split('\n') if p.strip()]
        
        created_users = []
        errors = []
        
        for i, username in enumerate(username_list):
            if User.query.filter_by(username=username).first():
                errors.append(f'用户名 {username} 已存在')
                continue
            
            # 如果提供了密码列表，使用对应的密码，否则使用默认密码
            if i < len(password_list):
                password = password_list[i]
            else:
                password = '123456'  # 默认密码
            
            user = User(
                username=username,
                password_hash=generate_password_hash(password),
                role=role,
                created_by=current_user.id
            )
            db.session.add(user)
            created_users.append({'username': username, 'password': password})
        
        try:
            db.session.commit()
            if created_users:
                flash(f'成功创建 {len(created_users)} 个用户', 'success')
            if errors:
                for error in errors:
                    flash(error, 'warning')
            return render_template('user_created.html', users=created_users)
        except Exception as e:
            db.session.rollback()
            flash(f'创建用户失败：{str(e)}', 'error')
    
    return render_template('create_user.html')

@app.route('/toggle_user/<int:user_id>')
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('不能禁用自己的账号', 'error')
    else:
        user.is_enabled = not user.is_enabled
        db.session.commit()
        status = '启用' if user.is_enabled else '禁用'
        flash(f'已{status}用户 {user.username}', 'success')
    return redirect(url_for('users'))

@app.route('/print')
@login_required
def print_page():
    return render_template('print.html', template_mapping=TEMPLATE_MAPPING)

@app.route('/search_student')
@login_required
def search_student():
    student_code = request.args.get('student_code', '').strip()
    
    if not student_code:
        return jsonify({'error': '请输入学员编码'}), 400
    
    # 模拟数据 - 后续需要替换为实际的数据库查询
    mock_data = {
        'NC6080119755': {
            'student_name': '王淳懿',
            'gender': '未知',
            'reports': [
                {
                    'biz_type': 6,
                    'biz_name': '学员账户充值提现凭证',
                    'data': {
                        "nSchoolId": 35,
                        "sSchoolName": "南昌学校",
                        "sTelePhone": "400-175-9898",
                        "sOperator": current_user.username,
                        "dtCreate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Title": "提现凭证",
                        "PrintNumber": 1,
                        "YNVIEWPrint": 1,
                        "PrintDocument": "",
                        "sStudentCode": student_code,
                        "sStudentName": "王淳懿",
                        "sGender": "未知",
                        "sPay": "提现金额：¥1499.00",
                        "dSumBalance": "余额：¥0.00",
                        "sPayType": "提现方式：现金支付¥1499.00",
                        "dtCreateDate": "2025-06-04 09:04:30",
                        "sProofName": "提现凭证",
                        "sBizType": "提现",
                        "nBizId": 126560050,
                        "sRegZoneName": "客服行政"
                    }
                },
            ]
        },
        'NC6080119756': {
            'student_name': '张三',
            'gender': '男',
            'reports': [
                {
                    'biz_type': 6,
                    'biz_name': '学员账户充值提现凭证',
                    'data': {
                        "nSchoolId": 35,
                        "sSchoolName": "南昌学校",
                        "sTelePhone": "400-175-9898",
                        "sOperator": current_user.username,
                        "dtCreate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Title": "提现凭证",
                        "PrintNumber": 1,
                        "YNVIEWPrint": 1,
                        "PrintDocument": "",
                        "sStudentCode": student_code,
                        "sStudentName": "张三",
                        "sGender": "男",
                        "sPay": "报名费用：¥3999.00",
                        "dSumBalance": "余额：¥0.00",
                        "sPayType": "支付方式：支付宝¥3999.00",
                        "dtCreateDate": "2025-06-04 10:30:20",
                        "sProofName": "学员账户充值提现凭证",
                        "sBizType": "提现",
                        "nBizId": 126560002,
                        "sRegZoneName": "客服行政"
                    }
                }
            ]
        }
    }
    
    if student_code in mock_data:
        return jsonify(mock_data[student_code])
    else:
        return jsonify({'error': '未找到该学员的信息'}), 404

@app.route('/generate_print', methods=['POST'])
@login_required
def generate_print():
    try:
        data = request.json
        biz_type = data.get('biz_type')
        student_data = data.get('student_data')
        
        if not biz_type or not student_data:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 创建打印消息
        message = {
            "PrintType": "proofprintnew",
            "Info": {
                "Params": {
                    "BizType": biz_type,
                    "JsonString": json.dumps(student_data),
                    "DefaultPrinter": "",
                    "DefaultPrintNumber": 1,
                    "NeedPreview": True,
                    "SchoolId": 35,
                    "CurrencySymbol": "¥"
                }
            }
        }
        
        # 生成打印图像
        simulator = ProofPrintSimulator()
        image_path = simulator.process_print_request(message)
        
        if image_path and os.path.exists(image_path):
            # 将图像转换为base64
            with open(image_path, 'rb') as img_file:
                img_data = base64.b64encode(img_file.read()).decode()
            
            # 获取文件名
            filename = os.path.basename(image_path)
            
            # 记录打印日志
            print_log = PrintLog(
                user_id=current_user.id,
                student_code=student_data.get('sStudentCode', ''),
                student_name=student_data.get('sStudentName', ''),
                biz_type=biz_type,
                biz_name=TEMPLATE_MAPPING.get(biz_type, '未知类型').replace('.mrt', ''),
                print_data=json.dumps(student_data, ensure_ascii=False)
            )
            db.session.add(print_log)
            db.session.commit()
            
            # 清理临时文件
            try:
                os.remove(image_path)
                json_file = image_path.replace('.png', '.json')
                if os.path.exists(json_file):
                    os.remove(json_file)
            except:
                pass
            
            return jsonify({
                'success': True,
                'image': img_data,
                'filename': filename
            })
        else:
            return jsonify({'error': '打印处理失败'}), 500
            
    except Exception as e:
        return jsonify({'error': f'生成打印失败：{str(e)}'}), 500

@app.route('/print_logs')
@login_required
def print_logs():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    if current_user.role == 'admin':
        # 管理员可以查看所有日志
        logs = PrintLog.query.order_by(PrintLog.print_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    else:
        # 普通用户只能查看自己的日志
        logs = PrintLog.query.filter_by(user_id=current_user.id).order_by(
            PrintLog.print_time.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('print_logs.html', logs=logs)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证输入
        if not current_password or not new_password or not confirm_password:
            flash('所有字段都是必填的', 'error')
            return render_template('change_password.html')
        
        # 验证当前密码
        if not check_password_hash(current_user.password_hash, current_password):
            flash('当前密码不正确', 'error')
            return render_template('change_password.html')
        
        # 验证新密码长度
        if len(new_password) < 6:
            flash('新密码长度至少6位', 'error')
            return render_template('change_password.html')
        
        # 验证密码确认
        if new_password != confirm_password:
            flash('新密码和确认密码不匹配', 'error')
            return render_template('change_password.html')
        
        # 检查新密码是否与当前密码相同
        if check_password_hash(current_user.password_hash, new_password):
            flash('新密码不能与当前密码相同', 'error')
            return render_template('change_password.html')
        
        try:
            # 更新密码
            current_user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            flash('密码修改成功！', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'密码修改失败：{str(e)}', 'error')
            return render_template('change_password.html')
    
    return render_template('change_password.html')

def create_admin_user():
    """创建默认管理员账户"""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("默认管理员账户已创建 - 用户名: admin, 密码: admin123")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_user()
    
    app.run(debug=True, host='0.0.0.0', port=5000) 