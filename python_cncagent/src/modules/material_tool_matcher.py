"""
材料-刀具智能匹配模块
"""
import math
from typing import Dict, List, Any, Optional


# 材料数据库
MATERIAL_DATABASE = {
    # 钢材
    'steel': {
        'name': '钢',
        'hardness': {'min': 150, 'max': 600, 'unit': 'HB'},
        'tensile_strength': {'min': 400, 'max': 2000, 'unit': 'MPa'},
        'default_tool_material': 'carbide',
        'recommended_cutting_speed': { 
            'rough': {'min': 80, 'max': 150, 'unit': 'm/min'},
            'finish': {'min': 120, 'max': 200, 'unit': 'm/min'}
        }
    },
    'stainless_steel': {
        'name': '不锈钢',
        'hardness': {'min': 150, 'max': 300, 'unit': 'HB'},
        'tensile_strength': {'min': 500, 'max': 800, 'unit': 'MPa'},
        'default_tool_material': 'carbide',
        'recommended_cutting_speed': {
            'rough': {'min': 60, 'max': 120, 'unit': 'm/min'},
            'finish': {'min': 100, 'max': 160, 'unit': 'm/min'}
        }
    },
    'aluminum': {
        'name': '铝',
        'hardness': {'min': 15, 'max': 150, 'unit': 'HB'},
        'tensile_strength': {'min': 70, 'max': 300, 'unit': 'MPa'},
        'default_tool_material': 'carbide',
        'recommended_cutting_speed': {
            'rough': {'min': 200, 'max': 1000, 'unit': 'm/min'},
            'finish': {'min': 300, 'max': 1200, 'unit': 'm/min'}
        }
    },
    'copper': {
        'name': '铜',
        'hardness': {'min': 35, 'max': 100, 'unit': 'HB'},
        'tensile_strength': {'min': 200, 'max': 300, 'unit': 'MPa'},
        'default_tool_material': 'hss',
        'recommended_cutting_speed': {
            'rough': {'min': 100, 'max': 300, 'unit': 'm/min'},
            'finish': {'min': 150, 'max': 400, 'unit': 'm/min'}
        }
    },
    'plastic': {
        'name': '塑料',
        'hardness': {'min': 10, 'max': 50, 'unit': 'HB'},
        'tensile_strength': {'min': 20, 'max': 100, 'unit': 'MPa'},
        'default_tool_material': 'carbide',
        'recommended_cutting_speed': {
            'rough': {'min': 150, 'max': 500, 'unit': 'm/min'},
            'finish': {'min': 200, 'max': 600, 'unit': 'm/min'}
        }
    },
    'titanium': {
        'name': '钛合金',
        'hardness': {'min': 300, 'max': 450, 'unit': 'HB'},
        'tensile_strength': {'min': 900, 'max': 1200, 'unit': 'MPa'},
        'default_tool_material': 'carbide',
        'recommended_cutting_speed': {
            'rough': {'min': 30, 'max': 60, 'unit': 'm/min'},
            'finish': {'min': 50, 'max': 80, 'unit': 'm/min'}
        }
    }
}

# 刀具数据库
TOOL_DATABASE = {
    'hss': {
        'name': '高速钢刀具',
        'materials': ['steel', 'aluminum', 'copper', 'plastic'],
        'coating': 'none',
        'max_rpm': 8000,
        'max_cutting_speed': 150,
        'feed_per_tooth': {'steel': 0.05, 'aluminum': 0.15, 'copper': 0.12, 'plastic': 0.2}
    },
    'carbide_uncoated': {
        'name': '未涂层硬质合金刀具',
        'materials': ['steel', 'stainless_steel', 'aluminum', 'copper', 'plastic', 'titanium'],
        'coating': 'none',
        'max_rpm': 15000,
        'max_cutting_speed': 300,
        'feed_per_tooth': {'steel': 0.08, 'stainless_steel': 0.06, 'aluminum': 0.18, 'copper': 0.15, 'plastic': 0.25, 'titanium': 0.03}
    },
    'carbide_ticn': {
        'name': 'TiCN涂层硬质合金刀具',
        'materials': ['steel', 'stainless_steel', 'aluminum', 'copper', 'titanium'],
        'coating': 'TiCN',
        'max_rpm': 20000,
        'max_cutting_speed': 400,
        'feed_per_tooth': {'steel': 0.10, 'stainless_steel': 0.08, 'aluminum': 0.20, 'copper': 0.18, 'titanium': 0.04}
    },
    'carbide_alcrn': {
        'name': 'AlCrN涂层硬质合金刀具',
        'materials': ['steel', 'stainless_steel', 'titanium'],
        'coating': 'AlCrN',
        'max_rpm': 25000,
        'max_cutting_speed': 500,
        'feed_per_tooth': {'steel': 0.12, 'stainless_steel': 0.10, 'titanium': 0.05}
    }
}

# 特征类型到刀具映射
FEATURE_TO_TOOL_MAPPING = {
    'hole': {
        'center_drill': ['steel', 'stainless_steel', 'aluminum', 'copper'],
        'twist_drill': ['steel', 'stainless_steel', 'aluminum', 'copper', 'plastic'],
        'step_drill': ['aluminum', 'copper', 'plastic'],
        'reamer': ['steel', 'stainless_steel', 'aluminum', 'copper']
    },
    'counterbore': {
        'counterbore_tool': ['steel', 'stainless_steel', 'aluminum', 'copper'],
        'spotface_tool': ['steel', 'stainless_steel', 'aluminum', 'copper']
    },
    'pocket': {
        'endmill': ['steel', 'stainless_steel', 'aluminum', 'copper', 'plastic', 'titanium'],
        'face_mill': ['steel', 'aluminum', 'copper', 'plastic']
    },
    'slot': {
        'slot_drill': ['steel', 'aluminum', 'copper'],
        'side_mill': ['steel', 'aluminum', 'copper', 'plastic']
    },
    'face_mill': {
        'face_mill': ['steel', 'stainless_steel', 'aluminum', 'copper', 'plastic']
    },
    'thread': {
        'tap': ['steel', 'aluminum', 'copper', 'plastic'],
        'thread_mill': ['steel', 'stainless_steel', 'aluminum', 'copper']
    }
}


def recommend_machining_parameters(material_type: str, tool_type: str, feature_type: str, feature_size: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """
    推荐加工参数
    
    Args:
        material_type: 材料类型
        tool_type: 刀具类型
        feature_type: 特征类型
        feature_size: 特征尺寸
        
    Returns:
        推荐的加工参数
    """
    if feature_size is None:
        feature_size = {}
    
    material = MATERIAL_DATABASE.get(material_type)
    tool = TOOL_DATABASE.get(tool_type)
    
    if not material or not tool:
        return None

    # 基础参数计算
    base_cutting_speed = material['recommended_cutting_speed']['finish']['min']
    feed_per_tooth = tool['feed_per_tooth'].get(material_type, 0.1)

    # 根据特征类型调整参数
    cutting_speed = base_cutting_speed
    spindle_speed = 0
    feed_rate = 0

    # 计算主轴转速 (RPM = (Cutting Speed * 1000) / (π * Tool Diameter))
    tool_diameter = feature_size.get('diameter', 6)  # 默认6mm
    spindle_speed = round((cutting_speed * 1000) / (math.pi * tool_diameter))

    # 限制主轴转速不超过刀具最大RPM
    spindle_speed = min(spindle_speed, tool['max_rpm'])

    # 计算进给率 (Feed Rate = Spindle Speed * Feed Per Tooth * Number of Flutes)
    number_of_flutes = feature_size.get('flutes', 2)  # 默认2刃
    feed_rate = round(spindle_speed * feed_per_tooth * number_of_flutes)

    # 根据特征类型进一步调整
    if feature_type == 'hole':
        # 钻孔时降低主轴转速和进给率
        spindle_speed = round(spindle_speed * 0.7)
        feed_rate = round(feed_rate * 0.6)
    elif feature_type == 'pocket':
        # 铣削口袋时使用中等参数
        spindle_speed = round(spindle_speed * 0.9)
        feed_rate = round(feed_rate * 0.85)
    elif feature_type == 'face_mill':
        # 面铣时可以使用较高参数
        spindle_speed = round(spindle_speed * 0.95)
        feed_rate = round(feed_rate * 0.9)
    elif feature_type == 'thread':
        # 攻丝时使用较低参数
        spindle_speed = round(spindle_speed * 0.5)
        feed_rate = round(feed_rate * 0.4)
    # 其他特征类型使用计算值

    return {
        'spindle_speed': spindle_speed,
        'feed_rate': feed_rate,
        'cutting_speed': cutting_speed,
        'tool_diameter': tool_diameter,
        'number_of_flutes': number_of_flutes,
        'material': material['name'],
        'tool': tool['name'],
        'adjustments': {
            'feature_specific': True,
            'speed_factor': spindle_speed / (base_cutting_speed * 1000 / (math.pi * tool_diameter)),
            'feed_factor': feed_rate / (spindle_speed * feed_per_tooth * number_of_flutes)
        }
    }


def match_material_and_tool(material_type: str, feature_type: str, feature_size: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    智能匹配材料和刀具
    
    Args:
        material_type: 材料类型
        feature_type: 特征类型
        feature_size: 特征尺寸
        
    Returns:
        适合的刀具列表
    """
    if feature_size is None:
        feature_size = {}
    
    material = MATERIAL_DATABASE.get(material_type)
    if not material:
        raise ValueError(f'不支持的材料类型: {material_type}')

    # 获取适合该材料和特征的刀具列表
    suitable_tools = []

    for tool_key, tool in TOOL_DATABASE.items():
        # 检查刀具是否适用于该材料
        if material_type in tool['materials']:
            # 获取适合该特征的刀具类型
            feature_tools = FEATURE_TO_TOOL_MAPPING.get(feature_type, {})

            # 检查是否有该特征对应的刀具
            has_feature_tool = False
            for feature_tool_materials in feature_tools.values():
                if material_type in feature_tool_materials:
                    has_feature_tool = True
                    break

            if has_feature_tool:
                # 推荐加工参数
                parameters = recommend_machining_parameters(material_type, tool_key, feature_type, feature_size)

                suitable_tools.append({
                    'tool_type': tool_key,
                    'tool_name': tool['name'],
                    'parameters': parameters,
                    'ranking': calculate_tool_ranking(material, tool, feature_type, feature_size)
                })

    # 按排名排序
    suitable_tools.sort(key=lambda x: x['ranking'], reverse=True)

    return suitable_tools


def calculate_tool_ranking(material: Dict[str, Any], tool: Dict[str, Any], feature_type: str, feature_size: Dict[str, Any]) -> int:
    """
    计算刀具排名
    
    Args:
        material: 材料信息
        tool: 刀具信息
        feature_type: 特征类型
        feature_size: 特征尺寸
        
    Returns:
        排名分数
    """
    ranking = 0

    # 基础分
    ranking += 50

    # 根据涂层加分
    if tool['coating'] == 'AlCrN':
        ranking += 20
    elif tool['coating'] == 'TiCN':
        ranking += 15

    # 根据最大切削速度加分
    ranking += (tool['max_cutting_speed'] / 100)

    # 根据材料硬度调整
    material_hardness = (material['hardness']['min'] + material['hardness']['max']) / 2
    if material_hardness > 400 and tool['max_cutting_speed'] > 300:
        ranking += 10

    # 根据特征类型特殊加分
    if feature_type == 'thread' and tool['coating']:
        ranking += 5
    if feature_type == 'pocket' and tool['max_cutting_speed'] > 200:
        ranking += 5

    return ranking


def get_materials_list() -> List[Dict[str, Any]]:
    """
    获取材料列表
    
    Returns:
        材料列表
    """
    return [
        {
            'key': key,
            'name': value['name'],
            'properties': {
                'hardness': value['hardness'],
                'tensile_strength': value['tensile_strength']
            }
        }
        for key, value in MATERIAL_DATABASE.items()
    ]


def get_tools_list() -> List[Dict[str, Any]]:
    """
    获取刀具列表
    
    Returns:
        刀具列表
    """
    return [
        {
            'key': key,
            'name': value['name'],
            'properties': {
                'coating': value['coating'],
                'max_rpm': value['max_rpm'],
                'max_cutting_speed': value['max_cutting_speed']
            }
        }
        for key, value in TOOL_DATABASE.items()
    ]


if __name__ == "__main__":
    # 测试代码
    print("材料列表:")
    for material in get_materials_list():
        print(f"  {material['key']}: {material['name']}")
    
    print("\n刀具列表:")
    for tool in get_tools_list():
        print(f"  {tool['key']}: {tool['name']}")
    
    print("\n为铝材孔加工推荐刀具:")
    tools = match_material_and_tool('aluminum', 'hole', {'diameter': 6})
    for tool in tools:
        print(f"  {tool['tool_name']}: 排名 {tool['ranking']}, 参数 {tool['parameters']}")
