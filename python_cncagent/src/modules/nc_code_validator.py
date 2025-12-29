"""
NC代码验证器模块
用于验证AI生成的NC代码的安全性和正确性
提供传统方法作为备选和对比验证
"""
import re
from typing import Dict, List, Optional, Tuple
from .gcode_generation import generate_fanuc_nc as traditional_generate
from .material_tool_matcher import analyze_user_description

class NCCodeValidator:
    """
    NC代码验证器
    验证AI生成的代码安全性和正确性，提供传统方法作为备选
    """
    
    def __init__(self):
        self.safety_rules = [
            self._check_required_initialization,
            self._check_safe_height_usage,
            self._check_program_end,
            self._check_tool_compensation,
            self._check_spindle_control
        ]
        
        self.correctness_rules = [
            self._check_syntax_validity,
            self._check_coordinate_system,
            self._check_feed_rate_reasonableness,
            self._check_spindle_speed_reasonableness
        ]
    
    def validate_nc_code(self, nc_code: str, user_description: str = "") -> Dict[str, any]:
        """
        验证NC代码
        
        Args:
            nc_code: 待验证的NC代码
            user_description: 用户描述，用于对比验证
            
        Returns:
            Dict: 验证结果
        """
        lines = [line.strip() for line in nc_code.split('\n') if line.strip()]
        
        safety_results = []
        for rule in self.safety_rules:
            result = rule(lines)
            safety_results.append(result)
        
        correctness_results = []
        for rule in self.correctness_rules:
            result = rule(lines)
            correctness_results.append(result)
        
        # 检查是否存在严重安全问题
        has_critical_issues = any(
            not result['passed'] and result.get('severity', 'medium') == 'critical'
            for result in safety_results
        )
        
        return {
            'safety_passed': all(result['passed'] for result in safety_results),
            'correctness_passed': all(result['passed'] for result in correctness_results),
            'safety_results': safety_results,
            'correctness_results': correctness_results,
            'has_critical_issues': has_critical_issues,
            'overall_score': self._calculate_overall_score(safety_results, correctness_results),
            'suggested_fixes': self._get_suggested_fixes(safety_results, correctness_results)
        }
    
    def _check_required_initialization(self, lines: List[str]) -> Dict[str, any]:
        """检查必需的初始化指令"""
        required_gcodes = ['G21', 'G90', 'G40', 'G49', 'G80']
        missing_codes = []
        
        for code in required_gcodes:
            found = any(code in line for line in lines[:20])  # 检查前20行
            if not found:
                missing_codes.append(code)
        
        return {
            'rule': 'Required initialization codes',
            'passed': len(missing_codes) == 0,
            'details': f'Missing: {missing_codes}' if missing_codes else 'All present',
            'severity': 'critical' if missing_codes else 'none'
        }
    
    def _check_safe_height_usage(self, lines: List[str]) -> Dict[str, any]:
        """检查安全高度使用"""
        # 检查是否有安全高度设置（通常>50mm）
        has_safe_height = any('Z' in line and 
                             re.search(r'Z([+-]?\d+\.?\d*)', line) and 
                             float(re.search(r'Z([+-]?\d+\.?\d*)', line).group(1)) > 50 
                             for line in lines)
        
        return {
            'rule': 'Safe height usage',
            'passed': has_safe_height,
            'details': 'Safe height found (>50mm)' if has_safe_height else 'No safe height found',
            'severity': 'critical' if not has_safe_height else 'none'
        }
    
    def _check_program_end(self, lines: List[str]) -> Dict[str, any]:
        """检查程序结束指令"""
        has_end = any('M30' in line or 'M02' in line for line in lines[-5:])  # 检查最后5行
        
        return {
            'rule': 'Program end instruction',
            'passed': has_end,
            'details': 'Program end found' if has_end else 'No program end found',
            'severity': 'critical' if not has_end else 'none'
        }
    
    def _check_tool_compensation(self, lines: List[str]) -> Dict[str, any]:
        """检查刀具补偿"""
        has_compensation = any('G43' in line or 'G49' in line for line in lines)
        
        return {
            'rule': 'Tool compensation',
            'passed': has_compensation,
            'details': 'Tool compensation found' if has_compensation else 'No tool compensation found',
            'severity': 'high' if not has_compensation else 'none'
        }
    
    def _check_spindle_control(self, lines: List[str]) -> Dict[str, any]:
        """检查主轴控制"""
        has_spindle_control = any('M03' in line or 'M04' in line or 'M05' in line for line in lines)
        
        return {
            'rule': 'Spindle control',
            'passed': has_spindle_control,
            'details': 'Spindle control found' if has_spindle_control else 'No spindle control found',
            'severity': 'high' if not has_spindle_control else 'none'
        }
    
    def _check_syntax_validity(self, lines: List[str]) -> Dict[str, any]:
        """检查语法有效性"""
        # 识别无效的G/M代码格式
        invalid_lines = []
        valid_gcode_pattern = re.compile(r'^(G|M)\d+(\.\d+)?(\s+[XYZIJKRFPSTL]\s*[-+]?\d+(\.\d+)*)*(.*)?$')
        
        for line in lines:
            if line and not line.startswith('('):  # 忽略注释行
                # 移除注释部分
                clean_line = line.split('(')[0].strip()
                if clean_line and not valid_gcode_pattern.match(clean_line):
                    invalid_lines.append(clean_line)
        
        return {
            'rule': 'Syntax validity',
            'passed': len(invalid_lines) == 0,
            'details': f'Invalid lines: {invalid_lines[:3]}...' if len(invalid_lines) > 3 else f'Invalid lines: {invalid_lines}' if invalid_lines else 'All valid',
            'severity': 'high' if invalid_lines else 'none'
        }
    
    def _check_coordinate_system(self, lines: List[str]) -> Dict[str, any]:
        """检查坐标系统设置"""
        has_coordinate_system = any('G54' in line or 'G55' in line or 'G56' in line 
                                   or 'G57' in line or 'G58' in line or 'G59' in line 
                                   for line in lines[:10])
        
        return {
            'rule': 'Coordinate system',
            'passed': has_coordinate_system,
            'details': 'Coordinate system found' if has_coordinate_system else 'No coordinate system found',
            'severity': 'high' if not has_coordinate_system else 'none'
        }
    
    def _check_feed_rate_reasonableness(self, lines: List[str]) -> Dict[str, any]:
        """检查进给速度合理性"""
        feed_rates = []
        for line in lines:
            matches = re.findall(r'F(\d+\.?\d*)', line)
            feed_rates.extend([float(match) for match in matches])
        
        # 检查是否存在明显不合理的进给速度（如过大或过小）
        unreasonable_rates = [fr for fr in feed_rates if fr < 1 or fr > 5000]
        
        return {
            'rule': 'Feed rate reasonableness',
            'passed': len(unreasonable_rates) == 0,
            'details': f'Unreasonable rates: {unreasonable_rates[:3]}...' if len(unreasonable_rates) > 3 else f'Unreasonable rates: {unreasonable_rates}' if unreasonable_rates else 'All rates reasonable',
            'severity': 'medium' if unreasonable_rates else 'none'
        }
    
    def _check_spindle_speed_reasonableness(self, lines: List[str]) -> Dict[str, any]:
        """检查主轴转速合理性"""
        spindle_speeds = []
        for line in lines:
            matches = re.findall(r'S(\d+\.?\d*)', line)
            spindle_speeds.extend([float(match) for match in matches])
        
        # 检查是否存在明显不合理的主轴转速
        unreasonable_speeds = [ss for ss in spindle_speeds if ss > 20000]  # 通常不超过20000rpm
        
        return {
            'rule': 'Spindle speed reasonableness',
            'passed': len(unreasonable_speeds) == 0,
            'details': f'Unreasonable speeds: {unreasonable_speeds[:3]}...' if len(unreasonable_speeds) > 3 else f'Unreasonable speeds: {unreasonable_speeds}' if unreasonable_speeds else 'All speeds reasonable',
            'severity': 'medium' if unreasonable_speeds else 'none'
        }
    
    def _calculate_overall_score(self, safety_results: List[Dict], correctness_results: List[Dict]) -> float:
        """计算整体评分"""
        total_checks = len(safety_results) + len(correctness_results)
        passed_checks = sum(1 for result in safety_results + correctness_results if result['passed'])
        
        return passed_checks / total_checks if total_checks > 0 else 0.0
    
    def _get_suggested_fixes(self, safety_results: List[Dict], correctness_results: List[Dict]) -> List[str]:
        """获取建议修复"""
        fixes = []
        
        for result in safety_results + correctness_results:
            if not result['passed']:
                rule_name = result['rule']
                details = result['details']
                fixes.append(f"{rule_name}: {details}")
        
        return fixes
    
    def generate_with_traditional_fallback(self, features: List[Dict], description_analysis: Dict) -> str:
        """
        使用传统方法生成NC代码作为备选
        
        Args:
            features: 识别的特征列表
            description_analysis: 描述分析结果
            
        Returns:
            str: 传统方法生成的NC代码
        """
        return traditional_generate(features, description_analysis)
    
    def compare_with_traditional(self, ai_nc_code: str, features: List[Dict], description_analysis: Dict) -> Dict[str, any]:
        """
        将AI生成的代码与传统方法进行对比
        
        Args:
            ai_nc_code: AI生成的NC代码
            features: 识别的特征列表
            description_analysis: 描述分析结果
            
        Returns:
            Dict: 对比结果
        """
        # 生成传统方法的代码
        traditional_nc_code = self.generate_with_traditional_fallback(features, description_analysis)
        
        # 简单对比关键指标
        ai_lines = [line.strip() for line in ai_nc_code.split('\n') if line.strip() and not line.strip().startswith('(')]
        traditional_lines = [line.strip() for line in traditional_nc_code.split('\n') if line.strip() and not line.strip().startswith('(')]
        
        # 检查关键G/M代码的存在性
        ai_gcodes = set()
        traditional_gcodes = set()
        
        for line in ai_lines:
            g_matches = re.findall(r'G\d+', line)
            m_matches = re.findall(r'M\d+', line)
            ai_gcodes.update(g_matches + m_matches)
        
        for line in traditional_lines:
            g_matches = re.findall(r'G\d+', line)
            m_matches = re.findall(r'M\d+', line)
            traditional_gcodes.update(g_matches + m_matches)
        
        # 检查是否存在重要缺失
        missing_in_ai = traditional_gcodes - ai_gcodes
        missing_in_traditional = ai_gcodes - traditional_gcodes
        
        return {
            'ai_line_count': len(ai_lines),
            'traditional_line_count': len(traditional_lines),
            'missing_in_ai': list(missing_in_ai),
            'missing_in_traditional': list(missing_in_traditional),
            'ai_has_spindle_control': any('M03' in line or 'M04' in line or 'M05' in line for line in ai_lines),
            'traditional_has_spindle_control': any('M03' in line or 'M04' in line or 'M05' in line for line in traditional_lines),
            'ai_has_tool_compensation': any('G43' in line or 'G49' in line for line in ai_lines),
            'traditional_has_tool_compensation': any('G43' in line or 'G49' in line for line in traditional_lines),
            'ai_has_safe_operations': any('G21' in line and 'G90' in line for line in ai_lines[:10]),
            'traditional_has_safe_operations': any('G21' in line and 'G90' in line for line in traditional_lines[:10])
        }


# 创建全局实例
nc_validator = NCCodeValidator()
