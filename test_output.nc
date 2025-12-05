; CNCagent Generated G-Code
; Generated on: 2025-12-04T07:59:20.138Z

; Block: program_start
G21 ; 设置单位为毫米
G90 ; 设置绝对位置模式
G17 ; 选择XY平面
G40 ; 取消刀具半径补偿
G49 ; 取消刀具长度补偿
M3 S1000 ; 主轴正转，1000转/分钟
G0 Z5 ; 快速移动到安全高度

; Block: program_end
G0 Z5 ; 移动到安全高度
M5 ; 主轴停止
M30 ; 程序结束并返回开头

