#!/usr/bin/env python3
"""
数据库字符集修复脚本
用于修复MySQL数据库中文乱码问题
"""

import os
import sys
import pymysql

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import Config

def check_database_charset():
    """检查数据库字符集配置"""
    print("=== 检查当前数据库字符集配置 ===")

    # 连接MySQL服务器（不指定数据库）
    connection = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        charset='utf8mb4'
    )

    try:
        with connection.cursor() as cursor:
            # 检查服务器字符集
            cursor.execute("SHOW VARIABLES LIKE 'character_set_%';")
            charset_results = cursor.fetchall()

            print("\n服务器字符集配置:")
            for row in charset_results:
                print(f"  {row[0]}: {row[1]}")

            # 检查数据库字符集
            cursor.execute(f"SHOW CREATE DATABASE {Config.DB_NAME};")
            db_result = cursor.fetchone()

            print(f"\n数据库 {Config.DB_NAME} 创建语句:")
            print(f"  {db_result[1]}")

            # 检查表字符集
            cursor.execute(f"USE {Config.DB_NAME};")
            cursor.execute("SHOW TABLE STATUS;")
            table_results = cursor.fetchall()

            print("\n表字符集配置:")
            for row in table_results:
                table_name = row[0]
                charset = row[14]
                print(f"  {table_name}: {charset}")

    finally:
        connection.close()

def fix_database_charset():
    """修复数据库字符集配置"""
    print("\n=== 开始修复数据库字符集配置 ===")

    # 连接MySQL服务器（不指定数据库）
    connection = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        charset='utf8mb4'
    )

    try:
        with connection.cursor() as cursor:
            # 修改数据库字符集
            print(f"修改数据库 {Config.DB_NAME} 字符集...")
            cursor.execute(f"ALTER DATABASE {Config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            print("数据库字符集修改完成")

            # 修改表字符集
            cursor.execute(f"USE {Config.DB_NAME};")
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()

            for table in tables:
                table_name = table[0]
                print(f"修改表 {table_name} 字符集...")
                cursor.execute(f"ALTER TABLE {table_name} CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
                print(f"表 {table_name} 字符集修改完成")

        connection.commit()
        print("\n所有表字符集修改完成！")

    except Exception as e:
        print(f"修复过程中出错: {e}")
        connection.rollback()
        raise
    finally:
        connection.close()

def set_mysql_client_charset():
    """设置MySQL客户端字符集"""
    print("\n=== MySQL客户端字符集设置建议 ===")
    print("为了在MySQL命令行客户端中正确显示中文，请执行以下操作：")
    print("1. 在MySQL配置文件 (my.cnf 或 my.ini) 的 [client] 和 [mysql] 部分添加：")
    print("   [client]")
    print("   default-character-set = utf8mb4")
    print("   ")
    print("   [mysql]")
    print("   default-character-set = utf8mb4")
    print("   ")
    print("2. 或者在连接MySQL后执行：")
    print("   SET NAMES utf8mb4;")
    print("   SET CHARACTER SET utf8mb4;")
    print("   ")
    print("3. 重新连接MySQL客户端")

def main():
    """主函数"""
    print("数据库字符集诊断和修复工具")
    print("=" * 50)

    try:
        # 检查当前配置
        check_database_charset()

        # 询问是否修复
        response = input("\n是否要修复数据库字符集配置？(y/n): ").lower()
        if response == 'y':
            fix_database_charset()
            print("\n修复完成！建议重新创建数据库表以确保所有字段都使用正确的字符集。")
        else:
            print("跳过修复。")

        # 显示客户端设置建议
        set_mysql_client_charset()

    except Exception as e:
        print(f"执行失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()