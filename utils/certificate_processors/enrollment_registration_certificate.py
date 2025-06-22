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
        """生成报班凭证 - 支持分页"""
        try:
            print(f"开始处理报班凭证...")
            
            # 验证数据
            self.validate_data(data)
            
            # 处理数据
            processed_data = self.process_data(data)
            
            # 解析模板
            mrt_parser = self.parse_template()
            
            # 计算分页
            class_array = processed_data.get('ClassAndCardArray', [])
            pages = self._calculate_pages(class_array)
            
            output_paths = []
            
            # 生成每一页
            for page_num, page_data in enumerate(pages, 1):
                is_last_page = (page_num == len(pages))
                
                # 创建当前页的数据副本
                page_processed_data = processed_data.copy()
                page_processed_data['ClassAndCardArray'] = page_data['classes']
                page_processed_data['current_page'] = page_num
                page_processed_data['total_pages'] = len(pages)
                page_processed_data['is_last_page'] = is_last_page
                
                # 生成图像
                image = self._create_certificate_image(page_processed_data, mrt_parser, currency_symbol)
                
                # 保存文件
                output_path = self._save_certificate_page(image, processed_data, page_num, len(pages))
                output_paths.append(output_path)
            
            print(f"报班凭证生成成功，共{len(pages)}页: {output_paths}")
            return output_paths
            
        except Exception as e:
            print(f"生成报班凭证失败: {str(e)}")
            raise
    
    def _create_certificate_image(self, data, mrt_parser, currency_symbol):
        """创建凭证图像 - 支持分页，使用固定纸张大小"""
        try:
            # 重置已绘制组件缓存（每页重新开始）
            self._drawn_components = set()
            
            # 使用与print_simulator相同的像素转换比例
            pixels_per_cm = PIXELS_PER_CM
            
            # 固定页面尺寸 - 横向A5尺寸，稍微增加高度确保二维码下方有空隙
            width = int(21.0 * pixels_per_cm)  # A5横向宽度
            height = int(16.0 * pixels_per_cm)  # 增加高度到16cm，确保二维码下方有足够空隙
            
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
            
            # 处理模板组件，但完全跳过页脚相关的Band
            if hasattr(mrt_parser, 'components') and mrt_parser.components:
                for component in mrt_parser.components:
                    # 简单粗暴：完全跳过所有页脚相关组件
                    text = component.get('text', '')
                    if any(keyword in text for keyword in ['请妥善保存', '客户代办人签字', '操作员', '日期', 'sOperator', 'dtCreate', 'PageNofM']):
                        continue
                    
                    # 跳过其他需要过滤的组件
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
            
            # 添加二维码到左下角
            self._add_qr_code(image, draw, pixels_per_cm, center_offset_x, center_offset_y, font_cache, default_font)
            
            return image
            
        except Exception as e:
            print(f"创建凭证图像时出错: {str(e)}")
            raise
    
    def _should_skip_component(self, component, data):
        """判断是否应该跳过绘制某个组件 - 使用精确位置过滤重复组件"""
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
        
        # === 0. 去重处理：跟踪已绘制的组件，避免重复绘制相同位置的相同内容 ===
        if not hasattr(self, '_drawn_components'):
            self._drawn_components = set()
        
        component_key = f"{text}@{rect}"
        if component_key in self._drawn_components:
            print(f"跳过重复组件: {text} at ({x_pos}, {y_pos})")
            return True
        
        # 调试：查看所有包含ClassAndCardArray的组件
        if 'ClassAndCardArray' in text:
            print(f"发现DataBand组件: {text} at ({x_pos}, {y_pos}) type={component_type}")
        
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
            
            # === 1.5. 严格过滤所有页脚相关组件（基于Y坐标位置） ===
            # 如果Y坐标小于等于1cm（页面底部区域），很可能是页脚组件
            if y_pos <= 1.0:
                footer_related_texts = [
                    '请妥善保存', '客户代办人签字', '操作员', '日期', 
                    '{ArrayList.sOperator}', '{ArrayList.dtCreate}', '{PageNofM}'
                ]
                for footer_text in footer_related_texts:
                    if footer_text in text:
                        print(f"过滤底部页脚组件(Y≤1cm): {text} at ({x_pos}, {y_pos})")
                        return True
            
            # === 2. 彻底过滤所有FooterBand汇总信息 ===
            # 我们将自己重新绘制这些信息，所以过滤掉模板中的所有相关组件
            
            # 过滤所有应收金额相关（无论位置）
            if text == '应收金额：':
                print(f"过滤模板应收金额: {text} at ({x_pos}, {y_pos})")
                return True
            
            if text == '优惠金额：':
                print(f"过滤模板优惠金额: {text} at ({x_pos}, {y_pos})")
                return True
            
            if text == '实收金额：':
                print(f"过滤模板实收金额: {text} at ({x_pos}, {y_pos})")
                return True
            
            if text == '支付方式：':
                print(f"过滤模板支付方式: {text} at ({x_pos}, {y_pos})")
                return True
            
            # === 3. 彻底过滤所有PageFooterBand信息 ===
            # 我们将自己重新绘制这些信息，所以过滤掉模板中的所有相关组件
            
            # 过滤所有操作员相关（无论位置）
            if '操作员' in text and text.strip() in ['操作员：', '操作员']:
                print(f"过滤模板操作员: {text} at ({x_pos}, {y_pos})")
                return True
            
            # 过滤所有日期相关（无论位置）
            if '日期' in text and text.strip() in ['日期：', '日期']:
                print(f"过滤模板日期: {text} at ({x_pos}, {y_pos})")
                return True
            
            # 过滤所有客户代办人签字相关（无论位置）
            if '客户代办人签字' in text:
                print(f"过滤模板客户代办人签字: {text} at ({x_pos}, {y_pos})")
                return True
            
            # 过滤所有请妥善保存相关（无论位置）
            if '请妥善保存' in text:
                print(f"过滤模板请妥善保存: {text} at ({x_pos}, {y_pos})")
                return True
            
            # === 4. 彻底过滤所有汇总动态字段 ===
            # 我们将自己重新绘制这些信息，所以过滤掉模板中的所有相关字段
            
            if text == '{ArrayList.dShouldFee}':
                print(f"过滤模板汇总字段: {text} at ({x_pos}, {y_pos})")
                return True
            
            if text == '{ArrayList.dFee}':
                print(f"过滤模板汇总字段: {text} at ({x_pos}, {y_pos})")
                return True
            
            if text == '{ArrayList.Discounttype}':
                print(f"过滤模板汇总字段: {text} at ({x_pos}, {y_pos})")
                return True
            
            # PageFooterBand字段：彻底过滤，我们将自己重新绘制
            if text == '{ArrayList.sOperator}':
                print(f"过滤模板操作员字段: {text} at ({x_pos}, {y_pos})")
                return True
            
            if text == '{ArrayList.dtCreate}':
                print(f"过滤模板日期字段: {text} at ({x_pos}, {y_pos})")
                return True
            
            # 过滤页码相关字段，我们会用英文格式替换
            if '{PageNofM}' in text or 'PageNofM' in text:
                print(f"过滤页码字段: {text} at ({x_pos}, {y_pos})")
                return True
            
            # 过滤所有可能包含页脚关键词的文本（更严格的过滤）
            footer_keywords = ['请妥善保存', '客户代办人签字', '操作员', '日期']
            for keyword in footer_keywords:
                if keyword in text:
                    print(f"过滤包含页脚关键词的组件: {text} at ({x_pos}, {y_pos})")
                    return True
            
            # 过滤其他字段
            skip_other_fields = ['{ArrayList.sPayType}', '{ArrayList.microServiceTitle}', '{ArrayList.feedBackTitle}']
            for field in skip_other_fields:
                if field in text:
                    print(f"过滤其他字段: {text} at ({x_pos}, {y_pos})")
                    return True
            
            # 删除的联系信息
            contact_keywords = ['微信公众号：', '客服热线：']
            for keyword in contact_keywords:
                if keyword in text:
                    print(f"过滤联系信息: {text} at ({x_pos}, {y_pos})")
                    return True
            
            # === 5. 保留的重要组件 ===
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
        
        # === 6. 其他组件类型 ===
        # 保留图片组件（logo等）
        if component_type == 'Image':
            return False
            
        # 过滤所有线条组件，我们会重新绘制
        if component_type == 'Line':
            print(f"过滤原模板线条 at ({x_pos}, {y_pos})")
            return True
        
        # === 7. 记录不跳过的组件，避免后续重复绘制 ===
        self._drawn_components.add(component_key)
        print(f"记录组件: {text} at ({x_pos}, {y_pos})")
        return False
    
    def _draw_databand_content(self, draw, data, pixels_per_cm, center_offset_x, center_offset_y, font_cache, chinese_font_path, default_font):
        """绘制DataBand内容 - 支持分页"""
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
            
            # 字体设置 - 改为宋体
            font_to_use = self._get_font_with_scaling('SimSun', font_size, False, True, 
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
                # 报名序号位置在 current_y + 2.21cm，横线要在报名序号下方留1/3字距离
                if i < len(class_array) - 1:  # 不是最后一条数据
                    registration_number_y = current_y + 2.21 * pixels_per_cm  # 报名序号的Y位置
                    # 使用更大的间距确保横线在报名序号下方
                    line_y = registration_number_y + (0.5 * pixels_per_cm)  # 固定0.5cm间距，约等于1.5个字高
                    draw.line([(line_start_x, line_y), (line_end_x, line_y)], fill='black', width=1)
                    print(f"绘制第{i+1}条数据下方横线(细): y={line_y}")
                    print(f"  - DataBand起始位置: {current_y/pixels_per_cm:.2f}cm")
                    print(f"  - 报名序号位置: {registration_number_y/pixels_per_cm:.2f}cm")
                    print(f"  - 横线绑定位置: {line_y/pixels_per_cm:.2f}cm")
                    print(f"  - 报名序号到横线距离: 0.5cm")
            
            # 4. 在所有DataBand下方绘制横线
            # 最后一个DataBand的结束位置（不包括间距）
            last_databand_start = databand_start_y + (len(class_array) - 1) * total_databand_height
            last_databand_end = last_databand_start + actual_content_height
            
            # 在所有DataBand下方绘制横线
            databand_bottom_line_y = last_databand_end + 0.1 * pixels_per_cm  # DataBand结束后0.1cm
            draw.line([(line_start_x, databand_bottom_line_y), (line_end_x, databand_bottom_line_y)], fill='black', width=2)
            print(f"绘制DataBand底部横线(加粗): y={databand_bottom_line_y/pixels_per_cm:.2f}cm")
            
            footer_start_y = databand_bottom_line_y + 0.2 * pixels_per_cm  # 横线下方0.2cm开始页脚
            
            # 5. 只在最后一页绘制FooterBand汇总信息
            is_last_page = data.get('is_last_page', True)
            if is_last_page:
                # 直接绘制FooterBand汇总信息，不再添加额外横线（DataBand下方已有横线）
                self._draw_footer_summary(data, draw, footer_start_y, pixels_per_cm, 
                                        center_offset_x, chinese_font_path, font_cache, default_font)
                
                # 更新页脚起始位置（汇总信息下方）
                footer_start_y += 1.0 * pixels_per_cm  # 汇总信息高度约1cm
            
            # 6. 绘制PageFooter信息（每页都显示，固定在页面底部）
            # 计算页面底部位置
            page_height = int(16.0 * pixels_per_cm)  # 更新后的页面高度
            fixed_footer_y = page_height - 4.7 * pixels_per_cm  # 距离底部4.7cm的固定位置（往上移动3行字，约1.2cm）
            self._draw_fixed_page_footer(draw, data, fixed_footer_y, pixels_per_cm, center_offset_x, chinese_font_path, font_cache, default_font)
                
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
            # 使用加粗宋体 (从mrt文件: Font>Arial,9.5,Bold)
            bold_font = self._get_font_with_scaling('SimSun', 9.5, True, True, 
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
            
            # 页脚信息由_draw_fixed_page_footer统一处理，这里不再重复绘制
            
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
            # 页脚字体 - 改为宋体
            footer_font = self._get_font_with_scaling('SimSun', 8, False, True, 
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
            current_page = data.get('current_page', 1)
            total_pages = data.get('total_pages', 1)
            page_text = f"Page {current_page} of {total_pages}"
            draw.text((center_offset_x + 16.4 * pixels_per_cm, center_offset_y + 13.3 * pixels_per_cm), 
                     page_text, font=footer_font, fill='black')
            
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
            
            # 字体文件名映射
            font_file_mapping = {
                'SimSun': ['simsun.ttc', 'simsun.ttf'],
                '宋体': ['simsun.ttc', 'simsun.ttf'],
                'Arial': ['arial.ttf', 'arial.ttc'],
                'Microsoft YaHei': ['msyh.ttc', 'msyh.ttf'],
                '微软雅黑': ['msyh.ttc', 'msyh.ttf']
            }
            
            # 对于中文字体或宋体，优先使用中文字体路径或系统宋体
            if has_chinese or font_name in ['SimSun', '宋体']:
                # 先尝试系统宋体
                if font_name in ['SimSun', '宋体']:
                    fonts_dir = os.path.join(os.environ.get('WINDIR', ''), 'Fonts')
                    for font_file in font_file_mapping.get('SimSun', ['simsun.ttc']):
                        font_path = os.path.join(fonts_dir, font_file)
                        if os.path.exists(font_path):
                            try:
                                font = ImageFont.truetype(font_path, adjusted_size)
                                font_cache[font_key] = font
                                print(f"成功加载宋体: {font_path}")
                                return font
                            except Exception as e:
                                print(f"加载宋体失败 {font_path}: {str(e)}")
                                continue
                
                # 如果找不到宋体，尝试使用中文字体路径
                if chinese_font_path:
                    try:
                        font = ImageFont.truetype(chinese_font_path, adjusted_size)
                        font_cache[font_key] = font
                        print(f"使用中文字体路径: {chinese_font_path}")
                        return font
                    except Exception as e:
                        print(f"加载中文字体失败 {chinese_font_path}: {str(e)}")
            
            # 尝试英文字体
            try:
                fonts_dir = os.path.join(os.environ.get('WINDIR', ''), 'Fonts')
                font_files = font_file_mapping.get(font_name, [f"{font_name.lower()}.ttf", f"{font_name.lower()}.ttc"])
                
                for font_file in font_files:
                    font_path = os.path.join(fonts_dir, font_file)
                    if os.path.exists(font_path):
                        try:
                            font = ImageFont.truetype(font_path, adjusted_size)
                            font_cache[font_key] = font
                            print(f"成功加载字体: {font_path}")
                            return font
                        except Exception as e:
                            print(f"加载字体失败 {font_path}: {str(e)}")
                            continue

                # 如果找不到指定字体，使用中文字体作为备用
                if chinese_font_path:
                    font = ImageFont.truetype(chinese_font_path, adjusted_size)
                    font_cache[font_key] = font
                    print(f"使用中文字体作为备用: {chinese_font_path}")
                    return font
                else:
                    # 使用默认字体
                    font_cache[font_key] = default_font
                    print(f"使用默认字体")
                    return default_font

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
        """获取字体对象 - 保持向后兼容性，但强制使用宋体"""
        # 解析字体信息
        if isinstance(font_info, str):
            # 解析字体字符串，例如 "Arial,8" 或 "Arial,8,Bold"
            parts = font_info.split(',')
            font_name = parts[0] if len(parts) > 0 else 'Arial'
            font_size = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 9
            # 检查是否包含Bold
            if len(parts) > 2 and 'Bold' in parts[2]:
                should_bold = True
        else:
            # 如果是字典格式
            font_name = font_info.get('name', 'Arial')
            font_size = font_info.get('size', 9)
        
        # 强制使用宋体，不管原来指定的是什么字体
        return self._get_font_with_scaling(
            'SimSun',  # 强制使用宋体
            font_size,
            should_bold,
            True,  # 强制当作中文字体处理
            chinese_font_path,
            font_cache,
            default_font
        )
    
    def _save_certificate_page(self, image, data, page_num, total_pages):
        """保存凭证页面"""
        try:
            # 生成文件名
            order_code = data.get('sOrderCode', 'unknown')
            
            # 添加时间戳用于版本对比
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if total_pages == 1:
                # 单页情况，添加时间戳
                filename = f"enrollment_registration_certificate_{order_code}_{timestamp}.png"
            else:
                # 多页情况，添加页码和时间戳
                filename = f"enrollment_registration_certificate_{order_code}_page{page_num}of{total_pages}_{timestamp}.png"
            
            # 确保输出目录存在 - 使用项目根目录下的image文件夹
            # 从当前文件位置（utils/certificate_processors/）回到项目根目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            output_dir = os.path.join(project_root, "image")
            os.makedirs(output_dir, exist_ok=True)
            
            # 保存文件
            output_path = os.path.join(output_dir, filename)
            image.save(output_path, 'PNG', dpi=(300, 300))
            
            print(f"保存凭证页面到根目录: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"保存凭证页面时出错: {str(e)}")
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
            
            # 使用宋体字体
            font_to_use = self._get_font_with_scaling('SimSun', 8, False, has_chinese, 
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

    def _add_qr_code(self, image, draw, pixels_per_cm, center_offset_x, center_offset_y, font_cache, default_font):
        """添加二维码到左下角"""
        try:
            # 获取图像尺寸
            width, height = image.size
            
            # 二维码文件路径
            qr_code_path = os.path.join(self.base_dir, "properties", "qr_code.jpg")
            
            if os.path.exists(qr_code_path):
                # 加载二维码图片
                qr_image = Image.open(qr_code_path)
                
                # 设置二维码大小 - 与其他凭证保持一致，使用更大的尺寸
                qr_size = int(2.5 * pixels_per_cm)  # 2.5cm的二维码，与print_simulator一致
                qr_image = qr_image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
                
                # 计算二维码位置 - 固定在左下角，整体往上移动3行字的距离
                qr_margin = int(0.4 * pixels_per_cm)  # 0.4cm边距
                qr_x = qr_margin + center_offset_x
                # 二维码位置：整体往上移动约3行字高度（约1.2cm）
                qr_y = height - qr_size - int(1.7 * pixels_per_cm) + center_offset_y
                
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
                
                # 获取中文字体 - 使用稍大的字体
                service_font = self._get_font_with_scaling('SimSun', 10, False, True, 
                                                         self.chinese_font_path, font_cache, default_font)
                
                # 计算文字位置 - 在二维码正上方居中
                text_bbox = draw.textbbox((0, 0), service_text, font=service_font)
                text_width = text_bbox[2] - text_bbox[0]
                text_x = qr_x + (qr_size - text_width) / 2  # 居中对齐
                text_y = qr_y - int(0.6 * pixels_per_cm)  # 在二维码上方0.6cm
                
                # 绘制"【在线客服】"文字
                draw.text((text_x, text_y), service_text, fill='black', font=service_font)
                
                print(f"已添加二维码和在线客服文字到左下角位置: ({int(qr_x)}, {int(qr_y)})")
            else:
                print(f"警告: 二维码文件不存在: {qr_code_path}")
                # 如果没有二维码文件，绘制一个简单的方框作为占位符
                qr_size = int(2.5 * pixels_per_cm)
                qr_margin = int(0.4 * pixels_per_cm)
                qr_x = qr_margin + center_offset_x
                # 二维码位置：整体往上移动约3行字高度（约1.2cm）
                qr_y = height - qr_size - int(1.7 * pixels_per_cm) + center_offset_y
                
                # 绘制方框
                draw.rectangle([qr_x, qr_y, qr_x + qr_size, qr_y + qr_size], 
                             outline='black', width=2)
                
                # 添加"二维码"文字
                placeholder_font = self._get_font_with_scaling('SimSun', 10, False, True, 
                                                             self.chinese_font_path, font_cache, default_font)
                draw.text((qr_x + qr_size//4, qr_y + qr_size//2), "二维码", fill='black', font=placeholder_font)
                
        except Exception as e:
            print(f"添加二维码时出错: {str(e)}")

    def _calculate_pages(self, class_array):
        """计算分页逻辑 - 确保最后一页只有1-2条数据"""
        total_classes = len(class_array)
        pages = []
        
        if total_classes == 0:
            return pages
        
        if total_classes <= 2:
            # 1-2条数据：全部放在一页
            pages.append({
                'classes': class_array,
                'has_summary': True
            })
        elif total_classes == 3:
            # 正好3条数据：第一页2条，第二页1条+汇总
            pages.append({
                'classes': class_array[:2],
                'has_summary': False
            })
            pages.append({
                'classes': class_array[2:],
                'has_summary': True
            })
        elif total_classes == 4:
            # 4条数据：第一页3条，第二页1条+汇总
            pages.append({
                'classes': class_array[:3],
                'has_summary': False
            })
            pages.append({
                'classes': class_array[3:],
                'has_summary': True
            })
        elif total_classes == 5:
            # 5条数据：第一页3条，第二页2条+汇总
            pages.append({
                'classes': class_array[:3],
                'has_summary': False
            })
            pages.append({
                'classes': class_array[3:],
                'has_summary': True
            })
        else:
            # 6条及以上：确保最后一页只有1-2条数据
            remaining = total_classes
            start_index = 0
            
            while remaining > 0:
                if remaining <= 2:
                    # 最后一页：1-2条数据+汇总
                    pages.append({
                        'classes': class_array[start_index:start_index + remaining],
                        'has_summary': True
                    })
                    break
                elif remaining == 3:
                    # 剩余3条：当前页1条，最后一页2条+汇总
                    pages.append({
                        'classes': class_array[start_index:start_index + 1],
                        'has_summary': False
                    })
                    pages.append({
                        'classes': class_array[start_index + 1:start_index + 3],
                        'has_summary': True
                    })
                    break
                elif remaining == 4:
                    # 剩余4条：当前页2条，最后一页2条+汇总
                    pages.append({
                        'classes': class_array[start_index:start_index + 2],
                        'has_summary': False
                    })
                    pages.append({
                        'classes': class_array[start_index + 2:start_index + 4],
                        'has_summary': True
                    })
                    break
                else:
                    # 剩余5条及以上：当前页3条，继续下一页
                    pages.append({
                        'classes': class_array[start_index:start_index + 3],
                        'has_summary': False
                    })
                    start_index += 3
                    remaining -= 3
        
        print(f"分页计算结果：总共{total_classes}条数据，分为{len(pages)}页")
        for i, page in enumerate(pages, 1):
            print(f"  第{i}页：{len(page['classes'])}条数据，{'包含汇总' if page['has_summary'] else '不含汇总'}")
        
        return pages

    def _draw_page_number(self, draw, data, pixels_per_cm, center_offset_x, center_offset_y, chinese_font_path, font_cache, default_font):
        """绘制页码信息"""
        try:
            current_page = data.get('current_page', 1)
            total_pages = data.get('total_pages', 1)
            
            # 页码文本
            page_text = f"Page {current_page} of {total_pages}"
            
            # 字体设置
            font_size = 8
            font_to_use = self._get_font_with_scaling('SimSun', font_size, False, True, 
                                                    chinese_font_path, font_cache, default_font)
            
            # 页码位置（右下角）
            page_x = center_offset_x + 17 * pixels_per_cm  # 右对齐
            page_y = center_offset_y + 13.5 * pixels_per_cm  # 底部
            
            # 绘制页码
            draw.text((page_x, page_y), page_text, fill='black', font=font_to_use)
            print(f"绘制页码: {page_text} at ({page_x/pixels_per_cm:.2f}cm, {page_y/pixels_per_cm:.2f}cm)")
            
        except Exception as e:
            print(f"绘制页码时出错: {str(e)}")

    def _draw_fixed_page_footer(self, draw, data, footer_y, pixels_per_cm, center_offset_x, chinese_font_path, font_cache, default_font):
        """绘制固定位置的页脚信息 - 固定在页面底部"""
        try:
            # 页脚字体 - 改为宋体
            footer_font = self._get_font_with_scaling('SimSun', 8, False, True, 
                                                    chinese_font_path, font_cache, default_font)
            
            # 页脚信息布局 - 固定在页面底部
            base_footer_y = footer_y  # 直接使用传入的固定位置
            
            # 请妥善保存 - 左对齐
            draw.text((center_offset_x, base_footer_y), 
                     "请妥善保存", font=footer_font, fill='black')
            
            # 客户代办人签字 - 中左位置
            draw.text((center_offset_x + 4.2 * pixels_per_cm, base_footer_y), 
                     "客户代办人签字：", font=footer_font, fill='black')
            
            # 操作员 - 中右位置，与其他元素对齐
            draw.text((center_offset_x + 11.2 * pixels_per_cm, base_footer_y), 
                     "操作员：", font=footer_font, fill='black')
            draw.text((center_offset_x + 12.4 * pixels_per_cm, base_footer_y), 
                     str(data.get('sOperator', '')), font=footer_font, fill='black')
            
            # 日期 - 右对齐
            draw.text((center_offset_x + 15.0 * pixels_per_cm, base_footer_y), 
                     "日期：", font=footer_font, fill='black')
            draw.text((center_offset_x + 16.0 * pixels_per_cm, base_footer_y), 
                     str(data.get('dtCreate', '')), font=footer_font, fill='black')
            
            # 页码 - 右下角，英文格式，在页脚信息下方
            current_page = data.get('current_page', 1)
            total_pages = data.get('total_pages', 1)
            page_text = f"Page {current_page} of {total_pages}"
            page_y = base_footer_y + 0.6 * pixels_per_cm  # 在页脚信息下方0.6cm
            draw.text((center_offset_x + 16.4 * pixels_per_cm, page_y), 
                     page_text, font=footer_font, fill='black')
            
            print(f"绘制固定页脚信息(距底部{(16.0*pixels_per_cm-base_footer_y)/pixels_per_cm:.1f}cm): 基础Y={base_footer_y/pixels_per_cm:.2f}cm, 页码Y={page_y/pixels_per_cm:.2f}cm")
            
        except Exception as e:
            print(f"绘制固定页脚信息时出错: {str(e)}")

    def _draw_custom_page_footer(self, draw, data, pixels_per_cm, center_offset_x, center_offset_y, chinese_font_path, font_cache, default_font):
        """绘制自定义页脚信息 - 已废弃，使用_draw_fixed_page_footer替代"""
        # 这个方法已被_draw_fixed_page_footer替代，保留以防兼容性问题
        pass



def generate_enrollment_registration_certificate(data, currency_symbol="¥"):
    """生成报班凭证的便捷函数"""
    processor = EnrollmentRegistrationCertificateProcessor()
    return processor.generate_certificate(data, currency_symbol)

def create_mock_data(num_classes=4):
    """创建模拟数据用于测试 - 默认4个班级测试分页"""
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
        
        # 班级和卡片信息数组 (DataBand数据) - 根据参数动态生成
        "ClassAndCardArray": []
    }
    
    # 动态生成指定数量的班级数据
    base_classes = [
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
            "dFee": 1500.00,
            "dRegisterFee": 1400.00,
            "dClassVoucherFee": 100.00,
            "dShouldFee": 1400.00
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
            "dFee": 1600.00,
            "dRegisterFee": 1550.00,
            "dClassVoucherFee": 50.00,
            "dShouldFee": 1550.00
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
            "dFee": 1300.00,
            "dRegisterFee": 1250.00,
            "dClassVoucherFee": 50.00,
            "dShouldFee": 1250.00
        },
        {
            "sSeatNo": "D004",
            "sClassCode": "CHEM001", 
            "sClassName": "化学实验班",
            "dtBeginDate": "2024-04-01",
            "dtEndDate": "2024-06-01",
            "sRegisterTime": "2024-03-15 报名成功",
            "sPrintAddress": "北京市朝阳区XX路XX号401教室",
            "sPrintTime": "2024-04-01 10:00-13:00",
            "nTryLesson": "1",
            "dVoucherFee": 80.00,
            "dFee": 1800.00,
            "dRegisterFee": 1720.00,
            "dClassVoucherFee": 80.00,
            "dShouldFee": 1720.00
        },
        {
            "sSeatNo": "E005",
            "sClassCode": "LANG001", 
            "sClassName": "语文阅读班",
            "dtBeginDate": "2024-05-01",
            "dtEndDate": "2024-07-01",
            "sRegisterTime": "2024-04-10 报名成功",
            "sPrintAddress": "北京市朝阳区XX路XX号501教室",
            "sPrintTime": "2024-05-01 15:00-18:00",
            "nTryLesson": "0",
            "dVoucherFee": 60.00,
            "dFee": 1200.00,
            "dRegisterFee": 1140.00,
            "dClassVoucherFee": 60.00,
            "dShouldFee": 1140.00
        }
    ]
    
    # 根据需要的班级数量截取
    mock_data["ClassAndCardArray"] = base_classes[:num_classes]
    
    return mock_data

def test_enrollment_registration_certificate(num_classes=4):
    """测试报班凭证生成 - 支持分页"""
    try:
        print(f"开始测试报班凭证生成（{num_classes}个班级）...")
        
        # 创建模拟数据
        mock_data = create_mock_data(num_classes)
        
        # 生成凭证
        output_paths = generate_enrollment_registration_certificate(mock_data)
        
        print(f"测试成功！凭证已生成：{output_paths}")
        return output_paths
        
    except Exception as e:
        print(f"测试失败：{str(e)}")
        raise

def test_multiple_classes():
    """测试不同数量班级的报班凭证生成效果"""
    
    def create_test_data(class_count):
        """创建指定数量班级的测试数据"""
        base_data = {
            "sOrderCode": f"ORD2024010100{class_count}",
            "sBatchCode": "BATCH001",
            "Discounttype": 200.00,
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
            "Student": {
                "sStudentName": "李小明",
                "sStudentCode": "STU20240001",
                "sGender": "男",
                "sMobile": "13800138000"
            },
            "ClassAndCardArray": []
        }
        
        # 生成指定数量的班级数据
        subjects = ["数学基础班", "英语提高班", "物理基础班", "化学实验班", "语文阅读班"]
        codes = ["MATH001", "ENG001", "PHY001", "CHEM001", "LANG001"]
        
        for i in range(class_count):
            class_data = {
                "sSeatNo": f"{chr(65+i)}{str(i+1).zfill(3)}",  # A001, B002, etc.
                "sClassCode": codes[i % len(codes)],
                "sClassName": subjects[i % len(subjects)],
                "dtBeginDate": f"2024-{str((i%12)+1).zfill(2)}-15",
                "dtEndDate": f"2024-{str(((i%12)+3)%12+1).zfill(2)}-15",
                "sRegisterTime": f"2024-01-{str(10+i)} 报名成功",
                "sPrintAddress": f"北京市朝阳区XX路XX号{i+1}01教室",
                "sPrintTime": f"2024-{str((i%12)+1).zfill(2)}-15 {9+i}:00-{12+i}:00",
                "nTryLesson": str(i % 3),
                "dVoucherFee": 50.00 + i * 10,
                "dFee": 1500.00 + i * 100,
                "dRegisterFee": 1450.00 + i * 100,
                "dClassVoucherFee": 50.00 + i * 10,
                "dShouldFee": 1450.00 + i * 100
            }
            base_data["ClassAndCardArray"].append(class_data)
        
        return base_data
    
    try:
        print("开始测试不同数量班级的报班凭证生成...")
        
        for class_count in range(1, 6):  # 测试1-5条数据
            print(f"\n=== 测试 {class_count} 个班级 ===")
            
            # 创建测试数据
            test_data = create_test_data(class_count)
            
            # 生成凭证
            output_path = generate_enrollment_registration_certificate(test_data)
            
            print(f"✓ {class_count}个班级的凭证生成成功: {output_path}")
        
        print(f"\n所有测试完成！已生成1-5个班级的报班凭证，请检查布局效果。")
        
    except Exception as e:
        print(f"测试失败：{str(e)}")
        raise

if __name__ == "__main__":
    # 测试分页功能
    print("=== 测试分页功能 ===")
    
    # 测试不同数量的班级
    test_cases = [
        (1, "1个班级 - 单页"),
        (2, "2个班级 - 单页"), 
        (3, "3个班级 - 分页：第一页2个，第二页1个+汇总"),
        (4, "4个班级 - 分页：第一页3个，第二页1个+汇总"),
        (5, "5个班级 - 分页：第一页3个，第二页1个，第三页1个+汇总")
    ]
    
    for num_classes, description in test_cases:
        print(f"\n--- {description} ---")
        try:
            output_paths = test_enrollment_registration_certificate(num_classes)
            print(f"✓ 成功生成 {len(output_paths)} 页凭证")
        except Exception as e:
            print(f"✗ 测试失败: {e}")
    
    print("\n=== 分页测试完成 ===") 