#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
退班凭证专门处理器
使用退班凭证.mrt模板生成退班凭证
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

class WithdrawalCertificateProcessor:
    """退班凭证处理器"""
    
    def __init__(self):
        """初始化处理器"""
        # 获取项目根目录
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.template_dir = os.path.join(self.base_dir, "properties")
        self.output_dir = os.path.join(self.base_dir, "image")
        self.template_file = "退班凭证.mrt"
        
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
        """验证退班凭证的数据字段"""
        # 注意：这个验证方法在process_data之后调用，数据已经被预处理
        # 所以此时应该有必要的字段了
        
        # 验证学生信息（已在process_data中补充）
        if 'Student' not in data:
            print("警告：缺少学生信息，将使用默认值")
        
        # 验证班级和卡片信息（已在process_data中补充）
        if 'ClassAndCardArray' not in data:
            print("警告：缺少班级信息，将使用空数组")
        
        return True
    
    def process_data(self, data):
        """处理退班凭证的特殊数据逻辑"""
        processed_data = data.copy()
        
        # 处理主订单信息
        # 如果没有订单号，尝试从其他字段获取或生成一个
        if not processed_data.get('sOrderCode'):
            # 尝试从batchCode或其他字段获取
            order_code = processed_data.get('sBatchCode') or processed_data.get('batchCode')
            if not order_code:
                # 生成一个基于时间戳的订单号
                from datetime import datetime
                order_code = f"WD{datetime.now().strftime('%Y%m%d%H%M%S')}"
            processed_data['sOrderCode'] = order_code
        
        processed_data.setdefault('sBatchCode', processed_data.get('sOrderCode', ''))
        processed_data.setdefault('sSchoolName', '新东方学校')
        processed_data.setdefault('sTelePhone', '400-000-0000')
        processed_data.setdefault('Discounttype', 0)
        processed_data.setdefault('BizType', '退班')
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
        else:
            # 如果没有学生信息，创建一个空的学生信息结构
            processed_data['Student'] = {
                'sStudentName': '',
                'sStudentCode': '',
                'sGender': '不详',
                'sMobile': ''
            }
        
        # 处理班级和卡片信息数组
        if 'ClassAndCardArray' in processed_data:
            for item in processed_data['ClassAndCardArray']:
                # 退班凭证特有字段
                item.setdefault('sOldClassCode', item.get('sClassCode', ''))  # 退费商品编号
                item.setdefault('sOldClassName', item.get('sClassName', ''))  # 退费商品名称
                item.setdefault('dOldClassFee', 0.0)  # 原商品标准金额
                item.setdefault('dOldClassVoucherFee', 0.0)  # 原商品优惠金额
                item.setdefault('dGivenFee', 0.0)  # 原商品支付金额
                item.setdefault('dShouldDeductFee', 0.0)  # 应扣金额
                item.setdefault('dShouldReturnFee', 0.0)  # 应退金额
                
                # 通用字段
                item.setdefault('sSeatNo', '')
                item.setdefault('sClassCode', '')
                item.setdefault('sClassName', '')
                item.setdefault('dtBeginDate', '')
                item.setdefault('dtEndDate', '')
                item.setdefault('sRegisterTime', get_beijing_time_str())
                item.setdefault('sPrintAddress', '')
                item.setdefault('sPrintTime', get_beijing_time_str())
                
                # 处理费用字段
                for fee_field in ['dOldClassFee', 'dOldClassVoucherFee', 'dGivenFee', 
                                'dShouldDeductFee', 'dShouldReturnFee']:
                    if fee_field in item:
                        try:
                            item[fee_field] = float(item[fee_field])
                        except (ValueError, TypeError):
                            item[fee_field] = 0.0
        else:
            # 如果没有班级信息，创建一个空的班级信息数组
            processed_data['ClassAndCardArray'] = []
        
        # 处理图像数据字段
        processed_data.setdefault('RWMImage', '')
        
        return processed_data
    
    def parse_template(self):
        """解析退班凭证模板"""
        template_path = os.path.join(self.template_dir, self.template_file)
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"模板文件不存在: {template_path}")
        
        from utils.certificate_processors.print_simulator import MrtParser
        return MrtParser(template_path)
    
    def generate_certificate(self, data, currency_symbol="¥"):
        """生成退班凭证 - 支持分页"""
        try:
            print(f"开始处理退班凭证...")
            
            # 处理数据
            processed_data = self.process_data(data)
            
            # 验证数据
            self.validate_data(processed_data)
            
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
            
            print(f"退班凭证生成成功，共{len(pages)}页: {output_paths}")
            return output_paths
            
        except Exception as e:
            print(f"生成退班凭证失败: {str(e)}")
            raise
    
    def _create_certificate_image(self, data, mrt_parser, currency_symbol):
        """创建凭证图像 - 支持分页，使用固定纸张大小"""
        try:
            # 重置已绘制组件缓存（每页重新开始）
            self._drawn_components = set()
            
            # 使用与print_simulator相同的像素转换比例
            pixels_per_cm = PIXELS_PER_CM
            
            # 固定页面尺寸 - 横向A5尺寸
            width = int(21.0 * pixels_per_cm)  # A5横向宽度
            height = int(16.0 * pixels_per_cm)  # 增加高度到16cm
            
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
            
            # 首先绘制DataBand内容（只绘制一次）
            databand_drawn = False
            
            # 处理模板组件
            if hasattr(mrt_parser, 'components') and mrt_parser.components:
                for component in mrt_parser.components:
                    component_id = component.get('id', id(component))
                    
                    # 跳过已绘制的组件
                    if component_id in self._drawn_components:
                        continue
                    
                    component_type = component.get('type', '')
                    text = component.get('text', '')
                    
                    # 绘制DataBand内容（班级列表）- 只绘制一次
                    if not databand_drawn:
                        self._draw_databand_content(draw, data, pixels_per_cm, center_offset_x, center_offset_y, font_cache, self.chinese_font_path, default_font)
                        databand_drawn = True
                    
                    # 处理文本组件
                    if component_type == 'Text':
                        try:
                            # 解析位置信息
                            rect_str = component.get('rect', '0,0,1,1')
                            rect_parts = rect_str.split(',')
                            
                            if len(rect_parts) >= 4:
                                x_pos = float(rect_parts[0]) * pixels_per_cm + center_offset_x
                                y_pos = float(rect_parts[1]) * pixels_per_cm + center_offset_y
                                
                                # === 1. 过滤原模板的DataBand区域组件 ===
                                # 过滤DataBand动态字段（位置检测）
                                if self._is_in_databand_region(y_pos, pixels_per_cm):
                                    print(f"过滤DataBand动态字段: {text} at ({x_pos}, {y_pos})")
                                    continue
                                
                                # 过滤所有DataBand相关的标签组件（无论位置）
                                databand_labels = [
                                    "退费商品编号：", "退费听课证号：", "退费商品名称：", 
                                    "原商品标准金额：", "原商品优惠金额：", "原商品支付金额：",
                                    "应扣金额：", "应退金额："
                                ]
                                
                                if text.strip() in databand_labels:
                                    print(f"过滤DataBand标签: {text} at ({x_pos}, {y_pos})")
                                    continue
                                
                                # 绘制非DataBand文本组件
                                self._draw_text_component(component, data, draw, pixels_per_cm, 
                                                        center_offset_x, center_offset_y, 
                                                        self.chinese_font_path, font_cache, default_font)
                        
                        except Exception as e:
                            print(f"处理文本组件时出错: {str(e)}")
                            continue
                    
                    # 处理其他组件类型
                    elif component_type == 'Image':
                        try:
                            self._draw_image_component(component, image, pixels_per_cm, center_offset_x, center_offset_y)
                        except Exception as e:
                            print(f"处理图像组件时出错: {str(e)}")
                            continue
                    
                    elif component_type == 'HorizontalLinePrimitive':
                        try:
                            self._draw_line_component(component, draw, pixels_per_cm, center_offset_x, center_offset_y)
                        except Exception as e:
                            print(f"处理线条组件时出错: {str(e)}")
                            continue
                    
                    # 标记组件已绘制
                    self._drawn_components.add(component_id)
            
            return image
            
        except Exception as e:
            print(f"创建退班凭证图像时出错: {str(e)}")
            raise
    
    def _is_in_databand_region(self, y_pos, pixels_per_cm):
        """检查Y坐标是否在DataBand区域内"""
        # DataBand区域大约在3cm到7cm之间
        databand_start = 3.0 * pixels_per_cm
        databand_end = 7.0 * pixels_per_cm
        return databand_start <= y_pos <= databand_end
    
    def _draw_databand_content(self, draw, data, pixels_per_cm, center_offset_x, center_offset_y, font_cache, chinese_font_path, default_font):
        """绘制DataBand内容 - 退班凭证的特殊布局"""
        try:
            print("开始绘制退班凭证DataBand内容")
            
            class_array = data.get('ClassAndCardArray', [])
            if not class_array:
                print("没有班级数据，跳过DataBand绘制")
                return
            
            # 字体高度（厘米）
            font_height_cm = 0.4
            
            # DataBand起始位置
            databand_start_y = 3.2 * pixels_per_cm + center_offset_y
            
            # DataBand的实际内容高度（3行数据）
            actual_content_height = font_height_cm * 3 * pixels_per_cm
            
            # 每个DataBand之间的间距
            databand_spacing = font_height_cm * 0.8 * pixels_per_cm
            
            # 总的DataBand高度
            total_databand_height = actual_content_height + databand_spacing
            
            # 列宽定义（根据退班凭证模板）
            col_widths = {
                'code_label': 2.2,     # 退费商品编号：
                'code_value': 7.6,     # 商品编号值
                'fee1_label': 2.2,     # 原商品标准金额：
                'fee1_value': 2.4,     # 金额值
                'fee2_label': 1.6,     # 应扣金额：
                'fee2_value': 2.0,     # 金额值
                'name_label': 2.2,     # 退费商品名称：
                'name_value': 7.6,     # 商品名称值
                'fee3_label': 2.2,     # 原商品优惠金额：
                'fee3_value': 2.4,     # 金额值
                'fee4_label': 1.6,     # 应退金额：
                'fee4_value': 2.0      # 金额值
            }
            
            # 列位置定义（X坐标，厘米）
            col_positions = {
                'col1': 0.2,   # 第一列起始位置
                'col2': 2.4,   # 第二列起始位置（商品编号/名称值）
                'col3': 10.0,  # 第三列起始位置（费用标签）
                'col4': 12.4,  # 第四列起始位置（费用值）
                'col5': 14.8,  # 第五列起始位置（应扣/应退标签）
                'col6': 16.4   # 第六列起始位置（应扣/应退值）
            }
            
            # 行高定义
            row_height = font_height_cm * pixels_per_cm
            
            # 绘制每个班级的DataBand
            for i, class_item in enumerate(class_array):
                print(f"绘制第{i+1}个班级的DataBand")
                
                # 当前DataBand的起始位置
                current_y = databand_start_y + (i * total_databand_height)
                
                # 绘制3行数据
                self._draw_withdrawal_three_row_layout(class_item, draw, current_y, pixels_per_cm, 
                                                     center_offset_x, col_positions, font_cache, 
                                                     chinese_font_path, default_font)
            
            # 在所有DataBand下方绘制横线
            last_databand_start = databand_start_y + (len(class_array) - 1) * total_databand_height
            last_databand_end = last_databand_start + actual_content_height
            
            # 绘制DataBand底部横线
            line_start_x = 0.2 * pixels_per_cm + center_offset_x
            line_end_x = 18.6 * pixels_per_cm + center_offset_x
            databand_bottom_line_y = last_databand_end + 0.1 * pixels_per_cm
            draw.line([(line_start_x, databand_bottom_line_y), (line_end_x, databand_bottom_line_y)], fill='black', width=2)
            print(f"绘制DataBand底部横线: y={databand_bottom_line_y/pixels_per_cm:.2f}cm")
            
            # 页脚起始位置
            footer_start_y = databand_bottom_line_y + 0.2 * pixels_per_cm
            
            # 绘制页脚汇总信息
            self._draw_footer_summary(data, draw, footer_start_y, pixels_per_cm, 
                                    center_offset_x, chinese_font_path, font_cache, default_font)
            
            print("退班凭证DataBand内容绘制完成")
            
        except Exception as e:
            print(f"绘制退班凭证DataBand内容时出错: {str(e)}")
    
    def _draw_withdrawal_three_row_layout(self, class_item, draw, base_y, pixels_per_cm, 
                                        center_offset_x, col_positions, font_cache, 
                                        chinese_font_path, default_font):
        """绘制退班凭证的三行布局"""
        try:
            # 字体大小
            font_size = 8
            font_to_use = self._get_font_with_scaling('Arial', font_size, False, True, 
                                                    chinese_font_path, font_cache, default_font)
            
            row_height = 0.4 * pixels_per_cm
            
            # 第一行：退费商品编号 + 原商品标准金额 + 应扣金额
            y1 = base_y + 0.2 * pixels_per_cm
            
            # 退费商品编号标签
            draw.text((col_positions['col1'] * pixels_per_cm + center_offset_x, y1), 
                     "退费商品编号：", fill='black', font=font_to_use)
            
            # 退费商品编号值
            code_value = str(class_item.get('sOldClassCode', ''))
            draw.text((col_positions['col2'] * pixels_per_cm + center_offset_x, y1), 
                     code_value, fill='black', font=font_to_use)
            
            # 原商品标准金额标签
            draw.text((col_positions['col3'] * pixels_per_cm + center_offset_x, y1), 
                     "原商品标准金额：", fill='black', font=font_to_use)
            
            # 原商品标准金额值
            fee1_value = f"¥{class_item.get('dOldClassFee', 0.0):.2f}"
            draw.text((col_positions['col4'] * pixels_per_cm + center_offset_x, y1), 
                     fee1_value, fill='black', font=font_to_use)
            
            # 应扣金额标签
            draw.text((col_positions['col5'] * pixels_per_cm + center_offset_x, y1), 
                     "应扣金额：", fill='black', font=font_to_use)
            
            # 应扣金额值
            deduct_value = f"¥{class_item.get('dShouldDeductFee', 0.0):.2f}"
            draw.text((col_positions['col6'] * pixels_per_cm + center_offset_x, y1), 
                     deduct_value, fill='black', font=font_to_use)
            
            # 第二行：退费听课证号 + 原商品优惠金额 + 应退金额
            y2 = base_y + 0.6 * pixels_per_cm
            
            # 退费听课证号标签
            draw.text((col_positions['col1'] * pixels_per_cm + center_offset_x, y2), 
                     "退费听课证号：", fill='black', font=font_to_use)
            
            # 退费听课证号值（使用sOldClassCode或其他字段）
            ticket_value = str(class_item.get('sOldClassCode', ''))
            draw.text((col_positions['col2'] * pixels_per_cm + center_offset_x, y2), 
                     ticket_value, fill='black', font=font_to_use)
            
            # 原商品优惠金额标签
            draw.text((col_positions['col3'] * pixels_per_cm + center_offset_x, y2), 
                     "原商品优惠金额：", fill='black', font=font_to_use)
            
            # 原商品优惠金额值
            voucher_value = f"¥{class_item.get('dOldClassVoucherFee', 0.0):.2f}"
            draw.text((col_positions['col4'] * pixels_per_cm + center_offset_x, y2), 
                     voucher_value, fill='black', font=font_to_use)
            
            # 应退金额标签
            draw.text((col_positions['col5'] * pixels_per_cm + center_offset_x, y2), 
                     "应退金额：", fill='black', font=font_to_use)
            
            # 应退金额值
            return_value = f"¥{class_item.get('dShouldReturnFee', 0.0):.2f}"
            draw.text((col_positions['col6'] * pixels_per_cm + center_offset_x, y2), 
                     return_value, fill='black', font=font_to_use)
            
            # 第三行：退费商品名称 + 原商品支付金额
            y3 = base_y + 1.0 * pixels_per_cm
            
            # 退费商品名称标签
            draw.text((col_positions['col1'] * pixels_per_cm + center_offset_x, y3), 
                     "退费商品名称：", fill='black', font=font_to_use)
            
            # 退费商品名称值
            name_value = str(class_item.get('sOldClassName', ''))
            draw.text((col_positions['col2'] * pixels_per_cm + center_offset_x, y3), 
                     name_value, fill='black', font=font_to_use)
            
            # 原商品支付金额标签
            draw.text((col_positions['col3'] * pixels_per_cm + center_offset_x, y3), 
                     "原商品支付金额：", fill='black', font=font_to_use)
            
            # 原商品支付金额值
            paid_value = f"¥{class_item.get('dGivenFee', 0.0):.2f}"
            draw.text((col_positions['col4'] * pixels_per_cm + center_offset_x, y3), 
                     paid_value, fill='black', font=font_to_use)
            
            print(f"  - 退费商品: {name_value}")
            print(f"  - 商品编号: {code_value}")
            print(f"  - 应退金额: {return_value}")
            
        except Exception as e:
            print(f"绘制退班凭证三行布局时出错: {str(e)}")
    
    def _draw_footer_summary(self, data, draw, footer_y, pixels_per_cm, 
                           center_offset_x, chinese_font_path, font_cache, default_font):
        """绘制页脚汇总信息"""
        try:
            # 计算总的退费金额
            class_array = data.get('ClassAndCardArray', [])
            total_return_fee = sum(float(item.get('dShouldReturnFee', 0.0)) for item in class_array)
            total_deduct_fee = sum(float(item.get('dShouldDeductFee', 0.0)) for item in class_array)
            
            # 字体设置
            font_size = 10
            font_to_use = self._get_font_with_scaling('Arial', font_size, True, True, 
                                                    chinese_font_path, font_cache, default_font)
            
            # 绘制汇总信息
            summary_text = f"合计 - 应退金额：¥{total_return_fee:.2f}  应扣金额：¥{total_deduct_fee:.2f}"
            draw.text((1.0 * pixels_per_cm + center_offset_x, footer_y), 
                     summary_text, fill='black', font=font_to_use)
            
            print(f"页脚汇总 - 总应退金额: ¥{total_return_fee:.2f}, 总应扣金额: ¥{total_deduct_fee:.2f}")
            
        except Exception as e:
            print(f"绘制页脚汇总时出错: {str(e)}")
    
    def _get_font_with_scaling(self, font_name, font_size, should_bold, has_chinese, 
                             chinese_font_path, font_cache, default_font):
        """获取缩放后的字体"""
        try:
            cache_key = f"{font_name}_{font_size}_{should_bold}_{has_chinese}"
            
            if cache_key in font_cache:
                return font_cache[cache_key]
            
            font_to_use = default_font
            
            if has_chinese and chinese_font_path:
                try:
                    font_to_use = ImageFont.truetype(chinese_font_path, font_size)
                except Exception as e:
                    print(f"加载中文字体失败: {str(e)}")
                    font_to_use = default_font
            else:
                try:
                    font_to_use = ImageFont.truetype("arial.ttf", font_size)
                except Exception:
                    font_to_use = default_font
            
            font_cache[cache_key] = font_to_use
            return font_to_use
            
        except Exception as e:
            print(f"获取字体时出错: {str(e)}")
            return default_font
    
    def _draw_text_component(self, component, data, draw, pixels_per_cm, 
                           center_offset_x, center_offset_y, chinese_font_path, 
                           font_cache, default_font):
        """绘制文本组件"""
        try:
            text = component.get('text', '')
            rect_str = component.get('rect', '0,0,1,1')
            
            # 解析位置
            rect_parts = rect_str.split(',')
            if len(rect_parts) < 4:
                return
            
            x = float(rect_parts[0]) * pixels_per_cm + center_offset_x
            y = float(rect_parts[1]) * pixels_per_cm + center_offset_y
            
            # 处理文本内容
            if text and '{' in text and '}' in text:
                # 替换数据字段
                processed_text = self._replace_data_fields(text, data)
            else:
                processed_text = text
            
            # 检测是否包含中文
            has_chinese = bool(re.search(r'[\u4e00-\u9fff]', processed_text))
            
            # 获取字体
            font_size = 8  # 默认字体大小
            font_to_use = self._get_font_with_scaling('Arial', font_size, False, has_chinese, 
                                                    chinese_font_path, font_cache, default_font)
            
            # 绘制文本
            draw.text((x, y), processed_text, fill='black', font=font_to_use)
            
        except Exception as e:
            print(f"绘制文本组件时出错: {str(e)}")
    
    def _replace_data_fields(self, text, data):
        """替换文本中的数据字段"""
        try:
            # 定义字段映射
            field_mapping = {
                '{ArrayList.sOrderCode}': data.get('sOrderCode', ''),
                '{ArrayList.sSchoolName}': data.get('sSchoolName', ''),
                '{ArrayList.sTelePhone}': data.get('sTelePhone', ''),
                '{ArrayList.sOperator}': data.get('sOperator', ''),
                '{ArrayList.dtCreate}': data.get('dtCreate', ''),
                '{ArrayList.Student.sStudentName}': data.get('Student', {}).get('sStudentName', ''),
                '{ArrayList.Student.sStudentCode}': data.get('Student', {}).get('sStudentCode', ''),
                '{ArrayList.Student.sGender}': data.get('Student', {}).get('sGender', ''),
                '{ArrayList.Student.sMobile}': data.get('Student', {}).get('sMobile', ''),
                '{ArrayList.dShouldFee}': f"¥{data.get('dShouldFee', 0.0):.2f}",
                '{ArrayList.dFee}': f"¥{data.get('dFee', 0.0):.2f}",
                '{ArrayList.dReturnFee}': f"¥{data.get('dReturnFee', 0.0):.2f}",
            }
            
            # 替换所有字段
            result = text
            for field, value in field_mapping.items():
                result = result.replace(field, str(value))
            
            return result
            
        except Exception as e:
            print(f"替换数据字段时出错: {str(e)}")
            return text
    
    def _draw_image_component(self, component, main_image, pixels_per_cm, center_offset_x, center_offset_y):
        """绘制图像组件"""
        try:
            # 图像组件处理逻辑
            pass
        except Exception as e:
            print(f"绘制图像组件时出错: {str(e)}")
    
    def _draw_line_component(self, component, draw, pixels_per_cm, center_offset_x, center_offset_y):
        """绘制线条组件"""
        try:
            rect_str = component.get('rect', '0,0,1,0.1')
            rect_parts = rect_str.split(',')
            
            if len(rect_parts) >= 4:
                x1 = float(rect_parts[0]) * pixels_per_cm + center_offset_x
                y1 = float(rect_parts[1]) * pixels_per_cm + center_offset_y
                width = float(rect_parts[2]) * pixels_per_cm
                
                x2 = x1 + width
                y2 = y1
                
                draw.line([(x1, y1), (x2, y2)], fill='black', width=1)
                
        except Exception as e:
            print(f"绘制线条组件时出错: {str(e)}")
    
    def _calculate_pages(self, class_array):
        """计算分页"""
        if not class_array:
            return [{'classes': [], 'total_fee': 0.0, 'refund_fee': 0.0}]
        
        # 退班凭证每页最多显示3个班级
        items_per_page = 3
        pages = []
        
        for i in range(0, len(class_array), items_per_page):
            page_classes = class_array[i:i + items_per_page]
            
            # 计算本页的费用汇总
            total_deduct = sum(float(item.get('dShouldDeductFee', 0.0)) for item in page_classes)
            total_return = sum(float(item.get('dShouldReturnFee', 0.0)) for item in page_classes)
            
            pages.append({
                'classes': page_classes,
                'total_deduct_fee': total_deduct,
                'total_return_fee': total_return
            })
        
        return pages
    
    def _save_certificate_page(self, image, data, page_num, total_pages):
        """保存凭证页面"""
        try:
            timestamp = get_beijing_timestamp()
            student_name = data.get('Student', {}).get('sStudentName', '学员')
            order_code = data.get('sOrderCode', 'ORDER')
            
            if total_pages > 1:
                filename = f"退班凭证_{student_name}_{order_code}_第{page_num}页_{timestamp}.png"
            else:
                filename = f"退班凭证_{student_name}_{order_code}_{timestamp}.png"
            
            output_path = os.path.join(self.output_dir, filename)
            image.save(output_path, 'PNG', optimize=True, dpi=(200, 200))
            
            print(f"退班凭证第{page_num}页已保存: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"保存凭证页面时出错: {str(e)}")
            return None


def generate_withdrawal_certificate(data, currency_symbol="¥"):
    """生成退班凭证的便捷函数"""
    processor = WithdrawalCertificateProcessor()
    return processor.generate_certificate(data, currency_symbol)


def create_mock_withdrawal_data(num_classes=2):
    """创建退班凭证的模拟数据"""
    from datetime import datetime, timedelta
    
    # 基础数据
    mock_data = {
        "sOrderCode": f"WD{datetime.now().strftime('%Y%m%d')}001",
        "sBatchCode": f"BATCH{datetime.now().strftime('%Y%m%d')}",
        "sSchoolName": "北京新东方学校",
        "sTelePhone": "400-175-9898",
        "sOperator": "张财务",
        "dtCreate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "BizType": "退班",
        "sChannel": "直营",
        "sPayType": "现金",
        "feedBackTitle": "客服热线：400-175-9898",
        "feedBackImg": "",
        "microServiceTitle": "微信公众号：新东方",
        "microServiceImg": "",
        "Student": {
            "sStudentName": "李小明",
            "sStudentCode": "BJ2024001234",
            "sGender": "男",
            "sMobile": "138****5678"
        },
        "ClassAndCardArray": []
    }
    
    # 班级数据模板
    class_templates = [
        {
            "sOldClassCode": "CLS001",
            "sOldClassName": "数学基础班（上）",
            "dOldClassFee": 1200.0,
            "dOldClassVoucherFee": 150.0,
            "dGivenFee": 1050.0,
            "dShouldDeductFee": 200.0,
            "dShouldReturnFee": 850.0
        },
        {
            "sOldClassCode": "CLS002",
            "sOldClassName": "英语提高班（中）",
            "dOldClassFee": 1500.0,
            "dOldClassVoucherFee": 200.0,
            "dGivenFee": 1300.0,
            "dShouldDeductFee": 300.0,
            "dShouldReturnFee": 1000.0
        },
        {
            "sOldClassCode": "CLS003",
            "sOldClassName": "物理强化班（下）",
            "dOldClassFee": 1800.0,
            "dOldClassVoucherFee": 250.0,
            "dGivenFee": 1550.0,
            "dShouldDeductFee": 400.0,
            "dShouldReturnFee": 1150.0
        },
        {
            "sOldClassCode": "CLS004",
            "sOldClassName": "化学实验班（全）",
            "dOldClassFee": 2000.0,
            "dOldClassVoucherFee": 300.0,
            "dGivenFee": 1700.0,
            "dShouldDeductFee": 450.0,
            "dShouldReturnFee": 1250.0
        },
        {
            "sOldClassCode": "CLS005",
            "sOldClassName": "语文阅读理解专项班",
            "dOldClassFee": 1100.0,
            "dOldClassVoucherFee": 120.0,
            "dGivenFee": 980.0,
            "dShouldDeductFee": 180.0,
            "dShouldReturnFee": 800.0
        }
    ]
    
    # 根据指定数量生成班级数据
    for i in range(min(num_classes, len(class_templates))):
        class_data = class_templates[i].copy()
        # 添加一些基本字段
        class_data.update({
            "sSeatNo": f"A{i+1:02d}",
            "sClassCode": class_data["sOldClassCode"],
            "sClassName": class_data["sOldClassName"],
            "dtBeginDate": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            "dtEndDate": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
            "sRegisterTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sPrintAddress": "北京海淀区",
            "sPrintTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        mock_data["ClassAndCardArray"].append(class_data)
    
    # 计算总金额
    total_given_fee = sum(item["dGivenFee"] for item in mock_data["ClassAndCardArray"])
    total_deduct_fee = sum(item["dShouldDeductFee"] for item in mock_data["ClassAndCardArray"])
    total_return_fee = sum(item["dShouldReturnFee"] for item in mock_data["ClassAndCardArray"])
    
    mock_data.update({
        "dShouldFee": total_given_fee,
        "dFee": total_given_fee - total_deduct_fee,
        "dReturnFee": total_return_fee
    })
    
    return mock_data

def test_withdrawal_certificate_generation(num_classes=2):
    """测试退班凭证生成功能"""
    print(f"开始测试退班凭证生成（{num_classes}个班级）...")
    
    try:
        # 创建测试数据
        test_data = create_mock_withdrawal_data(num_classes)
        
        # 生成退班凭证
        output_paths = generate_withdrawal_certificate(test_data)
        
        print(f"✅ 退班凭证生成成功!")
        print(f"   - 学员姓名: {test_data['Student']['sStudentName']}")
        print(f"   - 订单号: {test_data['sOrderCode']}")
        print(f"   - 班级数量: {len(test_data['ClassAndCardArray'])}")
        print(f"   - 总退费金额: ¥{test_data['dReturnFee']:.2f}")
        print(f"   - 生成页数: {len(output_paths)}")
        
        for i, path in enumerate(output_paths, 1):
            print(f"   - 第{i}页: {path}")
        
        return output_paths
        
    except Exception as e:
        print(f"❌ 退班凭证生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_multiple_withdrawal_classes():
    """测试不同数量班级的退班凭证生成效果"""
    print("开始测试不同数量班级的退班凭证生成...")
    
    # 测试1-5个班级
    for class_count in range(1, 6):
        print(f"\n{'='*50}")
        print(f"测试 {class_count} 个班级的退班凭证")
        print(f"{'='*50}")
        
        try:
            output_paths = test_withdrawal_certificate_generation(class_count)
            if output_paths:
                print(f"✅ {class_count}个班级测试成功")
            else:
                print(f"❌ {class_count}个班级测试失败")
        except Exception as e:
            print(f"❌ {class_count}个班级测试异常: {str(e)}")
    
    print(f"\n所有测试完成！已生成1-5个班级的退班凭证，请检查布局效果。")


if __name__ == "__main__":
    # 显示退班凭证处理器信息
    print("="*60)
    print("退班凭证处理器测试")
    print("="*60)
    
    # 测试单个退班凭证生成
    print("\n1. 测试基本退班凭证生成（2个班级）")
    test_withdrawal_certificate_generation(2)
    
    # 测试多种班级数量
    print("\n2. 测试不同数量班级的退班凭证生成")
    test_multiple_withdrawal_classes() 