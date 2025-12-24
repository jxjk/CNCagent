"""
模拟输出模块
用于生成加工模拟报告和可视化结果
"""
import os
from typing import List, Dict
from datetime import datetime

def generate_simulation_report(features: List[Dict], 
                             description_analysis: Dict, 
                             nc_program: str, 
                             output_path: str = "simulation_report.txt"):
    """
    生成加工模拟报告
    
    Args:
        features: 识别出的特征列表
        description_analysis: 用户描述分析结果
        nc_program: 生成的NC程序
        output_path: 报告输出路径
    """
    import logging
    report = []
    report.append("=" * 60)
    report.append("CNC 加工模拟报告")
    report.append("=" * 60)
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # 添加特征信息
    report.append("识别出的几何特征:")
    report.append("-" * 30)
    for i, feature in enumerate(features):
        report.append(f"特征 {i+1}:")
        report.append(f"  类型: {feature['shape']}")
        report.append(f"  位置: ({feature['center'][0]:.2f}, {feature['center'][1]:.2f})")
        report.append(f"  尺寸: {feature.get('dimensions', 'N/A')}")
        report.append(f"  面积: {feature['area']:.2f}")
        report.append("")
    
    # 添加用户描述分析结果
    report.append("用户描述分析:")
    report.append("-" * 30)
    report.append(f"加工类型: {description_analysis['processing_type']}")
    report.append(f"所需刀具: {description_analysis['tool_required']}")
    report.append(f"加工深度: {description_analysis.get('depth', 'N/A')} mm")
    report.append(f"进给速度: {description_analysis.get('feed_rate', 'N/A')} mm/min")
    report.append(f"主轴转速: {description_analysis.get('spindle_speed', 'N/A')} RPM")
    report.append(f"材料: {description_analysis.get('material', 'N/A')}")
    report.append(f"精度要求: {description_analysis.get('precision', 'N/A')}")
    report.append("")
    
    # 添加NC程序统计
    lines = nc_program.split('\n')
    g_codes = [line for line in lines if line.strip().startswith('G')]
    m_codes = [line for line in lines if line.strip().startswith('M')]
    tool_changes = [line for line in lines if 'M06' in line]
    
    report.append("NC程序统计:")
    report.append("-" * 30)
    report.append(f"总行数: {len(lines)}")
    report.append(f"G代码行数: {len(g_codes)}")
    report.append(f"M代码行数: {len(m_codes)}")
    report.append(f"换刀次数: {len(tool_changes)}")
    report.append("")
    
    # 添加NC程序预览
    report.append("NC程序预览 (前20行):")
    report.append("-" * 30)
    preview_lines = lines[:20]
    for line in preview_lines:
        report.append(f"  {line}")
    
    if len(lines) > 20:
        report.append(f"  ... 还有 {len(lines) - 20} 行")
    
    report.append("")
    report.append("=" * 60)
    report.append("报告结束")
    report.append("=" * 60)
    
    # 保存报告
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    logging.info(f"模拟报告已生成: {output_path}")

def visualize_features(features: List[Dict], output_path: str = "feature_visualization.html"):
    """
    生成特征可视化HTML文件
    
    Args:
        features: 识别出的特征列表
        output_path: 输出文件路径
    """
    import logging
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>几何特征可视化</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .feature { margin: 10px 0; padding: 10px; border: 1px solid #ccc; border-radius: 5px; }
        .shape { display: inline-block; margin-right: 10px; }
        .circle { width: 50px; height: 50px; border-radius: 50%; background-color: lightblue; }
        .rectangle { width: 60px; height: 40px; background-color: lightgreen; }
        .triangle { width: 0; height: 0; border-left: 25px solid transparent; border-right: 25px solid transparent; border-bottom: 50px solid lightcoral; }
        .info { display: inline-block; }
    </style>
</head>
<body>
    <h1>识别的几何特征</h1>
    <div class="container">
"""
    
    for i, feature in enumerate(features):
        shape_class = ""
        if feature['shape'] == 'circle':
            shape_class = 'circle'
        elif feature['shape'] in ['rectangle', 'square']:
            shape_class = 'rectangle'
        elif feature['shape'] == 'triangle':
            shape_class = 'triangle'
        else:
            shape_class = 'rectangle'  # 默认为矩形
        
        html_content += f"""
        <div class="feature">
            <div class="shape {shape_class}"></div>
            <div class="info">
                <h3>特征 {i+1}</h3>
                <p><strong>类型:</strong> {feature['shape']}</p>
                <p><strong>位置:</strong> ({feature['center'][0]:.2f}, {feature['center'][1]:.2f})</p>
                <p><strong>尺寸:</strong> {feature.get('dimensions', 'N/A')}</p>
                <p><strong>面积:</strong> {feature['area']:.2f}</p>
            </div>
        </div>
"""
    
    html_content += """
    </div>
</body>
</html>
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logging.info(f"特征可视化已生成: {output_path}")