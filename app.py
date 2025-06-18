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
from utils import (
    ProofPrintSimulator, 
    TEMPLATE_MAPPING,
    CERTIFICATE_TYPES,
    print_certificate_by_biz_type,
    get_available_certificates
)
# 新的凭证管理器
from utils.certificate_manager import (
    generate_certificate_by_type,
    get_available_certificates as get_new_certificates
)
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
    # 新增字段用于列表展示
    detail_info = db.Column(db.String(200), nullable=True)  # 详细信息，如"类型：充值，金额：¥1000.00"

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
        # 新功能测试数据（使用原有编码）
        'NC2024001': {
            'student_name': '张小明',
            'gender': '男',
            'reports': [
                {
                    'biz_type': 1,  # 班级凭证（使用原有编码1）
                    'biz_name': '班级凭证',
                    'data': {
                        # 基本信息
                        'sSchoolName': '南昌学校',
                        'sTelePhone': '400-175-9898',
                        'sChannel': '直营',
                        
                        # 学员信息
                        'sStudentName': '张小明',
                        'sStudentCode': 'NC2024001',
                        'sGender': '男',
                        'sCardCode': 'CARD001234',
                        
                        # 班级信息
                        'sClassName': '高中数学春季班',
                        'sClassCode': 'MATH2024SP001',
                        'sSeatNo': 'A015',
                        'dtBeginDate': '2024-03-01',
                        'dtEndDate': '2024-06-30',
                        'nTryLesson': '2节',
                        
                        # 时间信息
                        'sRegisterTime': '2024-02-15 10:30:00 报名成功，欢迎参加南昌学校高中数学春季班学习！',
                        'sPrintAddress': '南昌市红谷滩新区学府大道1号南昌学校',
                        'sPrintTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'dtCreate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        
                        # 费用信息
                        'dFee': 3800.00,           # 商品标准金额
                        'dVoucherFee': 300.00,     # 商品优惠金额
                        'dShouldFee': 3800.00,     # 商品应收金额
                        'dRealFee': 3500.00,       # 商品实收金额
                        
                        # 操作信息
                        'sOperator': current_user.username,
                        
                        # 图像数据（可选）
                        'RWMImage': ''
                    }
                }
            ]
        },
        'NC2024002': {
            'student_name': '李小红',
            'gender': '女',
            'reports': [
                {
                    'biz_type': 6,  # 学员账户凭证 - 充值（使用原有编码6）
                    'biz_name': '学员账户充值提现凭证',
                    'data': {
                        'nSchoolId': '001',
                        'sSchoolName': '南昌学校',
                        'sOperator': current_user.username,
                        'sStudentCode': 'NC2024002',
                        'sStudentName': '李小红',
                        'sPay': '15000.00',
                        'sPayType': '支付宝',
                        'sProofName': '充值凭证',
                        'sBizType': '充值',
                        'dSumBalance': '25000.00',
                        'dtCreateDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'sTelePhone': '400-175-9898',
                        'Title': '充值凭证'
                    }
                },
                {
                    'biz_type': 6,  # 学员账户凭证 - 提现（使用原有编码6）
                    'biz_name': '学员账户充值提现凭证',
                    'data': {
                        'nSchoolId': '001',
                        'sSchoolName': '南昌学校',
                        'sOperator': current_user.username,
                        'sStudentCode': 'NC2024002',
                        'sStudentName': '李小红',
                        'sPay': '8000.00',
                        'sPayType': '银行转账',
                        'sProofName': '提现凭证',
                        'sBizType': '提现',
                        'dSumBalance': '17000.00',
                        'dtCreateDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'sTelePhone': '400-175-9898',
                        'Title': '提现凭证'
                    }
                }
            ]
        },
        'NC2024003': {
            'student_name': '王小强',
            'gender': '男',
            'reports': [
                {
                    'biz_type': 8,  
                    'biz_name': '退费凭证',
                    'data': {
                        # 基本信息
                        'sSchoolName': '南昌学校',
                        'sTelePhone': '400-175-9898',
                        'Title': '退费凭证',
                        'sBizType': '退费',
                        'sOperator': current_user.username,
                        'dtCreate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'dtCreateDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        
                        # 学员信息
                        'sStudentName': '王小强',
                        'sStudentCode': 'NC2024003',
                        'sGender': '男',
                        'sSeatNo': 'B012',
                        'sRegZoneName': '南昌红谷滩校区',
                        
                        # 班级信息
                        'sClassName': '初中英语暑期班',
                        'sClassCode': 'ENG2024SU001',
                        
                        # 金额信息
                        'dRefundFee': 2800.00,          # 退费金额
                        'sPay': '2800.00',              # 退费金额（字符串格式）
                        'sPayType': '银行转账',          # 退费方式
                        'dSumBalance': '3200.00',       # 余额
                    }
                }
            ]
        },
        
        # 传统凭证测试数据（保持原有）
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
                        "sPay": "提现金额：¥1,499.00",
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
        student_info = mock_data[student_code]
        
        # 为每个报告添加详细信息描述
        for report in student_info.get('reports', []):
            biz_type = report.get('biz_type')
            data = report.get('data', {})
            
            # 生成详细信息描述
            _, detail_info = _get_certificate_info(biz_type, data)
            report['description'] = detail_info
        
        return jsonify(student_info)
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
        
        # 使用新的凭证管理器生成打印图像
        # 方法1: 使用新的独立处理器（推荐）
        try:
            image_path = generate_certificate_by_type(biz_type, student_data)
        except Exception as e:
            print(f"新处理器失败: {str(e)}")
            image_path = None
        
        # 方法2: 如果新处理器失败，使用原有方法（备选）
        if not image_path:
            try:
                image_path = print_certificate_by_biz_type(biz_type, student_data)
            except Exception as e:
                print(f"原有方法也失败: {str(e)}")
                image_path = None
        
        # 方法3: 最后的传统方法（保底）
        if not image_path:
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
            
            # 根据biz_type确定凭证名称和详细信息
            biz_name, detail_info = _get_certificate_info(biz_type, student_data)
            
            print_log = PrintLog(
                user_id=current_user.id,
                student_code=student_data.get('sStudentCode', ''),
                student_name=student_data.get('sStudentName', ''),
                biz_type=biz_type,
                biz_name=biz_name,
                print_data=json.dumps(student_data, ensure_ascii=False),
                detail_info=detail_info
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

@app.route('/api/certificate_types')
@login_required  
def api_certificate_types():
    """获取所有可用的凭证类型信息"""
    try:
        certificates = get_available_certificates()
        
        # 转换为前端友好的格式
        result = []
        for cert_type, config in certificates.items():
            for i, template in enumerate(config['templates']):
                biz_type = config['biz_types'][i] if i < len(config['biz_types']) else config['biz_types'][0]
                result.append({
                    'biz_type': biz_type,
                    'template_name': template,
                    'category': cert_type,
                    'processor': config['processor'],
                    'display_name': template.replace('.mrt', '')
                })
        
        return jsonify({
            'success': True,
            'certificates': result,
            'template_mapping': TEMPLATE_MAPPING
        })
    except Exception as e:
        return jsonify({'error': f'获取凭证类型失败：{str(e)}'}), 500

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

def _get_certificate_info(biz_type, student_data):
    """根据业务类型和学员数据生成凭证名称和详细信息"""
    from utils.certificate_manager import CERTIFICATE_MAPPING
    
    # 获取基本凭证名称
    if biz_type in CERTIFICATE_MAPPING:
        biz_name = CERTIFICATE_MAPPING[biz_type]['name']
    else:
        biz_name = "未知凭证类型"
    
    # 生成详细信息
    detail_info = ""
    
    if biz_type == 6:  # 学员账户充值提现凭证
        # 判断是充值还是提现
        operation_type = "充值"
        pay_info = student_data.get('sPay', '')
        if '提现' in pay_info or '退' in pay_info:
            operation_type = "提现"
        
        # 获取金额信息 - 改进逻辑
        amount = ""
        
        # 首先尝试从sPay字段提取金额
        if pay_info:
            import re
            # 尝试从字符串中提取金额数字
            amount_match = re.search(r'¥?(\d+(?:,\d{3})*(?:\.\d{2})?)', pay_info)
            if amount_match:
                amount_str = amount_match.group(1).replace(',', '')
                try:
                    amount_value = float(amount_str)
                    amount = f"¥{amount_value:,.2f}"
                except:
                    amount = pay_info  # 如果解析失败，使用原始字符串
            else:
                amount = pay_info  # 如果没有找到数字，使用原始字符串
        
        # 如果sPay没有金额信息，尝试dSumBalance
        if not amount and student_data.get('dSumBalance'):
            balance_info = student_data.get('dSumBalance', '')
            if isinstance(balance_info, (int, float)):
                amount = f"¥{balance_info:,.2f}"
            else:
                # 尝试从字符串中提取数字
                import re
                balance_match = re.search(r'¥?(\d+(?:,\d{3})*(?:\.\d{2})?)', str(balance_info))
                if balance_match:
                    balance_str = balance_match.group(1).replace(',', '')
                    try:
                        balance_value = float(balance_str)
                        amount = f"¥{balance_value:,.2f}"
                    except:
                        amount = str(balance_info)
        
        detail_info = f"类型：{operation_type}"
        if amount:
            detail_info += f"，金额：{amount}"
            
    elif biz_type == 1:  # 报班凭证
        class_name = student_data.get('sClassName', '')
        fee = student_data.get('dRealFee', student_data.get('dFee', ''))
        
        detail_info = f"班级：{class_name}"
        if fee:
            try:
                fee_value = float(fee)
                detail_info += f"，费用：¥{fee_value:,.2f}"
            except:
                detail_info += f"，费用：{fee}"
                
    elif biz_type == 8:  # 退费凭证
        refund_amount = student_data.get('dRefundFee', student_data.get('dFee', ''))
        
        detail_info = f"退费"
        if refund_amount:
            try:
                amount_value = float(refund_amount)
                detail_info += f"：¥{amount_value:,.2f}"
            except:
                detail_info += f"：{refund_amount}"
            
    elif biz_type == 3:  # 退班凭证
        class_name = student_data.get('sClassName', '')
        detail_info = f"退班"
        if class_name:
            detail_info += f"：{class_name}"
            
    elif biz_type == 5:  # 处理可能的biz_type=5（与biz_type=1相同逻辑）
        class_name = student_data.get('sClassName', '')
        fee = student_data.get('dRealFee', student_data.get('dFee', ''))
        
        detail_info = f"班级：{class_name}"
        if fee:
            try:
                fee_value = float(fee)
                detail_info += f"，费用：¥{fee_value:,.2f}"
            except:
                detail_info += f"，费用：{fee}"
    
    # 如果没有生成详细信息，使用默认信息
    if not detail_info:
        detail_info = f"BizType: {biz_type}"
    
    return biz_name, detail_info

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