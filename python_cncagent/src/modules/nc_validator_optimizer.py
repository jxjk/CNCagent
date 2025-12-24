"""
NC程序验证和优化模块
验证生成的NC程序的正确性，并进行优化
"""
import logging
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path

class NCValidator:
    """
    NC程序验证器
    验证NC程序的语法正确性、安全性等
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 定义关键的安全指令
        self.critical_commands = {
            'initialization': ['G21', 'G90', 'G40', 'G49', 'G80'],
            'safety': ['G54', 'G00', 'M03', 'M05', 'M08', 'M09', 'M30'],
            'modal': ['G00', 'G01', 'G02', 'G03', 'G80', 'G81', 'G82', 'G83', 'G84']
        }
        
        # 定义常见的编程错误模式
        self.error_patterns = [
            r'G0*[1-9]\d*.*G0*[1-9]\d*',  # 两个移动指令连续出现
            r'F0*\.?\d*\.',  # 进给率为0或格式错误
            r'S0*\.?\d*\.',  # 主轴转速为0或格式错误
            r'Z-?\d+\.?\d*\s*Z-?\d+\.?\d*',  # Z轴坐标重复
        ]
    
    def validate_nc_program(self, nc_program: str) -> Dict:
        """
        验证NC程序
        
        Args:
            nc_program: NC程序代码
            
        Returns:
            Dict: 验证结果
        """
        lines = [line.strip() for line in nc_program.split('\n') if line.strip()]
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': [],
            'completeness_score': 0.0,
            'safety_score': 0.0
        }
        
        # 检查必需的初始化指令
        self._check_initialization_commands(lines, validation_result)
        
        # 检查程序结束指令
        self._check_program_end(lines, validation_result)
        
        # 检查语法错误
        self._check_syntax_errors(lines, validation_result)
        
        # 检查安全相关问题
        self._check_safety_issues(lines, validation_result)
        
        # 计算完整性分数
        validation_result['completeness_score'] = self._calculate_completeness_score(lines)
        
        # 计算安全性分数
        validation_result['safety_score'] = self._calculate_safety_score(lines)
        
        # 总体有效性判断
        validation_result['is_valid'] = len(validation_result['errors']) == 0
        
        return validation_result
    
    def _check_initialization_commands(self, lines: List[str], result: Dict):
        """检查初始化指令"""
        program_start = lines[:20]  # 检查前20行
        
        missing_init = []
        for cmd in self.critical_commands['initialization']:
            if not any(cmd in line for line in program_start):
                missing_init.append(cmd)
        
        if missing_init:
            result['warnings'].append(f"缺少初始化指令: {', '.join(missing_init)}")
    
    def _check_program_end(self, lines: List[str], result: Dict):
        """检查程序结束指令"""
        program_end = lines[-10:]  # 检查最后10行
        
        has_end = any('M30' in line or 'M02' in line for line in program_end)
        if not has_end:
            result['errors'].append("程序缺少结束指令 (M30 或 M02)")
    
    def _check_syntax_errors(self, lines: List[str], result: Dict):
        """检查语法错误"""
        for i, line in enumerate(lines):
            # 检查是否有重复的坐标指令
            if re.search(r'X-?\d+\.?\d*\s*X-?\d+\.?\d*', line):
                result['errors'].append(f"第{i+1}行: X坐标重复定义")
            
            if re.search(r'Y-?\d+\.?\d*\s*Y-?\d+\.?\d*', line):
                result['errors'].append(f"第{i+1}行: Y坐标重复定义")
            
            if re.search(r'Z-?\d+\.?\d*\s*Z-?\d+\.?\d*', line):
                result['errors'].append(f"第{i+1}行: Z坐标重复定义")
            
            # 检查进给率和转速是否为正数
            f_match = re.search(r'F(\d+\.?\d*)', line)
            if f_match:
                try:
                    f_value = float(f_match.group(1))
                    if f_value <= 0:
                        result['errors'].append(f"第{i+1}行: 进给率F值应为正数")
                except ValueError:
                    result['errors'].append(f"第{i+1}行: 进给率F格式错误")
            
            s_match = re.search(r'S(\d+\.?\d*)', line)
            if s_match:
                try:
                    s_value = float(s_match.group(1))
                    if s_value <= 0:
                        result['errors'].append(f"第{i+1}行: 主轴转速S值应为正数")
                except ValueError:
                    result['errors'].append(f"第{i+1}行: 主轴转速S格式错误")
    
    def _check_safety_issues(self, lines: List[str], result: Dict):
        """检查安全问题"""
        # 检查是否有适当的刀具补偿取消
        has_tool_comp_cancel = any('G49' in line for line in lines)
        if not has_tool_comp_cancel:
            result['warnings'].append("程序中缺少刀具长度补偿取消指令 (G49)")
        
        # 检查是否有适当的回零操作
        has_return_home = any('G28' in line for line in lines)
        if not has_return_home:
            result['warnings'].append("程序中缺少回参考点指令 (G28)")
    
    def _calculate_completeness_score(self, lines: List[str]) -> float:
        """计算完整性分数"""
        score = 0.0
        max_score = 5.0
        
        # 检查是否有初始化
        if any(cmd in ' '.join(lines[:10]) for cmd in ['G21', 'G90']):
            score += 1.0
        
        # 检查是否有安全指令
        if any(cmd in ' '.join(lines) for cmd in ['G40', 'G49', 'G80']):
            score += 1.0
        
        # 检查是否有程序结束
        if any('M30' in line or 'M02' in line for line in lines[-5:]):
            score += 1.0
        
        # 检查是否有刀具选择和调用
        if any('T' in line and 'M06' in line for line in lines):
            score += 1.0
        
        # 检查是否有主轴控制
        if any('M03' in line or 'M04' in line for line in lines):
            score += 0.5
        if any('M05' in line for line in lines):
            score += 0.5
        
        return min(score / max_score, 1.0)
    
    def _calculate_safety_score(self, lines: List[str]) -> float:
        """计算安全性分数"""
        score = 0.0
        max_score = 4.0
        
        # 检查是否有安全高度设置
        if any('G00 Z' in line and float(re.search(r'Z(-?\d+\.?\d*)', line).group(1)) > 50 
               for line in lines if re.search(r'Z(-?\d+\.?\d*)', line)):
            score += 1.0
        elif any('G00' in line and 'Z' in line for line in lines):
            # 如果有Z轴移动，假设有安全高度
            score += 0.5
        
        # 检查是否有冷却液控制
        if any('M08' in line and 'M09' in line for line in lines):
            score += 1.0
        elif any('M08' in line for line in lines):
            score += 0.5
        
        # 检查是否有回零操作
        if any('G28' in line for line in lines):
            score += 1.0
        
        # 检查是否有刀具补偿取消
        if any('G49' in line for line in lines):
            score += 1.0
        
        return min(score / max_score, 1.0)

class NCOptimizer:
    """
    NC程序优化器
    优化NC程序的效率和性能
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def optimize_nc_program(self, nc_program: str) -> str:
        """
        优化NC程序
        
        Args:
            nc_program: 原始NC程序
            
        Returns:
            str: 优化后的NC程序
        """
        lines = nc_program.split('\n')
        
        # 1. 移除多余的空行和注释
        optimized_lines = self._remove_excess_whitespace(lines)
        
        # 2. 优化刀具路径
        optimized_lines = self._optimize_toolpath(optimized_lines)
        
        # 3. 优化指令顺序
        optimized_lines = self._optimize_command_order(optimized_lines)
        
        # 4. 移除重复指令
        optimized_lines = self._remove_duplicate_commands(optimized_lines)
        
        return '\n'.join(optimized_lines)
    
    def _remove_excess_whitespace(self, lines: List[str]) -> List[str]:
        """移除多余的空白行和空格"""
        cleaned_lines = []
        empty_line_count = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                # 连续多个空行只保留一个
                if empty_line_count == 0:
                    cleaned_lines.append('')
                    empty_line_count += 1
            else:
                # 移除行首行尾空格，但保留指令间的必要空格
                cleaned_lines.append(self._clean_line_whitespace(stripped))
                empty_line_count = 0
        
        return cleaned_lines
    
    def _clean_line_whitespace(self, line: str) -> str:
        """清理行内多余的空格"""
        # 保留指令和参数之间的单个空格
        import re
        # 将多个空格替换为单个空格
        cleaned = re.sub(r'\s+', ' ', line)
        # 特别处理坐标值，确保格式正确
        cleaned = re.sub(r'([XYZIJKFST])(\d)', r'\1 \2', cleaned)
        return cleaned.strip()
    
    def _optimize_toolpath(self, lines: List[str]) -> List[str]:
        """优化刀具路径"""
        optimized = []
        
        for line in lines:
            # 简单的路径优化：合并连续的快速移动
            if 'G00' in line and optimized and 'G00' in optimized[-1]:
                # 如果前一行也是G00，尝试合并坐标
                prev_line = optimized[-1]
                if self._can_merge_moves(prev_line, line):
                    merged = self._merge_moves(prev_line, line)
                    optimized[-1] = merged
                    continue
            
            optimized.append(line)
        
        return optimized
    
    def _can_merge_moves(self, line1: str, line2: str) -> bool:
        """检查两个移动指令是否可以合并"""
        # 检查是否都是G00指令
        if 'G00' not in line1 or 'G00' not in line2:
            return False
        
        # 检查是否有重复的坐标轴
        axes1 = set(re.findall(r'[XYZ]', line1))
        axes2 = set(re.findall(r'[XYZ]', line2))
        
        # 如果有重复的轴，则不能合并
        return len(axes1.intersection(axes2)) == 0
    
    def _merge_moves(self, line1: str, line2: str) -> str:
        """合并两个移动指令"""
        import re
        
        # 提取所有坐标
        coords = {}
        
        # 从第一行提取坐标
        for match in re.finditer(r'([XYZ])(-?\d+\.?\d*)', line1):
            coords[match.group(1)] = match.group(2)
        
        # 从第二行提取坐标
        for match in re.finditer(r'([XYZ])(-?\d+\.?\d*)', line2):
            coords[match.group(1)] = match.group(2)
        
        # 重构指令
        parts = ['G00']
        for axis in sorted(coords.keys()):
            parts.append(f"{axis}{coords[axis]}")
        
        return ' '.join(parts)
    
    def _optimize_command_order(self, lines: List[str]) -> List[str]:
        """优化指令顺序"""
        # 确保安全指令在适当位置
        # 将G43(刀具长度补偿)紧随T代码之后
        optimized = []
        
        for i, line in enumerate(lines):
            if 'T' in line and 'M06' in line:
                # 查找下一个G43指令
                next_g43_idx = -1
                for j in range(i + 1, min(i + 5, len(lines))):
                    if 'G43' in lines[j]:
                        next_g43_idx = j
                        break
                
                # 如果G43不在下一行，重新排列
                if next_g43_idx > i + 1:
                    # 添加当前T代码
                    optimized.append(line)
                    # 添加G43代码
                    if next_g43_idx < len(lines):
                        optimized.append(lines[next_g43_idx])
                        # 跳过已添加的G43行
                        continue
                else:
                    optimized.append(line)
            else:
                # 跳过已处理的G43行
                if i > 0 and 'T' in lines[i-1] and 'M06' in lines[i-1] and 'G43' in line:
                    continue
                optimized.append(line)
        
        return optimized
    
    def _remove_duplicate_commands(self, lines: List[str]) -> List[str]:
        """移除重复指令"""
        optimized = []
        prev_commands = set()
        
        for line in lines:
            # 提取主要命令（不包括参数）
            main_cmd = self._extract_main_command(line)
            
            # 如果是重复的非移动命令，则跳过
            if main_cmd in prev_commands and not any(m in line for m in ['G00', 'G01', 'G02', 'G03', 'G81', 'G82', 'G83', 'G84']):
                continue
            
            optimized.append(line)
            
            # 更新已有的命令集
            if main_cmd:
                prev_commands.add(main_cmd)
            
            # 对于移动命令，清除之前的状态（因为位置已改变）
            if any(m in line for m in ['G00', 'G01', 'G02', 'G03']):
                prev_commands.clear()
        
        return optimized
    
    def _extract_main_command(self, line: str) -> str:
        """提取主要命令"""
        import re
        # 匹配G代码或M代码
        match = re.search(r'(G\d+|M\d+)', line.upper())
        return match.group(1) if match else ""

class NCProgramProcessor:
    """
    NC程序综合处理器
    整合验证和优化功能
    """
    
    def __init__(self):
        self.validator = NCValidator()
        self.optimizer = NCOptimizer()
        self.logger = logging.getLogger(__name__)
    
    def process_nc_program(self, nc_program: str, optimize: bool = True) -> Tuple[str, Dict]:
        """
        处理NC程序（验证和优化）
        
        Args:
            nc_program: 原始NC程序
            optimize: 是否进行优化
            
        Returns:
            Tuple[str, Dict]: (处理后的程序, 验证结果)
        """
        # 首先验证程序
        validation_result = self.validator.validate_nc_program(nc_program)
        
        # 如果程序无效，返回原始程序和验证错误
        if not validation_result['is_valid']:
            self.logger.warning(f"NC程序验证失败，发现 {len(validation_result['errors'])} 个错误")
            return nc_program, validation_result
        
        # 程序有效，进行优化
        if optimize:
            optimized_program = self.optimizer.optimize_nc_program(nc_program)
            # 再次验证优化后的程序
            final_validation = self.validator.validate_nc_program(optimized_program)
            if not final_validation['is_valid']:
                # 如果优化后程序无效，返回原始程序
                self.logger.warning("优化后的程序验证失败，返回原始程序")
                return nc_program, validation_result
            return optimized_program, final_validation
        else:
            return nc_program, validation_result

# 创建全局实例
processor = NCProgramProcessor()

def validate_nc_program(nc_program: str) -> Dict:
    """
    验证NC程序
    
    Args:
        nc_program: NC程序代码
        
    Returns:
        Dict: 验证结果
    """
    return processor.validator.validate_nc_program(nc_program)

def optimize_nc_program(nc_program: str) -> str:
    """
    优化NC程序
    
    Args:
        nc_program: NC程序代码
        
    Returns:
        str: 优化后的NC程序
    """
    return processor.optimizer.optimize_nc_program(nc_program)

def process_nc_program(nc_program: str, optimize: bool = True) -> Tuple[str, Dict]:
    """
    处理NC程序（验证和优化）
    
    Args:
        nc_program: NC程序代码
        optimize: 是否进行优化
        
    Returns:
        Tuple[str, Dict]: (处理后的程序, 验证结果)
    """
    return processor.process_nc_program(nc_program, optimize)
