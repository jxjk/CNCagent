// 生成在G54X0.Y0.用G81钻孔50深的CNC代码
// 这是根据您的要求直接生成的G代码

const gcode = `O0001 (CNC程序 - 钻孔操作)
G21 (毫米编程)
G40 (刀具半径补偿取消)
G49 (刀具长度补偿取消)
G80 (取消固定循环)
G90 (绝对编程)
G54 (工件坐标系1)
G0 X0. Y0. (快速定位到起始点)
G43 H01 Z100. (刀具长度补偿并快速定位Z轴)
G81 G98 X0. Y0. Z-50. R2. F100. (G81钻孔循环，钻孔深度50mm，参考平面R2mm，进给率F100)
G80 (取消固定循环)
M30 (程序结束)
`;

console.log('生成的G代码:');
console.log(gcode);

// 保存到文件
const fs = require('fs');
fs.writeFileSync('./output.nc', gcode);
console.log('G代码已保存到 output.nc 文件');