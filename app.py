#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
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
from utils.time_utils import get_beijing_time_str, get_beijing_timestamp, get_beijing_datetime
# 新的凭证管理器
from utils.certificate_manager import (
    generate_certificate_by_type,
    get_available_certificates as get_new_certificates
)
import base64
from io import BytesIO
from config import config
import pymysql
# 验证码相关导入
from PIL import Image, ImageDraw, ImageFont
import random
import string

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
    is_first_login = db.Column(db.Boolean, default=True)  # 是否是首次登录
    created_at = db.Column(db.DateTime, default=get_beijing_datetime)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    print_logs = db.relationship('PrintLog', backref='user', lazy=True)

class PrintLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student_code = db.Column(db.String(50), nullable=False)
    student_name = db.Column(db.String(100), nullable=False)
    biz_type = db.Column(db.Integer, nullable=False)
    biz_name = db.Column(db.String(50), nullable=False)
    print_time = db.Column(db.DateTime, default=get_beijing_datetime)
    print_data = db.Column(db.Text, nullable=False)
    # 新增字段用于列表展示
    detail_info = db.Column(db.String(200), nullable=True)  # 详细信息，如"类型：充值，金额：¥1000.00"
    # 软删除字段
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)  # 软删除标记

class CookiesConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default='ERP Cookies')
    cookies_data = db.Column(db.Text, nullable=False)  # JSON格式存储cookies
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_beijing_datetime)
    updated_at = db.Column(db.DateTime, default=get_beijing_datetime, onupdate=get_beijing_datetime)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    last_test_time = db.Column(db.DateTime, nullable=True)  # 最后测试时间
    test_status = db.Column(db.String(20), default='未测试')  # 测试状态：成功、失败、未测试

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Cookies超时检查
@app.before_request
def check_cookie_timeout():
    """检查cookies是否超时，超时则强制退出"""
    # 排除不需要登录的路由
    excluded_endpoints = ['login', 'captcha', 'static']
    
    if request.endpoint in excluded_endpoints:
        return
    
    # 如果用户已登录，检查cookies超时和用户身份
    if current_user.is_authenticated:
        login_time_cookie = request.cookies.get('login_time')
        login_user_cookie = request.cookies.get('login_user')
        login_user_id_cookie = request.cookies.get('login_user_id')
        
        # 检查用户身份是否匹配
        if login_user_cookie and login_user_id_cookie:
            try:
                cookie_user_id = int(login_user_id_cookie)
                if (login_user_cookie != current_user.username or 
                    cookie_user_id != current_user.id):
                    # 用户身份不匹配，可能是会话劫持或用户切换
                    logout_user()
                    session.clear()
                    response = make_response(redirect(url_for('login')))
                    # 删除所有相关cookies
                    response.set_cookie('login_time', '', expires=0)
                    response.set_cookie('login_user', '', expires=0)
                    response.set_cookie('login_user_id', '', expires=0)
                    flash('登录身份验证失败，请重新登录', 'warning')
                    return response
            except (ValueError, TypeError):
                # cookie值无效，强制退出
                logout_user()
                session.clear()
                response = make_response(redirect(url_for('login')))
                response.set_cookie('login_time', '', expires=0)
                response.set_cookie('login_user', '', expires=0)
                response.set_cookie('login_user_id', '', expires=0)
                flash('登录状态异常，请重新登录', 'warning')
                return response
        
        # 检查登录时间
        if login_time_cookie:
            try:
                # 解析登录时间
                login_time = datetime.fromtimestamp(float(login_time_cookie))
                now = datetime.now()
                
                # 检查是否超过12小时
                if now - login_time > timedelta(hours=12):
                    # 超时，强制退出
                    logout_user()
                    session.clear()
                    response = make_response(redirect(url_for('login')))
                    # 删除所有相关cookies
                    response.set_cookie('login_time', '', expires=0)
                    response.set_cookie('login_user', '', expires=0)
                    response.set_cookie('login_user_id', '', expires=0)
                    flash('登录已超时（12小时），请重新登录', 'warning')
                    return response
            except (ValueError, TypeError):
                # cookie值无效，强制退出
                logout_user()
                session.clear()
                response = make_response(redirect(url_for('login')))
                response.set_cookie('login_time', '', expires=0)
                response.set_cookie('login_user', '', expires=0)
                response.set_cookie('login_user_id', '', expires=0)
                flash('登录状态异常，请重新登录', 'warning')
                return response
        else:
            # 没有登录时间cookie，设置相关cookies
            response = make_response()
            current_timestamp = str(datetime.now().timestamp())
            
            response.set_cookie('login_time', 
                              current_timestamp, 
                              max_age=12*60*60)  # 12小时
            response.set_cookie('login_user', 
                              current_user.username, 
                              max_age=12*60*60)  # 12小时
            response.set_cookie('login_user_id', 
                              str(current_user.id), 
                              max_age=12*60*60)  # 12小时
            return response

# 验证码生成函数
def generate_captcha_code():
    """生成4位随机验证码"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

def create_captcha_image(code):
    """创建验证码图片"""
    # 图片尺寸
    width, height = 120, 50
    
    # 创建图片和绘图对象
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # 尝试使用系统字体，如果失败则使用默认字体
    try:
        # Windows 系统常见字体
        font = ImageFont.truetype('arial.ttf', 24)
    except:
        try:
            # 备选字体
            font = ImageFont.truetype('calibri.ttf', 24)
        except:
            # 使用默认字体
            font = ImageFont.load_default()
    
    # 绘制验证码文字
    for i, char in enumerate(code):
        x = 20 + i * 20
        y = random.randint(10, 15)
        # 随机颜色
        color = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
        draw.text((x, y), char, font=font, fill=color)
    
    # 添加干扰线
    for _ in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)), width=1)
    
    # 添加干扰点
    for _ in range(50):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    
    return image

# 权限装饰器
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('需要管理员权限才能访问此页面', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# 首次登录检查装饰器
def first_login_required(f):
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.is_first_login:
            flash('请先修改您的密码后再使用系统功能', 'warning')
            return redirect(url_for('first_login_change_password'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# 路由
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/captcha')
def captcha():
    """生成验证码图片"""
    # 生成验证码
    code = generate_captcha_code()
    
    # 将验证码存储到session中
    session['captcha_code'] = code.upper()
    
    # 创建验证码图片
    image = create_captcha_image(code)
    
    # 将图片转换为字节流
    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    
    # 返回图片响应
    response = make_response(img_io.getvalue())
    response.headers['Content-Type'] = 'image/png'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        captcha_input = request.form.get('captcha', '').upper()
        
        # 验证验证码
        if 'captcha_code' not in session or captcha_input != session.get('captcha_code'):
            flash('验证码错误', 'error')
            # 清除旧的验证码
            session.pop('captcha_code', None)
            return render_template('login.html')
        
        # 清除验证码（一次性使用）
        session.pop('captcha_code', None)
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            if not user.is_enabled:
                flash('账号已被禁用，请联系管理员', 'error')
                return render_template('login.html')
            
            login_user(user)
            
            # 检查是否是首次登录
            if user.is_first_login:
                flash('这是您的首次登录，请立即修改您的密码以确保账户安全！', 'warning')
                response = make_response(redirect(url_for('first_login_change_password')))
            else:
                flash(f'欢迎回来，{user.username}！', 'success')
                response = make_response(redirect(url_for('dashboard')))
            
            # 设置登录时间cookie和用户绑定cookie，有效期12小时
            current_timestamp = str(datetime.now().timestamp())
            
            response.set_cookie('login_time', 
                              current_timestamp, 
                              max_age=12*60*60,  # 12小时（秒）
                              httponly=True,     # 防止JavaScript访问
                              secure=False)      # 开发环境设为False，生产环境应设为True
            
            response.set_cookie('login_user', 
                              user.username,     # 存储用户名
                              max_age=12*60*60,  # 12小时（秒）
                              httponly=True,     # 防止JavaScript访问
                              secure=False)      # 开发环境设为False，生产环境应设为True
            
            response.set_cookie('login_user_id', 
                              str(user.id),      # 存储用户ID作为双重验证
                              max_age=12*60*60,  # 12小时（秒）
                              httponly=True,     # 防止JavaScript访问
                              secure=False)      # 开发环境设为False，生产环境应设为True
            
            return response
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  # 清除所有session数据
    flash('已成功退出登录', 'info')
    
    # 创建响应并删除所有登录相关cookies
    response = make_response(redirect(url_for('login')))
    response.set_cookie('login_time', '', expires=0)
    response.set_cookie('login_user', '', expires=0)
    response.set_cookie('login_user_id', '', expires=0)
    
    return response

@app.route('/dashboard')
@login_required
@first_login_required
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
@first_login_required
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
@first_login_required
def print_page():
    return render_template('print.html', template_mapping=TEMPLATE_MAPPING)

@app.route('/search_student')
@login_required
def search_student():
    student_code = request.args.get('student_code', '').strip()
    
    if not student_code:
        return jsonify({'error': '请输入学员编码'}), 400
    
    # 尝试使用实际的学员凭证搜索功能（包含班级凭证和充值提现记录）
    try:
        from utils.certificate_processors.search_student_certificate import search_student
        
        # 从数据库获取活跃的cookies配置
        cookies = None
        active_config = CookiesConfig.query.filter_by(is_active=True).first()
        if active_config:
            try:
                cookies = json.loads(active_config.cookies_data)
            except:
                pass
        
        # 调用实际的搜索功能
        search_result = search_student(cookies, current_user, student_code)
        
        if search_result == 0:
            return jsonify({'error': '未找到该学员的信息'}), 404
        elif search_result == 404:
            # API调用失败，返回错误信息并提醒管理员更新cookies
            error_msg = 'API调用失败，可能是网络问题或认证失效。'
            if current_user.role != 'admin':
                error_msg += '请联系管理员更新系统认证配置。'
            else:
                error_msg += '请前往Cookies配置页面更新认证信息。'
            
            return jsonify({
                'error': error_msg,
                'need_admin_attention': True,
                'is_admin': current_user.role == 'admin'
            }), 404
        elif isinstance(search_result, dict) and 'reports' in search_result:
            # 成功获取到实际数据（新格式）
            student_info = search_result
            
            # 为每个报告添加详细信息描述
            for report in student_info.get('reports', []):
                biz_type = report.get('biz_type')
                data = report.get('data', {})
                
                # 生成详细信息描述
                _, detail_info = _get_certificate_info(biz_type, data)
                report['description'] = detail_info
            
            return jsonify(student_info)
        else:
            return jsonify({'error': '未找到该学员的凭证信息'}), 404
            
    except Exception as e:
        print(f"搜索学生信息时发生错误: {str(e)}")
        # 发生错误时回退到模拟数据
        return _fallback_mock_search(student_code)


def _fallback_mock_search(student_code):
    """回退到模拟数据搜索"""
    # 不再提供测试数据，直接返回未找到
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
    per_page = request.args.get('per_page', 20, type=int)
    
    # 限制每页记录数量范围
    if per_page not in [10, 20, 50, 100]:
        per_page = 20
    
    # 搜索参数
    search_student = request.args.get('search_student', '').strip()  # 学员编码或姓名
    search_biz_type = request.args.get('search_biz_type', '', type=str)  # 凭证类型
    search_date_start = request.args.get('search_date_start', '').strip()  # 开始日期
    search_date_end = request.args.get('search_date_end', '').strip()  # 结束日期
    
    # 构建查询
    query = PrintLog.query.filter_by(is_deleted=False)  # 只显示未删除的记录
    
    # 权限控制
    if current_user.role != 'admin':
        # 普通用户只能查看自己的日志
        query = query.filter_by(user_id=current_user.id)
    
    # 学员信息筛选
    if search_student:
        query = query.filter(
            db.or_(
                PrintLog.student_code.like(f'%{search_student}%'),
                PrintLog.student_name.like(f'%{search_student}%')
            )
        )
    
    # 凭证类型筛选
    if search_biz_type:
        try:
            biz_type_int = int(search_biz_type)
            query = query.filter(PrintLog.biz_type == biz_type_int)
        except ValueError:
            # 如果不是数字，按凭证名称搜索
            query = query.filter(PrintLog.biz_name.like(f'%{search_biz_type}%'))
    
    # 时间范围筛选
    if search_date_start:
        try:
            start_date = datetime.strptime(search_date_start, '%Y-%m-%d')
            query = query.filter(PrintLog.print_time >= start_date)
        except ValueError:
            pass
    
    if search_date_end:
        try:
            end_date = datetime.strptime(search_date_end, '%Y-%m-%d')
            # 结束日期包含当天，所以加1天
            end_date = end_date + timedelta(days=1)
            query = query.filter(PrintLog.print_time < end_date)
        except ValueError:
            pass
    
    # 排序和分页
    logs = query.order_by(PrintLog.print_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取凭证类型列表用于下拉框
    biz_types = db.session.query(PrintLog.biz_type, PrintLog.biz_name).filter_by(is_deleted=False).distinct().all()
    
    # 构建搜索参数字典，用于分页链接保持搜索状态
    search_params = {}
    if search_student:
        search_params['search_student'] = search_student
    if search_biz_type:
        search_params['search_biz_type'] = search_biz_type
    if search_date_start:
        search_params['search_date_start'] = search_date_start
    if search_date_end:
        search_params['search_date_end'] = search_date_end
    
    # 添加per_page参数
    search_params['per_page'] = per_page
    
    # 构建分页URL参数字符串
    search_query_string = ''
    if search_params:
        query_parts = []
        for key, value in search_params.items():
            if value:  # 只包含非空值
                query_parts.append(f'{key}={value}')
        if query_parts:
            search_query_string = '&' + '&'.join(query_parts)
    
    return render_template('print_logs.html', 
                         logs=logs, 
                         biz_types=biz_types,
                         search_params=search_params,
                         search_query_string=search_query_string,
                         current_per_page=per_page)

@app.route('/delete_print_log/<int:log_id>')
@login_required
@admin_required
def delete_print_log(log_id):
    """软删除打印记录 - 仅管理员可操作"""
    log = PrintLog.query.get_or_404(log_id)
    
    # 检查记录是否已被删除
    if log.is_deleted:
        flash('记录已被删除', 'warning')
        return redirect(url_for('print_logs'))
    
    # 执行软删除
    log.is_deleted = True
    db.session.commit()
    
    flash(f'已删除 {log.student_name} 的打印记录', 'success')
    return redirect(url_for('print_logs'))

@app.route('/first_login_change_password', methods=['GET', 'POST'])
@login_required
def first_login_change_password():
    # 如果不是首次登录，重定向到普通密码修改页面
    if not current_user.is_first_login:
        return redirect(url_for('change_password'))
    
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        # 验证当前密码
        if not check_password_hash(current_user.password_hash, current_password):
            flash('当前密码错误', 'error') 
            return render_template('first_login_change_password.html')
        
        # 验证新密码
        if len(new_password) < 6:
            flash('新密码长度至少6位', 'error')
            return render_template('first_login_change_password.html')
        
        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'error')
            return render_template('first_login_change_password.html')
        
        # 检查新密码是否与旧密码相同
        if check_password_hash(current_user.password_hash, new_password):
            flash('新密码不能与当前密码相同', 'error')
            return render_template('first_login_change_password.html')
        
        # 更新密码并标记非首次登录
        current_user.password_hash = generate_password_hash(new_password)
        current_user.is_first_login = False
        db.session.commit()
        
        flash('密码修改成功，欢迎使用系统！', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('first_login_change_password.html')

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
@first_login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        # 验证当前密码
        if not check_password_hash(current_user.password_hash, current_password):
            flash('当前密码错误', 'error') 
            return render_template('change_password.html')
        
        # 验证新密码
        if len(new_password) < 6:
            flash('新密码长度至少6位', 'error')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('两次输入的新密码不一致', 'error')
            return render_template('change_password.html')
        
        # 更新密码
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash('密码修改成功', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('change_password.html')

@app.route('/tech_support')
@login_required
def tech_support():
    """技术支持页面"""
    return render_template('tech_support.html')

@app.route('/debug_cookies')
@login_required
def debug_cookies():
    """调试：显示当前所有cookies"""
    cookies_info = {}
    
    for cookie_name, cookie_value in request.cookies.items():
        cookies_info[cookie_name] = cookie_value
        
        # 特别处理login_time cookie
        if cookie_name == 'login_time':
            try:
                timestamp = float(cookie_value)
                login_time = datetime.fromtimestamp(timestamp)
                now = datetime.now()
                elapsed = now - login_time
                remaining = timedelta(hours=12) - elapsed
                
                cookies_info[f'{cookie_name}_详细信息'] = {
                    '原始时间戳': timestamp,
                    '登录时间': login_time.strftime('%Y-%m-%d %H:%M:%S'),
                    '当前时间': now.strftime('%Y-%m-%d %H:%M:%S'),
                    '已使用时间': f'{elapsed.total_seconds()/3600:.2f} 小时',
                    '剩余时间': f'{remaining.total_seconds()/3600:.2f} 小时',
                    '是否即将过期': remaining.total_seconds() < 3600,
                    '过期时间': (login_time + timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
                }
            except:
                cookies_info[f'{cookie_name}_详细信息'] = '解析失败'
    
    # 用户身份验证状态
    login_user_cookie = request.cookies.get('login_user')
    login_user_id_cookie = request.cookies.get('login_user_id')
    
    identity_check = {
        'cookie中的用户名': login_user_cookie,
        'cookie中的用户ID': login_user_id_cookie,
        '当前登录用户名': current_user.username,
        '当前登录用户ID': current_user.id,
        '用户名匹配': login_user_cookie == current_user.username if login_user_cookie else False,
        '用户ID匹配': str(login_user_id_cookie) == str(current_user.id) if login_user_id_cookie else False,
        '身份验证通过': (login_user_cookie == current_user.username and 
                      str(login_user_id_cookie) == str(current_user.id)) if login_user_cookie and login_user_id_cookie else False
    }
    
    return jsonify({
        '当前cookies': cookies_info,
        '用户身份验证': identity_check,
        '总cookies数量': len(request.cookies),
        '检查时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })



@app.route('/cookies_config')
@login_required
@admin_required
def cookies_config():
    """Cookies配置管理页面"""
    configs = CookiesConfig.query.order_by(CookiesConfig.updated_at.desc()).all()
    active_config = CookiesConfig.query.filter_by(is_active=True).first()
    return render_template('cookies_config.html', configs=configs, active_config=active_config)

@app.route('/save_cookies', methods=['POST'])
@login_required
@admin_required
def save_cookies():
    """保存cookies配置"""
    try:
        cookies_text = request.form.get('cookies_data', '').strip()
        config_name = request.form.get('config_name', 'ERP Cookies').strip()
        
        if not cookies_text:
            flash('请输入cookies数据', 'error')
            return redirect(url_for('cookies_config'))
        
        # 解析cookies文本
        cookies_dict = {}
        try:
            # 支持多种格式的cookies输入
            if cookies_text.startswith('{'):
                # JSON格式
                cookies_dict = json.loads(cookies_text)
            else:
                # 键值对格式，支持分号或换行分隔
                lines = cookies_text.replace(';', '\n').split('\n')
                for line in lines:
                    line = line.strip()
                    if '=' in line:
                        key, value = line.split('=', 1)
                        cookies_dict[key.strip()] = value.strip()
        except Exception as e:
            flash(f'Cookies格式解析失败：{str(e)}', 'error')
            return redirect(url_for('cookies_config'))
        
        if not cookies_dict:
            flash('未能解析到有效的cookies数据', 'error')
            return redirect(url_for('cookies_config'))
        
        # 将所有其他配置设为非活跃
        CookiesConfig.query.update({'is_active': False})
        
        # 创建新配置
        new_config = CookiesConfig(
            name=config_name,
            cookies_data=json.dumps(cookies_dict, ensure_ascii=False),
            is_active=True,
            created_by=current_user.id
        )
        
        db.session.add(new_config)
        db.session.commit()
        
        flash(f'Cookies配置 "{config_name}" 保存成功！', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'保存失败：{str(e)}', 'error')
    
    return redirect(url_for('cookies_config'))

@app.route('/test_cookies/<int:config_id>')
@login_required
@admin_required
def test_cookies(config_id):
    """测试cookies配置"""
    try:
        config = CookiesConfig.query.get_or_404(config_id)
        cookies_dict = json.loads(config.cookies_data)
        
        # 使用测试学员编号测试API
        from utils.certificate_processors.search_student_certificate import search_student
        test_result = search_student(cookies_dict, current_user, 'NC24048S6UzC')  # 使用一个测试学员编号
        
        # 更新测试状态
        config.last_test_time = get_beijing_datetime()
        
        if test_result == 404:
            config.test_status = '失败'
            flash(f'Cookies测试失败：API请求失败', 'error')
        elif test_result == 0:
            config.test_status = '成功'
            flash(f'Cookies测试成功：API连接正常（测试学员不存在是正常的）', 'success')
        elif isinstance(test_result, dict):
            config.test_status = '成功'
            flash(f'Cookies测试成功：找到学员数据', 'success')
        else:
            config.test_status = '失败'
            flash(f'Cookies测试失败：返回异常结果', 'error')
        
        db.session.commit()
        
    except Exception as e:
        flash(f'测试失败：{str(e)}', 'error')
    
    return redirect(url_for('cookies_config'))

@app.route('/activate_cookies/<int:config_id>')
@login_required
@admin_required
def activate_cookies(config_id):
    """激活指定的cookies配置"""
    try:
        # 将所有配置设为非活跃
        CookiesConfig.query.update({'is_active': False})
        
        # 激活指定配置
        config = CookiesConfig.query.get_or_404(config_id)
        config.is_active = True
        db.session.commit()
        
        flash(f'已激活配置：{config.name}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'激活失败：{str(e)}', 'error')
    
    return redirect(url_for('cookies_config'))

@app.route('/delete_cookies/<int:config_id>')
@login_required
@admin_required
def delete_cookies(config_id):
    """删除cookies配置"""
    try:
        config = CookiesConfig.query.get_or_404(config_id)
        db.session.delete(config)
        db.session.commit()
        
        flash(f'已删除配置：{config.name}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'error')
    
    return redirect(url_for('cookies_config'))

@app.route('/test_class_search')
@login_required
def test_class_search():
    """测试学员凭证搜索功能（包含班级凭证和充值提现记录）"""
    student_code = request.args.get('student_code', '').strip()
    
    if not student_code:
        return jsonify({'error': '请提供学生编号', 'example': '/test_class_search?student_code=NC12345678'}), 400
    
    try:
        from utils.certificate_processors.search_student_certificate import search_student
        
        # 使用None来让函数使用默认配置
        cookies = None
        
        # 调用搜索功能
        result = search_student(cookies, current_user, student_code)
        
        if result == 0:
            return jsonify({'error': '未找到该学员', 'student_code': student_code})
        elif result == 404:
            return jsonify({'error': 'API调用失败，可能是网络问题或认证失效', 'student_code': student_code})
        elif isinstance(result, dict) and 'reports' in result:
            return jsonify({
                'success': True,
                'student_code': student_code,
                'student_name': result.get('student_name', ''),
                'gender': result.get('gender', ''),
                'certificate_count': len(result['reports']),
                'certificates': result['reports']
            })
        else:
            return jsonify({'error': '未知的返回结果', 'result': result})
            
    except Exception as e:
        return jsonify({'error': f'测试失败: {str(e)}', 'student_code': student_code})

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
            role='admin',
            is_first_login=False  # 管理员账户不需要强制修改密码
        )
        db.session.add(admin)
        db.session.commit()
        print("默认管理员账户已创建 - 用户名: admin, 密码: admin123")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_admin_user()
    
    app.run(debug=True, host='0.0.0.0', port=5000) 