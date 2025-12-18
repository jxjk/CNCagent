
"""
模拟输出模块
"""
import re
import math
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from .validation import validate_gcode_safety, detect_collisions


def start_simulation(gcode_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    启动模拟
    
    Args:
        gcode_blocks: G代码块列表
        
    Returns:
        模拟结果
    """
    if not isinstance(gcode_blocks, list):
        raise ValueError('G代码块列表无效')

    # 模拟处理时间
    start_time = datetime.now()

    # 模拟执行G代码
    simulation_results = {
        'id': f'sim_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}',
        'status': 'completed',
        'start_time': datetime.now().isoformat(),
        'end_time': None,
        'execution_time': 0,
        'total_commands': len(gcode_blocks),
        'processed_commands': 0,
        'progress': 0,
        'tool_paths': [],
        'collision_checks': [],
        'material_removal': 0,
        'estimated_time': 0,
        'warnings': [],
        'errors': [],
        'statistics': {
            'total_path_length': 0,
            'total_cutting_time': 0,
            'total_air_time': 0,
            'rapid_moves': 0,
            'feed_moves': 0,
            'spindle_hours': 0
        }
    }

    # 模拟处理每个G代码块
    for i, block in enumerate(gcode_blocks):
        # 模拟处理时间
        processing_time = 0.05  # 50ms per block (模拟)
        simulation_results['processed_commands'] += 1
        simulation_results['progress'] = round((i + 1) / len(gcode_blocks) * 100)

        # 生成工具路径（简化的模拟）
        if block.get('type') == 'feature_operation':
            tool_path = generate_tool_path(block)
            if tool_path:
                simulation_results['tool_paths'].append(tool_path)

                # 累计统计信息
                simulation_results['statistics']['total_path_length'] += tool_path.get('length', 0)
                simulation_results['statistics']['total_cutting_time'] += tool_path.get('cutting_time', 0)
                simulation_results['statistics']['total_air_time'] += tool_path.get('air_time', 0)
                simulation_results['statistics']['rapid_moves'] += tool_path.get('rapid_moves', 0)
                simulation_results['statistics']['feed_moves'] += tool_path.get('feed_moves', 0)

                # 计算主轴运行时间（基于进给移动时间）
                if tool_path.get('spindle_speed', 0) > 0:
                    simulation_results['statistics']['spindle_hours'] += tool_path.get('cutting_time', 0) / 3600  # 转换为小时

        # 进行安全和碰撞验证
        if block.get('code') and isinstance(block['code'], list):
            safety_validation = validate_gcode_safety(block['code'])
            if safety_validation.get('errors'):
                simulation_results['errors'].extend(safety_validation['errors'])
            if safety_validation.get('warnings'):
                simulation_results['warnings'].extend(safety_validation['warnings'])

            # 进行碰撞检测
            collision_result = detect_collisions(block['code'])
            if collision_result.get('has_collisions'):
                simulation_results['collision_checks'].append({
                    'block_id': block.get('id'),
                    'collisions': collision_result.get('collisions', []),
                    'timestamp': datetime.now().isoformat()
                })

        # 检查潜在问题
        issues = check_for_issues(block)
        if issues.get('warnings'):
            simulation_results['warnings'].extend(issues['warnings'])
        if issues.get('errors'):
            simulation_results['errors'].extend(issues['errors'])

    simulation_results['end_time'] = datetime.now().isoformat()
    execution_time = (datetime.fromisoformat(simulation_results['end_time'].replace('Z', '+00:00')) - 
                      datetime.fromisoformat(simulation_results['start_time'].replace('Z', '+00:00'))).total_seconds()
    simulation_results['execution_time'] = execution_time
    simulation_results['estimated_time'] = simulation_results['statistics']['total_cutting_time'] + simulation_results['statistics']['total_air_time']

    # 计算材料移除量（基于路径长度和切削参数的模拟）
    # 这里使用简化的模拟，实际应用中需要更复杂的模型
    avg_path_length = simulation_results['statistics']['total_path_length'] / max(len(simulation_results['tool_paths']), 1)
    simulation_results['material_removal'] = avg_path_length * 0.5  # 简化的材料移除计算

    # 计算总体效率指标
    simulation_results['efficiency_metrics'] = {
        'path_optimization_ratio': simulation_results['statistics']['total_path_length'] / max(
            simulation_results['statistics']['rapid_moves'] + simulation_results['statistics']['feed_moves'], 1),
        'air_to_cut_ratio': simulation_results['statistics']['total_air_time'] / max(
            simulation_results['statistics']['total_cutting_time'], 1),
        'average_feed_rate': simulation_results['statistics']['total_path_length'] / max(
            simulation_results['statistics']['total_cutting_time'], 1)
    }

    return simulation_results


def generate_tool_path(gcode_block: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    生成详细的工具路径
    
    Args:
        gcode_block: G代码块
        
    Returns:
        工具路径信息
    """
    if not gcode_block or not isinstance(gcode_block.get('code'), list):
        return None

    # 初始化工具路径对象
    path = {
        'id': f'path_{gcode_block.get("id", "unknown")}',
        'feature_id': gcode_block.get('feature_id'),
        'feature_type': gcode_block.get('feature_type'),
        'commands': len(gcode_block.get('code', [])),
        'start': {'x': 0, 'y': 0, 'z': 0},
        'end': {'x': 0, 'y': 0, 'z': 0},
        'length': 0,
        'estimated_time': 0,
        'tool': gcode_block.get('parameters', {}).get('recommended_tool', 'default_tool'),
        'spindle_speed': gcode_block.get('parameters', {}).get('spindle_speed', 0),
        'feed_rate': gcode_block.get('parameters', {}).get('feed_rate', 0),
        'operations': [],
        'rapid_moves': 0,
        'feed_moves': 0,
        'cutting_time': 0,
        'air_time': 0
    }

    # 当前位置
    current_position = {'x': 0, 'y': 0, 'z': 0}
    current_feed_rate = 0
    current_spindle_speed = 0
    total_cutting_time = 0
    total_air_time = 0

    # 解析G代码
    for line in gcode_block.get('code', []):
        # 跳过注释和空行
        if not line or line.strip().startswith(';'):
            continue

        # 解析坐标
        x_match = re.search(r'X\s*(-?\d+\.?\d*)', line, re.IGNORECASE)
        y_match = re.search(r'Y\s*(-?\d+\.?\d*)', line, re.IGNORECASE)
        z_match = re.search(r'Z\s*(-?\d+\.?\d*)', line, re.IGNORECASE)
        f_match = re.search(r'F\s*(\d+\.?\d*)', line, re.IGNORECASE)
        s_match = re.search(r'S\s*(\d+\.?\d*)', line, re.IGNORECASE)

        # 检查G代码类型
        is_rapid = 'G0' in line.upper() or 'G00' in line.upper()
        is_feed = 'G1' in line.upper() or 'G01' in line.upper()
        is_arc_cw = 'G2' in line.upper() or 'G02' in line.upper()
        is_arc_ccw = 'G3' in line.upper() or 'G03' in line.upper()

        # 更新当前参数
        if f_match:
            current_feed_rate = float(f_match.group(1))
        if s_match:
            current_spindle_speed = float(s_match.group(1))

        # 如果有坐标变化，记录操作
        if x_match or y_match or z_match:
            # 保存当前位置作为起点
            previous_position = current_position.copy()

            # 更新当前位置
            if x_match:
                current_position['x'] = float(x_match.group(1))
            if y_match:
                current_position['y'] = float(y_match.group(1))
            if z_match:
                current_position['z'] = float(z_match.group(1))

            # 计算移动距离
            dx = current_position['x'] - previous_position['x']
            dy = current_position['y'] - previous_position['y']
            dz = current_position['z'] - previous_position['z']
            distance = math.sqrt(dx * dx + dy * dy + dz * dz)

            # 计算移动时间
            move_time = 0
            if is_rapid:
                # 快速移动时间估算（假设快速移动速度为5000 mm/min）
                move_time = distance / 5000 * 60  # 转换为秒
                path['rapid_moves'] += 1
            elif is_feed or is_arc_cw or is_arc_ccw:
                # 进给移动时间
                if current_feed_rate > 0:
                    move_time = distance / current_feed_rate * 60  # 转换为秒
                    total_cutting_time += move_time
                path['feed_moves'] += 1

            # 记录操作
            operation = {
                'command': line.strip(),
                'start': previous_position.copy(),
                'end': current_position.copy(),
                'distance': distance,
                'move_time': move_time,
                'feed_rate': current_feed_rate,
                'spindle_speed': current_spindle_speed,
                'type': 'rapid' if is_rapid else 'linear_feed' if is_feed else 'arc_cw' if is_arc_cw else 'arc_ccw' if is_arc_ccw else 'other'
            }

            path['operations'].append(operation)

            # 累计总长度
            path['length'] += distance

            # 累计时间
            if is_rapid:
                total_air_time += move_time

    # 设置起始和结束位置
    if path['operations']:
        path['start'] = path['operations'][0]['start'].copy()
        path['end'] = path['operations'][-1]['end'].copy()

    # 计算总时间
    path['cutting_time'] = total_cutting_time
    path['air_time'] = total_air_time
    path['estimated_time'] = total_cutting_time + total_air_time

    return path


def check_for_issues(gcode_block: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    检查潜在问题
    
    Args:
        gcode_block: G代码块
        
    Returns:
        检查结果
    """
    issues = {
        'warnings': [],
        'errors': []
    }

    if not gcode_block or not isinstance(gcode_block.get('code'), list):
        issues['errors'].append('G代码块格式无效')
        return issues

    for line in gcode_block.get('code', []):
        # 检查潜在的错误
        if 'G91' in line.upper() and 'G90' not in line.upper():
            issues['warnings'].append('使用增量模式可能影响后续操作')

        if 'G54' in line.upper() or 'G55' in line.upper() or 'G56' in line.upper():
            issues['warnings'].append('使用工件坐标系，请确保已设置正确')

        # 检查过高的进给率
        f_match = re.search(r'F(\d+)', line)
        if f_match:
            feed_rate = int(f_match.group(1))
            if feed_rate > 2000:
                issues['warnings'].append(f'进给率 {feed_rate} 可能过高')

        # 检查过大的移动距离
        x_match = re.search(r'X(-?\d+\.?\d*)', line)
        y_match = re.search(r'Y(-?\d+\.?\d*)', line)
        z_match = re.search(r'Z(-?\d+\.?\d*)', line)

        if x_match and abs(float(x_match.group(1))) > 1000:
            issues['warnings'].append(f'X轴移动距离过大: {x_match.group(1)}')
        if y_match and abs(float(y_match.group(1))) > 1000:
            issues['warnings'].append(f'Y轴移动距离过大: {y_match.group(1)}')
        if z_match and abs(float(z_match.group(1))) > 500:
            issues['warnings'].append(f'Z轴移动距离过大: {z_match.group(1)}')

    return issues


def variable_driven_simulation(gcode_blocks: List[Dict[str, Any]], variable_values: Dict[str, Any]) -> Dict[str, Any]:
    """
    变量驱动模拟
    
    Args:
        gcode_blocks: G代码块列表
        variable_values: 变量值字典
        
    Returns:
        模拟结果
    """
    if not isinstance(gcode_blocks, list):
        raise ValueError('G代码块列表无效')

    if not variable_values or not isinstance(variable_values, dict):
        raise ValueError('变量值参数无效')

    # 创建G代码的副本以进行变量替换
    modified_blocks = []
    for block in gcode_blocks:
        if isinstance(block.get('code'), list):
            modified_code = []
            for line in block.get('code', []):
                modified_line = line
                
                # 替换宏变量（格式为 #1, #2, #3 等）
                for var_name, value in variable_values.items():
                    # 在实际应用中，这里会根据具体的变量映射进行替换
                    # 简化的模拟：查找并替换变量引用
                    import re
                    # 使用更安全的替换方法，避免替换注释中的内容
                    modified_line = re.sub(rf'\b{re.escape(var_name)}\b', str(value), modified_line)
                
                modified_code.append(modified_line)
            
            modified_blocks.append({
                **block,
                'code': modified_code
            })
        else:
            modified_blocks.append(block)

    # 执行修改后的G代码的模拟
    return start_simulation(modified_blocks)


def export_code(gcode_blocks: List[Dict[str, Any]], output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    导出代码
    
    Args:
        gcode_blocks: G代码块列表
        output_path: 输出路径
        
    Returns:
        导出结果
    """
    if not isinstance(gcode_blocks, list):
        raise ValueError('G代码块列表无效')

    # 验证输出路径
    if output_path and isinstance(output_path, str):
        import os
        
        # 确保输出目录存在
        directory = os.path.dirname(output_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # 生成完整的G代码字符串
        full_code = ''
        full_code += '; CNCagent Generated G-Code\n'
        full_code += f'; Generated on: {datetime.now().isoformat()}\n'
        full_code += '\n'
        
        for block in gcode_blocks:
            if isinstance(block.get('code'), list):
                full_code += f'; Block: {block.get("id", "unknown")}\n'
                for line in block['code']:
                    full_code += line + '\n'
                full_code += '\n'
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_code)
        
        return {
            'success': True,
            'output_path': output_path,
            'file_size': len(full_code.encode('utf-8')),
            'line_count': len(full_code.split('\n'))
        }
    else:
        # 如果没有提供输出路径，返回G代码字符串
        full_code = ''
        for block in gcode_blocks:
            if isinstance(block.get('code'), list):
                for line in block['code']:
                    full_code += line + '\n'
        
        return {
            'success': True,
            'gcode': full_code,
            'line_count': len(full_code.split('\n'))
        }


if __name__ == "__main__":
    # 测试代码
    test_gcode_blocks = [
        {
            'id': 'test_block_1',
            'type': 'feature_operation',
            'code': [
                'G0 X0 Y0',
                'G1 Z-5 F100',
                'G1 X10 Y10',
                'G0 Z100'
            ],
            'parameters': {
                'recommended_tool': 'Drill Bit',
                'spindle_speed': 1200,
                'feed_rate': 100
            }
        }
    ]
    
    result = start_simulation(test_gcode_blocks)
    print("模拟结果:")
    print(f"  总处理命令: {result['total_commands']}")
    print(f"  进度: {result['progress']}%")
    print(f"  警告: {len(result['warnings'])}")
    print(f"  错误: {len(result['errors'])}")
    print(f"  工具路径数: {len(result['tool_paths'])}")
    
    if result['tool_paths']:
        path = result['tool_paths'][0]
        print(f"  路径长度: {path['length']:.2f}mm")
        print(f"  快速移动: {path['rapid_moves']}")
        print(f"  进给移动: {path['feed_moves']}")
