"""
G代码生成模块
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import math

from .validation import validate_feature_parameters, validate_gcode_blocks, validate_gcode_syntax, validate_gcode_safety, detect_collisions
from .material_tool_matcher import match_material_and_tool, recommend_machining_parameters


def trigger_gcode_generation(project: Any) -> List[Dict[str, Any]]:
    """
    触发G代码生成
    
    Args:
        project: 项目对象
        
    Returns:
        生成的G代码块列表
    """
    if not project or not hasattr(project, 'features'):
        raise ValueError('项目参数无效')

    if not isinstance(project.features, list):
        raise ValueError('项目特征列表无效')

    # 按加工工艺类型对特征进行分类和分组
    grouped_features = group_features_by_type_and_parameters(project.features)

    # 初始化G代码块数组
    gcode_blocks = []

    # 添加程序开始代码
    program_start = {
        'id': 'program_start',
        'type': 'program_control',
        'code': [
            'O0001 (CNC程序 - 智能加工程序)',
            '(根据特征类型和位置优化加工顺序)',
            'G21 (毫米编程)',
            'G40 (刀具半径补偿取消)',
            'G49 (刀具长度补偿取消)',
            'G80 (取消固定循环)',
            'G90 (绝对编程)',
            'G54 (工件坐标系1)',
            'G0 X0. Y0. S500 M03 (主轴正转，500转/分钟，初始转速)'
        ],
        'feature_id': None,
        'created_at': datetime.now().isoformat()
    }

    # 为每个特征分组生成G代码
    for group_key, group in grouped_features.items():
        main_feature = group[0] if group else None  # 使用组中的第一个特征作为代表

        if main_feature and main_feature.get('feature_type'):
            # 验证特征参数
            feature_validation = validate_feature_parameters(main_feature)
            if not feature_validation.get('valid', False):
                print(f'特征组 {group_key} 中的特征验证失败:', feature_validation.get('errors', []))
                # 可以选择跳过无效特征组或使用默认参数
                continue

            # 将项目信息添加到特征中，以便G代码生成时使用
            if hasattr(project, 'material_type') and project.material_type:
                if 'project' not in main_feature:
                    main_feature['project'] = {}
                main_feature['project']['material_type'] = project.material_type

            # 生成批量加工G代码
            gcode_block = generate_feature_gcode(main_feature, group)
            if gcode_block:
                gcode_blocks.append(gcode_block)

    # 添加程序结束代码
    program_end = {
        'id': 'program_end',
        'type': 'program_control',
        'code': [
            'M05 (主轴停止)',
            'M30 (程序结束)'
        ],
        'feature_id': None,
        'created_at': datetime.now().isoformat()
    }

    gcode_blocks.insert(0, program_start)
    gcode_blocks.append(program_end)

    # 验证生成的G代码
    gcode_validation = validate_gcode_blocks(gcode_blocks)
    if gcode_validation.get('errors') and len(gcode_validation['errors']) > 0:
        print('G代码验证警告:', gcode_validation.get('errors'))

    # 对每块G代码进行安全验证
    for block in gcode_blocks:
        if isinstance(block.get('code'), list):
            safety_validation = validate_gcode_safety(block['code'])
            if safety_validation.get('errors') and len(safety_validation['errors']) > 0:
                print(f'G代码块 {block.get("id", "unknown")} 安全验证失败:', safety_validation.get('errors'))
            if safety_validation.get('warnings') and len(safety_validation['warnings']) > 0:
                print(f'G代码块 {block.get("id", "unknown")} 安全验证警告:', safety_validation.get('warnings'))

            # 进行碰撞检测
            collision_detection = detect_collisions(block['code'])
            if collision_detection.get('has_collisions'):
                print(f'G代码块 {block.get("id", "unknown")} 碰撞检测失败:', collision_detection.get('collisions'))
                # 如果有碰撞，可以标记该程序块为不安全
                if 'metadata' not in block:
                    block['metadata'] = {}
                block['metadata']['has_collision_risk'] = True
                block['metadata']['collision_issues'] = collision_detection.get('collisions')

    return gcode_blocks


def group_features_by_type_and_parameters(features: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    根据特征类型和参数对特征进行分组
    
    Args:
        features: 特征列表
        
    Returns:
        按类型和参数分组的特征字典
    """
    if not isinstance(features, list):
        return {}

    grouped_features = {}

    for feature in features:
        # 生成特征的唯一键用于分组
        feature_key = get_feature_key(feature)

        # 如果该特征类型和参数组合还没有分组，创建新分组
        if feature_key not in grouped_features:
            grouped_features[feature_key] = []

        # 将特征添加到对应的分组中
        grouped_features[feature_key].append(feature)

    return grouped_features


def sort_features_by_process(features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    根据加工工艺类型对特征进行排序和分组，优化换刀次数
    
    Args:
        features: 特征列表
        
    Returns:
        排序后的特征列表
    """
    if not isinstance(features, list):
        return []

    # 按加工工艺优先级排序：先加工孔类特征，再加工铣削特征
    process_order = {
        'hole': 1,           # 孔加工
        'counterbore': 1,    # 沉头孔加工
        'thread': 1,         # 螺纹加工
        'pocket': 2,         # 口袋铣削
        'slot': 2,           # 槽铣削
        'chamfer': 3,        # 倒角
        'fillet': 3,         # 圆角
        'surface_finish': 4, # 表面处理
        'tolerance': 5,      # 公差检查
    }

    # 首先根据工艺类型对特征进行分组
    grouped_features = {}
    for feature in features:
        feature_type = feature.get('feature_type', 'default')
        order = process_order.get(feature_type, 99)
        if order not in grouped_features:
            grouped_features[order] = {}
        
        # 为相同特征类型创建子分组（考虑参数相同的情况）
        feature_key = get_feature_key(feature)
        if feature_key not in grouped_features[order]:
            grouped_features[order][feature_key] = []
        grouped_features[order][feature_key].append(feature)

    # 按工艺优先级处理每个分组
    sorted_orders = sorted(grouped_features.keys())

    result = []
    for order in sorted_orders:
        group = grouped_features[order]
        # 处理每个特征类型的子分组
        for feature_key in group:
            feature_group = group[feature_key]
            # 对同一特征类型的特征按位置排序，以优化加工路径
            sorted_by_position = sorted(feature_group, key=lambda f: (
                f.get('base_geometry', {}).get('center', {}).get('x', 0),
                f.get('base_geometry', {}).get('center', {}).get('y', 0)
            ))
            result.extend(sorted_by_position)

    return result


def get_feature_key(feature: Dict[str, Any]) -> str:
    """
    生成特征的唯一键，用于识别相同特征（相同类型和参数）
    
    Args:
        feature: 特征对象
        
    Returns:
        特征唯一键
    """
    if not feature or not feature.get('feature_type'):
        return 'unknown'

    # 根据特征类型生成唯一键
    feature_type = feature['feature_type']
    params = feature.get('parameters', {})

    if feature_type == 'hole':
        diameter = params.get('diameter', 'default')
        depth = params.get('depth', 'default')
        return f"{feature_type}_{diameter}_{depth}"
    elif feature_type == 'counterbore':
        diameter = params.get('diameter', 'default')
        depth = params.get('depth', 'default')
        counterbore_diameter = params.get('counterbore_diameter', 'default')
        counterbore_depth = params.get('counterbore_depth', 'default')
        return f"{feature_type}_{diameter}_{depth}_{counterbore_diameter}_{counterbore_depth}"
    elif feature_type == 'pocket':
        width = params.get('width', 'default')
        length = params.get('length', 'default')
        depth = params.get('depth', 'default')
        return f"{feature_type}_{width}_{length}_{depth}"
    elif feature_type == 'slot':
        width = params.get('width', 'default')
        length = params.get('length', 'default')
        depth = params.get('depth', 'default')
        return f"{feature_type}_{width}_{length}_{depth}"
    elif feature_type == 'thread':
        diameter = params.get('diameter', 'default')
        pitch = params.get('pitch', 'default')
        depth = params.get('depth', 'default')
        return f"{feature_type}_{diameter}_{pitch}_{depth}"
    else:
        return feature_type


def generate_feature_gcode(feature: Dict[str, Any], grouped_features: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """
    生成特征G代码
    
    Args:
        feature: 特征对象
        grouped_features: 分组特征列表（用于批量加工）
        
    Returns:
        G代码块对象
    """
    if not feature or not isinstance(feature, dict):
        return None

    if not feature.get('feature_type'):
        return None

    # 如果项目中定义了材料类型，使用智能匹配
    recommended_params = None
    if feature.get('project') and feature['project'].get('material_type'):
        try:
            matches = match_material_and_tool(
                feature['project']['material_type'],
                feature['feature_type'],
                feature.get('parameters', {})
            )
            if matches:
                recommended_params = matches[0].get('parameters')
        except Exception as e:
            print(f'材料-刀具匹配失败: {e}')

    # 更新特征参数以包含推荐的加工参数
    if recommended_params:
        if 'parameters' not in feature:
            feature['parameters'] = {}
        feature['parameters']['spindle_speed'] = recommended_params.get('spindle_speed')
        feature['parameters']['feed_rate'] = recommended_params.get('feed_rate')
        feature['parameters']['recommended_tool'] = recommended_params.get('tool')

    gcode_lines = []

    # 如果存在分组特征且当前特征是分组的一部分，则生成批量加工代码
    if grouped_features and len(grouped_features) > 1:
        # 根据特征类型生成批量加工代码
        if feature['feature_type'] == 'hole':
            gcode_lines = generate_hole_gcode_batch(feature, grouped_features)
        elif feature['feature_type'] == 'counterbore':
            gcode_lines = generate_counterbore_gcode_batch(feature, grouped_features)
        else:
            # 对于不支持批量加工的特征类型，使用普通方法
            gcode_lines = generate_standard_feature_gcode(feature, recommended_params)
    else:
        # 使用标准方法生成单个特征的G代码
        gcode_lines = generate_standard_feature_gcode(feature, recommended_params)

    # 创建G代码块对象
    gcode_block = {
        'id': f'gcode_{feature.get("id", "unknown")}',
        'type': 'feature_operation',
        'code': gcode_lines,
        'feature_id': feature.get('id'),
        'feature_type': feature.get('feature_type'),
        'parameters': dict(feature.get('parameters', {})),
        'recommended_params': recommended_params,  # 添加推荐参数
        'created_at': datetime.now().isoformat()
    }

    # 如果是批量加工，添加批量加工信息
    if grouped_features and len(grouped_features) > 1:
        gcode_block['is_batch_operation'] = True
        gcode_block['batch_size'] = len(grouped_features)
        gcode_block['feature_group'] = [
            {
                'id': f.get('id'),
                'geometry': f.get('base_geometry')
            }
            for f in grouped_features
        ]

    return gcode_block


def generate_standard_feature_gcode(feature: Dict[str, Any], recommended_params: Optional[Dict[str, Any]]) -> List[str]:
    """
    生成标准特征G代码（单个特征）
    
    Args:
        feature: 特征对象
        recommended_params: 推荐参数
        
    Returns:
        G代码行列表
    """
    feature_type = feature.get('feature_type')
    
    if feature_type == 'hole':
        return generate_hole_gcode(feature)
    elif feature_type == 'counterbore':
        return generate_counterbore_gcode(feature)
    elif feature_type == 'pocket':
        return generate_pocket_gcode(feature)
    elif feature_type == 'slot':
        return generate_slot_gcode(feature)
    elif feature_type == 'chamfer':
        return generate_chamfer_gcode(feature)
    elif feature_type == 'fillet':
        return generate_fillet_gcode(feature)
    elif feature_type == 'thread':  # 螺纹特征
        return generate_thread_gcode(feature)
    elif feature_type == 'surface_finish':  # 表面光洁度
        return generate_surface_finish_gcode(feature)
    elif feature_type == 'tolerance':  # 形位公差
        return generate_tolerance_gcode(feature)
    else:
        return generate_generic_feature_gcode(feature)


def generate_hole_gcode_batch(main_feature: Dict[str, Any], features: List[Dict[str, Any]]) -> List[str]:
    """
    生成批量孔加工G代码
    
    Args:
        main_feature: 主特征
        features: 特征列表
        
    Returns:
        G代码行列表
    """
    params = main_feature.get('parameters', {})
    diameter = params.get('diameter', 5.5)  # 孔径5.5mm
    depth = params.get('depth', 14)         # 默认实际加工深度14mm
    tool_number = params.get('tool_number', 2)  # 默认使用钻头T02

    # 使用推荐参数或默认参数
    spindle_speed = params.get('spindle_speed') or (1200 if tool_number == 1 else 800 if tool_number == 2 else 600)
    feed_rate = params.get('feed_rate') or 100

    # 根据公式计算实际钻孔深度：图纸深度 + 1/3孔径 + 2mm
    drawing_depth = params.get('drawing_depth', 10)  # 图纸深度10mm
    calculated_depth = drawing_depth + diameter / 3 + 2
    actual_depth = round(calculated_depth * 10) / 10  # 保留一位小数

    gcode = []

    # 注释说明这是批量加工
    gcode.append(f'; 批量加工{len(features)}个相同孔特征')
    if params.get('recommended_tool'):
        gcode.append(f'; 推荐刀具: {params["recommended_tool"]}')
    gcode.append(f'; 孔径: {diameter}mm, 深度: {actual_depth}mm')

    # 换刀并启动主轴 - 只换一次刀
    gcode.append('')
    gcode.append(f'(批量钻孔操作 - 加工{len(features)}个孔)')
    gcode.append(f'T0{tool_number} M06 (换{tool_number}号刀 - 批量加工)')
    gcode.append(f'S{spindle_speed} M03 (主轴正转，{spindle_speed}转/分钟)')  # 使用推荐或计算的转速
    gcode.append(f'G43 H0{tool_number} Z100. (刀具长度补偿)')

    # 使用钻孔固定循环G81，先移动到第一个孔位置
    first_feature = features[0]
    x = first_feature.get('base_geometry', {}).get('center', {}).get('x', 0)
    y = first_feature.get('base_geometry', {}).get('center', {}).get('y', 0)
    gcode.append(f'G0 X{x:.3f} Y{y:.3f} (快速定位到第一个孔位置 X{x}, Y{y})')

    # 执行钻孔固定循环，钻第一个孔
    gcode.append(f'G81 G98 Z-{actual_depth:.1f} R2.0 F{feed_rate} (G81钻孔循环，钻孔深度{actual_depth:.1f}mm，参考平面R2mm，进给率F{feed_rate})')

    # 对后续孔只指定X、Y坐标，继续使用G81循环
    for i in range(1, len(features)):
        feature = features[i]
        x = feature.get('base_geometry', {}).get('center', {}).get('x', 0)
        y = feature.get('base_geometry', {}).get('center', {}).get('y', 0)
        gcode.append(f'X{x:.3f} Y{y:.3f} (继续钻孔到位置 X{x}, Y{y})')

    gcode.append('G80 (取消固定循环)')
    gcode.append('G0 Z100. (抬刀到安全高度)')

    return gcode


def generate_counterbore_gcode_batch(main_feature: Dict[str, Any], features: List[Dict[str, Any]]) -> List[str]:
    """
    生成批量沉头孔加工G代码
    
    Args:
        main_feature: 主特征
        features: 特征列表
        
    Returns:
        G代码行列表
    """
    params = main_feature.get('parameters', {})
    diameter = params.get('diameter', 5.5)  # 孔径5.5mm
    depth = params.get('depth', 14)         # 实际加工深度14mm
    counterbore_diameter = params.get('counterbore_diameter', 9)  # 沉孔径9mm
    counterbore_depth = params.get('counterbore_depth', 5.5)      # 沉孔深度5.5mm
    use_counterbore = params.get('use_counterbore', True)  # 是否使用沉孔

    # 使用推荐参数或默认参数
    center_drill_spindle = int(params.get('spindle_speed', 1200) * 0.8) if params.get('spindle_speed') else 1200  # 中心钻通常使用稍低转速
    drill_spindle = params.get('spindle_speed', 800)
    counterbore_spindle = int(params.get('spindle_speed', 600) * 0.7) if params.get('spindle_speed') else 600  # 沉孔使用较低转速
    drill_feed = params.get('feed_rate', 100)
    counterbore_feed = int(params.get('feed_rate', 80) * 0.8) if params.get('feed_rate') else 80

    # 根据公式计算实际钻孔深度：图纸深度 + 1/3孔径 + 2mm
    drawing_depth = params.get('drawing_depth', 10)  # 图纸深度10mm
    calculated_depth = drawing_depth + diameter / 3 + 2
    actual_depth = round(calculated_depth * 10) / 10  # 保留一位小数

    gcode = []

    # 注释说明这是批量加工
    gcode.append(f'; 批量加工{len(features)}个相同沉头孔特征')
    if params.get('recommended_tool'):
        gcode.append(f'; 推荐刀具: {params["recommended_tool"]}')
    gcode.append(f'; 孔径: {diameter}mm, 深度: {actual_depth}mm, 沉孔径: {counterbore_diameter}mm, 沉孔深: {counterbore_depth}mm')

    # 点孔操作 - 使用中心钻T01，批量加工
    gcode.append('')
    gcode.append('(批量点孔操作 - 使用中心钻T01)')
    gcode.append('T01 M06 (换1号刀: 中心钻 - 批量加工)')
    gcode.append(f'S{center_drill_spindle} M03 (主轴正转，{center_drill_spindle}转/分钟)')  # 使用推荐转速
    gcode.append('G43 H01 Z100. (刀具长度补偿)')

    # 使用G81固定循环进行批量点孔
    if features:
        first_feature = features[0]
        x = first_feature.get('base_geometry', {}).get('center', {}).get('x', 0)
        y = first_feature.get('base_geometry', {}).get('center', {}).get('y', 0)
        gcode.append(f'G0 X{x:.3f} Y{y:.3f} (快速定位到第一个孔位置 X{x}, Y{y})')
        gcode.append('G81 G98 Z-2.0 R2.0 F50. (G81点孔循环，深度2mm，参考平面R2mm，进给率F50.)')

        # 对后续孔只指定X、Y坐标，继续使用G81循环
        for i in range(1, len(features)):
            feature = features[i]
            x = feature.get('base_geometry', {}).get('center', {}).get('x', 0)
            y = feature.get('base_geometry', {}).get('center', {}).get('y', 0)
            gcode.append(f'X{x:.3f} Y{y:.3f} (继续点孔到位置 X{x}, Y{y})')

    gcode.append('G80 (取消固定循环)')
    gcode.append('G0 Z100. (抬刀到安全高度)')

    # 钻孔操作 - 使用钻头T02，批量加工
    gcode.append('')
    gcode.append('(批量钻孔操作 - 使用钻头T02)')
    gcode.append('T02 M06 (换2号刀: 钻头 - 批量加工)')
    gcode.append(f'S{drill_spindle} M03 (主轴正转，{drill_spindle}转/分钟)')  # 使用推荐转速
    gcode.append('G43 H02 Z100. (刀具长度补偿)')

    # 使用G83深孔钻固定循环进行批量钻孔
    if features:
        first_feature = features[0]
        x = first_feature.get('base_geometry', {}).get('center', {}).get('x', 0)
        y = first_feature.get('base_geometry', {}).get('center', {}).get('y', 0)
        gcode.append(f'G0 X{x:.3f} Y{y:.3f} (快速定位到第一个孔位置 X{x}, Y{y})')
        gcode.append(f'G83 G98 Z-{actual_depth:.1f} R2.0 Q2.0 F{drill_feed} (G83深孔钻循环，钻孔深度{actual_depth:.1f}mm，每次进给2mm)')

        # 对后续孔只指定X、Y坐标，继续使用G83循环
        for i in range(1, len(features)):
            feature = features[i]
            x = feature.get('base_geometry', {}).get('center', {}).get('x', 0)
            y = feature.get('base_geometry', {}).get('center', {}).get('y', 0)
            gcode.append(f'X{x:.3f} Y{y:.3f} (继续钻孔到位置 X{x}, Y{y})')

    gcode.append('G80 (取消固定循环)')
    gcode.append('G0 Z100. (抬刀到安全高度)')

    # 沉孔操作 - 使用沉头刀T03，批量加工（如果需要）
    if use_counterbore:
        gcode.append('')
        gcode.append('(批量沉孔操作 - 使用沉头刀T03)')
        gcode.append('T03 M06 (换3号刀: 沉头刀 - 批量加工)')
        gcode.append(f'S{counterbore_spindle} M03 (主轴正转，{counterbore_spindle}转/分钟)')  # 使用推荐转速
        gcode.append('G43 H03 Z100. (刀具长度补偿)')

        # 使用G82沉孔固定循环进行批量沉孔
        if features:
            first_feature = features[0]
            x = first_feature.get('base_geometry', {}).get('center', {}).get('x', 0)
            y = first_feature.get('base_geometry', {}).get('center', {}).get('y', 0)
            gcode.append(f'G0 X{x:.3f} Y{y:.3f} (快速定位到第一个孔位置 X{x}, Y{y})')
            gcode.append(f'G82 G98 Z-{counterbore_depth:.1f} R2.0 P2000 F{counterbore_feed} (G82沉孔循环，深度{counterbore_depth:.1f}mm，暂停2秒)')

            # 对后续孔只指定X、Y坐标，继续使用G82循环
            for i in range(1, len(features)):
                feature = features[i]
                x = feature.get('base_geometry', {}).get('center', {}).get('x', 0)
                y = feature.get('base_geometry', {}).get('center', {}).get('y', 0)
                gcode.append(f'X{x:.3f} Y{y:.3f} (继续沉孔到位置 X{x}, Y{y})')

        gcode.append('G80 (取消固定循环)')
        gcode.append('G0 Z100. (抬刀到安全高度)')

    return gcode


def generate_counterbore_gcode(feature: Dict[str, Any]) -> List[str]:
    """
    生成沉头孔的G代码（点孔、钻孔、沉孔工艺）
    
    Args:
        feature: 特征对象
        
    Returns:
        G代码行列表
    """
    params = feature.get('parameters', {})
    diameter = params.get('diameter', 5.5)  # 孔径5.5mm
    depth = params.get('depth', 14)         # 实际加工深度14mm左右
    counterbore_diameter = params.get('counterbore_diameter', 9)  # 沉孔径9mm
    counterbore_depth = params.get('counterbore_depth', 5.5)      # 沉孔深度5.5mm
    use_counterbore = params.get('use_counterbore', True)  # 是否使用沉孔

    # 使用推荐参数或默认参数
    center_drill_spindle = int(params.get('spindle_speed', 1200) * 0.8) if params.get('spindle_speed') else 1200  # 中心钻通常使用稍低转速
    drill_spindle = params.get('spindle_speed', 800)
    counterbore_spindle = int(params.get('spindle_speed', 600) * 0.7) if params.get('spindle_speed') else 600  # 沉孔使用较低转速
    drill_feed = params.get('feed_rate', 100)
    counterbore_feed = int(params.get('feed_rate', 80) * 0.8) if params.get('feed_rate') else 80

    # 根据公式计算实际钻孔深度：图纸深度 + 1/3孔径 + 2mm
    drawing_depth = params.get('drawing_depth', 10)  # 图纸深度10mm
    calculated_depth = drawing_depth + diameter / 3 + 2
    actual_depth = round(calculated_depth * 10) / 10  # 保留一位小数

    center = feature.get('base_geometry', {}).get('center', {})
    x = center.get('x', 0)
    y = center.get('y', 0)

    gcode = []

    # 注释说明此孔为加工目标
    gcode.append(f'; 加工沉头孔 - 坐标: X{x}, Y{y}')
    if params.get('recommended_tool'):
        gcode.append(f'; 推荐刀具: {params["recommended_tool"]}')

    # 点孔操作 - 使用中心钻T01
    gcode.append('')
    gcode.append('(点孔操作 - 使用中心钻T01)')
    gcode.append('T01 M06 (换1号刀: 中心钻)')
    gcode.append(f'S{center_drill_spindle} M03 (主轴正转，{center_drill_spindle}转/分钟)')  # 使用推荐转速
    gcode.append('G43 H01 Z100. (刀具长度补偿)')
    gcode.append(f'G0 X{x:.3f} Y{y:.3f} (定位到孔位置)')
    gcode.append('G81 G98 Z-2.0 R2.0 F50. (点孔，深度2mm)')  # 标准G81格式
    gcode.append('G80 (取消固定循环)')
    gcode.append('G0 Z100. (抬刀到安全高度)')

    # 钻孔操作 - 使用钻头T02
    gcode.append('')
    gcode.append('(钻孔操作 - 使用钻头T02)')
    gcode.append('T02 M06 (换2号刀: 钻头)')
    gcode.append(f'S{drill_spindle} M03 (主轴正转，{drill_spindle}转/分钟)')  # 使用推荐转速
    gcode.append('G43 H02 Z100. (刀具长度补偿)')
    gcode.append(f'G0 X{x:.3f} Y{y:.3f} (定位到孔位置)')
    gcode.append(f'G83 G98 Z-{actual_depth:.1f} R2.0 Q2.0 F{drill_feed} (深孔钻，每次进给2mm，深度{actual_depth:.1f}mm)')
    gcode.append('G80 (取消固定循环)')
    gcode.append('G0 Z100. (抬刀到安全高度)')

    # 沉孔操作 - 使用沉头刀T03
    if use_counterbore:
        gcode.append('')
        gcode.append('(沉孔操作 - 使用沉头刀T03)')
        gcode.append('T03 M06 (换3号刀: 沉头刀)')
        gcode.append(f'S{counterbore_spindle} M03 (主轴正转，{counterbore_spindle}转/分钟)')  # 使用推荐转速
        gcode.append('G43 H03 Z100. (刀具长度补偿)')
        gcode.append(f'G0 X{x:.3f} Y{y:.3f} (定位到孔位置)')
        gcode.append(f'G82 G98 Z-{counterbore_depth:.1f} R2.0 P2000 F{counterbore_feed} (沉孔，深度{counterbore_depth:.1f}mm，暂停2秒)')
        gcode.append('G80 (取消固定循环)')
        gcode.append('G0 Z100. (抬刀到安全高度)')

    return gcode


def generate_hole_gcode(feature: Dict[str, Any]) -> List[str]:
    """
    生成孔的G代码
    
    Args:
        feature: 特征对象
        
    Returns:
        G代码行列表
    """
    params = feature.get('parameters', {})
    diameter = params.get('diameter', 5.5)  # 默认孔径5.5mm
    depth = params.get('depth', 14)         # 默认实际加工深度14mm
    tool_number = params.get('tool_number', 2)  # 默认使用钻头T02
    hole_type = params.get('hole_type', 'through')  # 默认为通孔，可以是 'through' 或 'blind'

    # 使用推荐参数或默认参数
    if 'spindle_speed' in params:
        spindle_speed = params['spindle_speed']
    else:
        spindle_speed = 1200 if tool_number == 1 else 800 if tool_number == 2 else 600
    
    feed_rate = params.get('feed_rate', 100)

    # 根据公式计算实际钻孔深度：图纸深度 + 1/3孔径 + 2mm
    drawing_depth = params.get('drawing_depth', 10)  # 图纸深度10mm
    calculated_depth = drawing_depth + diameter / 3 + 2
    actual_depth = round(calculated_depth * 10) / 10  # 保留一位小数

    center = feature.get('base_geometry', {}).get('center', {})
    x = center.get('x', 0)
    y = center.get('y', 0)

    # 构建G代码列表
    gcode = []
    gcode.append(f'; 加工孔 - 坐标: X{x:.3f}, Y{y:.3f}')
    if params.get('recommended_tool'):
        gcode.append(f'; 推荐刀具: {params["recommended_tool"]}')
    gcode.append(f'T0{tool_number} M06 (换{tool_number}号刀)')
    gcode.append(f'S{spindle_speed} M03 (主轴正转，{spindle_speed}转/分钟)')  # 使用推荐或计算的转速
    gcode.append(f'G43 H0{tool_number} Z100. (刀具长度补偿)')
    gcode.append(f'G0 X{x:.3f} Y{y:.3f} (快速定位到孔位置)')

    # 使用标准G81钻孔循环格式
    if hole_type == 'through':
        # 对于通孔，使用G81钻孔循环
        gcode.append(f'G81 G98 Z-{actual_depth:.1f} R2.0 F{feed_rate} (G81钻孔循环，钻孔深度{actual_depth:.1f}mm，参考平面R2mm，进给率F{feed_rate})')
    else:
        # 对于盲孔，同样使用G81，但深度可能不同
        gcode.append(f'G81 G98 Z-{actual_depth:.1f} R2.0 F{feed_rate} (G81钻孔循环，钻孔深度{actual_depth:.1f}mm，参考平面R2mm，进给率F{feed_rate})')

    gcode.extend([
        'G80 (取消固定循环)',
        'G0 Z100. (抬刀到安全高度)'
    ])

    return gcode


def generate_pocket_gcode(feature: Dict[str, Any]) -> List[str]:
    """
    生成口袋的G代码
    
    Args:
        feature: 特征对象
        
    Returns:
        G代码行列表
    """
    params = feature.get('parameters', {})
    width = params.get('width', 20)
    length = params.get('length', 20)
    depth = params.get('depth', 10)
    feed_rate = params.get('feed_rate', 300)

    center = feature.get('base_geometry', {}).get('center', {})
    center_x = center.get('x', 0)
    center_y = center.get('y', 0)

    gcode = [
        f'; 生成口袋 - 宽度: {width}, 长度: {length}, 深度: {depth}',
        'G43 H1 ; 刀具长度补偿',
        f'G0 X{center_x - width/2} Y{center_y - length/2} ; 快速移动到口袋起点',
        f'G0 Z2 ; 快速移动到加工起始点',
        f'G1 Z-{depth} F{feed_rate} ; 开始铣削',
        f'G1 X{center_x + width/2} F{feed_rate} ; 铣削X方向',
        f'G1 Y{center_y + length/2} ; 铣削Y方向',
        f'G1 X{center_x - width/2} ; 返回X方向',
        f'G1 Y{center_y - length/2} ; 返回Y方向',
        'G0 Z2 ; 快速退刀'
    ]

    return gcode


def generate_slot_gcode(feature: Dict[str, Any]) -> List[str]:
    """
    生成槽的G代码
    
    Args:
        feature: 特征对象
        
    Returns:
        G代码行列表
    """
    params = feature.get('parameters', {})
    width = params.get('width', 5)
    length = params.get('length', 30)
    depth = params.get('depth', 5)
    feed_rate = params.get('feed_rate', 250)

    start = feature.get('base_geometry', {}).get('start', {})
    start_x = start.get('x', 0)
    start_y = start.get('y', 0)

    gcode = [
        f'; 生成槽 - 宽度: {width}, 长度: {length}, 深度: {depth}',
        'G43 H1 ; 刀具长度补偿',
        f'G0 X{start_x} Y{start_y} ; 快速移动到槽起点',
        f'G0 Z2 ; 快速移动到加工起始点',
        f'G1 Z-{depth} F{feed_rate} ; 开始铣槽',
        f'G1 X{start_x + length} F{feed_rate} ; 铣槽',
        'G0 Z2 ; 快速退刀'
    ]

    return gcode


def generate_chamfer_gcode(feature: Dict[str, Any]) -> List[str]:
    """
    生成倒角的G代码
    
    Args:
        feature: 特征对象
        
    Returns:
        G代码行列表
    """
    params = feature.get('parameters', {})
    angle = params.get('angle', 45)
    distance = params.get('distance', 2)

    gcode = [
        f'; 生成倒角 - 角度: {angle}, 距离: {distance}',
        '; 倒角操作通常在路径转角处进行'
    ]

    return gcode


def generate_fillet_gcode(feature: Dict[str, Any]) -> List[str]:
    """
    生成圆角的G代码
    
    Args:
        feature: 特征对象
        
    Returns:
        G代码行列表
    """
    params = feature.get('parameters', {})
    radius = params.get('radius', 5)

    gcode = [
        f'; 生成圆角 - 半径: {radius}',
        '; 圆角操作通常在路径转角处进行'
    ]

    return gcode


def generate_generic_feature_gcode(feature: Dict[str, Any]) -> List[str]:
    """
    生成通用特征的G代码
    
    Args:
        feature: 特征对象
        
    Returns:
        G代码行列表
    """
    feature_type = feature.get('feature_type', 'unknown')
    return [
        f'; 通用特征操作: {feature_type}',
        '; 此特征类型暂无具体的G代码生成逻辑'
    ]


def generate_thread_gcode(feature: Dict[str, Any]) -> List[str]:
    """
    生成螺纹的G代码
    
    Args:
        feature: 特征对象
        
    Returns:
        G代码行列表
    """
    params = feature.get('parameters', {})
    diameter = params.get('diameter', 6)  # 默认螺纹直径
    pitch = params.get('pitch', 1)       # 默认螺距
    depth = params.get('depth', 10)      # 默认螺纹深度
    thread_type = params.get('thread_type', 'internal')  # 默认内螺纹

    center = feature.get('base_geometry', {}).get('center', {})
    x = center.get('x', 0)
    y = center.get('y', 0)

    gcode = [
        f'; 生成{ "内" if thread_type == "internal" else "外" }螺纹 - 直径: {diameter}, 螺距: {pitch}, 深度: {depth}',
        '; 螺纹加工通常使用G33或G76指令',
        f'G0 X{x:.3f} Y{y:.3f} ; 定位到螺纹孔位置',
        f'G84.2 Z-{depth} F{diameter/pitch} ; 攻丝循环 (根据螺距计算进给)',
        'G80 ; 取消固定循环'
    ]

    return gcode


def generate_surface_finish_gcode(feature: Dict[str, Any]) -> List[str]:
    """
    生成表面光洁度相关的G代码
    
    Args:
        feature: 特征对象
        
    Returns:
        G代码行列表
    """
    params = feature.get('parameters', {})
    roughness = params.get('roughness', 'Ra3.2')  # 默认粗糙度
    operation = params.get('operation', 'finish')  # 默认精加工
    feed_rate = params.get('feed_rate', 200)      # 默认进给率

    gcode = [
        f'; 表面光洁度要求: {roughness}',
        f'; 执行{operation}加工以达到要求的表面质量',
        f'; 使用较小的进给率{feed_rate}以保证表面质量',
        '; 通常需要使用特殊的刀具和工艺参数'
    ]

    return gcode


def generate_tolerance_gcode(feature: Dict[str, Any]) -> List[str]:
    """
    生成形位公差相关的G代码
    
    Args:
        feature: 特征对象
        
    Returns:
        G代码行列表
    """
    params = feature.get('parameters', {})
    tolerance_type = params.get('type', 'position')  # 默认位置公差
    tolerance_value = params.get('value', 0.1)      # 默认公差值
    datum = params.get('datum', 'A')               # 默认基准

    gcode = [
        f'; 形位公差要求: {tolerance_type}公差 {tolerance_value}mm',
        f'; 相对基准{datum}进行加工',
        '; 加工时需确保达到指定的形位精度要求',
        '; 可能需要使用特殊的加工工艺或检测手段'
    ]

    return gcode


if __name__ == "__main__":
    # 测试代码
    test_feature = {
        'id': 'test_hole_1',
        'feature_type': 'hole',
        'base_geometry': {
            'center': {'x': 10, 'y': 10}
        },
        'parameters': {
            'diameter': 5.5,
            'depth': 14,
            'drawing_depth': 10,
            'tool_number': 2
        }
    }
    
    gcode_block = generate_feature_gcode(test_feature)
    print("生成的G代码块:")
    for line in gcode_block['code']:
        print(f"  {line}")