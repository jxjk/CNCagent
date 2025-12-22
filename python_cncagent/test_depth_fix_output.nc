O0001 ; 程序号
G21 ; 毫米单位
G90 ; 绝对坐标
G40 ; 取消刀具半径补偿
G49 ; 取消刀具长度补偿
G80 ; 取消固定循环

; 坐标 system说明：
; G90 - 使用绝对坐标系统
; 原点(0,0)位于工件左上角（G54坐标系）
; 所有坐标值相对于此原点
; Y轴向下为正方向，X轴向右为正方向

G00 Z50 ; 快速移动到安全高度


; 注意: 图纸中未识别到具体孔位置，以下使用示例位置 50.0, 50.0
; 请根据实际图纸修改孔位置
; 螺纹孔加工工艺 - 总共 1 个螺纹孔（示例）
; 螺纹孔 1: 位置 X50.000 Y50.000（请修改为实际位置）

; --- 第一步：点孔工艺 ---
T1 M06 ; Select center drill T1 (Pilot drilling)
M03 S1000 ; Spindle forward, pilot drilling speed
G04 P1000 ; Delay 1 second, wait for spindle to reach set speed
G82 Z-1 R2 P1000 F50 ; Spot drilling cycle, dwell 1 second
G82 X50.000 Y50.000 Z-1 R2 P1000 F50 ; Spot drilling 1: X50.0,Y50.0
G80 ; Cancel fixed cycle
G00 Z50 ; Rapid move to safe height

; --- 第二步：Drilling Process (Pilot hole diameter 8.5mm) ---
T2 M06 ; Select drill bit T2
M03 S800 ; Spindle forward, drilling speed
G04 P1000 ; Delay 1 second, wait for spindle to reach set speed
G83 Z-15.400000000000002 R2 Q1 F100 ; Deep hole drilling cycle
G83 X50.000 Y50.000 Z-15.400000000000002 R2 Q1 F100 ; Drilling 1: X50.0,Y50.0
G80 ; Cancel fixed cycle
G00 Z50 ; Rapid move to safe height

; --- 第三步：Tapping Process ---
T3 M06 ; Select tap T3
M03 S300 ; Spindle forward, tapping speed
G04 P1000 ; Delay 1 second, wait for spindle to reach set speed
G84 Z-14.0 R2 F7.5 ; Tapping cycle
G84 X50.000 Y50.000 Z-14.0 R2 F7.5 ; Tapping 1: X50.0,Y50.0 (M10 thread)
G80 ; Cancel fixed cycle
M04 S300 ; Spindle reverse, prepare for retraction
G00 Z50 ; Rapid retraction to safe height
M05 ; Spindle stop

M05 ; 主轴停止
G00 Z100 ; 抬刀到安全高度
G00 X0 Y0 ; 返回原点
G00 Z0 ; 返回Z轴原点
M30 ; 程序结束