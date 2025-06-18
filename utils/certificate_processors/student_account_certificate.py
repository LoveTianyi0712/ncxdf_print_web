#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
学员账户充值提现凭证专门处理器
"""

import json
import os
import base64
import xml.etree.ElementTree as ET
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io

class StudentAccountCertificateProcessor:
    """学员账户充值提现凭证处理器"""
    
    def __init__(self):
        """初始化处理器"""
        # 获取项目根目录
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.template_dir = os.path.join(self.base_dir, "properties")
        self.output_dir = os.path.join(self.base_dir, "image")
        self.template_file = "学员账户充值提现凭证.mrt"
        
        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # 字体路径
        self.font_path = os.path.join(os.environ.get('WINDIR', ''), 'Fonts', 'simhei.ttf')
        if not os.path.exists(self.font_path):
            self.font_path = None
    
    def validate_data(self, data):
        """验证充值提现凭证的数据字段"""
        required_fields = [
            'nSchoolId', 'sSchoolName', 'sOperator', 'sStudentCode', 
            'sStudentName', 'sPay', 'sPayType', 'sProofName'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in data or not data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"缺少必要字段: {', '.join(missing_fields)}")
        
        return True
    
    def process_data(self, data):
        """处理充值提现凭证的特殊数据逻辑"""
        processed_data = data.copy()
        
        # 处理余额信息
        if 'dSumBalance' in processed_data:
            balance = processed_data['dSumBalance']
            if not balance.startswith('余额：'):
                processed_data['dSumBalance'] = f"余额：{balance}"
        
        # 处理金额信息格式
        if 'sPay' in processed_data:
            pay_info = processed_data['sPay']
            # 确保金额格式正确
            if '充值金额' in pay_info or '提现金额' in pay_info:
                processed_data['sPay'] = pay_info
            else:
                # 根据业务类型判断是充值还是提现
                if '充值' in processed_data.get('sBizType', ''):
                    processed_data['sPay'] = f"充值金额：{pay_info}"
                elif '提现' in processed_data.get('sBizType', ''):
                    processed_data['sPay'] = f"提现金额：{pay_info}"
        
        # 处理支付方式
        if 'sPayType' in processed_data:
            pay_type = processed_data['sPayType']
            if not any(word in pay_type for word in ['充值方式', '提现方式', '支付方式']):
                if '充值' in processed_data.get('sBizType', ''):
                    processed_data['sPayType'] = f"充值方式：{pay_type}"
                elif '提现' in processed_data.get('sBizType', ''):
                    processed_data['sPayType'] = f"提现方式：{pay_type}"
                else:
                    processed_data['sPayType'] = f"支付方式：{pay_type}"
        
        # 设置默认值
        processed_data.setdefault('sTelePhone', '400-175-9898')
        processed_data.setdefault('dtCreate', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        processed_data.setdefault('dtCreateDate', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # 处理标题
        if 'Title' not in processed_data:
            if '充值' in processed_data.get('sBizType', ''):
                processed_data['Title'] = '充值凭证'
            elif '提现' in processed_data.get('sBizType', ''):
                processed_data['Title'] = '提现凭证'
            else:
                processed_data['Title'] = '学员账户凭证'
        
        return processed_data
    
    def parse_template(self):
        """解析充值提现凭证模板"""
        template_path = os.path.join(self.template_dir, self.template_file)
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板文件不存在: {template_path}")
        
        from utils.print_simulator import MrtParser
        return MrtParser(template_path)
    
    def generate_certificate(self, data, currency_symbol="¥"):
        """生成充值提现凭证"""
        try:
            print(f"开始处理学员账户充值提现凭证...")
            
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
            
            print(f"学员账户充值提现凭证生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"生成学员账户充值提现凭证失败: {str(e)}")
            raise
    
    def _create_certificate_image(self, data, mrt_parser, currency_symbol):
        """创建凭证图像"""
        # 使用与原系统相同的图像生成逻辑，但针对充值提现凭证优化
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
        
        return image
    
    def _draw_text_component(self, component, data, draw, pixels_per_cm, 
                           center_offset_x, center_offset_y, chinese_font_path, 
                           font_cache, default_font):
        """绘制文本组件 - 专门针对充值提现凭证优化"""
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
                            text = text[:start_idx] + replacement + text[end_idx+1:]
                        else:
                            text = text[:start_idx] + "" + text[end_idx+1:]
            
            # 替换货币符号
            text = text.replace('&yen;', '¥')
            
            # 渲染文本
            if text and not text.startswith('{'):
                font_info = component.get('font', {'name': 'Arial', 'size': 9, 'bold': False})
                
                # 判断是否需要加粗 - 与原系统保持一致的规则
                should_bold = (
                    '余额' in text or
                    '提现凭证' in text or
                    '充值凭证' in text or
                    '南昌学校' in text or
                    ('学校' in text and '凭证' in text) or
                    'Title' in text or  # 包含Title的文字
                    component.get('font', {}).get('bold', False) or
                    font_info.get('bold', False) or
                    font_info.get('size', 9) >= 10.5  # 较大字体也加粗
                )
                
                # 选择字体
                has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text) or '¥' in text
                font_to_use = self._get_font(font_info, chinese_font_path, has_chinese, 
                                           should_bold, font_cache, default_font)
                
                # 处理文本对齐
                text_alignment = component.get('alignment', 'Left')
                if text_alignment == 'Right':
                    text_bbox = draw.textbbox((0, 0), text, font=font_to_use)
                    text_width = text_bbox[2] - text_bbox[0]
                    x = x + width_comp - text_width
                elif text_alignment == 'Center':
                    text_bbox = draw.textbbox((0, 0), text, font=font_to_use)
                    text_width = text_bbox[2] - text_bbox[0]
                    x = x + (width_comp - text_width) / 2
                
                # 绘制文本
                if should_bold:
                    # 加粗效果
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx != 0 or dy != 0:
                                draw.text((x + dx, y + dy), text, fill='black', font=font_to_use)
                    draw.text((x + 1, y), text, fill='black', font=font_to_use)
                    draw.text((x, y + 1), text, fill='black', font=font_to_use)
                
                draw.text((x, y), text, fill='black', font=font_to_use)
    
    def _draw_image_component(self, component, main_image, pixels_per_cm, center_offset_x, center_offset_y):
        """绘制图像组件 - 处理logo等图片"""
        rect_parts = component['rect'].split(',') if component['rect'] else [0, 0, 1, 1]
        if len(rect_parts) >= 4:
            # 使用正确的转换因子，并添加居中偏移
            x = float(rect_parts[0]) * pixels_per_cm + center_offset_x
            y = float(rect_parts[1]) * pixels_per_cm + center_offset_y
            width_comp = float(rect_parts[2]) * pixels_per_cm
            height_comp = float(rect_parts[3]) * pixels_per_cm

            # 尝试解码图像数据
            try:
                image_data = component['image_data']
                if image_data:
                    # 解码Base64
                    img_bytes = base64.b64decode(image_data)
                    img = Image.open(io.BytesIO(img_bytes))

                    # 调整大小并粘贴到主图像
                    img = img.resize((int(width_comp), int(height_comp)), Image.Resampling.LANCZOS)
                    
                    # 如果图像有透明度，需要处理alpha通道
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        # 创建一个白色背景
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    
                    # 直接粘贴到主图像上
                    main_image.paste(img, (int(x), int(y)))
                    print(f"成功绘制图像组件，位置: ({x}, {y}), 大小: ({width_comp}, {height_comp})")
            except Exception as e:
                print(f"处理图像时出错: {str(e)}")
                # 如果图像无法加载，绘制一个占位符
                draw = ImageDraw.Draw(main_image)
                draw.rectangle([x, y, x + width_comp, y + height_comp], outline='gray', width=1)
    
    def _draw_line_component(self, component, draw, pixels_per_cm, center_offset_x, center_offset_y):
        """绘制线条组件"""
        rect_parts = component['rect'].split(',') if component['rect'] else [0, 0, 1, 0.01]
        if len(rect_parts) >= 4:
            x1 = float(rect_parts[0]) * pixels_per_cm + center_offset_x
            y1 = float(rect_parts[1]) * pixels_per_cm + center_offset_y
            line_width = float(rect_parts[2]) * pixels_per_cm
            line_height = float(rect_parts[3]) * pixels_per_cm
            
            if line_height > line_width:
                x2, y2 = x1, y1 + line_height
            else:
                x2, y2 = x1 + line_width, y1
            
            line_color = component.get('color', 'black')
            if line_color.lower() in ['dimgray', 'gray']:
                line_color = 'gray'
            else:
                line_color = 'black'
            
            draw.line([(x1, y1), (x2, y2)], fill=line_color, width=2)
    
    def _get_font(self, font_info, chinese_font_path, has_chinese, should_bold, font_cache, default_font):
        """获取合适的字体"""
        font_name = font_info.get('name', 'Arial')
        font_size = font_info.get('size', 9)
        
        font_key = f"{font_name}_{font_size}_{should_bold}_{has_chinese}"
        if font_key in font_cache:
            return font_cache[font_key]
        
        try:
            if has_chinese and chinese_font_path:
                base_size = max(16, int(font_size * 2.7))
                adjusted_size = int(base_size * 1.1) if should_bold else base_size
                font_to_use = ImageFont.truetype(chinese_font_path, adjusted_size)
            else:
                font_path = os.path.join(os.environ.get('WINDIR', ''), 'Fonts', f"{font_name}.ttf")
                if not os.path.exists(font_path):
                    font_path = chinese_font_path if chinese_font_path else None
                
                if font_path:
                    base_size = max(16, int(font_size * 2.7))
                    adjusted_size = int(base_size * 1.1) if should_bold else base_size
                    font_to_use = ImageFont.truetype(font_path, adjusted_size)
                else:
                    font_to_use = default_font
        except:
            font_to_use = default_font
        
        font_cache[font_key] = font_to_use
        return font_to_use
    
    def _add_footer(self, draw, width, height, chinese_font_path, default_font, 
                   center_offset_x, center_offset_y, components):
        """添加页脚信息"""
        # 仅在模板中没有打印时间字段时添加
        if not any("打印时间" in c.get('text', '') for c in components):
            footer_font = default_font
            if chinese_font_path:
                try:
                    footer_font = ImageFont.truetype(chinese_font_path, 24)
                except:
                    pass
            
            footer_x = width - 400 + center_offset_x
            footer_y = height - 50 + center_offset_y
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            draw.text((footer_x, footer_y), f"打印时间: {timestamp}", fill='black', font=footer_font)
    
    def _save_certificate(self, image, data):
        """保存凭证文件"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        proof_name = data.get('sProofName', '学员账户凭证')
        
        # 保存图像
        filename = f"{proof_name}_{timestamp}.png"
        output_path = os.path.join(self.output_dir, filename)
        image.save(output_path, 'PNG', optimize=True, dpi=(200, 200))
        
        # 保存JSON数据
        json_filename = f"{proof_name}_{timestamp}.json"
        json_output_path = os.path.join(self.output_dir, json_filename)
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        print(f"凭证文件已保存: {output_path}")
        print(f"数据文件已保存: {json_output_path}")
        
        return output_path


def generate_student_account_certificate(data, currency_symbol="¥"):
    """生成学员账户充值提现凭证的便捷函数"""
    processor = StudentAccountCertificateProcessor()
    return processor.generate_certificate(data, currency_symbol)


if __name__ == "__main__":
    # 测试数据
    test_data = {
        "nSchoolId": 35,
        "sSchoolName": "南昌学校",
        "sTelePhone": "400-175-9898",
        "sOperator": "张会计",
        "dtCreate": "2024-12-23 17:30:00",
        "Title": "提现凭证",
        "sStudentCode": "NC6080119764",
        "sStudentName": "测试学员",
        "sGender": "男",
        "sPay": "提现金额：¥1500.00",
        "dSumBalance": "余额：¥500.00",
        "sPayType": "提现方式：银行卡",
        "dtCreateDate": "2024-12-23 17:30:00",
        "sProofName": "提现凭证",
        "sBizType": "提现",
        "nBizId": 126560058,
        "sRegZoneName": "财务处"
    }
    
    # 测试生成
    result = generate_student_account_certificate(test_data)
    print(f"测试完成，生成文件: {result}") 