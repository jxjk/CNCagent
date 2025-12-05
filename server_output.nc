; CNCagent Generated G-Code
; Generated on: 2025-12-04T06:40:35.940Z

; Block: program_start
G21 ; 设置单位为毫米
G90 ; 设置绝对位置模式
G17 ; 选择XY平面
G40 ; 取消刀具半径补偿
G49 ; 取消刀具长度补偿
M3 S1000 ; 主轴正转，1000转/分钟
G0 Z5 ; 快速移动到安全高度

; Block: gcode_feat_mir2h3k9g2fkg
; 生成孔 - 直径: 10, 深度: 20
G43 H1 ; 刀具长度补偿
G0 X0 Y0 ; 快速移动到孔位置
G0 Z2 ; 快速移动到加工起始点
G1 Z-20 F200 ; 钻孔
G0 Z2 ; 快速退刀

; Block: program_end
G0 Z5 ; 移动到安全高度
M5 ; 主轴停止
M30 ; 程序结束并返回开头

