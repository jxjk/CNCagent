#!/usr/bin/env python3
"""
CNCagent - Python Version CNC Code Assistant
Main application entry and state management
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import sys
import os
# 添加src目录toPython路径，以便能够导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.project_initialization import Project, initialize_project, clear_workspace, handle_drawing_import
from modules.subprocesses.pdf_parsing_process import pdf_parsing_process
from modules.feature_definition import select_feature, start_feature_definition, select_feature_type, associate_macro_variable
from modules.gcode_generation import trigger_gcode_generation
from modules.simulation_output import start_simulation, variable_driven_simulation, export_code
from modules.validation import validate_gcode_blocks, validate_gcode_syntax, validate_gcode_safety, detect_collisions


class CNCStateManager:
    """
    CNC State Manager, manages state transitions for the entire CNC machining process
    """
    def __init__(self):
        self.state = 'waiting_import'  # 等待导入
        self.project = None
        self.selected_feature = None  # 保持兼容性
        self.selected_features = []  # 支持多个特征选择
        self.state_history = ['waiting_import']  # 状态历史，用于回溯
        self.max_state_history = 10  # 最大状态历史记录数

    def set_state(self, new_state: str) -> None:
        """
        Set new state
        """
        if not new_state or not isinstance(new_state, str):
            print('Invalid state value')
            return

        valid_states = [
            'waiting_import', 'drawing_loaded', 'processing', 'ready',
            'feature_selected', 'defining_feature', 'code_generated',
            'simulation_running', 'code_exported', 'error'
        ]

        if new_state not in valid_states:
            print(f'Invalid state: {new_state}')
            return

        print(f'State transition from {self.state} to {new_state}')
        self.state = new_state

        # 更新状态历史
        self.state_history.append(new_state)
        if len(self.state_history) > self.max_state_history:
            self.state_history.pop(0)

    def get_allowed_transitions(self) -> List[str]:
        """
        Get allowed state transitions
        """
        transitions = {
            'waiting_import': ['drawing_loaded', 'error'],
            'drawing_loaded': ['processing', 'error'],
            'processing': ['ready', 'error'],
            'ready': ['feature_selected', 'code_generated', 'error'],
            'feature_selected': ['defining_feature', 'ready', 'feature_selected', 'error'],  # Allow staying in same state to select more features
            'defining_feature': ['ready', 'code_generated', 'feature_selected', 'error'],  # Allow returning to feature selection state
            'code_generated': ['simulation_running', 'code_exported', 'error'],
            'simulation_running': ['code_generated', 'code_exported', 'error'],
            'code_exported': ['waiting_import'],
            'error': ['waiting_import']
        }

        return transitions.get(self.state, [])

    def start_new_project(self) -> Dict[str, Any]:
        """
        Start a new project
        """
        try:
            clear_workspace()
            self.project = initialize_project()
            self.selected_feature = None
            self.selected_features = []  # Reset multiple feature selection
            self.set_state('waiting_import')
            print('New project initialized')
            return {'success': True}
        except Exception as e:
            print(f'Failed to initialize new project: {e}')
            self.set_state('error')
            return {'success': False, 'error': str(e)}

    def handle_import(self, file_path: str) -> Dict[str, Any]:
        """
        处理图纸导入
        """
        try:
            # 输入验证
            if not file_path or not isinstance(file_path, str):
                raise ValueError('Invalid file path')

            self.project = handle_drawing_import(file_path)
            self.set_state('drawing_loaded')

            # 等待PDF解析流程完成
            result = self.process_drawing()
            return {'success': True, 'project': self.project.serialize() if self.project else None}
        except Exception as e:
            print(f'Drawing import failed: {e}')
            self.set_state('error')
            return {'success': False, 'error': str(e)}

    def process_drawing(self) -> Dict[str, Any]:
        """
        处理图纸解析
        """
        try:
            if not self.project or not self.project.file_path:
                raise ValueError('项目or项目Invalid file path')

            print('Starting to parse drawing...')
            self.set_state('processing')

            parsing_result = pdf_parsing_process(self.project.file_path)

            # 更新项目数据
            self.project.drawing_info = parsing_result.get('drawing_info', {})
            self.project.geometry_elements = parsing_result.get('geometry_elements', [])
            self.project.dimensions = parsing_result.get('dimensions', [])
            self.project.tolerances = parsing_result.get('tolerances', [])  # 形位公差
            self.project.surface_finishes = parsing_result.get('surface_finishes', [])  # 表面光洁度
            self.project.updated_at = datetime.now()

            self.set_state('ready')
            print('Drawing parsing completed')
            return {'success': True, 'parsing_result': parsing_result}
        except Exception as e:
            print(f'Drawing parsing failed: {e}')
            self.set_state('error')
            return {'success': False, 'error': str(e)}

    def handle_feature_selection(self, x: float, y: float) -> Dict[str, Any]:
        """
        用户选择特征
        """
        try:
            # 输入验证
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                raise ValueError('Coordinate parameters must be numbers')

            # 现在允许在 'ready' 和 'feature_selected' 状态下选择特征
            if self.state != 'ready' and self.state != 'feature_selected':
                raise ValueError(f'Current state {self.state} does not allow feature selection, requires "ready" or "feature_selected" 状态')

            if not self.project:
                raise ValueError('Project not initialized')

            selection = select_feature(self.project, x, y)
            if selection and selection.get('element'):
                # 如果找to了确切的元素，添加to选中的特征列表中
                self.selected_feature = selection  # 保持向后兼容
                # 检查是否已经选择过这个元素，避免重复添加
                existing_index = next((i for i, f in enumerate(self.selected_features) 
                                       if f.get('element') and f['element'].get('id') == selection['element'].get('id')), -1)
                if existing_index == -1:
                    self.selected_features.append(selection)
                else:
                    # 如果已存在，则更新该元素
                    self.selected_features[existing_index] = selection
                # 保持在 feature_selected 状态，允许选择多个特征
                self.set_state('feature_selected')
                return {
                    **selection,
                    'selected_features_count': len(self.selected_features)  # 返回当前选中的特征总数
                }
            else:
                # 如果没有找to确切的元素，但有目标坐标，也添加to选中的特征列表中
                # 创建一个虚拟选择对象并更新状态
                virtual_selection = {
                    'element': None,
                    'coordinates': {'x': x, 'y': y},
                    'timestamp': datetime.now().isoformat(),
                    'message': 'No matching geometric element found, but target coordinates recorded',
                    'success': True
                }
                self.selected_feature = virtual_selection  # 保持向后兼容
                self.selected_features.append(virtual_selection)  # 添加to多选列表
                # 保持在 feature_selected 状态，允许选择多个特征
                self.set_state('feature_selected')
                return {
                    **virtual_selection,
                    'selected_features_count': len(self.selected_features)  # 返回当前选中的特征总数
                }
        except Exception as e:
            print(f'Error selecting feature: {e}')
            return {'success': False, 'error': str(e)}

    def start_feature_definition(self):
        """
        启动特征定义（为当前选中的单个特征创建定义）
        """
        try:
            if self.state != 'feature_selected':
                raise ValueError(f'Current state {self.state} 不允许启动特征定义，需要 "feature_selected" 状态')

            if not self.selected_feature:
                raise ValueError('No selected feature')

            if not self.project:
                raise ValueError('Project not initialized')

            # 如果没有找to确切的元素，但有目标坐标，创建一个虚拟元素
            element_to_use = self.selected_feature.get('element')
            if not element_to_use:
                # 创建虚拟圆元素用于指定坐标处的孔
                element_to_use = {
                    'id': f'virtual_circle_{int(datetime.now().timestamp())}_{hash(str(self.selected_feature["coordinates"])) % 10000}',
                    'type': 'circle',
                    'center': self.selected_feature['coordinates'],
                    'radius': 2.75,  # 默认半径对应5.5mm直径
                    'text': f'Target hole at X{self.selected_feature["coordinates"]["x"]}, Y{self.selected_feature["coordinates"]["y"]}',
                    'is_virtual': True  # 标记为虚拟元素
                }

                # 添加to项目的几何元素中
                if not isinstance(self.project.geometry_elements, list):
                    self.project.geometry_elements = []
                self.project.geometry_elements.append(element_to_use)

            feature = start_feature_definition(
                self.project,
                element_to_use,
                self.selected_feature.get('dimensions', [])
            )

            if feature:
                self.project.features.append(feature)
                self.project.updated_at = datetime.now()
                self.set_state('defining_feature')
                return feature

            return None
        except Exception as e:
            print(f'Error starting feature definition: {e}')
            return {'success': False, 'error': str(e)}

    def start_feature_definition_batch(self):
        """
        批量启动特征定义（为所有选中的特征创建定义）
        """
        try:
            if self.state != 'feature_selected':
                raise ValueError(f'Current state {self.state} 不允许启动特征定义，需要 "feature_selected" 状态')

            if len(self.selected_features) == 0:
                raise ValueError('No selected feature')

            if not self.project:
                raise ValueError('Project not initialized')

            created_features = []

            for selected_feature in self.selected_features:
                element_to_use = selected_feature.get('element')
                if not element_to_use:
                    # 创建虚拟圆元素用于指定坐标处的孔
                    element_to_use = {
                        'id': f'virtual_circle_{int(datetime.now().timestamp())}_{hash(str(selected_feature["coordinates"])) % 10000}',
                        'type': 'circle',
                        'center': selected_feature['coordinates'],
                        'radius': 2.75,  # 默认半径对应5.5mm直径
                        'text': f'Target hole at X{selected_feature["coordinates"]["x"]}, Y{selected_feature["coordinates"]["y"]}',
                        'is_virtual': True  # 标记为虚拟元素
                    }

                    # 添加to项目的几何元素中
                    if not isinstance(self.project.geometry_elements, list):
                        self.project.geometry_elements = []
                    self.project.geometry_elements.append(element_to_use)

                feature = start_feature_definition(
                    self.project,
                    element_to_use,
                    selected_feature.get('dimensions', [])
                )

                if feature:
                    self.project.features.append(feature)
                    created_features.append(feature)

            if created_features:
                self.project.updated_at = datetime.now()
                self.set_state('defining_feature')
                return created_features

            return []
        except Exception as e:
            print(f'批量Error starting feature definition: {e}')
            return {'success': False, 'error': str(e)}

    def clear_selected_features(self):
        """
        清空已选择的特征
        """
        self.selected_feature = None
        self.selected_features = []
        # 如果Current state是 feature_selected，则回to ready 状态
        if self.state == 'feature_selected':
            self.set_state('ready')

    def remove_selected_feature(self, feature_index: int):
        """
        从已选择的特征中移除指定的特征
        """
        if 0 <= feature_index < len(self.selected_features):
            self.selected_features.pop(feature_index)
            # 如果移除了所有特征，更新状态
            if len(self.selected_features) == 0:
                self.selected_feature = None
                if self.state == 'feature_selected':
                    self.set_state('ready')
            else:
                # 否则，更新当前选中的特征为列表中的最后一个
                self.selected_feature = self.selected_features[-1]

    def select_feature_type(self, feature_id: str, feature_type: str):
        """
        选择特征类型
        """
        try:
            # 输入验证
            if not feature_id or not isinstance(feature_id, str):
                raise ValueError('Feature ID invalid')

            if not feature_type or not isinstance(feature_type, str):
                raise ValueError('Feature type invalid')

            if not self.project or not isinstance(self.project.features, list):
                raise ValueError('项目or项目特征列表无效')

            feature = next((f for f in self.project.features if f.get('id') == feature_id), None)
            if feature:
                select_feature_type(feature, feature_type)
                self.project.updated_at = datetime.now()
                return feature

            raise ValueError(f'未找toID为 {feature_id} 的特征')
        except Exception as e:
            print(f'Error selecting feature type: {e}')
            return {'success': False, 'error': str(e)}

    def associate_macro_variable(self, feature_id: str, dimension_id: str, variable_name: str):
        """
        关联宏变量
        """
        try:
            # 输入验证
            if not feature_id or not isinstance(feature_id, str):
                raise ValueError('Feature ID invalid')

            if not dimension_id or not isinstance(dimension_id, str):
                raise ValueError('Dimension ID invalid')

            if not variable_name or not isinstance(variable_name, str):
                raise ValueError('Variable name invalid')

            if not self.project or not isinstance(self.project.features, list):
                raise ValueError('项目or项目特征列表无效')

            feature = next((f for f in self.project.features if f.get('id') == feature_id), None)
            if feature:
                associate_macro_variable(feature, dimension_id, variable_name)
                self.project.updated_at = datetime.now()
                return feature

            raise ValueError(f'未找toID为 {feature_id} 的特征')
        except Exception as e:
            print(f'Error associating macro variable: {e}')
            return {'success': False, 'error': str(e)}

    def generate_gcode(self):
        """
        生成G代码
        """
        try:
            if self.state != 'ready' and self.state != 'defining_feature':
                raise ValueError(f'Current state {self.state} 不允许生成G代码')

            if not self.project:
                raise ValueError('Project not initialized')

            self.project.gcode_blocks = trigger_gcode_generation(self.project)

            # 验证生成的G代码
            gcode_validation = validate_gcode_blocks(self.project.gcode_blocks)
            if gcode_validation.get('errors') and len(gcode_validation['errors']) > 0:
                print(f'G code validation failed: {gcode_validation["errors"]}')
                self.set_state('error')
                return {'success': False, 'error': f'G code validation failed: {"; ".join(gcode_validation["errors"])}'}

            # 对每块G代码进行语法验证和安全验证
            has_collision_risk = False
            for block in self.project.gcode_blocks:
                if isinstance(block.get('code'), list):
                    syntax_validation = validate_gcode_syntax(block['code'])
                    if syntax_validation.get('errors') and len(syntax_validation['errors']) > 0:
                        print(f'G code block {block.get("id", "unknown")} syntax validation failed: {syntax_validation["errors"]}')

                    safety_validation = validate_gcode_safety(block['code'])
                    if safety_validation.get('errors') and len(safety_validation['errors']) > 0:
                        print(f'G code block {block.get("id", "unknown")} safety validation failed: {safety_validation["errors"]}')

                    # 进行碰撞检测
                    collision_detection = detect_collisions(block['code'])
                    if collision_detection.get('has_collisions'):
                        has_collision_risk = True
                        print(f'G code block {block.get("id", "unknown")} collision detection failed: {collision_detection["collisions"]}')
                        # 添加碰撞风险信息to项目
                        if not hasattr(self.project, 'collision_warnings'):
                            self.project.collision_warnings = []
                        self.project.collision_warnings.append({
                            'block_id': block.get('id'),
                            'collisions': collision_detection['collisions'],
                            'timestamp': datetime.now().isoformat()
                        })

            self.project.updated_at = datetime.now()
            self.set_state('code_generated')
            print('G代码generation and validation completed')

            # 如果有碰撞风险，可以设置特殊状态or添加警告
            if has_collision_risk:
                print('Generated G code has collision risk, please check carefully before running')

            return self.project.gcode_blocks
        except Exception as e:
            print(f'Error generating G code: {e}')
            self.set_state('error')
            return {'success': False, 'error': str(e)}

    def run_simulation(self):
        """
        启动模拟
        """
        try:
            if self.state != 'code_generated':
                raise ValueError(f'Current state {self.state} 不允许启动模拟，需要 "code_generated" 状态')

            if not self.project or not isinstance(self.project.gcode_blocks, list):
                raise ValueError('项目orG code block列表无效')

            simulation_results = start_simulation(self.project.gcode_blocks)
            self.set_state('simulation_running')
            return simulation_results
        except Exception as e:
            print(f'Error running simulation: {e}')
            self.set_state('error')
            return {'success': False, 'error': str(e)}

    def run_variable_driven_simulation(self, variable_values: Dict[str, Any]):
        """
        变量驱动模拟
        """
        try:
            if self.state != 'code_generated' and self.state != 'simulation_running':
                raise ValueError(f'Current state {self.state} 不允许运行变量驱动模拟')

            if not self.project or not isinstance(self.project.gcode_blocks, list):
                raise ValueError('项目orG code block列表无效')

            simulation_results = variable_driven_simulation(self.project.gcode_blocks, variable_values)
            print('变量驱动模拟完成')
            return simulation_results
        except Exception as e:
            print(f'Error running variable-driven simulation: {e}')
            return {'success': False, 'error': str(e)}

    def export_code(self, output_path: str = None):
        """
        导出代码
        """
        try:
            if self.state != 'code_generated':
                raise ValueError(f'Current state {self.state} 不允许导出代码，需要 "code_generated" 状态')

            if not self.project or not isinstance(self.project.gcode_blocks, list):
                raise ValueError('项目orG code block列表无效')

            gcode = export_code(self.project.gcode_blocks, output_path)
            self.set_state('code_exported')
            print('代码导出完成')
            return gcode
        except Exception as e:
            print(f'Error exporting code: {e}')
            self.set_state('error')
            return {'success': False, 'error': str(e)}

    def get_state_info(self) -> Dict[str, Any]:
        """
        获取Current state信息
        """
        return {
            'current_state': self.state,
            'allowed_transitions': self.get_allowed_transitions(),
            'state_history': self.state_history[:],
            'project_exists': bool(self.project),
            'feature_selected': bool(self.selected_feature),
            'selected_feature_count': len(self.selected_features),  # 返回选中特征的数量
            'selected_features': self.selected_features  # 返回选中的特征列表
        }


# 创建状态管理器实例
cnc_state_manager = CNCStateManager()

# 创建Flask应用
app = Flask(__name__)
PORT = int(os.environ.get('PORT', 3000))

# Security middleware
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)
limiter.init_app(app)

# 输入验证中间件
def validate_input():
    """验证请求输入"""
    if request.is_json:
        data = request.get_json()
        if data:
            # 检查是否包含潜在的恶意内容
            data_str = json.dumps(data) if isinstance(data, (dict, list)) else str(data)
            dangerous_patterns = [
                '<script',
                'javascript:',
                'vbscript:',
                r'on\w+\s*=',
                '<iframe',
                '<object',
                '<embed'
            ]

            for pattern in dangerous_patterns:
                if pattern.lower() in data_str.lower():
                    return jsonify({'success': False, 'error': '请求包含潜在的恶意内容'}), 400

    return None


@app.before_request
def before_request():
    """在请求前进行验证"""
    result = validate_input()
    if result:
        return result


# API路由
@app.route('/api/project/new', methods=['POST'])
def api_project_new():
    """创建新项目"""
    try:
        result = cnc_state_manager.start_new_project()
        return jsonify({**result, 'state': cnc_state_manager.state})
    except Exception as e:
        print(f'创建新项目时出错: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/project/import', methods=['POST'])
def api_project_import():
    """导入项目"""
    try:
        data = request.get_json()
        file_path = data.get('file_path') if data else None
        
        if not file_path:
            return jsonify({'success': False, 'error': 'Missing file path'}), 400

        result = cnc_state_manager.handle_import(file_path)
        return jsonify({**result, 'state': cnc_state_manager.state})
    except Exception as e:
        print(f'导入项目时出错: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/feature/select', methods=['POST'])
def api_feature_select():
    """选择特征"""
    try:
        data = request.get_json()
        x = data.get('x') if data else None
        y = data.get('y') if data else None
        
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            return jsonify({'success': False, 'error': 'Coordinates must be numbers'}), 400

        selection = cnc_state_manager.handle_feature_selection(x, y)
        if selection and isinstance(selection, dict) and selection.get('success') is False:
            return jsonify(selection), 400
        # 总是返回成功，但包含selection信息，让客户端决定如何处理
        has_valid_element = bool(selection and selection.get('element'))
        return jsonify({'success': True, 'selection': selection, 'has_element': has_valid_element})
    except Exception as e:
        print(f'Error selecting feature: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/feature/define', methods=['POST'])
def api_feature_define():
    """定义特征"""
    try:
        data = request.get_json()
        batch = data.get('batch', False) if data else False
        
        if batch:
            result = cnc_state_manager.start_feature_definition_batch()
            if isinstance(result, dict) and result.get('success') is False:
                return jsonify(result), 400
            return jsonify({'success': isinstance(result, list), 'features': result})
        else:
            result = cnc_state_manager.start_feature_definition()
            if isinstance(result, dict) and result.get('success') is False:
                return jsonify(result), 400
            return jsonify({'success': bool(result), 'feature': result})
    except Exception as e:
        print(f'定义特征时出错: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/feature/type', methods=['POST'])
def api_feature_type():
    """选择特征类型"""
    try:
        data = request.get_json()
        feature_id = data.get('feature_id') if data else None
        feature_type = data.get('feature_type') if data else None
        
        if not feature_id or not feature_type:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400

        result = cnc_state_manager.select_feature_type(feature_id, feature_type)
        if isinstance(result, dict) and result.get('success') is False:
            return jsonify(result), 400
        return jsonify({'success': bool(result), 'feature': result})
    except Exception as e:
        print(f'Error selecting feature type: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/feature/variable', methods=['POST'])
def api_feature_variable():
    """关联宏变量"""
    try:
        data = request.get_json()
        feature_id = data.get('feature_id') if data else None
        dimension_id = data.get('dimension_id') if data else None
        variable_name = data.get('variable_name') if data else None
        
        if not feature_id or not dimension_id or not variable_name:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400

        result = cnc_state_manager.associate_macro_variable(feature_id, dimension_id, variable_name)
        if isinstance(result, dict) and result.get('success') is False:
            return jsonify(result), 400
        return jsonify({'success': bool(result), 'feature': result})
    except Exception as e:
        print(f'Error associating macro variable: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/gcode/generate', methods=['POST'])
def api_gcode_generate():
    """生成G代码"""
    try:
        result = cnc_state_manager.generate_gcode()
        if isinstance(result, dict) and result.get('success') is False:
            return jsonify(result), 400
        return jsonify({'success': bool(result), 'gcode_blocks': result})
    except Exception as e:
        print(f'Error generating G code: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/simulation/start', methods=['POST'])
def api_simulation_start():
    """启动模拟"""
    try:
        results = cnc_state_manager.run_simulation()
        if isinstance(results, dict) and results.get('success') is False:
            return jsonify(results), 400
        return jsonify({'success': bool(results), 'results': results})
    except Exception as e:
        print(f'Error running simulation: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/simulation/variable', methods=['POST'])
def api_simulation_variable():
    """变量驱动模拟"""
    try:
        data = request.get_json()
        variable_values = data.get('variable_values') if data else None
        
        if not variable_values:
            return jsonify({'success': False, 'error': 'Missing variable values'}), 400

        results = cnc_state_manager.run_variable_driven_simulation(variable_values)
        if isinstance(results, dict) and results.get('success') is False:
            return jsonify(results), 400
        return jsonify({'success': bool(results), 'results': results})
    except Exception as e:
        print(f'Error running variable-driven simulation: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/gcode/export', methods=['POST'])
def api_gcode_export():
    """导出代码"""
    try:
        data = request.get_json()
        output_path = data.get('output_path') if data else None
        
        gcode = cnc_state_manager.export_code(output_path)
        if isinstance(gcode, dict) and gcode.get('success') is False:
            return jsonify(gcode), 400
        return jsonify({'success': bool(gcode), 'gcode': gcode})
    except Exception as e:
        print(f'Error exporting code: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/state', methods=['GET'])
def api_get_state():
    """获取状态"""
    try:
        state_info = cnc_state_manager.get_state_info()
        return jsonify(state_info)
    except Exception as e:
        print(f'Error getting state: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# 错误处理中间件
@app.errorhandler(Exception)
def handle_error(error):
    """全局错误处理"""
    print(f'Server error: {error}')
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


# 404中间件
@app.errorhandler(404)
def handle_404(error):
    """404处理"""
    return jsonify({
        'success': False,
        'error': 'API endpoint does not exist'
    }), 404


if __name__ == '__main__':
    # 启动服务器
    current_port = PORT
    max_retries = 10  # 尝试最多10个端口
    
    # 监听所有接口
    app.run(host='0.0.0.0', port=current_port, debug=False)
