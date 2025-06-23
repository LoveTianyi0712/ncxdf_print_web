#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
班级凭证专门处理器
使用班级凭证.mrt模板生成报班凭证
"""

import json
import os
import base64
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
from ..time_utils import get_beijing_time_str, get_beijing_timestamp

class EnrollmentCertificateProcessor:
    """班级凭证处理器"""
    
    def __init__(self):
        """初始化处理器"""
        # 获取项目根目录
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.template_dir = os.path.join(self.base_dir, "properties")
        self.output_dir = os.path.join(self.base_dir, "image")
        self.template_file = "班级凭证.mrt"
        
        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # 字体路径
        self.font_path = os.path.join(os.environ.get('WINDIR', ''), 'Fonts', 'simhei.ttf')
        if not os.path.exists(self.font_path):
            self.font_path = None
    
    def validate_data(self, data):
        """验证班级凭证的数据字段"""
        required_fields = [
            'sSchoolName', 'sStudentName', 'sClassName', 'sOperator'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in data or not data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"缺少必要字段: {', '.join(missing_fields)}")
        
        return True
    
    def process_data(self, data):
        """处理班级凭证的特殊数据逻辑"""
        processed_data = data.copy()
        
        # 处理费用信息 - 确保数值类型正确
        for fee_field in ['dFee', 'dVoucherFee', 'dRealFee', 'dShouldFee']:
            if fee_field in processed_data:
                try:
                    processed_data[fee_field] = float(processed_data[fee_field])
                except (ValueError, TypeError):
                    processed_data[fee_field] = 0.0
        
        # 设置费用默认值和逻辑
        base_fee = processed_data.get('dFee', 0.0)
        processed_data.setdefault('dFee', base_fee)
        processed_data.setdefault('dVoucherFee', 0.0)
        processed_data.setdefault('dRealFee', base_fee)
        processed_data.setdefault('dShouldFee', base_fee)
        
        # 设置默认值 - 根据模板字段要求
        processed_data.setdefault('sChannel', '直营')
        # 已移除联系电话字段
        processed_data.setdefault('sStudentCode', '')
        processed_data.setdefault('sGender', '不详')
        processed_data.setdefault('sCardCode', '')
        processed_data.setdefault('sClassCode', '')
        processed_data.setdefault('sSeatNo', '')
        processed_data.setdefault('dtBeginDate', '')
        processed_data.setdefault('dtEndDate', '')
        processed_data.setdefault('sRegisterTime', get_beijing_time_str())
        processed_data.setdefault('sPrintAddress', '')
        processed_data.setdefault('sPrintTime', get_beijing_time_str())
        processed_data.setdefault('nTryLesson', '0')
        processed_data.setdefault('sOperator', '系统')
        processed_data.setdefault('dtCreate', get_beijing_time_str())
        
        # 处理图像数据字段
        processed_data.setdefault('RWMImage', '')
        
        return processed_data
    
    def parse_template(self):
        """解析班级凭证模板"""
        template_path = os.path.join(self.template_dir, self.template_file)
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板文件不存在: {template_path}")
        
        from utils.certificate_processors.print_simulator import MrtParser
        return MrtParser(template_path)
    
    def generate_certificate(self, data, currency_symbol="¥"):
        """生成班级凭证"""
        try:
            print(f"开始处理班级凭证...")
            
            # 验证数据
            self.validate_data(data)
            
            # 处理数据
            processed_data = self.process_data(data)
            
            # 解析模板
            mrt_parser = self.parse_template()
            
            # 生成图像
            image = self._create_certificate_image(processed_data, mrt_parser, currency_symbol)
            
            # 保存文件
            output_path = self._save_certificate(image, processed_data)
            
            print(f"班级凭证生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"生成班级凭证失败: {str(e)}")
            raise
    
    def _create_certificate_image(self, data, mrt_parser, currency_symbol):
        """创建凭证图像"""
        # 使用与原系统相同的图像生成逻辑，但针对班级凭证优化
        width, height = mrt_parser.page_settings['width'], mrt_parser.page_settings['height']
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # 绘制页面边框
        margin = 3
        draw.rectangle([margin, margin, width-margin, height-margin], outline='lightgray', width=2)
        
        # 默认字体
        default_font = ImageFont.load_default()
        
        # 中文字体
        chinese_font_path = None
        for font_name in ['simsun.ttc', 'simhei.ttf', 'msyh.ttc']:
            potential_path = os.path.join(os.environ.get('WINDIR', ''), 'Fonts', font_name)
            if os.path.exists(potential_path):
                chinese_font_path = potential_path
                break
        
        # 字体缓存
        font_cache = {}
        
        # 像素转换因子
        PIXELS_PER_CM = 78.74
        
        # 居中偏移
        content_width = width * 0.85
        left_margin = (width - content_width) / 2
        center_offset_x = left_margin - 30
        center_offset_y = 20
        
        # 绘制模板组件
        for component in mrt_parser.components:
            if component['type'] == 'Text':
                self._draw_text_component(component, data, draw, PIXELS_PER_CM, 
                                        center_offset_x, center_offset_y, chinese_font_path, 
                                        font_cache, default_font)
            elif component['type'] == 'Image' and component.get('image_data'):
                self._draw_image_component(component, image, PIXELS_PER_CM, 
                                         center_offset_x, center_offset_y)
            elif component['type'] == 'Line':
                self._draw_line_component(component, draw, PIXELS_PER_CM, 
                                        center_offset_x, center_offset_y)
        
        # 添加页脚
        self._add_footer(draw, width, height, chinese_font_path, default_font, 
                        center_offset_x, center_offset_y, mrt_parser.components)
        
        # 添加二维码和在线客服文字到左下角
        self._add_qr_code(image, draw, PIXELS_PER_CM, center_offset_x, center_offset_y, 
                         font_cache, chinese_font_path, default_font)
        
        return image
    
    def _draw_text_component(self, component, data, draw, pixels_per_cm, 
                           center_offset_x, center_offset_y, chinese_font_path, 
                           font_cache, default_font):
        """绘制文本组件 - 专门针对班级凭证优化"""
        rect_parts = component['rect'].split(',') if component['rect'] else [0, 0, 1, 1]
        if len(rect_parts) >= 4:
            x = float(rect_parts[0]) * pixels_per_cm + center_offset_x
            y = float(rect_parts[1]) * pixels_per_cm + center_offset_y
            width_comp = float(rect_parts[2]) * pixels_per_cm
            height_comp = float(rect_parts[3]) * pixels_per_cm
            
            # 获取文本内容
            text = component['text']
            
            # 处理数据字段替换
            if text and '{ArrayList.' in text and '}' in text:
                while '{ArrayList.' in text and '}' in text:
                    start_idx = text.find('{ArrayList.')
                    end_idx = text.find('}', start_idx)
                    if start_idx != -1 and end_idx != -1:
                        field_name = text[start_idx+11:end_idx]
                        if field_name in data:
                            replacement = str(data[field_name])
                            # 对费用字段进行格式化，添加人民币符号
                            if field_name.startswith('d') and field_name.endswith('Fee'):
                                try:
                                    fee_value = float(replacement)
                                    replacement = f"¥{fee_value:,.2f}"
                                except (ValueError, TypeError):
                                    replacement = "¥0.00"
                            text = text[:start_idx] + replacement + text[end_idx+1:]
                        else:
                            # 对于缺失的字段，提供默认值
                            if field_name.startswith('d') and field_name.endswith('Fee'):
                                replacement = "¥0.00"
                            elif field_name.startswith('dt') or field_name.startswith('s') and 'Time' in field_name:
                                replacement = ""
                            else:
                                replacement = ""
                            text = text[:start_idx] + replacement + text[end_idx+1:]
            
            # 替换货币符号
            text = text.replace('&yen;', '¥')
            
            # 渲染文本
            if text and not text.startswith('{'):
                font_info = component.get('font', {'name': 'Arial', 'size': 9, 'bold': False})
                
                # 判断是否需要加粗 - 针对班级凭证的规则
                should_bold = (
                    '服务凭证' in text or
                    '南昌学校' in text or
                    ('学校' in text and '凭证' in text) or
                    component.get('font', {}).get('bold', False) or
                    font_info.get('bold', False) or
                    font_info.get('size', 9) >= 10.5  # 较大字体也加粗
                )
                
                # 排除不需要加粗的字段 - 针对数据内容而不是标签
                # 检查是否是服务地点的内容（通常包含地址信息）
                is_address_content = (
                    '南昌市' in text or 
                    '红谷滩' in text or 
                    '学府大道' in text or
                    'sPrintAddress' in component.get('text', '')
                )
                
                # 检查是否是报到情况的内容（通常包含报名信息或时间）
                is_register_content = (
                    '报名成功' in text or
                    '欢迎参加' in text or
                    'sRegisterTime' in component.get('text', '') or
                    (len(text) > 50 and '2024' in text and ('报名' in text or '学习' in text))
                )
                
                if should_bold and (is_address_content or is_register_content):
                    should_bold = False
                
                # 选择字体
                has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
                font = self._get_font(font_info, chinese_font_path, has_chinese, should_bold, font_cache, default_font)
                
                # 处理文本对齐
                text_alignment = component.get('alignment', 'Left')
                if text_alignment == 'Right':
                    text_bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    x = x + width_comp - text_width
                elif text_alignment == 'Center':
                    text_bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    x = x + (width_comp - text_width) / 2
                
                # 绘制文本
                try:
                    if should_bold:
                        # 更好的加粗效果
                        for dx in [-1, 0, 1]:
                            for dy in [-1, 0, 1]:
                                if dx != 0 or dy != 0:
                                    draw.text((x + dx, y + dy), text, fill='black', font=font)
                        draw.text((x + 1, y), text, fill='black', font=font)
                        draw.text((x, y + 1), text, fill='black', font=font)
                    
                    draw.text((x, y), text, font=font, fill='black')
                except Exception as e:
                    print(f"文本绘制失败: {text}, 错误: {e}")
                    draw.text((x, y), text, font=default_font, fill='black')
    
    def _draw_image_component(self, component, main_image, pixels_per_cm, center_offset_x, center_offset_y):
        """绘制图像组件"""
        try:
            rect_parts = component['rect'].split(',') if component['rect'] else [0, 0, 1, 1]
            if len(rect_parts) >= 4:
                x = int(float(rect_parts[0]) * pixels_per_cm + center_offset_x)
                y = int(float(rect_parts[1]) * pixels_per_cm + center_offset_y)
                width = int(float(rect_parts[2]) * pixels_per_cm)
                height = int(float(rect_parts[3]) * pixels_per_cm)
                
                # 解码图像数据
                image_data = component.get('image_data', '')
                if image_data:
                    try:
                        # 尝试解码base64图像
                        img_bytes = base64.b64decode(image_data)
                        img = Image.open(io.BytesIO(img_bytes))
                        
                        # 调整图像大小
                        img = img.resize((width, height), Image.Resampling.LANCZOS)
                        
                        # 粘贴到主图像上
                        if img.mode == 'RGBA':
                            main_image.paste(img, (x, y), img)
                        else:
                            main_image.paste(img, (x, y))
                            
                        print(f"图像组件绘制成功: 位置({x}, {y}), 尺寸({width}, {height})")
                    except Exception as e:
                        print(f"图像解码失败: {e}")
                        
        except Exception as e:
            print(f"图像组件绘制失败: {e}")
    
    def _draw_line_component(self, component, draw, pixels_per_cm, center_offset_x, center_offset_y):
        """绘制线条组件"""
        try:
            rect_parts = component['rect'].split(',') if component['rect'] else [0, 0, 1, 0.01]
            if len(rect_parts) >= 4:
                x1 = float(rect_parts[0]) * pixels_per_cm + center_offset_x
                y1 = float(rect_parts[1]) * pixels_per_cm + center_offset_y
                line_width = float(rect_parts[2]) * pixels_per_cm
                line_height = float(rect_parts[3]) * pixels_per_cm
                
                # 判断线条方向
                if line_height > line_width:
                    # 垂直线条
                    x2, y2 = x1, y1 + line_height
                else:
                    # 水平线条
                    x2, y2 = x1 + line_width, y1
                
                # 获取线条颜色
                line_color = component.get('color', 'black')
                if line_color.lower() in ['dimgray', 'gray']:
                    line_color = 'gray'
                else:
                    line_color = 'black'
                
                # 绘制线条，使用更粗的线条以确保清晰度
                draw.line([(x1, y1), (x2, y2)], fill=line_color, width=2)
                
        except Exception as e:
            print(f"线条组件绘制失败: {e}")
    
    def _get_font(self, font_info, chinese_font_path, has_chinese, should_bold, font_cache, default_font):
        """获取字体"""
        try:
            font_size = int(font_info.get('size', 9))
            font_key = f"{font_size}_{should_bold}_{has_chinese}"
            
            if font_key in font_cache:
                return font_cache[font_key]
            
            font = None
            if has_chinese and chinese_font_path:
                try:
                    # 使用与student_account_certificate相同的字体放大逻辑
                    base_size = max(16, int(font_size * 2.7))
                    adjusted_size = int(base_size * 1.1) if should_bold else base_size
                    font = ImageFont.truetype(chinese_font_path, adjusted_size)
                except:
                    pass
            
            if not font:
                try:
                    font_name = "arial.ttf" if not has_chinese else "simsun.ttc"
                    font_path = os.path.join(os.environ.get('WINDIR', ''), 'Fonts', font_name)
                    if os.path.exists(font_path):
                        # 同样的字体放大逻辑
                        base_size = max(16, int(font_size * 2.7))
                        adjusted_size = int(base_size * 1.1) if should_bold else base_size
                        font = ImageFont.truetype(font_path, adjusted_size)
                except:
                    pass
            
            if not font:
                font = default_font
            
            font_cache[font_key] = font
            return font
            
        except Exception as e:
            print(f"字体获取失败: {e}")
            return default_font
    
    def _add_footer(self, draw, width, height, chinese_font_path, default_font, 
                   center_offset_x, center_offset_y, components):
        """添加页脚信息"""
        try:
            # 不再添加联系电话信息 - 已从模板中移除
            pass
                
        except Exception as e:
            print(f"页脚添加失败: {e}")

    def _add_qr_code(self, image, draw, pixels_per_cm, center_offset_x, center_offset_y, 
                     font_cache, chinese_font_path, default_font):
        """添加二维码和"【在线客服】"文字到左下角 - 与充值提现凭证保持一致"""
        try:
            # 获取图像尺寸
            width, height = image.size
            
            # 二维码文件路径
            qr_code_path = os.path.join(self.base_dir, "properties", "qr_code.jpg")
            
            if os.path.exists(qr_code_path):
                # 加载二维码图片
                qr_image = Image.open(qr_code_path)
                
                # 设置二维码大小 - 与提现凭证保持一致的调整后大小
                scale_factor = 1.2  # 与student_account_certificate.py保持一致
                qr_size = int(120 * scale_factor)  # 144px
                qr_image = qr_image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
                
                # 计算二维码位置 - 与提现凭证完全一致
                qr_x = int(30 * scale_factor)  # 左边距36像素，与提现凭证一致
                qr_y = height - qr_size - int(25 * scale_factor)  # 底边距30像素，与提现凭证一致
                
                # 处理图像透明度
                if qr_image.mode in ('RGBA', 'LA') or (qr_image.mode == 'P' and 'transparency' in qr_image.info):
                    # 处理有透明度的图像
                    background = Image.new('RGB', qr_image.size, (255, 255, 255))
                    if qr_image.mode == 'P':
                        qr_image = qr_image.convert('RGBA')
                    background.paste(qr_image, mask=qr_image.split()[-1] if qr_image.mode == 'RGBA' else None)
                    qr_image = background
                
                # 粘贴二维码到图像
                image.paste(qr_image, (int(qr_x), int(qr_y)))
                
                # 添加"【在线客服】"文字，在二维码正上方
                service_text = "【在线客服】"
                
                # 获取中文字体 - 直接使用与提现凭证相同的字体大小，不经过_get_font的放大处理
                service_font = default_font
                if chinese_font_path:
                    try:
                        service_font = ImageFont.truetype(chinese_font_path, int(18 * scale_factor))  # 22px，与提现凭证一致
                    except:
                        pass
                
                # 计算文字位置 - 在二维码正上方居中，与提现凭证完全一致
                text_bbox = draw.textbbox((0, 0), service_text, font=service_font)
                text_width = text_bbox[2] - text_bbox[0]
                text_x = qr_x + (qr_size - text_width) // 2  # 在二维码正上方居中，使用整数除法与提现凭证一致
                text_y = qr_y - int(25 * scale_factor)  # 在二维码上方30像素，与提现凭证一致
                
                # 绘制"【在线客服】"文字
                draw.text((text_x, text_y), service_text, fill='black', font=service_font)
                
                print(f"已添加二维码和在线客服文字到左下角位置: ({int(qr_x)}, {int(qr_y)})")
            else:
                print(f"警告: 二维码文件不存在: {qr_code_path}")
                # 如果没有二维码文件，绘制一个简单的方框作为占位符
                scale_factor = 1.2  # 与上面保持一致
                qr_size = int(120 * scale_factor)  # 144px
                qr_x = int(30 * scale_factor)  # 左边距36像素，与提现凭证一致
                qr_y = height - qr_size - int(25 * scale_factor)  # 底边距30像素，与提现凭证一致
                
                # 绘制方框
                draw.rectangle([qr_x, qr_y, qr_x + qr_size, qr_y + qr_size], 
                             outline='black', width=2)
                
                # 添加"二维码"文字
                placeholder_font = self._get_font({'name': 'SimSun', 'size': 10, 'bold': False}, 
                                                chinese_font_path, True, False, font_cache, default_font)
                draw.text((qr_x + qr_size//4, qr_y + qr_size//2), "二维码", fill='black', font=placeholder_font)
                
        except Exception as e:
            print(f"添加二维码时出错: {str(e)}")
    
    def _save_certificate(self, image, data):
        """保存凭证文件"""
        timestamp = get_beijing_timestamp()
        filename = f"班级凭证_{timestamp}.png"
        output_path = os.path.join(self.output_dir, filename)
        
        # 保存图像
        image.save(output_path, 'PNG', quality=95)
        
        # 保存JSON数据用于调试
        json_filename = f"班级凭证_{timestamp}.json"
        json_path = os.path.join(self.output_dir, json_filename)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return output_path


def generate_enrollment_certificate(data, currency_symbol="¥"):
    """生成班级凭证的便捷函数"""
    processor = EnrollmentCertificateProcessor()
    return processor.generate_certificate(data, currency_symbol)


if __name__ == "__main__":
    # 测试数据 - 包含所有班级凭证模板需要的字段
    test_data = {
        # 基本信息
        'sSchoolName': '南昌学校',
        'sChannel': '直营',
        
        # 学员信息
        'sStudentName': '张小明',
        'sStudentCode': 'NC12345678',
        'sGender': '男',
        'sCardCode': 'CARD001234',
        
        # 班级信息
        'sClassName': '初中数学寒假班',
        'sClassCode': 'MATH2024WB001',
        'sSeatNo': 'A001',
        'dtBeginDate': '2024-01-15',
        'dtEndDate': '2024-02-28',
        'nTryLesson': '2节',
        
        # 时间信息
        'sRegisterTime': '2024-01-01 09:00:00 报名成功，欢迎参加南昌学校初中数学寒假班学习！',
        'sPrintAddress': '南昌市红谷滩新区学府大道1号南昌学校',
        'sPrintTime': '2024-01-01 10:30:00',
        'dtCreate': '2024-01-01 09:30:00',
        
        # 费用信息
        'dFee': 2800.00,           # 商品标准金额
        'dVoucherFee': 200.00,     # 商品优惠金额
        'dShouldFee': 2800.00,     # 商品应收金额
        'dRealFee': 2600.00,       # 商品实收金额
        
        # 操作信息
        'sOperator': '系统管理员',
        
        # 图像数据（可选）
        'RWMImage': ''
    }
    
    print("测试班级凭证生成器...")
    result = generate_enrollment_certificate(test_data)
    print(f"测试结果: {result}") 