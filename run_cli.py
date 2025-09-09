"""
CLI应用启动脚本

用于启动全景标注工具的命令行界面
"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    # 导入核心模块
    from src.core.app import create_app, get_app
    from src.core.config import get_config
    from src.core.logger import initialize_logging, get_logger
    from src.core.exceptions import handle_exception
    from src.core.utils import FileUtils, ValidationUtils
    
    # 导入CLI模块
    from src.cli.main import CLIApplication
    
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保已安装所有依赖包：pip install -r requirements.txt")
    sys.exit(1)


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='全景标注工具 - 命令行界面',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # 基本参数
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='配置文件路径'
    )
    
    parser.add_argument(
        '--log-level', '-l',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='日志级别'
    )
    
    parser.add_argument(
        '--data-dir', '-d',
        type=str,
        help='数据目录路径'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        help='输出目录路径'
    )
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 处理图像命令
    process_parser = subparsers.add_parser('process', help='处理图像')
    process_parser.add_argument('input', help='输入图像路径')
    process_parser.add_argument('--output', help='输出文件路径')
    process_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='输出格式')
    
    # 批量处理命令
    batch_parser = subparsers.add_parser('batch', help='批量处理')
    batch_parser.add_argument('input_dir', help='输入目录路径')
    batch_parser.add_argument('--output-dir', help='输出目录路径')
    batch_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='输出格式')
    batch_parser.add_argument('--recursive', action='store_true', help='递归处理子目录')
    
    # 验证命令
    validate_parser = subparsers.add_parser('validate', help='验证数据')
    validate_parser.add_argument('input', help='输入文件路径')
    validate_parser.add_argument('--schema', help='验证模式文件路径')
    
    # 统计命令
    stats_parser = subparsers.add_parser('stats', help='统计信息')
    stats_parser.add_argument('input', help='输入文件路径')
    stats_parser.add_argument('--format', choices=['text', 'json'], default='text', help='输出格式')
    
    # 导出命令
    export_parser = subparsers.add_parser('export', help='导出数据')
    export_parser.add_argument('input', help='输入文件路径')
    export_parser.add_argument('--output', help='输出文件路径')
    export_parser.add_argument('--format', choices=['json', 'csv', 'excel'], default='json', help='输出格式')
    
    # 导入命令
    import_parser = subparsers.add_parser('import', help='导入数据')
    import_parser.add_argument('input', help='输入文件路径')
    import_parser.add_argument('--format', choices=['json', 'csv'], help='输入格式')
    import_parser.add_argument('--validate', action='store_true', help='验证数据')
    
    return parser


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # 初始化日志系统
        initialize_logging()
        logger = get_logger(__name__)
        
        logger.info("正在启动全景标注工具CLI...")
        
        # 加载配置
        if args.config:
            # 使用指定配置文件
            from src.core.config import ConfigManager
            config_manager = ConfigManager(args.config)
            app_config = config_manager.get_config()
        else:
            # 使用默认配置
            app_config = get_config()
        
        # 设置日志级别
        if args.log_level:
            app_config.logging.level = args.log_level
        
        # 设置数据目录
        if args.data_dir:
            app_config.data_dir = args.data_dir
        
        # 设置输出目录
        if args.output_dir:
            # 确保目录存在
            FileUtils.ensure_dir(args.output_dir)
            app_config.temp_dir = args.output_dir
        
        # 创建应用实例
        app = create_app(app_config)
        
        # 注册CLI应用服务
        app.register_service(
            'cli_app',
            lambda: CLIApplication(app),
            dependencies=['config', 'event_manager'],
            singleton=True,
            priority=50
        )
        
        # 启动核心应用
        app.start()
        
        # 获取CLI应用实例
        cli_app = app.get_service('cli_app')
        
        # 注册应用事件处理器
        def on_app_error(error):
            logger.error(f"应用错误: {error}")
            print(f"错误: {error}")
        
        def on_app_stopping():
            logger.info("应用正在停止...")
        
        app.subscribe_event('app_error', on_app_error)
        app.subscribe_event('app_stopping', on_app_stopping)
        
        # 执行命令
        if args.command == 'process':
            cli_app.process_image(args.input, args.output, args.format)
        elif args.command == 'batch':
            cli_app.batch_process(args.input_dir, args.output_dir, args.format, args.recursive)
        elif args.command == 'validate':
            cli_app.validate_data(args.input, args.schema)
        elif args.command == 'stats':
            cli_app.show_stats(args.input, args.format)
        elif args.command == 'export':
            cli_app.export_data(args.input, args.output, args.format)
        elif args.command == 'import':
            cli_app.import_data(args.input, args.format, args.validate)
        else:
            # 显示帮助信息
            cli_app.show_help()
        
    except KeyboardInterrupt:
        logger.info("用户中断应用")
    except Exception as e:
        logger.error(f"应用执行失败: {e}")
        print(f"应用执行失败: {e}")
        sys.exit(1)
    finally:
        # 确保应用正确停止
        try:
            app = get_app()
            app.stop()
        except:
            pass


if __name__ == "__main__":
    main()