#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys
import asyncio
import base64
import xml.etree.ElementTree as ET
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
from ..time_utils import get_beijing_time_str, get_beijing_timestamp

# 模板映射表 - 根据BizType映射到对应的.mrt文件
TEMPLATE_MAPPING = {
    1: "报班凭证.mrt",
    2: "转班凭证.mrt",
    3: "退班凭证.mrt",
    4: "调课凭证.mrt",
    5: "班级凭证.mrt",
    6: "学员账户充值提现凭证.mrt",
    7: "优惠重算凭证.mrt",
    8: "退费凭证.mrt",
    9: "高端报班凭证.mrt",
    10: "高端报名凭证.mrt",
    11: "高端退费凭证.mrt",
    }

# 凭证类型配置 - 不同类型的凭证可能需要不同的处理方式
CERTIFICATE_TYPES = {
    "报班类": {
        "biz_types": [1, 9, 10],  # 报班凭证、高端报班凭证、高端报名凭证
        "templates": ["报班凭证.mrt", "高端报班凭证.mrt", "高端报名凭证.mrt"],
        "processor": "enrollment_processor"
    },
    "退费类": {
        "biz_types": [3, 8, 11],  # 退班凭证、退费凭证、高端退费凭证
        "templates": ["退班凭证.mrt", "退费凭证.mrt", "高端退费凭证.mrt"],
        "processor": "refund_processor"
    },
    "调整类": {
        "biz_types": [2, 4, 7],  # 转班凭证、调课凭证、优惠重算凭证
        "templates": ["转班凭证.mrt", "调课凭证.mrt", "优惠重算凭证.mrt"],
        "processor": "adjustment_processor"
    },
    "财务类": {
        "biz_types": [6],  # 学员账户充值提现凭证
        "templates": ["学员账户充值提现凭证.mrt"],
        "processor": "financial_processor"
    },
    "管理类": {
        "biz_types": [5],  # 班级凭证
        "templates": ["班级凭证.mrt"],
        "processor": "management_processor"
    }
}

# 根据凭证名称映射到BizType（用于直接指定凭证类型的情况）
TEMPLATE_NAME_TO_BIZTYPE = {
    "报班凭证.mrt": 1,
    "转班凭证.mrt": 2,
    "退班凭证.mrt": 3,
    "调课凭证.mrt": 4,
    "班级凭证.mrt": 5,
    "学员账户充值提现凭证.mrt": 6,
    "优惠重算凭证.mrt": 7,
    "退费凭证.mrt": 8,
    "高端报班凭证.mrt": 9,
    "高端报名凭证.mrt": 10,
    "高端退费凭证.mrt": 11
}

class MrtParser:
    """解析.mrt文件的类"""

    def __init__(self, mrt_file_path):
        """初始化MRT解析器"""
        self.mrt_file_path = mrt_file_path
        self.components = []
        self.data_fields = {}
        self.tree = None
        self.root = None
        self.page_settings = {
            'width': 800,  # 默认宽度
            'height': 1100,  # 默认高度
            'margin_left': 10,
            'margin_right': 10,
            'margin_top': 10,
            'margin_bottom': 10,
        }
        self.parse()

    def parse(self):
        """解析.mrt文件"""
        try:
            # 解析XML
            with open(self.mrt_file_path, 'r', encoding='utf-8') as file:
                xml_content = file.read()

            # 尝试解析XML内容
            try:
                self.tree = ET.fromstring(xml_content)
                # 提取数据字段信息和组件信息
                self._extract_data_fields()
                self._extract_components()
                self._extract_page_settings(xml_content)
                print(f"XML解析成功，共提取 {len(self.components)} 个组件")
                return True
            except Exception as e:
                print(f"XML解析错误: {str(e)}")
                # 如果解析失败，使用备用方法提取关键信息
                self._extract_components_manually(xml_content)
                self._extract_page_settings(xml_content)
                print(f"手动解析完成，共提取 {len(self.components)} 个组件")
                return True

        except Exception as e:
            print(f"解析.mrt文件出错: {str(e)}")
            # 即使解析失败，仍然返回一些基本组件，这样至少可以显示一些内容
            self._create_default_components()
            return False

    def _extract_data_fields(self):
        """提取数据字段信息"""
        try:
            # 尝试查找所有列定义
            columns = self.tree.findall(".//Columns/value")
            for column in columns:
                if column is not None and column.text:
                    parts = column.text.split(',')
                    if len(parts) == 2:
                        field_name = parts[0].strip()
                        field_type = parts[1].strip()
                        self.data_fields[field_name] = field_type
        except Exception as e:
            print(f"提取数据字段时出错: {str(e)}")

    def _extract_components(self):
        """提取组件信息"""
        try:
            # 尝试查找所有组件
            components = self.tree.findall(".//Components//*")

            for component in components:
                component_type = component.get('type')

                # 文本组件
                if component_type == 'Text':
                    font_info = self._extract_font_info(component)
                    alignment = self._find_element_text(component, 'HorAlignment') or 'Left'
                    comp_info = {
                        'type': 'Text',
                        'name': component.get('Name', ''),
                        'rect': self._find_element_text(component, 'ClientRectangle'),
                        'text': self._find_element_text(component, 'Text'),
                        'data_type': self._find_element_text(component, 'Type'),
                        'font': font_info,  # 添加字体信息
                        'alignment': alignment  # 添加对齐信息
                    }
                    self.components.append(comp_info)

                # 图像组件
                elif component_type == 'Image':
                    comp_info = {
                        'type': 'Image',
                        'name': component.get('Name', ''),
                        'rect': self._find_element_text(component, 'ClientRectangle'),
                        'image_data': self._find_element_text(component, 'Image')
                    }
                    self.components.append(comp_info)

                # 线条组件
                elif component_type and ('LinePrimitive' in component_type):
                    color = self._find_element_text(component, 'Color') or 'Black'
                    comp_info = {
                        'type': 'Line',
                        'name': component.get('Name', ''),
                        'rect': self._find_element_text(component, 'ClientRectangle'),
                        'color': color
                    }
                    self.components.append(comp_info)
        except Exception as e:
            print(f"提取组件时出错: {str(e)}")

    def _extract_font_info(self, component):
        """提取字体信息"""
        try:
            font_element = component.find('./Font')
            if font_element is not None and font_element.text:
                # 格式通常为 "Arial,9,Bold" 或 "Arial,9"
                font_info = font_element.text.split(',')
                font_name = font_info[0] if len(font_info) > 0 else "Arial"
                font_size = int(float(font_info[1])) if len(font_info) > 1 else 9
                font_bold = "Bold" in font_info if len(font_info) > 2 else False
                return {
                    'name': font_name,
                    'size': font_size,
                    'bold': font_bold
                }
        except Exception:
            pass

        # 默认字体信息
        return {
            'name': 'Arial',
            'size': 9,
            'bold': False
        }

    def _extract_page_settings(self, xml_content):
        """提取页面设置"""
        try:
            # Stimulsoft MRT文件使用厘米作为单位，我们需要将其转换为像素
            # 提高分辨率到200 DPI，1厘米 = 78.74像素
            # 1英寸 = 2.54厘米，1英寸 = 200像素，所以1厘米 = 200/2.54 = 78.74像素
            PIXELS_PER_CM = 78.74

            # 查找纸张尺寸信息
            paper_size = self._extract_attribute(xml_content, 'PaperSize')

            # 先尝试直接从PageWidth和PageHeight获取尺寸
            page_width = self._extract_attribute(xml_content, 'PageWidth')
            page_height = self._extract_attribute(xml_content, 'PageHeight')

            # 如果找到了宽度和高度，直接使用这些值
            if page_width and page_height:
                width = float(page_width) * PIXELS_PER_CM
                height = float(page_height) * PIXELS_PER_CM
                self.page_settings['width'] = int(width)
                self.page_settings['height'] = int(height)
                print(f"使用模板指定尺寸: 宽={page_width}厘米, 高={page_height}厘米")
                print(f"转换为像素: 宽={int(width)}, 高={int(height)}")

            # 如果没有明确的宽度和高度，但有纸张规格，尝试从纸张规格推断尺寸
            elif paper_size:
                # 纸张规格的标准尺寸（厘米）
                paper_sizes = {
                    'A3': {'width': 29.7, 'height': 42.0},
                    'A4': {'width': 21.0, 'height': 29.7},
                    'A5': {'width': 14.8, 'height': 21.0},  # A5是A4的一半
                    'A6': {'width': 10.5, 'height': 14.8},
                    'Letter': {'width': 21.6, 'height': 27.9},
                    'Legal': {'width': 21.6, 'height': 35.6}
                }

                if paper_size in paper_sizes:
                    size = paper_sizes[paper_size]
                    width = size['width'] * PIXELS_PER_CM
                    height = size['height'] * PIXELS_PER_CM

                    # 检查模板中的纸张方向是否为横向（宽度和高度互换）
                    is_landscape = self._extract_attribute(xml_content, 'IsLandscape')
                    if is_landscape and is_landscape.lower() == 'true':
                        width, height = height, width

                    self.page_settings['width'] = int(width)
                    self.page_settings['height'] = int(height)
                    print(f"使用{paper_size}纸张规格: 宽={int(width)}像素, 高={int(height)}像素")
                else:
                    # 未知纸张规格，使用默认A4尺寸
                    self.page_settings['width'] = 794  # A4宽度约为21cm * 37.8 = 794像素
                    self.page_settings['height'] = 1123 # A4高度约为29.7cm * 37.8 = 1123像素
                    print(f"未知纸张规格 {paper_size}，使用默认A4尺寸")
            else:
                # 尝试从Page的ClientRectangle获取尺寸
                page_start = xml_content.find('<Page')
                if page_start != -1:
                    page_end = xml_content.find('</Page>', page_start)
                    if page_end != -1:
                        page_xml = xml_content[page_start:page_end]
                        rect = self._extract_attribute(page_xml, 'ClientRectangle')
                        if rect:
                            parts = rect.split(',')
                            if len(parts) >= 4:
                                width = float(parts[2]) * PIXELS_PER_CM
                                height = float(parts[3]) * PIXELS_PER_CM

                                # 检查值是否合理
                                if width > 100 and height > 100:
                                    self.page_settings['width'] = int(width)
                                    self.page_settings['height'] = int(height)
                                    print(f"使用ClientRectangle尺寸: 宽={int(width)}像素, 高={int(height)}像素")
                                else:
                                    # 值过小，使用标准A4尺寸
                                    self.page_settings['width'] = 794
                                    self.page_settings['height'] = 1123
                                    print("ClientRectangle值过小，使用默认A4尺寸")
                        else:
                            # 没有尺寸信息，使用标准A4尺寸
                            self.page_settings['width'] = 794
                            self.page_settings['height'] = 1123
                            print("未找到页面尺寸信息，使用默认A4尺寸")

            # 寻找边距信息
            margins = self._extract_attribute(xml_content, 'Margins')
            if margins:
                margin_parts = margins.split(',')
                if len(margin_parts) >= 4:
                    self.page_settings['margin_left'] = float(margin_parts[0]) * PIXELS_PER_CM
                    self.page_settings['margin_top'] = float(margin_parts[1]) * PIXELS_PER_CM
                    self.page_settings['margin_right'] = float(margin_parts[2]) * PIXELS_PER_CM
                    self.page_settings['margin_bottom'] = float(margin_parts[3]) * PIXELS_PER_CM
                    print(f"设置页面边距: 左={self.page_settings['margin_left']}, 上={self.page_settings['margin_top']}, 右={self.page_settings['margin_right']}, 下={self.page_settings['margin_bottom']}")

        except Exception as e:
            print(f"提取页面设置时出错: {str(e)}")
            # 使用标准A4尺寸作为备用
            self.page_settings['width'] = 794
            self.page_settings['height'] = 1123
            print("出现错误，使用默认A4尺寸")

    def _find_element_text(self, parent, tag_name):
        """安全地获取元素文本"""
        try:
            element = parent.find(f'./{tag_name}')
            return element.text if element is not None else ''
        except:
            return ''

    def _extract_components_manually(self, xml_content):
        """手动从XML字符串提取组件信息"""
        try:
            # 使用简单的字符串处理方法提取文本组件
            text_components = self._extract_text_components(xml_content)
            self.components.extend(text_components)

            # 提取图像组件
            image_components = self._extract_image_components(xml_content)
            self.components.extend(image_components)

            print(f"手动提取了 {len(self.components)} 个组件")
        except Exception as e:
            print(f"手动提取组件时出错: {str(e)}")

    def _extract_text_components(self, xml_content):
        """从XML字符串提取文本组件"""
        components = []

        # 查找所有Text节点
        text_start = 0
        while True:
            text_start = xml_content.find('<Text ', text_start)
            if text_start == -1:
                break

            # 寻找此Text节点的结束
            end_tag = '</Text>'
            text_end = xml_content.find(end_tag, text_start)
            if text_end == -1:
                break
            text_end += len(end_tag)

            text_xml = xml_content[text_start:text_end]

            # 提取文本组件的属性
            rect = self._extract_attribute(text_xml, 'ClientRectangle')
            content = self._extract_tag_content(text_xml, 'Text')
            data_type = self._extract_tag_content(text_xml, 'Type')

            # 提取字体信息
            font_text = self._extract_tag_content(text_xml, 'Font')
            font_info = self._parse_font_string(font_text)
            
            # 提取对齐信息
            alignment = self._extract_tag_content(text_xml, 'HorAlignment') or 'Left'

            comp_info = {
                'type': 'Text',
                'name': '',
                'rect': rect,
                'text': content,
                'data_type': data_type,
                'font': font_info,
                'alignment': alignment
            }
            components.append(comp_info)

            text_start = text_end

        return components

    def _parse_font_string(self, font_text):
        """从字体字符串解析字体信息"""
        try:
            if (font_text):
                parts = font_text.split(',')
                name = parts[0] if len(parts) > 0 else "Arial"
                size = float(parts[1]) if len(parts) > 1 else 9
                bold = "Bold" in parts if len(parts) > 2 else False
                return {
                    'name': name,
                    'size': int(size),
                    'bold': bold
                }
        except:
            pass

        return {
            'name': 'Arial',
            'size': 9,
            'bold': False
        }

    def _extract_image_components(self, xml_content):
        """从XML字符串提取图像组件"""
        components = []

        # 查找所有Image节点
        img_start = 0
        while True:
            img_start = xml_content.find('<Image ', img_start)
            if img_start == -1:
                break

            # 寻找此Image节点的结束
            end_tag = '</Image>'
            img_end = xml_content.find(end_tag, img_start)
            if img_end == -1:
                break
            img_end += len(end_tag)

            img_xml = xml_content[img_start:img_end]

            # 提取图像组件的属性
            rect = self._extract_attribute(img_xml, 'ClientRectangle')
            image_data = self._extract_tag_content(img_xml, 'Image')

            comp_info = {
                'type': 'Image',
                'name': '',
                'rect': rect,
                'image_data': image_data
            }
            components.append(comp_info)

            img_start = img_end

        return components

    def _extract_attribute(self, xml_string, attribute_name):
        """从XML字符串中提取属性值"""
        start = xml_string.find(f'<{attribute_name}>')
        if (start != -1):
            start += len(f'<{attribute_name}>')
            end = xml_string.find(f'</{attribute_name}>', start)
            if (end != -1):
                return xml_string[start:end]
        return ''

    def _extract_tag_content(self, xml_string, tag_name):
        """从XML字符串中提取标签内容"""
        start = xml_string.find(f'<{tag_name}>')
        if (start != -1):
            start += len(f'<{tag_name}>')
            end = xml_string.find(f'</{tag_name}>', start)
            if (end != -1):
                return xml_string[start:end]
        return ''

    def _create_default_components(self):
        """创建默认组件以便在解析失败时使用"""
        default_components = [
            {
                'type': 'Text',
                'name': 'title',
                'rect': '3,0.6,12,1',
                'text': '凭证',
                'data_type': 'Expression',
                'font': {'name': 'Arial', 'size': 14, 'bold': True}
            },
            {
                'type': 'Text',
                'name': 'student_code',
                'rect': '1,3,6,0.6',
                'text': '学员编码：{ArrayList.sStudentCode}',
                'data_type': 'DataColumn',
                'font': {'name': 'Arial', 'size': 9, 'bold': False}
            },
            {
                'type': 'Text',
                'name': 'student_name',
                'rect': '1,4,6,0.6',
                'text': '学员姓名：{ArrayList.sStudentName}',
                'data_type': 'DataColumn',
                'font': {'name': 'Arial', 'size': 9, 'bold': False}
            }
        ]
        self.components = default_components

    def get_template_title(self):
        """获取模板标题"""
        # 尝试查找标题，通常是第一个文本组件或者特定名称的组件
        for component in self.components:
            if component['type'] == 'Text' and 'title' in component['name'].lower():
                return component['text']

        # 如果没有找到标题，返回文件名
        return os.path.basename(self.mrt_file_path).replace('.mrt', '')


class ProofPrintSimulator:
    def __init__(self):
        # 获取项目根目录，用于访问模板文件
        # print_simulator.py -> certificate_processors -> utils -> project_root
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.template_dir = os.path.join(self.base_dir, "properties")
        self.output_dir = os.path.join(self.base_dir, "image")  # 输出到image目录
        
        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"创建输出目录: {self.output_dir}")

        # 字体路径 - 可以根据需要更改
        self.font_path = os.path.join(os.environ.get('WINDIR', ''), 'Fonts', 'simhei.ttf')
        if not os.path.exists(self.font_path):
            self.font_path = None  # 如果找不到字体，将使用默认字体
    
    def get_certificate_type(self, biz_type):
        """根据BizType获取凭证类型"""
        for cert_type, config in CERTIFICATE_TYPES.items():
            if biz_type in config["biz_types"]:
                return cert_type
        return "通用类"
    
    def get_processor_method(self, biz_type):
        """根据BizType获取对应的处理方法"""
        cert_type = self.get_certificate_type(biz_type)
        for config in CERTIFICATE_TYPES.values():
            if biz_type in config["biz_types"]:
                return getattr(self, config["processor"], self.default_processor)
        return self.default_processor

    def process_print_request(self, message, template_name=None):
        """处理打印请求 - 支持直接指定模板名称或通过BizType自动选择"""
        try:
            print("开始处理打印请求...")
            
            # 支持直接传入模板名称的情况
            if template_name:
                print(f"直接使用指定模板: {template_name}")
                # 如果直接指定了模板名称，从消息中提取数据
                if "data" in message:
                    data = message["data"]
                    currency_symbol = message.get("currency_symbol", "¥")
                    biz_type = TEMPLATE_NAME_TO_BIZTYPE.get(template_name, 1)
                else:
                    print("错误: 直接指定模板时必须提供data字段")
                    return None
            else:
                # 原有的通过BizType选择模板的逻辑
                if "Info" in message and "Params" in message["Info"]:
                    params = message["Info"]["Params"]
                    biz_type = params.get("BizType")
                    json_string = params.get("JsonString")
                    currency_symbol = params.get("CurrencySymbol", "¥")

                    if biz_type is None or json_string is None:
                        print("错误: 缺少必要参数 BizType 或 JsonString")
                        return False

                    # 根据BizType获取模板名称
                    template_name = TEMPLATE_MAPPING.get(biz_type)
                    if not template_name:
                        print(f"错误: 不支持的BizType: {biz_type}")
                        return False

                    # 解析内部JSON
                    data = json.loads(json_string)
                else:
                    print("错误: 消息格式不正确")
                    return None

            # 获取凭证类型和对应的处理器
            cert_type = self.get_certificate_type(biz_type)
            processor = self.get_processor_method(biz_type)
            
            print(f"凭证类型: {cert_type}")
            print(f"使用模板: {template_name}")
            print(f"使用处理器: {processor.__name__}")
            
            # 使用专门的处理器处理数据
            processed_data = processor(data, biz_type)
            
            # 创建打印输出
            output_path = self.generate_print_output(template_name, processed_data, currency_symbol)
            return output_path
            
        except Exception as e:
            print(f"处理打印请求时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def default_processor(self, data, biz_type):
        """默认处理器 - 直接返回原始数据"""
        return data
    
    def enrollment_processor(self, data, biz_type):
        """报班类凭证处理器"""
        print("使用报班类凭证处理器")
        # 对于报班类凭证，可能需要特殊的字段处理
        processed_data = data.copy()
        
        # 根据不同的报班类型进行特殊处理
        if biz_type == 1:  # 普通报班凭证
            processed_data['证件类型'] = '报班凭证'
        elif biz_type == 9:  # 高端报班凭证
            processed_data['证件类型'] = '高端报班凭证'
        elif biz_type == 10:  # 高端报名凭证
            processed_data['证件类型'] = '高端报名凭证'
        
        return processed_data
    
    def refund_processor(self, data, biz_type):
        """退费类凭证处理器"""
        print("使用退费类凭证处理器")
        processed_data = data.copy()
        
        # 退费类凭证的特殊处理
        if biz_type == 3:  # 退班凭证
            processed_data['证件类型'] = '退班凭证'
        elif biz_type == 8:  # 退费凭证
            processed_data['证件类型'] = '退费凭证'
        elif biz_type == 11:  # 高端退费凭证
            processed_data['证件类型'] = '高端退费凭证'
        
        # 退费金额的特殊格式化
        if 'sPay' in processed_data:
            processed_data['sPay'] = processed_data['sPay'].replace('提现金额', '退费金额')
        
        return processed_data
    
    def adjustment_processor(self, data, biz_type):
        """调整类凭证处理器"""
        print("使用调整类凭证处理器")
        processed_data = data.copy()
        
        # 调整类凭证的特殊处理
        if biz_type == 2:  # 转班凭证
            processed_data['证件类型'] = '转班凭证'
        elif biz_type == 4:  # 调课凭证
            processed_data['证件类型'] = '调课凭证'
        elif biz_type == 7:  # 优惠重算凭证
            processed_data['证件类型'] = '优惠重算凭证'
        
        return processed_data
    
    def financial_processor(self, data, biz_type):
        """财务类凭证处理器"""
        print("使用财务类凭证处理器")
        processed_data = data.copy()
        
        # 财务类凭证的特殊处理（充值提现）
        processed_data['证件类型'] = '充值提现凭证'
        
        # 财务类凭证可能需要特殊的金额格式化
        if 'dSumBalance' in processed_data:
            # 确保余额格式正确
            balance = processed_data['dSumBalance']
            if not balance.startswith('余额：'):
                processed_data['dSumBalance'] = f"余额：{balance}"
        
        return processed_data
    
    def management_processor(self, data, biz_type):
        """管理类凭证处理器"""
        print("使用管理类凭证处理器")
        processed_data = data.copy()
        
        # 管理类凭证的特殊处理（班级凭证）
        processed_data['证件类型'] = '班级凭证'
        
        return processed_data

    def generate_print_output(self, template_name, data, currency_symbol):
        """生成打印输出"""
        # 获取模板文件路径
        template_path = os.path.join(self.template_dir, template_name)

        # 检查模板文件是否存在
        if not os.path.exists(template_path):
            print(f"错误: 无法找到模板文件 {template_path}")
            return None

        # 解析MRT模板
        mrt_parser = MrtParser(template_path)
        print(f"模板文件已找到并解析: {template_path}")

        # 检测是否需要移动端优化
        mobile_optimized = data.get('mobile_optimized', False)
        
        # 生成基于图像的打印预览，使用模板信息
        image = self._create_print_preview_from_template(data, mrt_parser, currency_symbol, mobile_optimized)

        # 保存图像到文件
        timestamp = get_beijing_timestamp()
        filename = f"{data.get('sProofName', '打印凭证')}_{timestamp}.png"
        output_path = os.path.join(self.output_dir, filename)
        # 使用高质量保存设置
        image.save(output_path, 'PNG', optimize=True, dpi=(200, 200))

        # 生成JSON输出文件
        json_filename = f"{data.get('sProofName', '打印凭证')}_{timestamp}.json"
        json_output_path = os.path.join(self.output_dir, json_filename)
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"打印输出已保存: {output_path}")
        print(f"JSON数据已保存: {json_output_path}")

        return output_path

    def _create_print_preview_from_template(self, data, mrt_parser, currency_symbol, mobile_optimized=False):
        """根据MRT模板创建打印预览图像"""
        # 获取原始尺寸
        original_width, original_height = mrt_parser.page_settings['width'], mrt_parser.page_settings['height']
        
        # 移动端优化：调整图像尺寸以适应小屏幕
        if mobile_optimized:
            # 移动端使用较小的尺寸，但保持宽高比
            max_mobile_width = 600  # 移动端最大宽度
            aspect_ratio = original_height / original_width
            width = min(original_width, max_mobile_width)
            height = int(width * aspect_ratio)
            scale_factor = width / original_width
        else:
            width, height = original_width, original_height
            scale_factor = 1.0
        
        # 创建一个白色背景的图像
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # 绘制页面边框 - 模拟打印纸张效果
        margin = 3  # 提高分辨率后，边框也应相应调整
        draw.rectangle([margin, margin, width-margin, height-margin], outline='lightgray', width=2)

        # 默认字体作为后备
        default_font = ImageFont.load_default()

        # 确保有一个中文字体可用 - 支持Linux和Windows系统
        chinese_font_path = None
        
        # Linux系统字体路径，优先使用中文字体
        linux_fonts = [
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc',
            '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans.ttf'
        ]
        
        # Windows系统字体
        windows_fonts = ['simsun.ttc', 'simhei.ttf', 'msyh.ttc', 'simkai.ttf']
        
        # 先尝试Linux字体
        for font_path in linux_fonts:
            if os.path.exists(font_path):
                chinese_font_path = font_path
                print(f"找到Linux字体: {os.path.basename(font_path)}")
                break
        
        # 如果Linux字体未找到，尝试Windows字体
        if not chinese_font_path:
            for font_name in windows_fonts:
                potential_path = os.path.join(os.environ.get('WINDIR', ''), 'Fonts', font_name)
                if os.path.exists(potential_path):
                    chinese_font_path = potential_path
                    print(f"找到Windows字体: {font_name}")
                    break

        if not chinese_font_path:
            print("警告: 无法找到中文字体，使用默认字体，中文可能显示为方框")

        # 字体缓存，避免重复创建相同的字体对象
        font_cache = {}

        # Stimulsoft MRT文件使用厘米作为单位，提高分辨率到200 DPI
        # 1厘米 = 200/2.54 = 78.74像素 (200 DPI)
        # 移动端优化：根据scale_factor调整像素密度
        base_pixels_per_cm = 78.74
        PIXELS_PER_CM = base_pixels_per_cm * scale_factor  # 根据缩放因子调整像素密度

        # 添加调试信息
        print(f"解析到 {len(mrt_parser.components)} 个组件")
        
        # 计算居中偏移量 - 让内容整体居中显示
        # 根据页面实际宽度计算更精确的居中偏移
        content_width = width * 0.85  # 内容区域占页面85%
        left_margin = (width - content_width) / 2
        center_offset_x = left_margin - 30  # 向右偏移，让左右对称
        center_offset_y = 20  # 向下偏移20像素
        
        # 绘制模板组件
        for component in mrt_parser.components:
            if component['type'] == 'Text':
                # 解析矩形区域
                rect_parts = component['rect'].split(',') if component['rect'] else [0, 0, 1, 1]
                if len(rect_parts) >= 4:
                    # 使用正确的转换因子，并添加居中偏移
                    x = float(rect_parts[0]) * PIXELS_PER_CM + center_offset_x
                    y = float(rect_parts[1]) * PIXELS_PER_CM + center_offset_y
                    width_comp = float(rect_parts[2]) * PIXELS_PER_CM
                    height_comp = float(rect_parts[3]) * PIXELS_PER_CM

                    # 获取文本内容
                    text = component['text']

                    # 处理混合内容（如 "{ArrayList.sSchoolName}{ArrayList.Title}"）
                    if text and '{' in text and '}' in text:
                        # 替换所有数据字段
                        while '{ArrayList.' in text and '}' in text:
                            start_idx = text.find('{ArrayList.')
                            end_idx = text.find('}', start_idx)
                            if (start_idx != -1 and end_idx != -1):
                                field_name = text[start_idx+11:end_idx]  # 去掉 {ArrayList.
                                if field_name in data:
                                    # 替换数据字段为实际值
                                    replacement = str(data[field_name])
                                    text = text[:start_idx] + replacement + text[end_idx+1:]
                                else:
                                    # 找不到数据，用空字符串替换
                                    text = text[:start_idx] + "" + text[end_idx+1:]

                    # 替换文本中可能存在的货币符号HTML实体
                    text = text.replace('&yen;', '¥')  # 替换HTML实体为普通人民币符号

                    # 渲染文本
                    if text and not text.startswith('{'):
                        # 从组件中获取字体信息
                        font_info = component.get('font', {'name': 'Arial', 'size': 9, 'bold': False})
                        font_name = font_info.get('name', 'Arial')
                        font_size = font_info.get('size', 9)
                        font_bold = font_info.get('bold', False)

                        # 检查文本是否包含中文字符或特殊符号（如人民币符号¥）
                        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
                        has_special_chars = '¥' in text or '￥' in text or any(ord(char) > 127 for char in text)
                        
                        # 检查是否需要加粗显示
                        should_bold = (
                            '余额' in text or
                            '提现凭证' in text or
                            '南昌学校' in text or
                            ('学校' in text and '凭证' in text) or
                            'Title' in text or  # 包含Title的文字
                            component.get('font', {}).get('bold', False) or
                            font_bold or
                            font_size >= 10.5  # 较大字体也加粗
                        )
                        
                        # 添加调试信息
                        if should_bold:
                            print(f"加粗文字: {text[:20]}{'...' if len(text) > 20 else ''}")

                        # 对于包含中文或特殊字符的文本，使用中文字体
                        if has_chinese or has_special_chars:
                            # 如果包含中文或特殊字符，使用中文字体
                            font_key = f"chinese_{font_size}_{should_bold}"
                            if font_key in font_cache:
                                font_to_use = font_cache[font_key]
                            else:
                                try:
                                    if chinese_font_path:
                                        # 字体大小按比例调整，由于分辨率提高到200 DPI，需要相应调整字体大小
                                        # 提高分辨率后，字体大小需要进一步放大
                                        base_size = max(16, int(font_size * 2.7))  # 至少16像素，放大2.7倍
                                        # 对于加粗文字，稍微增加字体大小，但主要靠多次绘制实现
                                        adjusted_size = int(base_size * 1.1) if should_bold else base_size
                                        font_to_use = ImageFont.truetype(chinese_font_path, adjusted_size)
                                        font_cache[font_key] = font_to_use
                                    else:
                                        # 如果没有找到中文字体，尝试使用默认字体
                                        font_to_use = default_font
                                        font_cache[font_key] = font_to_use
                                except Exception as e:
                                    print(f"加载中文字体失败: {str(e)}")
                                    font_to_use = default_font
                                    font_cache[font_key] = font_to_use
                        else:
                            # 对于纯ASCII文本，使用指定字体
                            font_key = f"{font_name}_{font_size}_{should_bold}"
                            if font_key in font_cache:
                                font_to_use = font_cache[font_key]
                            else:
                                try:
                                    # 尝试加载指定的字体
                                    font_path = os.path.join(os.environ.get('WINDIR', ''), 'Fonts', f"{font_name}.ttf")
                                    if not os.path.exists(font_path):
                                        # 尝试其他扩展名
                                        font_path = os.path.join(os.environ.get('WINDIR', ''), 'Fonts', f"{font_name}.ttc")

                                    if not os.path.exists(font_path):
                                        # 如果找不到指定字体，使用系统默认字体
                                        if chinese_font_path:
                                            font_path = chinese_font_path
                                        else:
                                            # 使用默认字体
                                            font_to_use = default_font
                                            font_cache[font_key] = font_to_use
                                            draw.text((x, y), text, fill='black', font=font_to_use)
                                            continue

                                    # 对于非中文字体，使用调整后的大小
                                    base_size = max(16, int(font_size * 2.7))  # 至少16像素，放大2.7倍
                                    # 对于加粗文字，稍微增加字体大小，但主要靠多次绘制实现
                                    adjusted_size = int(base_size * 1.1) if should_bold else base_size
                                    font_to_use = ImageFont.truetype(font_path, adjusted_size)
                                    font_cache[font_key] = font_to_use
                                except Exception as e:
                                    print(f"加载字体失败 {font_name} 大小 {font_size}: {str(e)}")
                                    # 如果加载失败，尝试使用中文字体
                                    if chinese_font_path:
                                        try:
                                            base_size = max(16, int(font_size * 2.7))  # 同样放大
                                            # 对于加粗文字，稍微增加字体大小，但主要靠多次绘制实现
                                            adjusted_size = int(base_size * 1.1) if should_bold else base_size
                                            font_to_use = ImageFont.truetype(chinese_font_path, adjusted_size)
                                            font_cache[font_key] = font_to_use
                                        except:
                                            font_to_use = default_font
                                            font_cache[font_key] = font_to_use
                                    else:
                                        font_to_use = default_font
                                        font_cache[font_key] = font_to_use

                        # 获取文本对齐方式
                        text_alignment = component.get('alignment', 'Left')  # 默认左对齐
                        
                        # 根据对齐方式调整文本位置
                        if text_alignment == 'Right':
                            # 右对齐 - 计算文本宽度并调整x坐标
                            text_bbox = draw.textbbox((0, 0), text, font=font_to_use)
                            text_width = text_bbox[2] - text_bbox[0]
                            x = x + width_comp - text_width
                        elif text_alignment == 'Center':
                            # 居中对齐
                            text_bbox = draw.textbbox((0, 0), text, font=font_to_use)
                            text_width = text_bbox[2] - text_bbox[0]
                            x = x + (width_comp - text_width) / 2

                        # 安全绘制文本，处理编码问题
                        try:
                            # 确保文本是UTF-8编码的字符串
                            if isinstance(text, bytes):
                                text = text.decode('utf-8', errors='replace')
                            elif not isinstance(text, str):
                                text = str(text)
                            
                            # 绘制文本，如果需要加粗，使用多次绘制技术
                            if should_bold:
                                # 通过在周围绘制多次来实现加粗效果，使用更粗的效果
                                for dx in [-1, 0, 1]:
                                    for dy in [-1, 0, 1]:
                                        if dx != 0 or dy != 0:  # 不绘制中心点
                                            try:
                                                draw.text((x + dx, y + dy), text, fill='black', font=font_to_use)
                                            except (UnicodeEncodeError, Exception):
                                                # 如果绘制失败，尝试使用替代字符
                                                safe_text = text.encode('ascii', errors='replace').decode('ascii')
                                                draw.text((x + dx, y + dy), safe_text, fill='black', font=font_to_use)
                                # 额外绘制一次稍微偏移的版本以增强加粗效果
                                try:
                                    draw.text((x + 1, y), text, fill='black', font=font_to_use)
                                    draw.text((x, y + 1), text, fill='black', font=font_to_use)
                                except (UnicodeEncodeError, Exception):
                                    safe_text = text.encode('ascii', errors='replace').decode('ascii')
                                    draw.text((x + 1, y), safe_text, fill='black', font=font_to_use)
                                    draw.text((x, y + 1), safe_text, fill='black', font=font_to_use)
                            
                            # 绘制主文本
                            try:
                                draw.text((x, y), text, fill='black', font=font_to_use)
                            except (UnicodeEncodeError, Exception) as e:
                                print(f"绘制文本失败: {str(e)}, 文本: {repr(text[:20])}")
                                # 尝试使用安全的文本替代
                                safe_text = text.encode('ascii', errors='replace').decode('ascii')
                                draw.text((x, y), safe_text, fill='black', font=font_to_use)
                                
                        except Exception as e:
                            print(f"文本处理错误: {str(e)}, 文本: {repr(text[:20])}")
                            # 如果所有尝试都失败，至少绘制一个占位符
                            try:
                                draw.text((x, y), "[文本显示错误]", fill='red', font=default_font)
                            except:
                                pass

            elif component['type'] == 'Image' and component.get('image_data'):
                # 解析矩形区域
                rect_parts = component['rect'].split(',') if component['rect'] else [0, 0, 1, 1]
                if len(rect_parts) >= 4:
                    # 使用正确的转换因子，并添加居中偏移
                    x = float(rect_parts[0]) * PIXELS_PER_CM + center_offset_x
                    y = float(rect_parts[1]) * PIXELS_PER_CM + center_offset_y
                    width_comp = float(rect_parts[2]) * PIXELS_PER_CM
                    height_comp = float(rect_parts[3]) * PIXELS_PER_CM

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
                            
                            image.paste(img, (int(x), int(y)))
                    except Exception as e:
                        print(f"处理图像时出错: {str(e)}")
                        # 如果图像无法加载，绘制一个占位符
                        draw.rectangle([x, y, x + width_comp, y + height_comp], outline='gray', width=1)

            elif component['type'] == 'Line':
                # 解析矩形区域
                rect_parts = component['rect'].split(',') if component['rect'] else [0, 0, 1, 0.01]
                if len(rect_parts) >= 4:
                    # 使用正确的转换因子，并添加居中偏移
                    x1 = float(rect_parts[0]) * PIXELS_PER_CM + center_offset_x
                    y1 = float(rect_parts[1]) * PIXELS_PER_CM + center_offset_y
                    line_width = float(rect_parts[2]) * PIXELS_PER_CM
                    line_height = float(rect_parts[3]) * PIXELS_PER_CM

                    # 判断是垂直线还是水平线
                    if line_height > line_width:  # 垂直线
                        x2 = x1
                        y2 = y1 + line_height
                    else:  # 水平线
                        x2 = x1 + line_width
                        y2 = y1

                    # 绘制线条，使用更合适的颜色
                    line_color = component.get('color', 'black')
                    if line_color.lower() in ['dimgray', 'gray']:
                        line_color = 'gray'
                    else:
                        line_color = 'black'
                    
                    draw.line([(x1, y1), (x2, y2)], fill=line_color, width=2)  # 高分辨率下线条更粗

        # 使用中文字体添加页脚信息
        footer_font = None
        if chinese_font_path:
            try:
                # 页脚字体也需要适应高分辨率
                footer_font = ImageFont.truetype(chinese_font_path, 24)  # 进一步放大到24
            except:
                footer_font = default_font
        else:
            footer_font = default_font

        # 仅在模板中没有相应字段时添加打印时间
        if not any("打印时间" in c.get('text', '') for c in mrt_parser.components):
            # 页脚位置也需要适应高分辨率和居中偏移
            footer_x = width - 400 + center_offset_x  # 调整位置
            footer_y = height - 50 + center_offset_y   # 调整位置
            draw.text((footer_x, footer_y), f"打印时间: {get_beijing_time_str()}", fill='black', font=footer_font)

        # 添加二维码和"【在线客服】"文字到左下角
        try:
            qr_code_path = os.path.join(self.base_dir, "properties", "qr_code.jpg")
            if os.path.exists(qr_code_path):
                # 加载二维码图片
                qr_image = Image.open(qr_code_path)
                
                # 设置二维码大小 - 稍微大一点
                qr_size = int(120 * scale_factor)  # 根据缩放因子调整大小
                qr_image = qr_image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
                
                # 计算二维码位置 - 固定在左下角，距离边缘有适当间距，向上调整两行字的距离
                qr_margin = int(30 * scale_factor)
                qr_x = qr_margin + center_offset_x
                # 向上调整大约两行字的距离（约50像素）
                qr_y = height - qr_size - qr_margin - int(50 * scale_factor) + center_offset_y
                
                # 粘贴二维码到图像
                if qr_image.mode in ('RGBA', 'LA') or (qr_image.mode == 'P' and 'transparency' in qr_image.info):
                    # 处理有透明度的图像
                    background = Image.new('RGB', qr_image.size, (255, 255, 255))
                    if qr_image.mode == 'P':
                        qr_image = qr_image.convert('RGBA')
                    background.paste(qr_image, mask=qr_image.split()[-1] if qr_image.mode == 'RGBA' else None)
                    qr_image = background
                
                image.paste(qr_image, (int(qr_x), int(qr_y)))
                
                # 添加"【在线客服】"文字，在二维码正上方
                service_text = "【在线客服】"
                service_font = None
                if chinese_font_path:
                    try:
                        service_font = ImageFont.truetype(chinese_font_path, int(20 * scale_factor))
                    except:
                        service_font = footer_font
                else:
                    service_font = footer_font
                
                # 计算文字位置 - 在二维码正上方居中，与二维码空一行距离
                text_bbox = draw.textbbox((0, 0), service_text, font=service_font)
                text_width = text_bbox[2] - text_bbox[0]
                text_x = qr_x + (qr_size - text_width) / 2  # 居中对齐
                text_y = qr_y - int(45 * scale_factor)  # 在二维码上方45像素，空出一行距离
                
                # 绘制"【在线客服】"文字
                draw.text((text_x, text_y), service_text, fill='black', font=service_font)
                
                print(f"已添加二维码和在线客服文字到位置: ({int(qr_x)}, {int(qr_y)})")
            else:
                print(f"警告: 二维码文件不存在: {qr_code_path}")
                
        except Exception as e:
            print(f"添加二维码时出错: {str(e)}")

        # 不再添加页码显示
        # 删除添加"第1页"的代码

        return image


async def simulate_print_request(message):
    """模拟打印请求处理过程"""
    simulator = ProofPrintSimulator()
    result = simulator.process_print_request(message)
    return result

def create_certificate_printer():
    """创建凭证打印器实例"""
    return ProofPrintSimulator()

def print_certificate_by_type(cert_type, data, currency_symbol="¥"):
    """根据凭证类型打印凭证的便捷方法"""
    simulator = create_certificate_printer()
    
    # 根据凭证类型选择第一个可用的模板
    for config in CERTIFICATE_TYPES.values():
        if cert_type in config["templates"]:
            template_name = cert_type
            biz_type = TEMPLATE_NAME_TO_BIZTYPE.get(template_name, 1)
            break
    else:
        print(f"错误: 不支持的凭证类型: {cert_type}")
        return None
    
    # 构造消息格式
    message = {
        "data": data,
        "currency_symbol": currency_symbol
    }
    
    return simulator.process_print_request(message, template_name)

def print_certificate_by_biz_type(biz_type, data, currency_symbol="¥"):
    """根据BizType打印凭证的便捷方法"""
    simulator = create_certificate_printer()
    
    # 构造标准消息格式
    message = {
        "PrintType": "proofprintnew",
        "Info": {
            "Params": {
                "BizType": biz_type,
                "JsonString": json.dumps(data, ensure_ascii=False),
                "CurrencySymbol": currency_symbol,
                "DefaultPrinter": "",
                "DefaultPrintNumber": 1,
                "NeedPreview": True,
                "SchoolId": data.get("nSchoolId", 35)
            }
        }
    }
    
    return simulator.process_print_request(message)

def get_available_certificates():
    """获取所有可用的凭证类型"""
    certificates = {}
    for cert_type, config in CERTIFICATE_TYPES.items():
        certificates[cert_type] = {
            "templates": config["templates"],
            "biz_types": config["biz_types"],
            "processor": config["processor"]
        }
    return certificates

def print_certificate_info():
    """打印所有凭证类型的信息"""
    print("=== 可用的凭证类型 ===")
    for cert_type, config in CERTIFICATE_TYPES.items():
        print(f"\n{cert_type}:")
        print(f"  - 模板文件: {', '.join(config['templates'])}")
        print(f"  - BizType: {', '.join(map(str, config['biz_types']))}")
        print(f"  - 处理器: {config['processor']}")
    
    print(f"\n=== 模板映射表 ===")
    for biz_type, template in TEMPLATE_MAPPING.items():
        print(f"BizType {biz_type}: {template}")

def main():
    # 显示所有可用的凭证类型信息
    print_certificate_info()
    print("\n" + "="*50 + "\n")
    
    # 示例1: 使用传统的BizType方式（充值提现凭证）
    print("示例1: 使用BizType方式打印充值提现凭证")
    message1 = {
        "PrintType": "proofprintnew",
        "Info": {
            "Params": {
                "BizType": 6,
                "JsonString": json.dumps({
                    "nSchoolId": 35,
                    "sSchoolName": "南昌学校",
                    "sTelePhone": "400-175-9898",
                    "sOperator": "张谦1234",
                    "dtCreate": "2025-06-05 09:49:44",
                    "Title": "提现凭证",
                    "PrintNumber": 1,
                    "YNVIEWPrint": 1,
                    "PrintDocument": "",
                    "sStudentCode": "NC6080119755",
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
                }),
                "DefaultPrinter": "", 
                "DefaultPrintNumber": 1,
                "NeedPreview": True,
                "SchoolId": 35,
                "CurrencySymbol": "¥"
            }
        }
    }
    
    # 示例2: 使用新的便捷方法打印报班凭证
    print("示例2: 使用便捷方法打印报班凭证")
    enrollment_data = {
        "nSchoolId": 35,
        "sSchoolName": "南昌学校",
        "sTelePhone": "400-175-9898",
        "sOperator": "李老师",
        "dtCreate": "2024-12-23 10:30:00",
        "Title": "报班凭证",
        "sStudentCode": "NC6080119756",
        "sStudentName": "张三",
        "sGender": "男",
        "sPay": "学费：¥2000.00",
        "sPayType": "支付方式：微信支付",
        "dtCreateDate": "2024-12-23 10:30:00",
        "sProofName": "报班凭证",
        "sBizType": "报班",
        "nBizId": 126560051,
        "sRegZoneName": "教务处"
    }
    
    # 示例3: 使用新的便捷方法打印退费凭证
    print("示例3: 使用便捷方法打印退费凭证")
    refund_data = {
        "nSchoolId": 35,
        "sSchoolName": "南昌学校",
        "sTelePhone": "400-175-9898",
        "sOperator": "王老师",
        "dtCreate": "2024-12-23 11:00:00",
        "Title": "退费凭证",
        "sStudentCode": "NC6080119757",
        "sStudentName": "李四",
        "sGender": "女",
        "sPay": "退费金额：¥1000.00",
        "sPayType": "退费方式：原路返回",
        "dtCreateDate": "2024-12-23 11:00:00",
        "sProofName": "退费凭证",
        "sBizType": "退费",
        "nBizId": 126560052,
        "sRegZoneName": "财务处"
    }
    
    print("开始运行示例...")
    
    # 运行示例1（传统方式）
    print("\n>>> 运行示例1...")
    asyncio.run(simulate_print_request(message1))
    
    # 运行示例2（便捷方法 - 按模板名称）
    print("\n>>> 运行示例2...")
    result2 = print_certificate_by_type("报班凭证.mrt", enrollment_data)
    print(f"报班凭证打印结果: {result2}")
    
    # 运行示例3（便捷方法 - 按BizType）
    print("\n>>> 运行示例3...")
    result3 = print_certificate_by_biz_type(8, refund_data)  # BizType 8 = 退费凭证
    print(f"退费凭证打印结果: {result3}")
    
    print("\n所有示例执行完成！")

if __name__ == "__main__":
    main()
