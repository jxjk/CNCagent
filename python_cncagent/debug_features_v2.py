import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.modules.feature_definition import identify_counterbore_features, select_coordinate_reference, adjust_coordinate_system
from src.modules.gcode_generation import generate_fanuc_nc

# 使用最新系统输出中的特征数据
detected_features = [
    {'shape': 'polygon', 'center': (1135, 1638), 'dimensions': (12, 24), 'confidence': 0.86, 'contour': [], 'bounding_box': (1129, 1626, 12, 24), 'area': 288},
    {'shape': 'square', 'center': (1124, 1638), 'dimensions': (32, 35), 'confidence': 1.00, 'contour': [], 'bounding_box': (1108, 1620.5, 32, 35), 'area': 1120},
    {'shape': 'square', 'center': (1090, 1638), 'dimensions': (32, 35), 'confidence': 1.00, 'contour': [], 'bounding_box': (1074, 1620.5, 32, 35), 'area': 1120},
    {'shape': 'square', 'center': (988, 1637), 'dimensions': (32, 35), 'confidence': 1.00, 'contour': [], 'bounding_box': (972, 1619.5, 32, 35), 'area': 1120},
    {'shape': 'rectangle', 'center': (1125, 1583), 'dimensions': (20, 15), 'confidence': 0.86, 'contour': [], 'bounding_box': (1115, 1575.5, 20, 15), 'area': 300},
    {'shape': 'rectangle', 'center': (955, 1606), 'dimensions': (32, 96), 'confidence': 1.00, 'contour': [], 'bounding_box': (939, 1558, 32, 96), 'area': 3072},
    {'shape': 'rectangle', 'center': (922, 1606), 'dimensions': (32, 96), 'confidence': 1.00, 'contour': [], 'bounding_box': (906, 1558, 32, 96), 'area': 3072},
    {'shape': 'rectangle', 'center': (1124, 1572), 'dimensions': (32, 91), 'confidence': 1.00, 'contour': [], 'bounding_box': (1108, 1526.5, 32, 91), 'area': 2912},
    {'shape': 'rectangle', 'center': (1090, 1572), 'dimensions': (32, 91), 'confidence': 1.00, 'contour': [], 'bounding_box': (1074, 1526.5, 32, 91), 'area': 2912},
    {'shape': 'rectangle', 'center': (1056, 1573), 'dimensions': (32, 91), 'confidence': 1.00, 'contour': [], 'bounding_box': (1040, 1527.5, 32, 91), 'area': 2912},
    {'shape': 'rectangle', 'center': (1023, 1572), 'dimensions': (33, 90), 'confidence': 1.00, 'contour': [], 'bounding_box': (1006.5, 1527, 33, 90), 'area': 2970},
    {'shape': 'rectangle', 'center': (989, 1571), 'dimensions': (33, 91), 'confidence': 1.00, 'contour': [], 'bounding_box': (972.5, 1525.5, 33, 91), 'area': 3003},
    {'shape': 'rectangle', 'center': (956, 1508), 'dimensions': (31, 96), 'confidence': 1.00, 'contour': [], 'bounding_box': (940.5, 1460, 31, 96), 'area': 2976},
    {'shape': 'square', 'center': (751, 1301), 'dimensions': (15, 14), 'confidence': 0.78, 'contour': [], 'bounding_box': (743.5, 1294, 15, 14), 'area': 210},
    {'shape': 'polygon', 'center': (198, 1297), 'dimensions': (15, 15), 'confidence': 0.74, 'contour': [], 'bounding_box': (190.5, 1289.5, 15, 15), 'area': 225},
    {'shape': 'rectangle', 'center': (1125, 1396), 'dimensions': (34, 257), 'confidence': 1.00, 'contour': [], 'bounding_box': (1108, 1267.5, 34, 257), 'area': 8738},
    {'shape': 'rectangle', 'center': (1091, 1396), 'dimensions': (33, 257), 'confidence': 1.00, 'contour': [], 'bounding_box': (1074.5, 1267.5, 33, 257), 'area': 8481},
    {'shape': 'rectangle', 'center': (1057, 1396), 'dimensions': (33, 257), 'confidence': 1.00, 'contour': [], 'bounding_box': (1040.5, 1267.5, 33, 257), 'area': 8481},
    {'shape': 'rectangle', 'center': (1024, 1396), 'dimensions': (33, 258), 'confidence': 1.00, 'contour': [], 'bounding_box': (1007.5, 1267, 33, 258), 'area': 8514},
    {'shape': 'rectangle', 'center': (990, 1396), 'dimensions': (33, 258), 'confidence': 1.00, 'contour': [], 'bounding_box': (973.5, 1267, 33, 258), 'area': 8514},
    {'shape': 'rectangle', 'center': (287, 1191), 'dimensions': (34, 5), 'confidence': 0.99, 'contour': [], 'bounding_box': (270, 1188.5, 34, 5), 'area': 170},
    {'shape': 'rectangle', 'center': (1127, 1211), 'dimensions': (33, 110), 'confidence': 1.00, 'contour': [], 'bounding_box': (1110.5, 1156, 33, 110), 'area': 3630},
    {'shape': 'rectangle', 'center': (1093, 1211), 'dimensions': (33, 110), 'confidence': 1.00, 'contour': [], 'bounding_box': (1076.5, 1156, 33, 110), 'area': 3630},
    {'shape': 'rectangle', 'center': (1059, 1211), 'dimensions': (33, 110), 'confidence': 1.00, 'contour': [], 'bounding_box': (1042.5, 1156, 33, 110), 'area': 3630},
    {'shape': 'rectangle', 'center': (1025, 1210), 'dimensions': (33, 109), 'confidence': 1.00, 'contour': [], 'bounding_box': (1008.5, 1155.5, 33, 109), 'area': 3597},
    {'shape': 'ellipse', 'center': (991, 1210), 'dimensions': (32, 110), 'confidence': 0.76, 'contour': [], 'bounding_box': (975, 1155, 32, 110), 'area': 3520},
    {'shape': 'polygon', 'center': (285, 1159), 'dimensions': (35, 54), 'confidence': 0.84, 'contour': [], 'bounding_box': (267.5, 1132, 35, 54), 'area': 1890},
    {'shape': 'rectangle', 'center': (257, 1145), 'dimensions': (20, 26), 'confidence': 1.00, 'contour': [], 'bounding_box': (247, 1132, 20, 26), 'area': 520},
    {'shape': 'rectangle', 'center': (287, 1127), 'dimensions': (35, 5), 'confidence': 0.98, 'contour': [], 'bounding_box': (269.5, 1124.5, 35, 5), 'area': 175},
    {'shape': 'triangle', 'center': (366, 1124), 'dimensions': (55, 6), 'confidence': 0.92, 'contour': [], 'bounding_box': (338.5, 1121, 55, 6), 'area': 165},
    {'shape': 'rectangle', 'center': (1159, 1134), 'dimensions': (27, 54), 'confidence': 1.00, 'contour': [], 'bounding_box': (1145.5, 1107, 27, 54), 'area': 1458},
    {'shape': 'polygon', 'center': (466, 1160), 'dimensions': (126, 127), 'confidence': 0.87, 'contour': [], 'bounding_box': (403, 1096.5, 126, 127), 'area': 15942},
    {'shape': 'rectangle', 'center': (1128, 1107), 'dimensions': (33, 95), 'confidence': 1.00, 'contour': [], 'bounding_box': (1111.5, 1064.5, 33, 95), 'area': 3135},
    {'shape': 'rectangle', 'center': (1094, 1106), 'dimensions': (33, 95), 'confidence': 1.00, 'contour': [], 'bounding_box': (1077.5, 1063.5, 33, 95), 'area': 3135},
    {'shape': 'rectangle', 'center': (1059, 1106), 'dimensions': (33, 96), 'confidence': 1.00, 'contour': [], 'bounding_box': (1042.5, 1060, 33, 96), 'area': 3168},
    {'shape': 'rectangle', 'center': (1025, 1106), 'dimensions': (33, 96), 'confidence': 1.00, 'contour': [], 'bounding_box': (1008.5, 1060, 33, 96), 'area': 3168},
    {'shape': 'rectangle', 'center': (992, 1105), 'dimensions': (33, 96), 'confidence': 1.00, 'contour': [], 'bounding_box': (975.5, 1059, 33, 96), 'area': 3168},
    {'shape': 'triangle', 'center': (834, 1057), 'dimensions': (41, 5), 'confidence': 1.00, 'contour': [], 'bounding_box': (813.5, 1054.5, 41, 5), 'area': 102.5},
    {'shape': 'rectangle', 'center': (1159, 1078), 'dimensions': (27, 54), 'confidence': 1.00, 'contour': [], 'bounding_box': (1145.5, 1051, 27, 54), 'area': 1458},
    {'shape': 'polygon', 'center': (734, 1039), 'dimensions': (9, 17), 'confidence': 0.87, 'contour': [], 'bounding_box': (729.5, 1030.5, 9, 17), 'area': 153},
    {'shape': 'rectangle', 'center': (1116, 1015), 'dimensions': (4, 35), 'confidence': 0.95, 'contour': [], 'bounding_box': (1114, 997.5, 4, 35), 'area': 140},
    {'shape': 'rectangle', 'center': (1160, 1022), 'dimensions': (27, 54), 'confidence': 1.00, 'contour': [], 'bounding_box': (1146.5, 995, 27, 54), 'area': 1458},
    {'shape': 'rectangle', 'center': (1160, 966), 'dimensions': (27, 54), 'confidence': 1.00, 'contour': [], 'bounding_box': (1146.5, 939, 27, 54), 'area': 1458},
    {'shape': 'rectangle', 'center': (1162, 914), 'dimensions': (26, 51), 'confidence': 1.00, 'contour': [], 'bounding_box': (1149, 888.5, 26, 51), 'area': 1326},
    {'shape': 'rectangle', 'center': (1136, 893), 'dimensions': (19, 24), 'confidence': 0.93, 'contour': [], 'bounding_box': (1126.5, 881, 19, 24), 'area': 456},
    {'shape': 'polygon', 'center': (997, 892), 'dimensions': (28, 29), 'confidence': 0.73, 'contour': [], 'bounding_box': (983, 877.5, 28, 29), 'area': 812},
    {'shape': 'rectangle', 'center': (1136, 871), 'dimensions': (19, 24), 'confidence': 0.93, 'contour': [], 'bounding_box': (1126.5, 859, 19, 24), 'area': 456},
    {'shape': 'rectangle', 'center': (1162, 850), 'dimensions': (27, 53), 'confidence': 1.00, 'contour': [], 'bounding_box': (1148.5, 823.5, 27, 53), 'area': 1431},
    {'shape': 'rectangle', 'center': (873, 924), 'dimensions': (40, 264), 'confidence': 1.00, 'contour': [], 'bounding_box': (853, 792, 40, 264), 'area': 10560},
    {'shape': 'polygon', 'center': (697, 793), 'dimensions': (21, 13), 'confidence': 0.83, 'contour': [], 'bounding_box': (686.5, 786.5, 21, 13), 'area': 273},
    {'shape': 'square', 'center': (289, 788), 'dimensions': (17, 20), 'confidence': 0.76, 'contour': [], 'bounding_box': (280.5, 778, 17, 20), 'area': 340},
    {'shape': 'ellipse', 'center': (1162, 798), 'dimensions': (27, 55), 'confidence': 0.73, 'contour': [], 'bounding_box': (1148.5, 770.5, 27, 55), 'area': 1485},
    {'shape': 'rectangle', 'center': (468, 751), 'dimensions': (126, 16), 'confidence': 1.00, 'contour': [], 'bounding_box': (405, 743, 126, 16), 'area': 2016},
    {'shape': 'ellipse', 'center': (700, 752), 'dimensions': (20, 36), 'confidence': 0.74, 'contour': [], 'bounding_box': (690, 734, 20, 36), 'area': 720},
    {'shape': 'rectangle', 'center': (1162, 742), 'dimensions': (26, 54), 'confidence': 1.00, 'contour': [], 'bounding_box': (1149, 715, 26, 54), 'area': 1404},
    {'shape': 'ellipse', 'center': (169, 739), 'dimensions': (20, 47), 'confidence': 0.74, 'contour': [], 'bounding_box': (159, 715.5, 20, 47), 'area': 940},
    {'shape': 'polygon', 'center': (518, 723), 'dimensions': (17, 19), 'confidence': 0.85, 'contour': [], 'bounding_box': (509.5, 713.5, 17, 19), 'area': 323},
    {'shape': 'square', 'center': (700, 722), 'dimensions': (20, 20), 'confidence': 1.00, 'contour': [], 'bounding_box': (690, 712, 20, 20), 'area': 400},
    {'shape': 'ellipse', 'center': (874, 742), 'dimensions': (40, 96), 'confidence': 0.74, 'contour': [], 'bounding_box': (854, 694, 40, 96), 'area': 3840},
    {'shape': 'square', 'center': (169, 703), 'dimensions': (21, 20), 'confidence': 1.00, 'contour': [], 'bounding_box': (158.5, 693, 21, 20), 'area': 420},
    {'shape': 'rectangle', 'center': (236, 700), 'dimensions': (20, 16), 'confidence': 0.95, 'contour': [], 'bounding_box': (226, 692, 20, 16), 'area': 320},
    {'shape': 'polygon', 'center': (247, 692), 'dimensions': (7, 33), 'confidence': 0.78, 'contour': [], 'bounding_box': (243.5, 675.5, 7, 33), 'area': 231},
    {'shape': 'square', 'center': (594, 682), 'dimensions': (19, 17), 'confidence': 0.77, 'contour': [], 'bounding_box': (584.5, 673.5, 19, 17), 'area': 323},
    {'shape': 'square', 'center': (564, 686), 'dimensions': (42, 44), 'confidence': 1.00, 'contour': [], 'bounding_box': (543, 664, 42, 44), 'area': 1848},
    {'shape': 'polygon', 'center': (517, 691), 'dimensions': (35, 53), 'confidence': 0.88, 'contour': [], 'bounding_box': (499.5, 664.5, 35, 53), 'area': 1855},
    {'shape': 'rectangle', 'center': (398, 704), 'dimensions': (13, 75), 'confidence': 1.00, 'contour': [], 'bounding_box': (391.5, 666.5, 13, 75), 'area': 975},
    {'shape': 'ellipse', 'center': (1163, 687), 'dimensions': (27, 54), 'confidence': 0.74, 'contour': [], 'bounding_box': (1149.5, 660, 27, 54), 'area': 1458},
    {'shape': 'rectangle', 'center': (590, 660), 'dimensions': (84, 13), 'confidence': 1.00, 'contour': [], 'bounding_box': (548, 653.5, 84, 13), 'area': 1092},
    {'shape': 'polygon', 'center': (337, 669), 'dimensions': (29, 33), 'confidence': 0.85, 'contour': [], 'bounding_box': (322.5, 652.5, 29, 33), 'area': 957},
    {'shape': 'ellipse', 'center': (237, 649), 'dimensions': (21, 47), 'confidence': 0.74, 'contour': [], 'bounding_box': (226.5, 625.5, 21, 47), 'area': 987},
    {'shape': 'ellipse', 'center': (1163, 631), 'dimensions': (26, 54), 'confidence': 0.75, 'contour': [], 'bounding_box': (1150, 604, 26, 54), 'area': 1404},
    {'shape': 'square', 'center': (238, 614), 'dimensions': (21, 20), 'confidence': 1.00, 'contour': [], 'bounding_box': (227.5, 604, 21, 20), 'area': 420},
    {'shape': 'rectangle', 'center': (216, 611), 'dimensions': (21, 17), 'confidence': 1.00, 'contour': [], 'bounding_box': (205.5, 602.5, 21, 17), 'area': 357},
    {'shape': 'polygon', 'center': (653, 625), 'dimensions': (43, 54), 'confidence': 0.81, 'contour': [], 'bounding_box': (631.5, 598, 43, 54), 'area': 2322},
    {'shape': 'triangle', 'center': (608, 624), 'dimensions': (51, 53), 'confidence': 0.99, 'contour': [], 'bounding_box': (582.5, 597.5, 51, 53), 'area': 1351.5},
    {'shape': 'triangle', 'center': (561, 627), 'dimensions': (53, 54), 'confidence': 1.00, 'contour': [], 'bounding_box': (534.5, 600, 53, 54), 'area': 1431},
    {'shape': 'polygon', 'center': (469, 631), 'dimensions': (126, 68), 'confidence': 0.89, 'contour': [], 'bounding_box': (406, 597, 126, 68), 'area': 8568},
    {'shape': 'triangle', 'center': (381, 622), 'dimensions': (50, 50), 'confidence': 1.00, 'contour': [], 'bounding_box': (356, 597, 50, 50), 'area': 1250},
    {'shape': 'polygon', 'center': (611, 568), 'dimensions': (21, 10), 'confidence': 0.78, 'contour': [], 'bounding_box': (600.5, 563, 21, 10), 'area': 210},
    {'shape': 'polygon', 'center': (878, 572), 'dimensions': (22, 20), 'confidence': 0.77, 'contour': [], 'bounding_box': (867, 562, 22, 20), 'area': 440},
    {'shape': 'ellipse', 'center': (339, 558), 'dimensions': (19, 74), 'confidence': 0.71, 'contour': [], 'bounding_box': (329.5, 521, 19, 74), 'area': 1406},
    {'shape': 'polygon', 'center': (1104, 774), 'dimensions': (88, 557), 'confidence': 0.85, 'contour': [], 'bounding_box': (1060, 495.5, 88, 557), 'area': 48916},
    {'shape': 'rectangle', 'center': (999, 777), 'dimensions': (129, 558), 'confidence': 1.00, 'contour': [], 'bounding_box': (934.5, 498, 129, 558), 'area': 71982},
    {'shape': 'rectangle', 'center': (876, 595), 'dimensions': (41, 194), 'confidence': 1.00, 'contour': [], 'bounding_box': (855.5, 498, 41, 194), 'area': 7954},
    {'shape': 'rectangle', 'center': (1044, 449), 'dimensions': (42, 96), 'confidence': 1.00, 'contour': [], 'bounding_box': (1023, 401, 42, 96), 'area': 4032},
    {'shape': 'rectangle', 'center': (959, 449), 'dimensions': (41, 96), 'confidence': 1.00, 'contour': [], 'bounding_box': (938.5, 401, 41, 96), 'area': 3936},
    {'shape': 'polygon', 'center': (802, 399), 'dimensions': (15, 40), 'confidence': 0.76, 'contour': [], 'bounding_box': (794.5, 379, 15, 40), 'area': 600},
    {'shape': 'polygon', 'center': (775, 395), 'dimensions': (15, 30), 'confidence': 0.83, 'contour': [], 'bounding_box': (767.5, 380, 15, 30), 'area': 450},
    {'shape': 'rectangle', 'center': (801, 436), 'dimensions': (27, 121), 'confidence': 1.00, 'contour': [], 'bounding_box': (787.5, 375.5, 27, 121), 'area': 3267},
    {'shape': 'rectangle', 'center': (773, 435), 'dimensions': (27, 121), 'confidence': 1.00, 'contour': [], 'bounding_box': (759.5, 374.5, 27, 121), 'area': 3267},
    {'shape': 'rectangle', 'center': (745, 436), 'dimensions': (27, 121), 'confidence': 1.00, 'contour': [], 'bounding_box': (731.5, 375.5, 27, 121), 'area': 3267},
    {'shape': 'rectangle', 'center': (716, 435), 'dimensions': (27, 121), 'confidence': 1.00, 'contour': [], 'bounding_box': (702.5, 374.5, 27, 121), 'area': 3267},
    {'shape': 'rectangle', 'center': (688, 435), 'dimensions': (27, 121), 'confidence': 1.00, 'contour': [], 'bounding_box': (674.5, 374.5, 27, 121), 'area': 3267},
    {'shape': 'rectangle', 'center': (661, 435), 'dimensions': (27, 121), 'confidence': 1.00, 'contour': [], 'bounding_box': (647.5, 374.5, 27, 121), 'area': 3267},
    {'shape': 'rectangle', 'center': (539, 365), 'dimensions': (26, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (526, 345, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (511, 364), 'dimensions': (26, 40), 'confidence': 0.73, 'contour': [], 'bounding_box': (498, 344, 26, 40), 'area': 1040},
    {'shape': 'rectangle', 'center': (483, 364), 'dimensions': (26, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (470, 344, 26, 40), 'area': 1040},
    {'shape': 'rectangle', 'center': (456, 364), 'dimensions': (26, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (443, 344, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (428, 364), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (415, 344, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (400, 364), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (387, 344, 26, 40), 'area': 1040},
    {'shape': 'rectangle', 'center': (372, 364), 'dimensions': (27, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (358.5, 344, 27, 40), 'area': 1080},
    {'shape': 'rectangle', 'center': (343, 364), 'dimensions': (27, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (329.5, 344, 27, 40), 'area': 1080},
    {'shape': 'rectangle', 'center': (315, 364), 'dimensions': (27, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (301.5, 344, 27, 40), 'area': 1080},
    {'shape': 'rectangle', 'center': (287, 364), 'dimensions': (26, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (274, 344, 26, 40), 'area': 1040},
    {'shape': 'square', 'center': (166, 336), 'dimensions': (21, 24), 'confidence': 0.75, 'contour': [], 'bounding_box': (155.5, 324, 21, 24), 'area': 504},
    {'shape': 'polygon', 'center': (1050, 332), 'dimensions': (9, 21), 'confidence': 0.85, 'contour': [], 'bounding_box': (1045.5, 321.5, 9, 21), 'area': 189},
    {'shape': 'polygon', 'center': (1041, 332), 'dimensions': (8, 20), 'confidence': 0.86, 'contour': [], 'bounding_box': (1037, 322, 8, 20), 'area': 160},
    {'shape': 'polygon', 'center': (540, 317), 'dimensions': (13, 17), 'confidence': 0.81, 'contour': [], 'bounding_box': (533.5, 308.5, 13, 17), 'area': 221},
    {'shape': 'rectangle', 'center': (960, 351), 'dimensions': (41, 96), 'confidence': 1.00, 'contour': [], 'bounding_box': (939.5, 303, 41, 96), 'area': 3936},
    {'shape': 'rectangle', 'center': (878, 400), 'dimensions': (41, 194), 'confidence': 1.00, 'contour': [], 'bounding_box': (857.5, 303, 41, 194), 'area': 7954},
    {'shape': 'rectangle', 'center': (834, 401), 'dimensions': (42, 193), 'confidence': 0.87, 'contour': [], 'bounding_box': (813, 304.5, 42, 193), 'area': 8106},
    {'shape': 'rectangle', 'center': (802, 338), 'dimensions': (27, 70), 'confidence': 1.00, 'contour': [], 'bounding_box': (788.5, 303, 27, 70), 'area': 1890},
    {'shape': 'ellipse', 'center': (539, 323), 'dimensions': (25, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (526.5, 303, 25, 40), 'area': 1000},
    {'shape': 'rectangle', 'center': (774, 338), 'dimensions': (27, 71), 'confidence': 1.00, 'contour': [], 'bounding_box': (760.5, 302.5, 27, 71), 'area': 1917},
    {'shape': 'rectangle', 'center': (746, 338), 'dimensions': (27, 71), 'confidence': 1.00, 'contour': [], 'bounding_box': (732.5, 302.5, 27, 71), 'area': 1917},
    {'shape': 'polygon', 'center': (717, 337), 'dimensions': (27, 71), 'confidence': 0.82, 'contour': [], 'bounding_box': (703.5, 301.5, 27, 71), 'area': 1917},
    {'shape': 'polygon', 'center': (689, 337), 'dimensions': (27, 71), 'confidence': 0.82, 'contour': [], 'bounding_box': (675.5, 301.5, 27, 71), 'area': 1917},
    {'shape': 'polygon', 'center': (661, 338), 'dimensions': (27, 71), 'confidence': 0.80, 'contour': [], 'bounding_box': (647.5, 302.5, 27, 71), 'area': 1917},
    {'shape': 'rectangle', 'center': (617, 402), 'dimensions': (56, 194), 'confidence': 1.00, 'contour': [], 'bounding_box': (589, 305, 56, 194), 'area': 10864},
    {'shape': 'triangle', 'center': (498, 323), 'dimensions': (5, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (495.5, 303, 5, 40), 'area': 100},
    {'shape': 'rectangle', 'center': (484, 322), 'dimensions': (26, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (471, 302, 26, 40), 'area': 1040},
    {'shape': 'rectangle', 'center': (456, 322), 'dimensions': (26, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (443, 302, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (429, 322), 'dimensions': (26, 40), 'confidence': 0.71, 'contour': [], 'bounding_box': (416, 302, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (400, 322), 'dimensions': (27, 40), 'confidence': 0.74, 'contour': [], 'bounding_box': (386.5, 302, 27, 40), 'area': 1080},
    {'shape': 'ellipse', 'center': (372, 322), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (359, 302, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (344, 322), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (331, 302, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (316, 322), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (303, 302, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (288, 322), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (275, 302, 26, 40), 'area': 1040},
    {'shape': 'polygon', 'center': (962, 293), 'dimensions': (40, 20), 'confidence': 0.77, 'contour': [], 'bounding_box': (942, 283, 40, 20), 'area': 800},
    {'shape': 'polygon', 'center': (146, 287), 'dimensions': (17, 11), 'confidence': 0.87, 'contour': [], 'bounding_box': (137.5, 281.5, 17, 11), 'area': 187},
    {'shape': 'square', 'center': (166, 278), 'dimensions': (20, 24), 'confidence': 0.77, 'contour': [], 'bounding_box': (156, 266, 20, 24), 'area': 480},
    {'shape': 'ellipse', 'center': (540, 281), 'dimensions': (26, 40), 'confidence': 0.74, 'contour': [], 'bounding_box': (527, 261, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (512, 281), 'dimensions': (26, 39), 'confidence': 0.75, 'contour': [], 'bounding_box': (499, 261.5, 26, 39), 'area': 1014},
    {'shape': 'rectangle', 'center': (484, 281), 'dimensions': (26, 39), 'confidence': 1.00, 'contour': [], 'bounding_box': (471, 261.5, 26, 39), 'area': 1014},
    {'shape': 'rectangle', 'center': (457, 280), 'dimensions': (26, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (444, 260, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (429, 280), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (416, 260, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (401, 280), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (388, 260, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (372, 280), 'dimensions': (27, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (358.5, 260, 27, 40), 'area': 1080},
    {'shape': 'ellipse', 'center': (344, 280), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (331, 260, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (316, 280), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (303, 260, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (288, 280), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (275, 260, 26, 40), 'area': 1040},
    {'shape': 'triangle', 'center': (443, 278), 'dimensions': (6, 42), 'confidence': 0.93, 'contour': [], 'bounding_box': (440, 257, 6, 42), 'area': 126},
    {'shape': 'rectangle', 'center': (413, 322), 'dimensions': (285, 131), 'confidence': 1.00, 'contour': [], 'bounding_box': (270.5, 256.5, 285, 131), 'area': 37335},
    {'shape': 'triangle', 'center': (986, 255), 'dimensions': (7, 37), 'confidence': 1.00, 'contour': [], 'bounding_box': (982.5, 236.5, 7, 37), 'area': 129.5},
    {'shape': 'triangle', 'center': (982, 235), 'dimensions': (5, 39), 'confidence': 1.00, 'contour': [], 'bounding_box': (979.5, 215.5, 5, 39), 'area': 97.5},
    {'shape': 'polygon', 'center': (963, 214), 'dimensions': (40, 20), 'confidence': 0.74, 'contour': [], 'bounding_box': (943, 204, 40, 20), 'area': 800},
    {'shape': 'polygon', 'center': (148, 207), 'dimensions': (17, 11), 'confidence': 0.87, 'contour': [], 'bounding_box': (139.5, 201.5, 17, 11), 'area': 187},
    {'shape': 'rectangle', 'center': (1131, 304), 'dimensions': (45, 389), 'confidence': 1.00, 'contour': [], 'bounding_box': (1108.5, 109.5, 45, 389), 'area': 17505},
    {'shape': 'rectangle', 'center': (1047, 205), 'dimensions': (43, 194), 'confidence': 1.00, 'contour': [], 'bounding_box': (1025.5, 108, 43, 194), 'area': 8342},
    {'shape': 'rectangle', 'center': (880, 204), 'dimensions': (41, 194), 'confidence': 1.00, 'contour': [], 'bounding_box': (859.5, 107, 41, 194), 'area': 7954},
    {'shape': 'rectangle', 'center': (802, 204), 'dimensions': (31, 194), 'confidence': 1.00, 'contour': [], 'bounding_box': (786.5, 107, 31, 194), 'area': 6014},
    {'shape': 'ellipse', 'center': (689, 204), 'dimensions': (192, 195), 'confidence': 0.77, 'contour': [], 'bounding_box': (593, 106.5, 192, 195), 'area': 37440},
    {'shape': 'triangle', 'center': (901, 121), 'dimensions': (6, 34), 'confidence': 0.93, 'contour': [], 'bounding_box': (898, 104, 6, 34), 'area': 102},
    {'shape': 'ellipse', 'center': (616, 879), 'dimensions': (1188, 1668), 'confidence': 0.79, 'contour': [], 'bounding_box': (22, 55, 1188, 1668), 'area': 1981632},
    {'shape': 'circle', 'center': (1049, 1674), 'dimensions': (16, 12), 'confidence': 0.81, 'contour': [], 'bounding_box': (1041, 1668, 16, 12), 'area': 192, 'radius': 8, 'circularity': 0.95},
    {'shape': 'circle', 'center': (924, 1625), 'dimensions': (19, 16), 'confidence': 0.78, 'contour': [], 'bounding_box': (914.5, 1617, 19, 16), 'area': 304, 'radius': 9.5, 'circularity': 0.92},
    {'shape': 'circle', 'center': (1091, 983), 'dimensions': (13, 13), 'confidence': 0.91, 'contour': [], 'bounding_box': (1084.5, 976.5, 13, 13), 'area': 169, 'radius': 6.5, 'circularity': 0.96},
    {'shape': 'circle', 'center': (272, 781), 'dimensions': (15, 11), 'confidence': 0.79, 'contour': [], 'bounding_box': (264.5, 775.5, 15, 11), 'area': 165, 'radius': 7.5, 'circularity': 0.88},
    {'shape': 'circle', 'center': (143, 431), 'dimensions': (17, 12), 'confidence': 0.78, 'contour': [], 'bounding_box': (134.5, 425, 17, 12), 'area': 204, 'radius': 8.5, 'circularity': 0.89},
    {'shape': 'circle', 'center': (776, 339), 'dimensions': (15, 10), 'confidence': 0.81, 'contour': [], 'bounding_box': (768.5, 334, 15, 10), 'area': 150, 'radius': 7.5, 'circularity': 0.87},
    {'shape': 'circle', 'center': (748, 339), 'dimensions': (15, 10), 'confidence': 0.82, 'contour': [], 'bounding_box': (740.5, 334, 15, 10), 'area': 150, 'radius': 7.5, 'circularity': 0.88},
    {'shape': 'circle', 'center': (147, 225), 'dimensions': (17, 12), 'confidence': 0.79, 'contour': [], 'bounding_box': (138.5, 219, 17, 12), 'area': 204, 'radius': 8.5, 'circularity': 0.89},
    {'shape': 'circle', 'center': (1063, 86), 'dimensions': (16, 12), 'confidence': 0.88, 'contour': [], 'bounding_box': (1055, 80, 16, 12), 'area': 192, 'radius': 8, 'circularity': 0.94}
]

print("当前系统输出特征分析:")
print(f"总特征数量: {len(detected_features)}")
circle_features = [f for f in detected_features if f['shape'] == 'circle']
print(f"圆形特征数量: {len(circle_features)}")

for i, f in enumerate(circle_features):
    print(f"  圆形特征 {i+1}: 位置{f['center']}, 半径{f.get('radius', 'N/A')}")

# 使用最新用户描述
user_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征，使用点孔、钻孔、沉孔工艺。坐标原点（0,0）选择正视图φ234的圆的圆心最高点。"
drawing_text = "图纸比例尺 4.001"

print(f"\n用户描述: {user_description}")

# 使用坐标基准策略
print("\n使用坐标基准策略: highest_y")
reference_point = select_coordinate_reference(detected_features, strategy="highest_y")
print(f"设置坐标原点为: {reference_point}")

# 调整坐标系统
adjusted_features = adjust_coordinate_system(detected_features, reference_point, "highest_y")

# 识别沉孔特征
counterbore_features = identify_counterbore_features(adjusted_features, user_description, drawing_text)
actual_counterbore_features = [f for f in counterbore_features if f.get("shape") == "counterbore"]

print(f"\n识别到的沉孔特征数量: {len(actual_counterbore_features)}")
for i, f in enumerate(actual_counterbore_features):
    print(f"  沉孔 {i+1}: 位置{f['center']}, 外径{f['outer_diameter']:.1f}, 内径{f['inner_diameter']:.1f}")

# 生成NC代码
description_analysis = {
    'description': user_description,
    'processing_type': 'counterbore',
    'depth': 20.0,
    'feed_rate': 100.0
}

nc_code = generate_fanuc_nc(actual_counterbore_features, description_analysis)

# 检查生成的代码中的孔数量
lines = nc_code.split('\n')
hole_lines = [line for line in lines if 'HOLE' in line and 'POSITION' in line and 'COUNTERBORE PROCESS' not in line]
print(f"\n生成的G代码中孔加工指令数量: {len(hole_lines)}")

for line in hole_lines:
    print(f"  {line.strip()}")

if len(actual_counterbore_features) != 3:
    print(f"\n❌ 问题: 期望3个沉孔特征，但识别到{len(actual_counterbore_features)}个")
else:
    print(f"\n✅ 成功: 识别到正确的{len(actual_counterbore_features)}个沉孔特征")

print(f"\n参考信息: 用户期望的极坐标位置为 X94.0Y-30.0 Y90.0 Y210.0")
