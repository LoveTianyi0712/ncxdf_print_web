#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
报班凭证专门处理器
使用报班凭证.mrt模板生成报班凭证
支持stimulsoft DataBand形式的多列表展示
"""

import json
import os
import sys
import base64
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import re
import xml.etree.ElementTree as ET

# 修复相对导入问题
try:
    from ..time_utils import get_beijing_time_str, get_beijing_timestamp
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from time_utils import get_beijing_time_str, get_beijing_timestamp

# 设置正确的像素转换比例，与print_simulator保持一致
PIXELS_PER_CM = 78.74  # 200 DPI: 1厘米 = 78.74像素

class EnrollmentRegistrationCertificateProcessor:
    """报班凭证处理器"""
    
    def __init__(self):
        """初始化处理器"""
        # 获取项目根目录
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.template_dir = os.path.join(self.base_dir, "properties")
        self.output_dir = os.path.join(self.base_dir, "image")
        self.template_file = "报班凭证.mrt"
        
        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # 字体路径
        self.font_path = os.path.join(os.environ.get('WINDIR', ''), 'Fonts', 'simhei.ttf')
        if not os.path.exists(self.font_path):
            self.font_path = None
        
        # 解析模板文件
        self.template_content = self.parse_template()
        
        # 寻找中文字体
        self.chinese_font_path = self._find_chinese_font()
    
    def _find_chinese_font(self):
        """寻找中文字体"""
        # 常见的中文字体路径
        font_paths = [
            r'C:\Windows\Fonts\msyh.ttc',    # 微软雅黑
            r'C:\Windows\Fonts\simsun.ttc',  # 宋体
            r'C:\Windows\Fonts\simhei.ttf',  # 黑体
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                return path
        return None
    
    def validate_data(self, data):
        """验证报班凭证的数据字段"""
        required_fields = [
            'sOrderCode', 'sSchoolName', 'sOperator'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in data or not data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"缺少必要字段: {', '.join(missing_fields)}")
        
        # 验证学生信息
        if 'Student' not in data or not data['Student']:
            raise ValueError("缺少学生信息")
        
        # 验证班级和卡片信息
        if 'ClassAndCardArray' not in data or not data['ClassAndCardArray']:
            raise ValueError("缺少班级和卡片信息")
        
        return True
    
    def process_data(self, data):
        """处理报班凭证的特殊数据逻辑"""
        processed_data = data.copy()
        
        # 处理主订单信息
        processed_data.setdefault('sOrderCode', '')
        processed_data.setdefault('sBatchCode', '')
        processed_data.setdefault('Discounttype', 0)
        processed_data.setdefault('BizType', '报班')
        processed_data.setdefault('sChannel', '直营')
        processed_data.setdefault('sPayType', '现金')
        processed_data.setdefault('sOperator', '系统')
        processed_data.setdefault('dtCreate', get_beijing_time_str())
        processed_data.setdefault('feedBackTitle', '客服热线：400-000-0000')
        processed_data.setdefault('feedBackImg', '')
        processed_data.setdefault('microServiceTitle', '微信公众号：XXXXX')
        processed_data.setdefault('microServiceImg', '')
        
        # 处理费用信息 - 确保数值类型正确
        for fee_field in ['dShouldFee', 'dFee', 'dReturnFee']:
            if fee_field in processed_data:
                try:
                    processed_data[fee_field] = float(processed_data[fee_field])
                except (ValueError, TypeError):
                    processed_data[fee_field] = 0.0
        
        # 设置费用默认值
        processed_data.setdefault('dShouldFee', 0.0)
        processed_data.setdefault('dFee', 0.0)
        processed_data.setdefault('dReturnFee', 0.0)
        
        # 处理学生信息
        if 'Student' in processed_data:
            student_info = processed_data['Student']
            student_info.setdefault('sStudentName', '')
            student_info.setdefault('sStudentCode', '')
            student_info.setdefault('sGender', '不详')
            student_info.setdefault('sMobile', '')
        
        # 处理班级和卡片信息数组
        if 'ClassAndCardArray' in processed_data:
            for item in processed_data['ClassAndCardArray']:
                item.setdefault('sSeatNo', '')
                item.setdefault('sClassCode', '')
                item.setdefault('sClassName', '')
                item.setdefault('dtBeginDate', '')
                item.setdefault('dtEndDate', '')
                item.setdefault('sRegisterTime', get_beijing_time_str())
                item.setdefault('sPrintAddress', '')
                item.setdefault('sPrintTime', get_beijing_time_str())
                item.setdefault('nTryLesson', '0')
                
                # 处理费用字段
                for fee_field in ['dVoucherFee', 'dFee', 'dRegisterFee', 'dClassVoucherFee', 'dShouldFee']:
                    if fee_field in item:
                        try:
                            item[fee_field] = float(item[fee_field])
                        except (ValueError, TypeError):
                            item[fee_field] = 0.0
                    else:
                        item[fee_field] = 0.0
        
        # 处理图像数据字段
        processed_data.setdefault('RWMImage', '')
        
        return processed_data
    
    def parse_template(self):
        """解析报班凭证模板"""
        template_path = os.path.join(self.template_dir, self.template_file)
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板文件不存在: {template_path}")
        
        from utils.certificate_processors.print_simulator import MrtParser
        return MrtParser(template_path)
    
    def generate_certificate(self, data, currency_symbol="¥"):
        """生成报班凭证"""
        try:
            print(f"开始处理报班凭证...")
            
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
            
            print(f"报班凭证生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"生成报班凭证失败: {str(e)}")
            raise
    
    def _create_certificate_image(self, data, mrt_parser, currency_symbol):
        """创建凭证图像"""
        try:
            # 使用与print_simulator相同的像素转换比例
            pixels_per_cm = PIXELS_PER_CM
            
            # 计算页面尺寸 - 横向A5尺寸 (从mrt文件: PageWidth>21, PageHeight>14.81, Orientation>Landscape)
            width = int(21.0 * pixels_per_cm)  # A5横向宽度
            
            # 根据班级数量动态计算高度
            class_count = len(data.get('ClassAndCardArray', []))
            base_height = 14.81  # A5横向高度
            extra_height = max(0, (class_count - 1) * 2.6)  # 每个额外班级增加2.6cm (DataBand高度)
            height = int((base_height + extra_height) * pixels_per_cm)
            
            # 创建图像
            image = Image.new('RGB', (width, height), 'white')
            draw = ImageDraw.Draw(image)
            
            # 页面边距 (从mrt文件: Margins>1,1,1,1)
            margin = 1.0 * pixels_per_cm
            center_offset_x = margin
            center_offset_y = margin
            
            # 字体缓存
            font_cache = {}
            
            # 获取默认字体
            try:
                default_font = ImageFont.load_default()
            except:
                default_font = ImageFont.load_default()
            
            # 处理模板组件，但过滤掉FooterBand和PageFooterBand相关的组件
            if hasattr(mrt_parser, 'components') and mrt_parser.components:
                for component in mrt_parser.components:
                    # 跳过FooterBand和PageFooterBand的组件，避免重复绘制
                    if self._should_skip_component(component, data):
                        continue
                        
                    if component['type'] == 'Text':
                        self._draw_text_component(component, data, draw, pixels_per_cm,
                                                center_offset_x, center_offset_y, 
                                                self.chinese_font_path, font_cache, default_font)
                    elif component['type'] == 'Image':
                        self._draw_image_component(component, image, pixels_per_cm,
                                                 center_offset_x, center_offset_y)
                    elif component['type'] == 'Line':
                        self._draw_line_component(component, draw, pixels_per_cm,
                                                center_offset_x, center_offset_y)
            
            # 绘制DataBand内容（班级列表）- 包含所有横线逻辑
            self._draw_databand_content(draw, data, pixels_per_cm, center_offset_x, center_offset_y, font_cache, self.chinese_font_path, default_font)
            
            return image
            
        except Exception as e:
            print(f"创建凭证图像时出错: {str(e)}")
            raise
    
    def _should_skip_component(self, component, data):
        """判断是否应该跳过绘制某个组件 - 清晰的逻辑区分"""
        text = component.get('text', '')
        component_type = component.get('type', '')
        rect = component.get('rect', '0,0,0,0')
        
        # 解析组件位置
        try:
            rect_parts = rect.split(',')
            if len(rect_parts) >= 4:
                x_pos = float(rect_parts[0])
                y_pos = float(rect_parts[1])
                width = float(rect_parts[2])
                height = float(rect_parts[3])
            else:
                x_pos = y_pos = width = height = 0
        except (ValueError, IndexError):
            x_pos = y_pos = width = height = 0
        
        # 调试：查看所有包含ClassAndCardArray的组件
        if 'ClassAndCardArray' in text:
            print(f"发现DataBand组件: {text} at ({x_pos}, {y_pos}) type={component_type}")
        
        # 调试：查看所有包含手机号相关的组件
        if '手机' in text or 'Mobile' in text or 'mobile' in text:
            print(f"发现手机号相关组件: {text} at ({x_pos}, {y_pos}) type={component_type}")
        
        if component_type == 'Text':
            # === 1. 过滤原模板的DataBand区域组件 ===
            # 无论位置在哪里，都过滤包含ClassAndCardArray的动态字段
            if '{ArrayList.ClassAndCardArray.' in text:
                print(f"过滤DataBand动态字段: {text} at ({x_pos}, {y_pos})")
                return True
            
            # 过滤所有DataBand相关的标签组件（无论位置）
            databand_labels = [
                '商品编号：', '商品名称：', '地点：', '时间：', '报到情况：',
                '开始时间：', '结束时间：', '标准金额：', '当前报名金额：', 
                '优惠金额：', '实收金额：', '试听次数：', '报名序号：'
            ]
            
            if text.strip() in databand_labels:
                print(f"过滤DataBand标签: {text} at ({x_pos}, {y_pos})")
                return True
            
            # === 2. 过滤FooterBand和PageFooterBand重复组件 ===
            footer_keywords = [
                '应收金额：', '优惠金额：', '实收金额：',  # FooterBand汇总信息
                '操作员：', '日期：', '客户代办人签字：',  # PageFooterBand信息
                '请妥善保存',  # PageFooterBand文字
                '微信公众号：', '客服热线：',  # 联系信息（已要求删除）
            ]
            
            for keyword in footer_keywords:
                if keyword in text:
                    print(f"过滤Footer组件: {text} at ({x_pos}, {y_pos})")
                    return True
            
            # === 3. 过滤特定动态字段组件 ===
            skip_dynamic_fields = [
                '{ArrayList.sOperator}', '{ArrayList.dtCreate}',
                '{ArrayList.dShouldFee}', '{ArrayList.dFee}', '{ArrayList.Discounttype}',
                '{ArrayList.sPayType}', '{ArrayList.microServiceTitle}', '{ArrayList.feedBackTitle}'
            ]
            
            # 过滤页码相关字段，我们会用英文格式替换
            if '{PageNofM}' in text:
                print(f"过滤页码字段: {text} at ({x_pos}, {y_pos})")
                return True
            
            for field in skip_dynamic_fields:
                if field in text:
                    print(f"过滤动态字段: {text} at ({x_pos}, {y_pos})")
                    return True
            
            # === 4. 保留的重要组件 ===
            # 保留标题相关组件
            if '报名凭证' in text or '{ArrayList.sSchoolName}' in text:
                print(f"保留标题组件: {text} at ({x_pos}, {y_pos})")
                return False
            
            # 保留学员信息组件
            student_fields = ['sStudentName', 'sStudentCode', 'sGender', 'sMobile']
            if any(field in text for field in student_fields):
                print(f"保留学员信息: {text} at ({x_pos}, {y_pos})")
                return False
            
            # 保留电话号码
            if '{ArrayList.sTelePhone}' in text:
                print(f"保留电话信息: {text} at ({x_pos}, {y_pos})")
                return False
            
            # 保留订单号等基本信息
            basic_fields = ['sOrderCode', 'sBatchCode']
            if any(field in text for field in basic_fields):
                print(f"保留基本信息: {text} at ({x_pos}, {y_pos})")
                return False
        
        # === 5. 其他组件类型 ===
        # 保留图片组件（logo等）
        if component_type == 'Image':
            return False
            
        # 过滤所有线条组件，我们会重新绘制
        if component_type == 'Line':
            print(f"过滤原模板线条 at ({x_pos}, {y_pos})")
            return True
            
        return False
    
    def _draw_databand_content(self, draw, data, pixels_per_cm, center_offset_x, center_offset_y, font_cache, chinese_font_path, default_font):
        """绘制DataBand内容 - 根据新的横线逻辑实现"""
        try:
            class_array = data.get('ClassAndCardArray', [])
            if not class_array:
                return
            
            # 计算字体高度用于精确定位
            font_size = 8
            font_height_cm = font_size * 0.035  # 大约字体高度转换为厘米
            
            # DataBand起始位置 - 再向上提升半个字的距离
            databand_start_y = (2.1 - font_height_cm * 0.5) * pixels_per_cm + center_offset_y
            
            # DataBand的实际内容高度（从商品编号到报名序号的距离）
            # 根据_draw_three_column_layout中的实际位置：报名序号在2.21cm处，再加上字体高度
            actual_content_height = (2.21 + font_height_cm) * pixels_per_cm  # 报名序号位置 + 字体高度
            
            # 每个DataBand之间的间距
            databand_spacing = font_height_cm * 0.8 * pixels_per_cm  # 总间距约0.8字高度
            
            # 总的DataBand高度 = 实际内容高度 + 间距
            total_databand_height = actual_content_height + databand_spacing
            
            # 字体设置
            font_to_use = self._get_font_with_scaling('Arial', font_size, False, True, 
                                                    chinese_font_path, font_cache, default_font)
            
            # 横线的起始和结束位置
            line_start_x = center_offset_x
            line_end_x = center_offset_x + 19 * pixels_per_cm
            
            # 1. 在业务类型下方绘制加粗横线（Y坐标约1.9cm处）
            business_line_y = 1.9 * pixels_per_cm + center_offset_y
            draw.line([(line_start_x, business_line_y), (line_end_x, business_line_y)], fill='black', width=2)
            print(f"绘制业务类型下方横线(加粗): y={business_line_y}")
            
            # 2. 绘制每个班级信息
            for i, class_item in enumerate(class_array):
                # 当前DataBand的起始位置
                current_y = databand_start_y + (i * total_databand_height)
                
                # 绘制三列布局
                self._draw_three_column_layout(class_item, draw, current_y, pixels_per_cm,
                                             center_offset_x, font_to_use)
                
                # 3. 在每条数据下方绘制细横线（但最后一条数据不画）
                # 横线位置 = 当前DataBand起始位置 + 实际内容高度（这样横线就紧贴在报名序号下方）
                if i < len(class_array) - 1:  # 不是最后一条数据
                    # 报名序号的精确位置：DataBand起始 + 2.21cm（报名序号Y位置）
                    registration_number_y = current_y + 2.21 * pixels_per_cm
                    # 使用更大的间距确保横线在报名序号下方
                    line_y = registration_number_y + (0.5 * pixels_per_cm)  # 固定0.5cm间距，约等于1.5个字高
                    draw.line([(line_start_x, line_y), (line_end_x, line_y)], fill='black', width=1)
                    print(f"绘制第{i+1}条数据下方横线(细): y={line_y}")
                    print(f"  - DataBand起始位置: {current_y/pixels_per_cm:.2f}cm")
                    print(f"  - 报名序号位置: {registration_number_y/pixels_per_cm:.2f}cm")
                    print(f"  - 横线绑定位置: {line_y/pixels_per_cm:.2f}cm")
                    print(f"  - 报名序号到横线距离: 0.5cm")
            
            # 4. 计算FooterBand位置并在应收金额上方绘制加粗横线
            # 最后一个DataBand的结束位置（不包括间距）
            last_databand_start = databand_start_y + (len(class_array) - 1) * total_databand_height
            last_databand_end = last_databand_start + actual_content_height
            footer_y = last_databand_end + 0.3 * pixels_per_cm  # 适当间距
            footer_line_y = footer_y - 0.1 * pixels_per_cm
            draw.line([(line_start_x, footer_line_y), (line_end_x, footer_line_y)], fill='black', width=2)
            print(f"绘制应收金额上方横线(加粗): y={footer_line_y}")
            
            # 5. 绘制FooterBand汇总信息
            self._draw_footer_summary(data, draw, footer_y, pixels_per_cm, 
                                    center_offset_x, chinese_font_path, font_cache, default_font)
                
        except Exception as e:
            print(f"绘制DataBand内容时出错: {str(e)}")

    def _draw_three_column_layout(self, class_item, draw, base_y, pixels_per_cm, 
                                center_offset_x, font_to_use):
        """绘制三列布局结构"""
        try:
            # 第一列：商品信息 (左侧)
            # 商品编号 (ClientRectangle>0,0.21,1.4,0.4)
            draw.text((center_offset_x, base_y + 0.21 * pixels_per_cm), 
                     "商品编号：", font=font_to_use, fill='black')
            draw.text((center_offset_x + 1.4 * pixels_per_cm, base_y + 0.21 * pixels_per_cm), 
                     str(class_item.get('sClassCode', '')), font=font_to_use, fill='black')
            
            # 商品名称 (ClientRectangle>0,0.6,1.4,0.4)
            draw.text((center_offset_x, base_y + 0.6 * pixels_per_cm), 
                     "商品名称：", font=font_to_use, fill='black')
            draw.text((center_offset_x + 1.4 * pixels_per_cm, base_y + 0.6 * pixels_per_cm), 
                     str(class_item.get('sClassName', '')), font=font_to_use, fill='black')
            
            # 地点 (ClientRectangle>0,1.01,1.4,0.4)
            draw.text((center_offset_x, base_y + 1.01 * pixels_per_cm), 
                     "地点：", font=font_to_use, fill='black')
            draw.text((center_offset_x + 1.4 * pixels_per_cm, base_y + 1.01 * pixels_per_cm), 
                     str(class_item.get('sPrintAddress', '')), font=font_to_use, fill='black')
            
            # 时间 (ClientRectangle>0,1.41,1.4,0.4)
            draw.text((center_offset_x, base_y + 1.41 * pixels_per_cm), 
                     "时间：", font=font_to_use, fill='black')
            draw.text((center_offset_x + 1.4 * pixels_per_cm, base_y + 1.41 * pixels_per_cm), 
                     str(class_item.get('sPrintTime', '')), font=font_to_use, fill='black')
            
            # 报到情况 (ClientRectangle>0,1.81,1.4,0.4)
            draw.text((center_offset_x, base_y + 1.81 * pixels_per_cm), 
                     "报到情况：", font=font_to_use, fill='black')
            draw.text((center_offset_x + 1.4 * pixels_per_cm, base_y + 1.81 * pixels_per_cm), 
                     str(class_item.get('sRegisterTime', '')), font=font_to_use, fill='black')
            
            # 第二列：时间信息 (中间)
            # 开始时间 (ClientRectangle>9.2,0.21,1.4,0.4)
            draw.text((center_offset_x + 9.2 * pixels_per_cm, base_y + 0.21 * pixels_per_cm), 
                     "开始时间：", font=font_to_use, fill='black')
            draw.text((center_offset_x + 10.6 * pixels_per_cm, base_y + 0.21 * pixels_per_cm), 
                     str(class_item.get('dtBeginDate', '')), font=font_to_use, fill='black')
            
            # 结束时间 (ClientRectangle>9.2,0.61,1.4,0.4)
            draw.text((center_offset_x + 9.2 * pixels_per_cm, base_y + 0.61 * pixels_per_cm), 
                     "结束时间：", font=font_to_use, fill='black')
            draw.text((center_offset_x + 10.6 * pixels_per_cm, base_y + 0.61 * pixels_per_cm), 
                     str(class_item.get('dtEndDate', '')), font=font_to_use, fill='black')
            
            # 第三列：金额信息 (右侧)
            # 标准金额 (ClientRectangle>14.8,0.21,2,0.4)
            draw.text((center_offset_x + 14.8 * pixels_per_cm, base_y + 0.21 * pixels_per_cm), 
                     "标准金额：", font=font_to_use, fill='black')
            draw.text((center_offset_x + 16.8 * pixels_per_cm, base_y + 0.21 * pixels_per_cm), 
                     f"¥{class_item.get('dFee', 0):.2f}", font=font_to_use, fill='black')
            
            # 当前报名金额 (ClientRectangle>14.8,0.6,2,0.4)
            draw.text((center_offset_x + 14.8 * pixels_per_cm, base_y + 0.6 * pixels_per_cm), 
                     "当前报名金额：", font=font_to_use, fill='black')
            draw.text((center_offset_x + 16.8 * pixels_per_cm, base_y + 0.6 * pixels_per_cm), 
                     f"¥{class_item.get('dShouldFee', 0):.2f}", font=font_to_use, fill='black')
            
            # 优惠金额 (ClientRectangle>14.8,1.01,2,0.4)
            draw.text((center_offset_x + 14.8 * pixels_per_cm, base_y + 1.01 * pixels_per_cm), 
                     "优惠金额：", font=font_to_use, fill='black')
            draw.text((center_offset_x + 16.8 * pixels_per_cm, base_y + 1.01 * pixels_per_cm), 
                     f"¥{class_item.get('dClassVoucherFee', 0):.2f}", font=font_to_use, fill='black')
            
            # 实收金额 (ClientRectangle>14.8,1.41,2,0.4)
            draw.text((center_offset_x + 14.8 * pixels_per_cm, base_y + 1.41 * pixels_per_cm), 
                     "实收金额：", font=font_to_use, fill='black')
            draw.text((center_offset_x + 16.8 * pixels_per_cm, base_y + 1.41 * pixels_per_cm), 
                     f"¥{class_item.get('dRegisterFee', 0):.2f}", font=font_to_use, fill='black')
            
            # 试听次数 (ClientRectangle>14.8,1.81,1.4,0.4)
            draw.text((center_offset_x + 14.8 * pixels_per_cm, base_y + 1.81 * pixels_per_cm), 
                     "试听次数：", font=font_to_use, fill='black')
            draw.text((center_offset_x + 16.2 * pixels_per_cm, base_y + 1.81 * pixels_per_cm), 
                     str(class_item.get('nTryLesson', '')), font=font_to_use, fill='black')
            
            # 报名序号 (ClientRectangle>14.8,2.21,1.4,0.4)
            draw.text((center_offset_x + 14.8 * pixels_per_cm, base_y + 2.21 * pixels_per_cm), 
                     "报名序号：", font=font_to_use, fill='black')
            draw.text((center_offset_x + 16.2 * pixels_per_cm, base_y + 2.21 * pixels_per_cm), 
                     str(class_item.get('sSeatNo', '')), font=font_to_use, fill='black')
            
        except Exception as e:
            print(f"绘制三列布局时出错: {str(e)}")

    def _draw_footer_summary(self, data, draw, footer_y, pixels_per_cm, 
                           center_offset_x, chinese_font_path, font_cache, default_font):
        """绘制FooterBand汇总信息 - 确保所有文字都加粗"""
        try:
            # 使用加粗字体 (从mrt文件: Font>Arial,9.5,Bold)
            bold_font = self._get_font_with_scaling('Arial', 9.5, True, True, 
                                                  chinese_font_path, font_cache, default_font)
            
            # 应收金额 (ClientRectangle>7.2,0.2,1.8,0.41)
            self._draw_bold_text(draw, (center_offset_x + 7.2 * pixels_per_cm, footer_y + 0.2 * pixels_per_cm), 
                                "应收金额：", bold_font)
            self._draw_bold_text(draw, (center_offset_x + 8.99 * pixels_per_cm, footer_y + 0.2 * pixels_per_cm), 
                                f"¥{data.get('dShouldFee', 0):.2f}", bold_font)
            
            # 优惠金额 (ClientRectangle>11.2,0.2,1.8,0.41)
            self._draw_bold_text(draw, (center_offset_x + 11.2 * pixels_per_cm, footer_y + 0.2 * pixels_per_cm), 
                                "优惠金额：", bold_font)
            self._draw_bold_text(draw, (center_offset_x + 13 * pixels_per_cm, footer_y + 0.2 * pixels_per_cm), 
                                f"¥{data.get('Discounttype', 0):.2f}", bold_font)
            
            # 实收金额 (ClientRectangle>15.21,0.2,1.8,0.41)
            self._draw_bold_text(draw, (center_offset_x + 15.21 * pixels_per_cm, footer_y + 0.2 * pixels_per_cm), 
                                "实收金额：", bold_font)
            self._draw_bold_text(draw, (center_offset_x + 17 * pixels_per_cm, footer_y + 0.2 * pixels_per_cm), 
                                f"¥{data.get('dFee', 0):.2f}", bold_font)
            
            # 支付方式 (ClientRectangle>0,0.8,18.99,0.81) - 右对齐
            pay_type_text = str(data.get('sPayType', ''))
            if pay_type_text:
                # 计算右对齐位置
                text_bbox = draw.textbbox((0, 0), pay_type_text, font=bold_font)
                text_width = text_bbox[2] - text_bbox[0]
                right_align_x = center_offset_x + 18.99 * pixels_per_cm - text_width
                self._draw_bold_text(draw, (right_align_x, footer_y + 0.8 * pixels_per_cm), 
                                   pay_type_text, bold_font)
            
            # 绘制页脚信息
            self._draw_page_footer(draw, footer_y + 1.8 * pixels_per_cm, pixels_per_cm, 
                                 center_offset_x, chinese_font_path, font_cache, default_font, data)
            
        except Exception as e:
            print(f"绘制FooterBand汇总信息时出错: {str(e)}")

    def _draw_bold_text(self, draw, pos, text, font):
        """绘制加粗文字 - 使用多次绘制技术"""
        x, y = pos
        
        # 绘制多个偏移位置实现加粗效果
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:  # 不绘制中心点
                    draw.text((x + dx, y + dy), text, fill='black', font=font)
        
        # 额外加粗绘制
        draw.text((x + 1, y), text, fill='black', font=font)
        draw.text((x, y + 1), text, fill='black', font=font)
        
        # 主文本
        draw.text((x, y), text, fill='black', font=font)

    def _draw_page_footer(self, draw, footer_start_y, pixels_per_cm, center_offset_x, 
                        chinese_font_path, font_cache, default_font, data):
        """绘制页脚信息"""
        try:
            # 页脚字体
            footer_font = self._get_font_with_scaling('Arial', 8, False, True, 
                                                    chinese_font_path, font_cache, default_font)
            
            # 请妥善保存 (ClientRectangle>0,-0.01,4.2,0.41)
            draw.text((center_offset_x, footer_start_y), 
                     "请妥善保存", font=footer_font, fill='black')
            
            # 客户代办人签字 (ClientRectangle>4.2,-0.01,6.8,0.41)
            draw.text((center_offset_x + 4.2 * pixels_per_cm, footer_start_y), 
                     "客户代办人签字：", font=footer_font, fill='black')
            
            # 操作员 (ClientRectangle>11.2,0.01,1.2,0.4)
            draw.text((center_offset_x + 11.2 * pixels_per_cm, footer_start_y + 0.02 * pixels_per_cm), 
                     "操作员：", font=footer_font, fill='black')
            draw.text((center_offset_x + 12.4 * pixels_per_cm, footer_start_y + 0.02 * pixels_per_cm), 
                     str(data.get('sOperator', '')), font=footer_font, fill='black')
            
            # 日期 (ClientRectangle>15.0,0.0,1.0,0.4)
            draw.text((center_offset_x + 15.0 * pixels_per_cm, footer_start_y), 
                     "日期：", font=footer_font, fill='black')
            draw.text((center_offset_x + 16.0 * pixels_per_cm, footer_start_y), 
                     str(data.get('dtCreate', '')), font=footer_font, fill='black')
            
            # 页码 - 修改为英文格式 (ClientRectangle>16.4,0.8,2.6,0.4)
            draw.text((center_offset_x + 16.4 * pixels_per_cm, footer_start_y + 0.8 * pixels_per_cm), 
                     "Page 1 of 1", font=footer_font, fill='black')
            
        except Exception as e:
            print(f"绘制页脚信息时出错: {str(e)}")

    def _mask_mobile_number(self, mobile):
        """对手机号进行打码处理，中间四位替换为星号"""
        if not mobile or len(mobile) < 7:
            return mobile
        
        # 移除所有非数字字符
        digits_only = ''.join(filter(str.isdigit, mobile))
        
        if len(digits_only) == 11:  # 标准11位手机号
            # 前3位 + 4个星号 + 后4位
            return digits_only[:3] + '****' + digits_only[7:]
        elif len(digits_only) >= 7:  # 其他长度的号码
            # 保留前3位和后4位，中间用星号
            front = digits_only[:3]
            back = digits_only[-4:]
            stars = '*' * (len(digits_only) - 7)
            return front + stars + back
        else:
            return mobile  # 太短的号码不处理

    def _draw_text_component(self, component, data, draw, pixels_per_cm, 
                           center_offset_x, center_offset_y, chinese_font_path, 
                           font_cache, default_font):
        """绘制文本组件"""
        try:
            text = component.get('text', '')
            if not text:
                return
            
            original_text = text  # 保存原始文本用于调试
            
            # 处理动态文本替换
            if '{ArrayList.sSchoolName}报名凭证' in text:
                # 修改标题为"南昌学校报名凭证"
                text = text.replace('{ArrayList.sSchoolName}报名凭证', '南昌学校报名凭证')
            elif '手机号：{ArrayList.Student.sMobile}' in text:
                # 特殊处理手机号字段（包含冒号的完整格式）
                mobile = data.get('Student', {}).get('sMobile', '')
                # 对手机号进行打码处理
                masked_mobile = self._mask_mobile_number(mobile)
                text = text.replace('{ArrayList.Student.sMobile}', masked_mobile)
                print(f"处理手机号(完整格式): {original_text} -> {text}")
            elif text.startswith('{ArrayList.Student.'):
                # 处理学员信息字段 - 特殊处理
                if '{ArrayList.Student.sStudentName}' in text:
                    student_name = data.get('Student', {}).get('sStudentName', '')
                    text = text.replace('{ArrayList.Student.sStudentName}', student_name)
                    print(f"处理学员姓名: {original_text} -> {text}")
                elif '{ArrayList.Student.sStudentCode}' in text:
                    student_code = data.get('Student', {}).get('sStudentCode', '')
                    text = text.replace('{ArrayList.Student.sStudentCode}', student_code)
                    print(f"处理学员编码: {original_text} -> {text}")
                elif '{ArrayList.Student.sGender}' in text:
                    gender = data.get('Student', {}).get('sGender', '')
                    text = text.replace('{ArrayList.Student.sGender}', gender)
                    print(f"处理性别: {original_text} -> {text}")
                elif '{ArrayList.Student.sMobile}' in text:
                    mobile = data.get('Student', {}).get('sMobile', '')
                    # 对手机号进行打码处理
                    masked_mobile = self._mask_mobile_number(mobile)
                    text = text.replace('{ArrayList.Student.sMobile}', masked_mobile)
                    print(f"处理手机号: {original_text} -> {text}")
            elif '{ArrayList.sTelePhone}' in text:
                # 处理联系电话字段
                phone = data.get('sTelePhone', '')
                text = text.replace('{ArrayList.sTelePhone}', phone)
                print(f"处理联系电话: {original_text} -> {text}")
            elif text.startswith('{ArrayList.'):
                # 处理其他动态字段
                field_name = text.strip('{}')
                if '.' in field_name:
                    parts = field_name.split('.')
                    if len(parts) >= 2:
                        field_key = parts[1]
                        if field_key in data:
                            text = str(data[field_key])
                        else:
                            text = ''
                else:
                    if field_name in data:
                        text = str(data[field_name])
                    else:
                        text = ''
            elif text.startswith('{') and text.endswith('}'):
                # 处理其他格式的动态字段
                field_name = text.strip('{}')
                if field_name in data:
                    text = str(data[field_name])
                else:
                    text = ''
            
            if not text:
                return
            
            # 获取位置和尺寸
            rect = component.get('rect', '0,0,0,0')
            rect_parts = rect.split(',')
            if len(rect_parts) < 4:
                return
            
            try:
                x = float(rect_parts[0]) * pixels_per_cm + center_offset_x
                y = float(rect_parts[1]) * pixels_per_cm + center_offset_y
                width = float(rect_parts[2]) * pixels_per_cm
                height = float(rect_parts[3]) * pixels_per_cm
            except (ValueError, IndexError):
                return
            
            # 获取字体信息
            font_info = component.get('font', 'Arial,8')
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
            should_bold = 'Bold' in font_info or '南昌学校报名凭证' in text  # 标题加粗
            
            # 获取字体
            font_to_use = self._get_font(font_info, chinese_font_path, has_chinese, 
                                       should_bold, font_cache, default_font)
            
            # 处理对齐方式
            alignment = component.get('alignment', 'Left')
            if alignment == 'Right':
                text_bbox = draw.textbbox((0, 0), text, font=font_to_use)
                text_width = text_bbox[2] - text_bbox[0]
                x = x + width - text_width
            elif alignment == 'Center':
                text_bbox = draw.textbbox((0, 0), text, font=font_to_use)
                text_width = text_bbox[2] - text_bbox[0]
                x = x + (width - text_width) / 2
            
            # 绘制文本 - 如果是标题则加粗
            if '南昌学校报名凭证' in text:
                self._draw_bold_text(draw, (x, y), text, font_to_use)
            else:
                draw.text((x, y), text, font=font_to_use, fill='black')
            
        except Exception as e:
            print(f"绘制文本组件时出错: {str(e)}")
    
    def _draw_image_component(self, component, main_image, pixels_per_cm, center_offset_x, center_offset_y):
        """绘制图像组件"""
        try:
            rect_parts = component['rect'].split(',') if component['rect'] else [0, 0, 1, 1]
            if len(rect_parts) >= 4:
                x = int(float(rect_parts[0]) * pixels_per_cm + center_offset_x)
                y = int(float(rect_parts[1]) * pixels_per_cm + center_offset_y)
                width = int(float(rect_parts[2]) * pixels_per_cm)
                height = int(float(rect_parts[3]) * pixels_per_cm)
                
                image_data = component.get('image_data', '')
                if image_data:
                    try:
                        # 解码base64图像数据
                        image_bytes = base64.b64decode(image_data)
                        image = Image.open(io.BytesIO(image_bytes))
                        image = image.resize((width, height), Image.Resampling.LANCZOS)
                        main_image.paste(image, (x, y))
                    except Exception as e:
                        print(f"处理图像数据时出错: {str(e)}")
        except Exception as e:
            print(f"绘制图像组件时出错: {str(e)}")
    
    def _draw_line_component(self, component, draw, pixels_per_cm, center_offset_x, center_offset_y):
        """绘制线条组件"""
        try:
            rect = component.get('rect', '0,0,0,0')
            rect_parts = rect.split(',')
            if len(rect_parts) < 4:
                return
            
            try:
                x1 = float(rect_parts[0]) * pixels_per_cm + center_offset_x
                y1 = float(rect_parts[1]) * pixels_per_cm + center_offset_y
                width = float(rect_parts[2]) * pixels_per_cm
                height = float(rect_parts[3]) * pixels_per_cm
                
                x2 = x1 + width
                y2 = y1 + height
                
                # 绘制线条
                draw.line([(x1, y1), (x2, y2)], fill='black', width=1)
                
            except (ValueError, IndexError):
                return
                
        except Exception as e:
            print(f"绘制线条组件时出错: {str(e)}")
    
    def _get_font_with_scaling(self, font_name, font_size, should_bold, has_chinese, 
                             chinese_font_path, font_cache, default_font):
        """使用与print_simulator相同的字体缩放逻辑获取字体对象"""
        try:
            font_key = f"{font_name}_{font_size}_{should_bold}_{has_chinese}"
            
            if font_key in font_cache:
                return font_cache[font_key]
            
            # 使用与print_simulator相同的字体大小计算公式
            # 字体大小按比例调整，由于分辨率提高到200 DPI，需要相应调整字体大小
            base_size = max(16, int(font_size * 2.7))  # 至少16像素，放大2.7倍
            # 对于加粗文字，稍微增加字体大小，但主要靠多次绘制实现
            adjusted_size = int(base_size * 1.1) if should_bold else base_size
            
            if has_chinese and chinese_font_path:
                try:
                    font = ImageFont.truetype(chinese_font_path, adjusted_size)
                    font_cache[font_key] = font
                    return font
                except Exception:
                    pass
            
            # 尝试英文字体
            try:
                font_path = os.path.join(os.environ.get('WINDIR', ''), 'Fonts', f"{font_name}.ttf")
                if not os.path.exists(font_path):
                    # 尝试其他扩展名
                    font_path = os.path.join(os.environ.get('WINDIR', ''), 'Fonts', f"{font_name}.ttc")

                if not os.path.exists(font_path):
                    # 如果找不到指定字体，使用中文字体
                    if chinese_font_path:
                        font = ImageFont.truetype(chinese_font_path, adjusted_size)
                        font_cache[font_key] = font
                        return font
                    else:
                        # 使用默认字体
                        font_cache[font_key] = default_font
                        return default_font

                font = ImageFont.truetype(font_path, adjusted_size)
                font_cache[font_key] = font
                return font
            except Exception as e:
                print(f"加载字体失败 {font_name} 大小 {font_size}: {str(e)}")
                # 如果加载失败，尝试使用中文字体作为备用
                if chinese_font_path:
                    try:
                        font = ImageFont.truetype(chinese_font_path, adjusted_size)
                        font_cache[font_key] = font
                        return font
                    except:
                        pass
                
                # 使用默认字体
                font_cache[font_key] = default_font
                return default_font
            
        except Exception as e:
            print(f"获取字体时出错: {str(e)}")
            return default_font

    def _get_font(self, font_info, chinese_font_path, has_chinese, should_bold, font_cache, default_font):
        """获取字体对象 - 保持向后兼容性"""
        return self._get_font_with_scaling(
            font_info.get('name', 'Arial'),
            font_info.get('size', 9),
            should_bold,
            has_chinese,
            chinese_font_path,
            font_cache,
            default_font
        )
    
    def _save_certificate(self, image, data):
        """保存凭证文件"""
        try:
            # 生成文件名
            order_code = data.get('sOrderCode', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"报班凭证_{order_code}_{timestamp}.png"
            output_path = os.path.join(self.output_dir, filename)
            
            # 保存图像
            image.save(output_path, 'PNG', quality=95)
            
            return output_path
        except Exception as e:
            print(f"保存凭证文件时出错: {str(e)}")
            raise

    def _draw_databand_cell(self, draw, text, x, y, pixels_per_cm, center_offset_x, center_offset_y, font_cache, chinese_font_path, default_font):
        """绘制DataBand单元格"""
        try:
            if not text:
                return
                
            # 计算实际位置
            actual_x = x * pixels_per_cm + center_offset_x
            actual_y = y * pixels_per_cm + center_offset_y
            
            # 检查是否包含中文
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in str(text))
            
            # 使用_get_font_with_scaling方法直接获取字体
            font_to_use = self._get_font_with_scaling('Arial', 8, False, has_chinese, 
                                                    chinese_font_path, font_cache, default_font)
            
            # 绘制文本
            draw.text((actual_x, actual_y), str(text), font=font_to_use, fill='black')
            
        except Exception as e:
            print(f"绘制DataBand单元格时出错: {str(e)}")
            # 使用默认字体作为备选
            try:
                draw.text((actual_x, actual_y), str(text), font=default_font, fill='black')
            except:
                pass

def generate_enrollment_registration_certificate(data, currency_symbol="¥"):
    """生成报班凭证的便捷函数"""
    processor = EnrollmentRegistrationCertificateProcessor()
    return processor.generate_certificate(data, currency_symbol)

def create_mock_data():
    """创建模拟数据用于测试 - 包含3个班级记录"""
    mock_data = {
        # 主订单信息
        "sOrderCode": "ORD20240101001",
        "sBatchCode": "BATCH001",
        "Discounttype": 200.00,  # 优惠金额
        "BizType": "报班",
        "sChannel": "直营",
        "sPayType": "现金支付",
        "sSchoolName": "南昌新东方培训学校",
        "sTelePhone": "400-000-0000",
        "sOperator": "张三",
        "dtCreate": get_beijing_time_str(),
        "feedBackTitle": "客服热线：400-000-0000",
        "feedBackImg": "",
        "microServiceTitle": "微信公众号：XXXXX",
        "microServiceImg": "",
        "RWMImage": "",
        
        # 学生信息
        "Student": {
            "sStudentName": "李小明",
            "sStudentCode": "STU20240001",
            "sGender": "男",
            "sMobile": "13800138000"
        },
        
        # 班级和卡片信息数组 (DataBand数据) - 3个班级
        "ClassAndCardArray": [
            {
                "sSeatNo": "A001",
                "sClassCode": "MATH001",
                "sClassName": "数学基础班",
                "dtBeginDate": "2024-01-15",
                "dtEndDate": "2024-03-15", 
                "sRegisterTime": "2024-01-10 报名成功",
                "sPrintAddress": "北京市朝阳区XX路XX号101教室",
                "sPrintTime": "2024-01-15 09:00-12:00",
                "nTryLesson": "2",
                "dVoucherFee": 100.00,
                "dFee": 1500.00,                    # 标准金额
                "dRegisterFee": 1400.00,            # 实收金额
                "dClassVoucherFee": 100.00,         # 优惠金额
                "dShouldFee": 1400.00               # 当前报名金额
            },
            {
                "sSeatNo": "B002",
                "sClassCode": "ENG001", 
                "sClassName": "英语提高班",
                "dtBeginDate": "2024-02-01",
                "dtEndDate": "2024-04-01",
                "sRegisterTime": "2024-01-25 报名成功",
                "sPrintAddress": "北京市朝阳区XX路XX号201教室",
                "sPrintTime": "2024-02-01 14:00-17:00",
                "nTryLesson": "1",
                "dVoucherFee": 50.00,
                "dFee": 1600.00,                    # 标准金额
                "dRegisterFee": 1550.00,            # 实收金额
                "dClassVoucherFee": 50.00,          # 优惠金额
                "dShouldFee": 1550.00               # 当前报名金额
            },
            {
                "sSeatNo": "C003",
                "sClassCode": "PHY001", 
                "sClassName": "物理基础班",
                "dtBeginDate": "2024-03-01",
                "dtEndDate": "2024-05-01",
                "sRegisterTime": "2024-02-20 报名成功",
                "sPrintAddress": "北京市朝阳区XX路XX号301教室",
                "sPrintTime": "2024-03-01 08:00-11:00",
                "nTryLesson": "0",
                "dVoucherFee": 50.00,
                "dFee": 1300.00,                    # 标准金额
                "dRegisterFee": 1250.00,            # 实收金额
                "dClassVoucherFee": 50.00,          # 优惠金额
                "dShouldFee": 1250.00               # 当前报名金额
            }
        ]
    }
    
    return mock_data

def test_enrollment_registration_certificate():
    """测试报班凭证生成"""
    try:
        print("开始测试报班凭证生成...")
        
        # 创建模拟数据
        mock_data = create_mock_data()
        
        # 生成凭证
        output_path = generate_enrollment_registration_certificate(mock_data)
        
        print(f"测试成功！凭证已生成：{output_path}")
        return output_path
        
    except Exception as e:
        print(f"测试失败：{str(e)}")
        raise

if __name__ == "__main__":
    # 运行测试
    test_enrollment_registration_certificate() 