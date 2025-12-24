import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.modules.feature_definition import identify_counterbore_features, select_coordinate_reference, adjust_coordinate_system
from src.modules.gcode_generation import generate_fanuc_nc

# 模拟从系统输出中提取的特征数据
detected_features = [
    {'shape': 'polygon', 'center': (1135, 1638), 'dimensions': (12, 24), 'confidence': 0.86, 'contour': [], 'bounding_box': (1135-6, 1638-12, 12, 24), 'area': 288},
    {'shape': 'square', 'center': (1124, 1638), 'dimensions': (32, 35), 'confidence': 1.00, 'contour': [], 'bounding_box': (1124-16, 1638-17.5, 32, 35), 'area': 1120},
    {'shape': 'square', 'center': (1090, 1638), 'dimensions': (32, 35), 'confidence': 1.00, 'contour': [], 'bounding_box': (1090-16, 1638-17.5, 32, 35), 'area': 1120},
    {'shape': 'square', 'center': (988, 1637), 'dimensions': (32, 35), 'confidence': 1.00, 'contour': [], 'bounding_box': (988-16, 1637-17.5, 32, 35), 'area': 1120},
    {'shape': 'rectangle', 'center': (1125, 1583), 'dimensions': (20, 15), 'confidence': 0.86, 'contour': [], 'bounding_box': (1125-10, 1583-7.5, 20, 15), 'area': 300},
    {'shape': 'rectangle', 'center': (955, 1606), 'dimensions': (32, 96), 'confidence': 1.00, 'contour': [], 'bounding_box': (955-16, 1606-48, 32, 96), 'area': 3072},
    {'shape': 'rectangle', 'center': (922, 1606), 'dimensions': (32, 96), 'confidence': 1.00, 'contour': [], 'bounding_box': (922-16, 1606-48, 32, 96), 'area': 3072},
    {'shape': 'rectangle', 'center': (1124, 1572), 'dimensions': (32, 91), 'confidence': 1.00, 'contour': [], 'bounding_box': (1124-16, 1572-45.5, 32, 91), 'area': 2912},
    {'shape': 'rectangle', 'center': (1090, 1572), 'dimensions': (32, 91), 'confidence': 1.00, 'contour': [], 'bounding_box': (1090-16, 1572-45.5, 32, 91), 'area': 2912},
    {'shape': 'rectangle', 'center': (1056, 1573), 'dimensions': (32, 91), 'confidence': 1.00, 'contour': [], 'bounding_box': (1056-16, 1573-45.5, 32, 91), 'area': 2912},
    {'shape': 'rectangle', 'center': (1023, 1572), 'dimensions': (33, 90), 'confidence': 1.00, 'contour': [], 'bounding_box': (1023-16.5, 1572-45, 33, 90), 'area': 2970},
    {'shape': 'rectangle', 'center': (989, 1571), 'dimensions': (33, 91), 'confidence': 1.00, 'contour': [], 'bounding_box': (989-16.5, 1571-45.5, 33, 91), 'area': 3003},
    {'shape': 'rectangle', 'center': (956, 1508), 'dimensions': (31, 96), 'confidence': 1.00, 'contour': [], 'bounding_box': (956-15.5, 1508-48, 31, 96), 'area': 2976},
    {'shape': 'square', 'center': (751, 1301), 'dimensions': (15, 14), 'confidence': 0.78, 'contour': [], 'bounding_box': (751-7.5, 1301-7, 15, 14), 'area': 210},
    {'shape': 'polygon', 'center': (198, 1297), 'dimensions': (15, 15), 'confidence': 0.74, 'contour': [], 'bounding_box': (198-7.5, 1297-7.5, 15, 15), 'area': 225},
    {'shape': 'rectangle', 'center': (1125, 1396), 'dimensions': (34, 257), 'confidence': 1.00, 'contour': [], 'bounding_box': (1125-17, 1396-128.5, 34, 257), 'area': 8738},
    {'shape': 'rectangle', 'center': (1091, 1396), 'dimensions': (33, 257), 'confidence': 1.00, 'contour': [], 'bounding_box': (1091-16.5, 1396-128.5, 33, 257), 'area': 8481},
    {'shape': 'rectangle', 'center': (1057, 1396), 'dimensions': (33, 257), 'confidence': 1.00, 'contour': [], 'bounding_box': (1057-16.5, 1396-128.5, 33, 257), 'area': 8481},
    {'shape': 'rectangle', 'center': (1024, 1396), 'dimensions': (33, 258), 'confidence': 1.00, 'contour': [], 'bounding_box': (1024-16.5, 1396-129, 33, 258), 'area': 8514},
    {'shape': 'rectangle', 'center': (990, 1396), 'dimensions': (33, 258), 'confidence': 1.00, 'contour': [], 'bounding_box': (990-16.5, 1396-129, 33, 258), 'area': 8514},
    {'shape': 'rectangle', 'center': (287, 1191), 'dimensions': (34, 5), 'confidence': 0.99, 'contour': [], 'bounding_box': (287-17, 1191-2.5, 34, 5), 'area': 170},
    {'shape': 'rectangle', 'center': (1127, 1211), 'dimensions': (33, 110), 'confidence': 1.00, 'contour': [], 'bounding_box': (1127-16.5, 1211-55, 33, 110), 'area': 3630},
    {'shape': 'rectangle', 'center': (1093, 1211), 'dimensions': (33, 110), 'confidence': 1.00, 'contour': [], 'bounding_box': (1093-16.5, 1211-55, 33, 110), 'area': 3630},
    {'shape': 'rectangle', 'center': (1059, 1211), 'dimensions': (33, 110), 'confidence': 1.00, 'contour': [], 'bounding_box': (1059-16.5, 1211-55, 33, 110), 'area': 3630},
    {'shape': 'rectangle', 'center': (1025, 1210), 'dimensions': (33, 109), 'confidence': 1.00, 'contour': [], 'bounding_box': (1025-16.5, 1210-54.5, 33, 109), 'area': 3597},
    {'shape': 'ellipse', 'center': (991, 1210), 'dimensions': (32, 110), 'confidence': 0.76, 'contour': [], 'bounding_box': (991-16, 1210-55, 32, 110), 'area': 3520},
    {'shape': 'polygon', 'center': (285, 1159), 'dimensions': (35, 54), 'confidence': 0.84, 'contour': [], 'bounding_box': (285-17.5, 1159-27, 35, 54), 'area': 1890},
    {'shape': 'rectangle', 'center': (257, 1145), 'dimensions': (20, 26), 'confidence': 1.00, 'contour': [], 'bounding_box': (257-10, 1145-13, 20, 26), 'area': 520},
    {'shape': 'rectangle', 'center': (287, 1127), 'dimensions': (35, 5), 'confidence': 0.98, 'contour': [], 'bounding_box': (287-17.5, 1127-2.5, 35, 5), 'area': 175},
    {'shape': 'triangle', 'center': (366, 1124), 'dimensions': (55, 6), 'confidence': 0.92, 'contour': [], 'bounding_box': (366-27.5, 1124-3, 55, 6), 'area': 165},
    {'shape': 'rectangle', 'center': (1159, 1134), 'dimensions': (27, 54), 'confidence': 1.00, 'contour': [], 'bounding_box': (1159-13.5, 1134-27, 27, 54), 'area': 1458},
    {'shape': 'polygon', 'center': (466, 1160), 'dimensions': (126, 127), 'confidence': 0.87, 'contour': [], 'bounding_box': (466-63, 1160-63.5, 126, 127), 'area': 15942},
    {'shape': 'rectangle', 'center': (1128, 1107), 'dimensions': (33, 95), 'confidence': 1.00, 'contour': [], 'bounding_box': (1128-16.5, 1107-47.5, 33, 95), 'area': 3135},
    {'shape': 'rectangle', 'center': (1094, 1106), 'dimensions': (33, 95), 'confidence': 1.00, 'contour': [], 'bounding_box': (1094-16.5, 1106-47.5, 33, 95), 'area': 3135},
    {'shape': 'rectangle', 'center': (1059, 1106), 'dimensions': (33, 96), 'confidence': 1.00, 'contour': [], 'bounding_box': (1059-16.5, 1106-48, 33, 96), 'area': 3168},
    {'shape': 'rectangle', 'center': (1025, 1106), 'dimensions': (33, 96), 'confidence': 1.00, 'contour': [], 'bounding_box': (1025-16.5, 1106-48, 33, 96), 'area': 3168},
    {'shape': 'rectangle', 'center': (992, 1105), 'dimensions': (33, 96), 'confidence': 1.00, 'contour': [], 'bounding_box': (992-16.5, 1105-48, 33, 96), 'area': 3168},
    {'shape': 'triangle', 'center': (834, 1057), 'dimensions': (41, 5), 'confidence': 1.00, 'contour': [], 'bounding_box': (834-20.5, 1057-2.5, 41, 5), 'area': 102.5},
    {'shape': 'rectangle', 'center': (1159, 1078), 'dimensions': (27, 54), 'confidence': 1.00, 'contour': [], 'bounding_box': (1159-13.5, 1078-27, 27, 54), 'area': 1458},
    {'shape': 'polygon', 'center': (734, 1039), 'dimensions': (9, 17), 'confidence': 0.87, 'contour': [], 'bounding_box': (734-4.5, 1039-8.5, 9, 17), 'area': 153},
    {'shape': 'rectangle', 'center': (1116, 1015), 'dimensions': (4, 35), 'confidence': 0.95, 'contour': [], 'bounding_box': (1116-2, 1015-17.5, 4, 35), 'area': 140},
    {'shape': 'rectangle', 'center': (1160, 1022), 'dimensions': (27, 54), 'confidence': 1.00, 'contour': [], 'bounding_box': (1160-13.5, 1022-27, 27, 54), 'area': 1458},
    {'shape': 'rectangle', 'center': (1160, 966), 'dimensions': (27, 54), 'confidence': 1.00, 'contour': [], 'bounding_box': (1160-13.5, 966-27, 27, 54), 'area': 1458},
    {'shape': 'rectangle', 'center': (1162, 914), 'dimensions': (26, 51), 'confidence': 1.00, 'contour': [], 'bounding_box': (1162-13, 914-25.5, 26, 51), 'area': 1326},
    {'shape': 'rectangle', 'center': (1136, 893), 'dimensions': (19, 24), 'confidence': 0.93, 'contour': [], 'bounding_box': (1136-9.5, 893-12, 19, 24), 'area': 456},
    {'shape': 'polygon', 'center': (997, 892), 'dimensions': (28, 29), 'confidence': 0.73, 'contour': [], 'bounding_box': (997-14, 892-14.5, 28, 29), 'area': 812},
    {'shape': 'rectangle', 'center': (1136, 871), 'dimensions': (19, 24), 'confidence': 0.93, 'contour': [], 'bounding_box': (1136-9.5, 871-12, 19, 24), 'area': 456},
    {'shape': 'rectangle', 'center': (1162, 850), 'dimensions': (27, 53), 'confidence': 1.00, 'contour': [], 'bounding_box': (1162-13.5, 850-26.5, 27, 53), 'area': 1431},
    {'shape': 'rectangle', 'center': (873, 924), 'dimensions': (40, 264), 'confidence': 1.00, 'contour': [], 'bounding_box': (873-20, 924-132, 40, 264), 'area': 10560},
    {'shape': 'polygon', 'center': (697, 793), 'dimensions': (21, 13), 'confidence': 0.83, 'contour': [], 'bounding_box': (697-10.5, 793-6.5, 21, 13), 'area': 273},
    {'shape': 'square', 'center': (289, 788), 'dimensions': (17, 20), 'confidence': 0.76, 'contour': [], 'bounding_box': (289-8.5, 788-10, 17, 20), 'area': 340},
    {'shape': 'ellipse', 'center': (1162, 798), 'dimensions': (27, 55), 'confidence': 0.73, 'contour': [], 'bounding_box': (1162-13.5, 798-27.5, 27, 55), 'area': 1485},
    {'shape': 'rectangle', 'center': (468, 751), 'dimensions': (126, 16), 'confidence': 1.00, 'contour': [], 'bounding_box': (468-63, 751-8, 126, 16), 'area': 2016},
    {'shape': 'ellipse', 'center': (700, 752), 'dimensions': (20, 36), 'confidence': 0.74, 'contour': [], 'bounding_box': (700-10, 752-18, 20, 36), 'area': 720},
    {'shape': 'rectangle', 'center': (1162, 742), 'dimensions': (26, 54), 'confidence': 1.00, 'contour': [], 'bounding_box': (1162-13, 742-27, 26, 54), 'area': 1404},
    {'shape': 'ellipse', 'center': (169, 739), 'dimensions': (20, 47), 'confidence': 0.74, 'contour': [], 'bounding_box': (169-10, 739-23.5, 20, 47), 'area': 940},
    {'shape': 'polygon', 'center': (518, 723), 'dimensions': (17, 19), 'confidence': 0.85, 'contour': [], 'bounding_box': (518-8.5, 723-9.5, 17, 19), 'area': 323},
    {'shape': 'square', 'center': (700, 722), 'dimensions': (20, 20), 'confidence': 1.00, 'contour': [], 'bounding_box': (700-10, 722-10, 20, 20), 'area': 400},
    {'shape': 'ellipse', 'center': (874, 742), 'dimensions': (40, 96), 'confidence': 0.74, 'contour': [], 'bounding_box': (874-20, 742-48, 40, 96), 'area': 3840},
    {'shape': 'square', 'center': (169, 703), 'dimensions': (21, 20), 'confidence': 1.00, 'contour': [], 'bounding_box': (169-10.5, 703-10, 21, 20), 'area': 420},
    {'shape': 'rectangle', 'center': (236, 700), 'dimensions': (20, 16), 'confidence': 0.95, 'contour': [], 'bounding_box': (236-10, 700-8, 20, 16), 'area': 320},
    {'shape': 'polygon', 'center': (247, 692), 'dimensions': (7, 33), 'confidence': 0.78, 'contour': [], 'bounding_box': (247-3.5, 692-16.5, 7, 33), 'area': 231},
    {'shape': 'square', 'center': (594, 682), 'dimensions': (19, 17), 'confidence': 0.77, 'contour': [], 'bounding_box': (594-9.5, 682-8.5, 19, 17), 'area': 323},
    {'shape': 'square', 'center': (564, 686), 'dimensions': (42, 44), 'confidence': 1.00, 'contour': [], 'bounding_box': (564-21, 686-22, 42, 44), 'area': 1848},
    {'shape': 'polygon', 'center': (517, 691), 'dimensions': (35, 53), 'confidence': 0.88, 'contour': [], 'bounding_box': (517-17.5, 691-26.5, 35, 53), 'area': 1855},
    {'shape': 'rectangle', 'center': (398, 704), 'dimensions': (13, 75), 'confidence': 1.00, 'contour': [], 'bounding_box': (398-6.5, 704-37.5, 13, 75), 'area': 975},
    {'shape': 'ellipse', 'center': (1163, 687), 'dimensions': (27, 54), 'confidence': 0.74, 'contour': [], 'bounding_box': (1163-13.5, 687-27, 27, 54), 'area': 1458},
    {'shape': 'rectangle', 'center': (590, 660), 'dimensions': (84, 13), 'confidence': 1.00, 'contour': [], 'bounding_box': (590-42, 660-6.5, 84, 13), 'area': 1092},
    {'shape': 'polygon', 'center': (337, 669), 'dimensions': (29, 33), 'confidence': 0.85, 'contour': [], 'bounding_box': (337-14.5, 669-16.5, 29, 33), 'area': 957},
    {'shape': 'ellipse', 'center': (237, 649), 'dimensions': (21, 47), 'confidence': 0.74, 'contour': [], 'bounding_box': (237-10.5, 649-23.5, 21, 47), 'area': 987},
    {'shape': 'ellipse', 'center': (1163, 631), 'dimensions': (26, 54), 'confidence': 0.75, 'contour': [], 'bounding_box': (1163-13, 631-27, 26, 54), 'area': 1404},
    {'shape': 'square', 'center': (238, 614), 'dimensions': (21, 20), 'confidence': 1.00, 'contour': [], 'bounding_box': (238-10.5, 614-10, 21, 20), 'area': 420},
    {'shape': 'rectangle', 'center': (216, 611), 'dimensions': (21, 17), 'confidence': 1.00, 'contour': [], 'bounding_box': (216-10.5, 611-8.5, 21, 17), 'area': 357},
    {'shape': 'polygon', 'center': (653, 625), 'dimensions': (43, 54), 'confidence': 0.81, 'contour': [], 'bounding_box': (653-21.5, 625-27, 43, 54), 'area': 2322},
    {'shape': 'triangle', 'center': (608, 624), 'dimensions': (51, 53), 'confidence': 0.99, 'contour': [], 'bounding_box': (608-25.5, 624-26.5, 51, 53), 'area': 1351.5},
    {'shape': 'triangle', 'center': (561, 627), 'dimensions': (53, 54), 'confidence': 1.00, 'contour': [], 'bounding_box': (561-26.5, 627-27, 53, 54), 'area': 1431},
    {'shape': 'polygon', 'center': (469, 631), 'dimensions': (126, 68), 'confidence': 0.89, 'contour': [], 'bounding_box': (469-63, 631-34, 126, 68), 'area': 8568},
    {'shape': 'triangle', 'center': (381, 622), 'dimensions': (50, 50), 'confidence': 1.00, 'contour': [], 'bounding_box': (381-25, 622-25, 50, 50), 'area': 1250},
    {'shape': 'polygon', 'center': (611, 568), 'dimensions': (21, 10), 'confidence': 0.78, 'contour': [], 'bounding_box': (611-10.5, 568-5, 21, 10), 'area': 210},
    {'shape': 'polygon', 'center': (878, 572), 'dimensions': (22, 20), 'confidence': 0.77, 'contour': [], 'bounding_box': (878-11, 572-10, 22, 20), 'area': 440},
    {'shape': 'ellipse', 'center': (339, 558), 'dimensions': (19, 74), 'confidence': 0.71, 'contour': [], 'bounding_box': (339-9.5, 558-37, 19, 74), 'area': 1406},
    {'shape': 'polygon', 'center': (1104, 774), 'dimensions': (88, 557), 'confidence': 0.85, 'contour': [], 'bounding_box': (1104-44, 774-278.5, 88, 557), 'area': 48916},
    {'shape': 'rectangle', 'center': (999, 777), 'dimensions': (129, 558), 'confidence': 1.00, 'contour': [], 'bounding_box': (999-64.5, 777-279, 129, 558), 'area': 71982},
    {'shape': 'rectangle', 'center': (876, 595), 'dimensions': (41, 194), 'confidence': 1.00, 'contour': [], 'bounding_box': (876-20.5, 595-97, 41, 194), 'area': 7954},
    {'shape': 'rectangle', 'center': (1044, 449), 'dimensions': (42, 96), 'confidence': 1.00, 'contour': [], 'bounding_box': (1044-21, 449-48, 42, 96), 'area': 4032},
    {'shape': 'rectangle', 'center': (959, 449), 'dimensions': (41, 96), 'confidence': 1.00, 'contour': [], 'bounding_box': (959-20.5, 449-48, 41, 96), 'area': 3936},
    {'shape': 'polygon', 'center': (802, 399), 'dimensions': (15, 40), 'confidence': 0.76, 'contour': [], 'bounding_box': (802-7.5, 399-20, 15, 40), 'area': 600},
    {'shape': 'polygon', 'center': (775, 395), 'dimensions': (15, 30), 'confidence': 0.83, 'contour': [], 'bounding_box': (775-7.5, 395-15, 15, 30), 'area': 450},
    {'shape': 'rectangle', 'center': (801, 436), 'dimensions': (27, 121), 'confidence': 1.00, 'contour': [], 'bounding_box': (801-13.5, 436-60.5, 27, 121), 'area': 3267},
    {'shape': 'rectangle', 'center': (773, 435), 'dimensions': (27, 121), 'confidence': 1.00, 'contour': [], 'bounding_box': (773-13.5, 435-60.5, 27, 121), 'area': 3267},
    {'shape': 'rectangle', 'center': (745, 436), 'dimensions': (27, 121), 'confidence': 1.00, 'contour': [], 'bounding_box': (745-13.5, 436-60.5, 27, 121), 'area': 3267},
    {'shape': 'rectangle', 'center': (716, 435), 'dimensions': (27, 121), 'confidence': 1.00, 'contour': [], 'bounding_box': (716-13.5, 435-60.5, 27, 121), 'area': 3267},
    {'shape': 'rectangle', 'center': (688, 435), 'dimensions': (27, 121), 'confidence': 1.00, 'contour': [], 'bounding_box': (688-13.5, 435-60.5, 27, 121), 'area': 3267},
    {'shape': 'rectangle', 'center': (661, 435), 'dimensions': (27, 121), 'confidence': 1.00, 'contour': [], 'bounding_box': (661-13.5, 435-60.5, 27, 121), 'area': 3267},
    {'shape': 'rectangle', 'center': (539, 365), 'dimensions': (26, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (539-13, 365-20, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (511, 364), 'dimensions': (26, 40), 'confidence': 0.73, 'contour': [], 'bounding_box': (511-13, 364-20, 26, 40), 'area': 1040},
    {'shape': 'rectangle', 'center': (483, 364), 'dimensions': (26, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (483-13, 364-20, 26, 40), 'area': 1040},
    {'shape': 'rectangle', 'center': (456, 364), 'dimensions': (26, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (456-13, 364-20, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (428, 364), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (428-13, 364-20, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (400, 364), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (400-13, 364-20, 26, 40), 'area': 1040},
    {'shape': 'rectangle', 'center': (372, 364), 'dimensions': (27, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (372-13.5, 364-20, 27, 40), 'area': 1080},
    {'shape': 'rectangle', 'center': (343, 364), 'dimensions': (27, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (343-13.5, 364-20, 27, 40), 'area': 1080},
    {'shape': 'rectangle', 'center': (315, 364), 'dimensions': (27, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (315-13.5, 364-20, 27, 40), 'area': 1080},
    {'shape': 'rectangle', 'center': (287, 364), 'dimensions': (26, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (287-13, 364-20, 26, 40), 'area': 1040},
    {'shape': 'square', 'center': (166, 336), 'dimensions': (21, 24), 'confidence': 0.75, 'contour': [], 'bounding_box': (166-10.5, 336-12, 21, 24), 'area': 504},
    {'shape': 'polygon', 'center': (1050, 332), 'dimensions': (9, 21), 'confidence': 0.85, 'contour': [], 'bounding_box': (1050-4.5, 332-10.5, 9, 21), 'area': 189},
    {'shape': 'polygon', 'center': (1041, 332), 'dimensions': (8, 20), 'confidence': 0.86, 'contour': [], 'bounding_box': (1041-4, 332-10, 8, 20), 'area': 160},
    {'shape': 'polygon', 'center': (540, 317), 'dimensions': (13, 17), 'confidence': 0.81, 'contour': [], 'bounding_box': (540-6.5, 317-8.5, 13, 17), 'area': 221},
    {'shape': 'rectangle', 'center': (960, 351), 'dimensions': (41, 96), 'confidence': 1.00, 'contour': [], 'bounding_box': (960-20.5, 351-48, 41, 96), 'area': 3936},
    {'shape': 'rectangle', 'center': (878, 400), 'dimensions': (41, 194), 'confidence': 1.00, 'contour': [], 'bounding_box': (878-20.5, 400-97, 41, 194), 'area': 7954},
    {'shape': 'rectangle', 'center': (834, 401), 'dimensions': (42, 193), 'confidence': 0.87, 'contour': [], 'bounding_box': (834-21, 401-96.5, 42, 193), 'area': 8106},
    {'shape': 'rectangle', 'center': (802, 338), 'dimensions': (27, 70), 'confidence': 1.00, 'contour': [], 'bounding_box': (802-13.5, 338-35, 27, 70), 'area': 1890},
    {'shape': 'ellipse', 'center': (539, 323), 'dimensions': (25, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (539-12.5, 323-20, 25, 40), 'area': 1000},
    {'shape': 'rectangle', 'center': (774, 338), 'dimensions': (27, 71), 'confidence': 1.00, 'contour': [], 'bounding_box': (774-13.5, 338-35.5, 27, 71), 'area': 1917},
    {'shape': 'rectangle', 'center': (746, 338), 'dimensions': (27, 71), 'confidence': 1.00, 'contour': [], 'bounding_box': (746-13.5, 338-35.5, 27, 71), 'area': 1917},
    {'shape': 'polygon', 'center': (717, 337), 'dimensions': (27, 71), 'confidence': 0.82, 'contour': [], 'bounding_box': (717-13.5, 337-35.5, 27, 71), 'area': 1917},
    {'shape': 'polygon', 'center': (689, 337), 'dimensions': (27, 71), 'confidence': 0.82, 'contour': [], 'bounding_box': (689-13.5, 337-35.5, 27, 71), 'area': 1917},
    {'shape': 'polygon', 'center': (661, 338), 'dimensions': (27, 71), 'confidence': 0.80, 'contour': [], 'bounding_box': (661-13.5, 338-35.5, 27, 71), 'area': 1917},
    {'shape': 'rectangle', 'center': (617, 402), 'dimensions': (56, 194), 'confidence': 1.00, 'contour': [], 'bounding_box': (617-28, 402-97, 56, 194), 'area': 10864},
    {'shape': 'triangle', 'center': (498, 323), 'dimensions': (5, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (498-2.5, 323-20, 5, 40), 'area': 100},
    {'shape': 'rectangle', 'center': (484, 322), 'dimensions': (26, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (484-13, 322-20, 26, 40), 'area': 1040},
    {'shape': 'rectangle', 'center': (456, 322), 'dimensions': (26, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (456-13, 322-20, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (429, 322), 'dimensions': (26, 40), 'confidence': 0.71, 'contour': [], 'bounding_box': (429-13, 322-20, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (400, 322), 'dimensions': (27, 40), 'confidence': 0.74, 'contour': [], 'bounding_box': (400-13.5, 322-20, 27, 40), 'area': 1080},
    {'shape': 'ellipse', 'center': (372, 322), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (372-13, 322-20, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (344, 322), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (344-13, 322-20, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (316, 322), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (316-13, 322-20, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (288, 322), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (288-13, 322-20, 26, 40), 'area': 1040},
    {'shape': 'polygon', 'center': (962, 293), 'dimensions': (40, 20), 'confidence': 0.77, 'contour': [], 'bounding_box': (962-20, 293-10, 40, 20), 'area': 800},
    {'shape': 'polygon', 'center': (146, 287), 'dimensions': (17, 11), 'confidence': 0.87, 'contour': [], 'bounding_box': (146-8.5, 287-5.5, 17, 11), 'area': 187},
    {'shape': 'square', 'center': (166, 278), 'dimensions': (20, 24), 'confidence': 0.77, 'contour': [], 'bounding_box': (166-10, 278-12, 20, 24), 'area': 480},
    {'shape': 'ellipse', 'center': (540, 281), 'dimensions': (26, 40), 'confidence': 0.74, 'contour': [], 'bounding_box': (540-13, 281-20, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (512, 281), 'dimensions': (26, 39), 'confidence': 0.75, 'contour': [], 'bounding_box': (512-13, 281-19.5, 26, 39), 'area': 1014},
    {'shape': 'rectangle', 'center': (484, 281), 'dimensions': (26, 39), 'confidence': 1.00, 'contour': [], 'bounding_box': (484-13, 281-19.5, 26, 39), 'area': 1014},
    {'shape': 'rectangle', 'center': (457, 280), 'dimensions': (26, 40), 'confidence': 1.00, 'contour': [], 'bounding_box': (457-13, 280-20, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (429, 280), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (429-13, 280-20, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (401, 280), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (401-13, 280-20, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (372, 280), 'dimensions': (27, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (372-13.5, 280-20, 27, 40), 'area': 1080},
    {'shape': 'ellipse', 'center': (344, 280), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (344-13, 280-20, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (316, 280), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (316-13, 280-20, 26, 40), 'area': 1040},
    {'shape': 'ellipse', 'center': (288, 280), 'dimensions': (26, 40), 'confidence': 0.75, 'contour': [], 'bounding_box': (288-13, 280-20, 26, 40), 'area': 1040},
    {'shape': 'triangle', 'center': (443, 278), 'dimensions': (6, 42), 'confidence': 0.93, 'contour': [], 'bounding_box': (443-3, 278-21, 6, 42), 'area': 126},
    {'shape': 'rectangle', 'center': (413, 322), 'dimensions': (285, 131), 'confidence': 1.00, 'contour': [], 'bounding_box': (413-142.5, 322-65.5, 285, 131), 'area': 37335},
    {'shape': 'triangle', 'center': (986, 255), 'dimensions': (7, 37), 'confidence': 1.00, 'contour': [], 'bounding_box': (986-3.5, 255-18.5, 7, 37), 'area': 129.5},
    {'shape': 'triangle', 'center': (982, 235), 'dimensions': (5, 39), 'confidence': 1.00, 'contour': [], 'bounding_box': (982-2.5, 235-19.5, 5, 39), 'area': 97.5},
    {'shape': 'polygon', 'center': (963, 214), 'dimensions': (40, 20), 'confidence': 0.74, 'contour': [], 'bounding_box': (963-20, 214-10, 40, 20), 'area': 800},
    {'shape': 'polygon', 'center': (148, 207), 'dimensions': (17, 11), 'confidence': 0.87, 'contour': [], 'bounding_box': (148-8.5, 207-5.5, 17, 11), 'area': 187},
    {'shape': 'rectangle', 'center': (1131, 304), 'dimensions': (45, 389), 'confidence': 1.00, 'contour': [], 'bounding_box': (1131-22.5, 304-194.5, 45, 389), 'area': 17505},
    {'shape': 'rectangle', 'center': (1047, 205), 'dimensions': (43, 194), 'confidence': 1.00, 'contour': [], 'bounding_box': (1047-21.5, 205-97, 43, 194), 'area': 8342},
    {'shape': 'rectangle', 'center': (880, 204), 'dimensions': (41, 194), 'confidence': 1.00, 'contour': [], 'bounding_box': (880-20.5, 204-97, 41, 194), 'area': 7954},
    {'shape': 'rectangle', 'center': (802, 204), 'dimensions': (31, 194), 'confidence': 1.00, 'contour': [], 'bounding_box': (802-15.5, 204-97, 31, 194), 'area': 6014},
    {'shape': 'ellipse', 'center': (689, 204), 'dimensions': (192, 195), 'confidence': 0.77, 'contour': [], 'bounding_box': (689-96, 204-97.5, 192, 195), 'area': 37440},
    {'shape': 'triangle', 'center': (901, 121), 'dimensions': (6, 34), 'confidence': 0.93, 'contour': [], 'bounding_box': (901-3, 121-17, 6, 34), 'area': 102},
    {'shape': 'ellipse', 'center': (616, 879), 'dimensions': (1188, 1668), 'confidence': 0.79, 'contour': [], 'bounding_box': (616-594, 879-834, 1188, 1668), 'area': 1981632},
    {'shape': 'circle', 'center': (1049, 1674), 'dimensions': (16, 12), 'confidence': 0.81, 'contour': [], 'bounding_box': (1049-8, 1674-6, 16, 12), 'area': 192, 'radius': 8, 'circularity': 0.95},
    {'shape': 'circle', 'center': (924, 1625), 'dimensions': (19, 16), 'confidence': 0.78, 'contour': [], 'bounding_box': (924-9.5, 1625-8, 19, 16), 'area': 304, 'radius': 9.5, 'circularity': 0.92},
    {'shape': 'circle', 'center': (1091, 983), 'dimensions': (13, 13), 'confidence': 0.91, 'contour': [], 'bounding_box': (1091-6.5, 983-6.5, 13, 13), 'area': 169, 'radius': 6.5, 'circularity': 0.96},
    {'shape': 'circle', 'center': (272, 781), 'dimensions': (15, 11), 'confidence': 0.79, 'contour': [], 'bounding_box': (272-7.5, 781-5.5, 15, 11), 'area': 165, 'radius': 7.5, 'circularity': 0.88},
    {'shape': 'circle', 'center': (143, 431), 'dimensions': (17, 12), 'confidence': 0.78, 'contour': [], 'bounding_box': (143-8.5, 431-6, 17, 12), 'area': 204, 'radius': 8.5, 'circularity': 0.89},
    {'shape': 'circle', 'center': (776, 339), 'dimensions': (15, 10), 'confidence': 0.81, 'contour': [], 'bounding_box': (776-7.5, 339-5, 15, 10), 'area': 150, 'radius': 7.5, 'circularity': 0.87},
    {'shape': 'circle', 'center': (748, 339), 'dimensions': (15, 10), 'confidence': 0.82, 'contour': [], 'bounding_box': (748-7.5, 339-5, 15, 10), 'area': 150, 'radius': 7.5, 'circularity': 0.88},
    {'shape': 'circle', 'center': (147, 225), 'dimensions': (17, 12), 'confidence': 0.79, 'contour': [], 'bounding_box': (147-8.5, 225-6, 17, 12), 'area': 204, 'radius': 8.5, 'circularity': 0.89},
    {'shape': 'circle', 'center': (1063, 86), 'dimensions': (16, 12), 'confidence': 0.88, 'contour': [], 'bounding_box': (1063-8, 86-6, 16, 12), 'area': 192, 'radius': 8, 'circularity': 0.94}
]

print("模拟系统输出特征分析:")
print(f"总特征数量: {len(detected_features)}")
circle_features = [f for f in detected_features if f['shape'] == 'circle']
print(f"圆形特征数量: {len(circle_features)}")

for i, f in enumerate(circle_features):
    print(f"  圆形特征 {i+1}: 位置{f['center']}, 半径{f.get('radius', 'N/A')}")

# 提取用户描述和处理相关信息
user_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征，使用点孔、钻孔、沉孔工艺。坐标原点（0,0）选择正视图φ234的圆的圆心最高点。"
drawing_text = "图纸比例尺 4.001"

print(f"\n用户描述: {user_description}")

# 使用最高Y坐标点作为原点的策略
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
    print(f"\n❌ 问题仍然存在: 期望3个沉孔特征，但识别到{len(actual_counterbore_features)}个")
else:
    print(f"\n✅ 成功: 识别到正确的{len(actual_counterbore_features)}个沉孔特征")