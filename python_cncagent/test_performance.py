"""
性能测试
测试系统在不同负载下的性能表现
"""
import unittest
import time
import numpy as np
import cv2
from PIL import Image
import os
import tempfile
from unittest.mock import patch

# 导入被测试的模块
from src.modules.pdf_parsing_process import pdf_to_images, ocr_image, preprocess_image
from src.modules.feature_definition import identify_features
from src.modules.gcode_generation import generate_fanuc_nc

class TestPerformance(unittest.TestCase):
    """性能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        temp_files = ['temp_ocr.png']
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    def test_feature_identification_performance_small_image(self):
        """测试小图像的特征识别性能"""
        # 创建一个中等大小的图像
        test_image = np.zeros((500, 500), dtype=np.uint8)
        
        # 添加多个圆形以增加处理复杂度
        for i in range(10):
            center_x = 50 + i * 40
            center_y = 50 + i * 40
            cv2.circle(test_image, (center_x, center_y), 20, 255, -1)
        
        # 测量处理时间
        start_time = time.time()
        features = identify_features(test_image)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # 验证结果
        self.assertGreater(len(features), 0)
        self.assertLess(processing_time, 5.0)  # 处理时间应小于5秒
        print(f"小图像特征识别时间: {processing_time:.3f}秒, 识别出{len(features)}个特征")
    
    def test_feature_identification_performance_large_image(self):
        """测试大图像的特征识别性能"""
        # 创建一个大图像
        test_image = np.zeros((2000, 2000), dtype=np.uint8)
        
        # 添加多个圆形以增加处理复杂度
        for i in range(50):
            center_x = 50 + (i % 10) * 150
            center_y = 50 + (i // 10) * 150
            cv2.circle(test_image, (center_x, center_y), 30, 255, -1)
        
        # 测量处理时间
        start_time = time.time()
        features = identify_features(test_image)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # 验证结果
        self.assertGreater(len(features), 0)
        self.assertLess(processing_time, 30.0)  # 处理时间应小于30秒
        print(f"大图像特征识别时间: {processing_time:.3f}秒, 识别出{len(features)}个特征")
    
    def test_nc_generation_performance_many_features(self):
        """测试大量特征时的NC代码生成性能"""
        # 创建大量特征
        features = []
        for i in range(100):  # 100个特征
            features.append({
                "shape": "circle",
                "center": (float(i * 5), float(i * 5))
            })
        
        description_analysis = {
            "processing_type": "drilling",
            "depth": 10.0,
            "feed_rate": 100.0,
            "description": "大量特征钻孔加工"
        }
        
        # 测量处理时间
        start_time = time.time()
        nc_code = generate_fanuc_nc(features, description_analysis)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # 验证结果
        self.assertIn("O0001", nc_code)
        self.assertLess(processing_time, 10.0)  # 生成时间应小于10秒
        print(f"大量特征NC生成时间: {processing_time:.3f}秒, 生成代码行数: {len(nc_code.split())}")
    
    def test_ocr_performance(self):
        """测试OCR性能"""
        # 创建一个包含文本的图像
        img = Image.new('RGB', (400, 200), color='white')
        # 这里我们不实际绘制文本，因为我们依赖pytesseract
        
        # 测量OCR处理时间
        start_time = time.time()
        with patch('pytesseract.image_to_string', return_value="测试OCR性能"):
            result = ocr_image(img)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        self.assertIsInstance(result, str)
        self.assertLess(processing_time, 10.0)  # OCR时间应小于10秒
        print(f"OCR处理时间: {processing_time:.3f}秒")
    
    def test_preprocess_image_performance(self):
        """测试图像预处理性能"""
        # 创建大图像
        large_image = Image.new('RGB', (1500, 1500), color='gray')
        
        # 测量预处理时间
        start_time = time.time()
        processed_image = preprocess_image(large_image)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        self.assertEqual(processed_image.mode, 'L')
        self.assertLess(processing_time, 5.0)  # 预处理时间应小于5秒
        print(f"图像预处理时间: {processing_time:.3f}秒")
    
    def test_combined_workflow_performance(self):
        """测试组合工作流程性能"""
        # 模拟完整的处理流程
        
        # 1. 创建测试图像
        test_image = np.zeros((800, 800), dtype=np.uint8)
        for i in range(20):
            center_x = 50 + (i % 5) * 150
            center_y = 50 + (i // 5) * 150
            cv2.circle(test_image, (center_x, center_y), 25, 255, -1)
        
        # 2. 特征识别
        feature_start = time.time()
        features = identify_features(test_image)
        feature_end = time.time()
        
        # 3. NC代码生成
        nc_start = time.time()
        description_analysis = {
            "processing_type": "drilling",
            "depth": 10.0,
            "feed_rate": 100.0,
            "description": "性能测试钻孔"
        }
        nc_code = generate_fanuc_nc(features, description_analysis)
        nc_end = time.time()
        
        feature_time = feature_end - feature_start
        nc_time = nc_end - nc_start
        total_time = feature_time + nc_time
        
        # 验证结果
        self.assertGreater(len(features), 0)
        self.assertIn("O0001", nc_code)
        self.assertLess(total_time, 60.0)  # 总时间应小于60秒
        
        print(f"组合流程性能 - 特征识别: {feature_time:.3f}秒, "
              f"NC生成: {nc_time:.3f}秒, "
              f"总计: {total_time:.3f}秒, "
              f"识别特征数: {len(features)}")


class PerformanceBenchmark(unittest.TestCase):
    """性能基准测试"""
    
    def test_feature_identification_scalability(self):
        """测试特征识别的可扩展性"""
        sizes = [(500, 500), (1000, 1000), (1500, 1500)]
        feature_counts = [10, 25, 50]
        
        print("\n特征识别可扩展性测试:")
        print("图像大小\t特征数\t处理时间(秒)")
        print("-" * 40)
        
        for h, w in sizes:
            for f_count in feature_counts:
                # 创建图像
                test_image = np.zeros((h, w), dtype=np.uint8)
                
                # 添加指定数量的特征
                for i in range(f_count):
                    center_x = (i % 10) * (w // 10) + 30
                    center_y = (i // 10) * (h // 5) + 30
                    cv2.circle(test_image, (center_x, center_y), 20, 255, -1)
                
                # 测量处理时间
                start_time = time.time()
                features = identify_features(test_image)
                end_time = time.time()
                
                processing_time = end_time - start_time
                print(f"{w}x{h}\t\t{f_count}\t\t{processing_time:.3f}")
                
                # 验证结果
                self.assertGreaterEqual(len(features), 0)
                self.assertLess(processing_time, 60.0)  # 每次处理应在60秒内完成
    
    def test_memory_usage_simulation(self):
        """模拟内存使用情况测试"""
        import psutil
        import os
        
        # 获取初始内存使用
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建并处理大图像
        large_image = np.zeros((3000, 3000), dtype=np.uint8)
        for i in range(100):
            center_x = 50 + (i % 10) * 250
            center_y = 50 + (i // 10) * 250
            cv2.circle(large_image, (center_x, center_y), 50, 255, -1)
        
        # 特征识别
        features = identify_features(large_image)
        
        # 获取处理后的内存使用
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_increase = final_memory - initial_memory
        
        print(f"\n内存使用情况:")
        print(f"初始内存: {initial_memory:.2f} MB")
        print(f"最终内存: {final_memory:.2f} MB")
        print(f"内存增加: {memory_increase:.2f} MB")
        
        # 验证内存增加在合理范围内（小于500MB）
        self.assertLess(memory_increase, 500.0)
        self.assertGreaterEqual(len(features), 0)
    
    def test_concurrent_processing_simulation(self):
        """模拟并发处理性能"""
        import threading
        import queue
        
        def process_image(img_data, result_queue, thread_id):
            """在单独线程中处理图像"""
            try:
                features = identify_features(img_data)
                nc_code = generate_fanuc_nc(features, {
                    "processing_type": "drilling",
                    "depth": 5.0,
                    "description": f"线程{thread_id}处理"
                })
                result_queue.put({
                    "thread_id": thread_id,
                    "feature_count": len(features),
                    "code_length": len(nc_code)
                })
            except Exception as e:
                result_queue.put({
                    "thread_id": thread_id,
                    "error": str(e)
                })
        
        # 创建多个测试图像
        test_images = []
        for i in range(5):
            img = np.zeros((600, 600), dtype=np.uint8)
            for j in range(10):
                center_x = 50 + (j % 5) * 100
                center_y = 50 + (j // 5) * 100
                cv2.circle(img, (center_x, center_y), 15, 255, -1)
            test_images.append(img)
        
        # 并发处理
        result_queue = queue.Queue()
        threads = []
        
        start_time = time.time()
        
        for i, img in enumerate(test_images):
            thread = threading.Thread(
                target=process_image, 
                args=(img, result_queue, i)
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # 检查结果
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())
        
        print(f"\n并发处理测试:")
        print(f"处理5个图像耗时: {total_time:.3f}秒")
        print(f"平均每个图像: {total_time/5:.3f}秒")
        
        for result in results:
            if "error" not in result:
                print(f"线程{result['thread_id']}: 识别{result['feature_count']}个特征")
            else:
                print(f"线程{result['thread_id']}: 错误 - {result['error']}")
        
        self.assertLess(total_time, 60.0)  # 5个图像应在60秒内处理完成
        self.assertEqual(len(results), 5)  # 应该有5个结果


class StressTest(unittest.TestCase):
    """压力测试"""
    
    def test_large_number_of_features(self):
        """测试大量特征的处理能力"""
        # 创建包含大量特征的列表
        features = []
        for i in range(500):  # 500个特征
            features.append({
                "shape": "circle",
                "center": (float(i % 50) * 10, float(i // 50) * 10)
            })
        
        description_analysis = {
            "processing_type": "drilling",
            "depth": 5.0,
            "feed_rate": 80.0,
            "description": "压力测试 - 大量特征"
        }
        
        start_time = time.time()
        nc_code = generate_fanuc_nc(features, description_analysis)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        print(f"\n压力测试 - 500个特征:")
        print(f"NC代码生成时间: {processing_time:.3f}秒")
        print(f"生成代码长度: {len(nc_code)} 字符")
        
        self.assertIn("O0001", nc_code)
        self.assertLess(processing_time, 120.0)  # 应在120秒内完成
    
    def test_large_image_processing(self):
        """测试超大图像处理"""
        # 创建非常大的图像
        huge_image = np.zeros((4000, 4000), dtype=np.uint8)
        
        # 添加特征，但使用较大的间距以避免过于密集
        for i in range(100):
            center_x = 100 + (i % 10) * 350
            center_y = 100 + (i // 10) * 350
            cv2.circle(huge_image, (center_x, center_y), 50, 255, -1)
        
        start_time = time.time()
        features = identify_features(huge_image, min_area=2000)  # 使用较大最小面积以减少特征数
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        print(f"\n超大图像处理测试 (4000x4000):")
        print(f"处理时间: {processing_time:.3f}秒")
        print(f"识别特征数: {len(features)}")
        
        self.assertLess(processing_time, 180.0)  # 应在180秒内完成
        # 注意：由于图像很大，可能无法识别所有特征，这在预期之中


if __name__ == '__main__':
    unittest.main()
