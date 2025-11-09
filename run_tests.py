"""
测试运行器
"""
import unittest
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入测试模块
import test_framework
import test_models
import test_rss_collector
import test_app


def run_all_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试模块
    test_modules = [
        test_models,
        test_rss_collector,
        test_app
    ]

    for module in test_modules:
        suite.addTests(loader.loadTestsFromModule(module))

    # 运行测试
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )

    result = runner.run(suite)

    # 返回测试结果
    return result.wasSuccessful()


def run_specific_tests(test_module_names):
    """运行指定模块的测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    module_mapping = {
        'models': test_models,
        'rss_collector': test_rss_collector,
        'app': test_app
    }

    for module_name in test_module_names:
        if module_name in module_mapping:
            module = module_mapping[module_name]
            suite.addTests(loader.loadTestsFromModule(module))
            print(f"添加测试模块: {module_name}")
        else:
            print(f"未找到测试模块: {module_name}")

    # 运行测试
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True
    )

    result = runner.run(suite)
    return result.wasSuccessful()


def print_usage():
    """打印使用说明"""
    print("测试运行器使用说明:")
    print("  python run_tests.py              # 运行所有测试")
    print("  python run_tests.py models      # 运行模型测试")
    print("  python run_tests.py rss_collector # 运行RSS收集器测试")
    print("  python run_tests.py app         # 运行Flask应用测试")
    print("  python run_tests.py models app  # 运行多个模块测试")


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        # 运行所有测试
        success = run_all_tests()
    else:
        # 运行指定测试
        test_modules = sys.argv[1:]
        if test_modules[0] in ['help', '-h', '--help']:
            print_usage()
            sys.exit(0)

        success = run_specific_tests(test_modules)

    # 退出码
    sys.exit(0 if success else 1)