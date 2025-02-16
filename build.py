# build.py

import os
import sys
import shutil
from datetime import datetime
import PyInstaller.__main__
from PIL import Image

def create_app_icon():
    """创建应用图标"""
    print("创建应用图标...")
    
    # 确保assets目录存在
    os.makedirs('ui/assets', exist_ok=True)
    
    # 创建一个简单的图标
    img = Image.new('RGBA', (256, 256), (33, 150, 243, 255))  # Material Blue
    
    # 创建一个简单的圆形
    circle = Image.new('RGBA', (200, 200), (255, 255, 255, 255))  # 白色圆形
    
    # 把圆形粘贴到主图像上
    img.paste(circle, (28, 28))
    
    # 保存为PNG和ICO文件
    icon_png = os.path.join('ui', 'assets', 'icon.png')
    icon_ico = os.path.join('ui', 'assets', 'icon.ico')
    try:
        img.save(icon_png, format='PNG')
        img.save(icon_ico, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
        return True
    except Exception as e:
        print(f"警告: 创建图标失败: {e}")
        return False

def clean_build():
    """清理构建文件"""
    print("清理构建文件...")
    
    # 要清理的目录
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    # 要删除的文件类型
    file_patterns = ['*.spec', '*.pyc', '*.pyo']
    
    # 清理目录
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"已删除目录: {dir_name}")
            except Exception as e:
                print(f"删除目录 {dir_name} 失败: {e}")
    
    # 清理文件
    import glob
    for pattern in file_patterns:
        for file_path in glob.glob(pattern, recursive=True):
            try:
                os.remove(file_path)
                print(f"已删除文件: {file_path}")
            except Exception as e:
                print(f"删除文件 {file_path} 失败: {e}")

def init_project_structure():
    """初始化项目结构"""
    print("初始化项目结构...")
    
    # 创建必要的目录
    directories = [
        'ui/assets',
        'ui/widgets',
        'core',
        'config',
        'models',
        'utils',
        'data',
        'logs',
        'sessions'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"已创建目录: {directory}")

def create_version_file():
    """创建版本信息文件"""
    version_info = '''
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'TG Forward'),
         StringStruct(u'FileDescription', u'Telegram Message Forward Tool'),
         StringStruct(u'FileVersion', u'1.0.0'),
         StringStruct(u'InternalName', u'tgforward'),
         StringStruct(u'LegalCopyright', u'Copyright (c) 2024'),
         StringStruct(u'OriginalFilename', u'TGForward.exe'),
         StringStruct(u'ProductName', u'TG Forward'),
         StringStruct(u'ProductVersion', u'1.0.0')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    print("已创建版本信息文件")

def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")

    # 创建版本信息文件
    create_version_file()

    # 检查UPX
    upx_path = "C:\\upx"
    if os.path.exists(upx_path):
        print("检测到UPX，将使用UPX压缩...")
        upx_args = [f'--upx-dir={upx_path}']
    else:
        print("未检测到UPX，将不使用压缩...")
        upx_args = ['--noupx']

    # 指定生成文件的目录，这里将所有生成文件放到 build 文件夹下
    dist_path = os.path.join('build', 'dist')
    work_path = os.path.join('build', 'build')
    spec_path = os.path.join('build')

    # 构建参数
    build_args = [
        'main.py',
        '--name=TGForward',
        '--windowed',
        '--icon=ui/assets/icon.ico',
        '--version-file=version_info.txt',
        '--onedir',
        '--noconfirm',
        '--clean',
        f'--distpath={dist_path}',
        f'--workpath={work_path}',
        f'--specpath={spec_path}',
    ]

    # 添加UPX相关参数
    build_args.extend(upx_args)

    # 添加资源文件
    datas = [
        ('ui/assets', 'ui/assets'),
        ('config', 'config'),
        ('utils', 'utils'),
    ]
    for src, dst in datas:
        if os.path.exists(src):
            build_args.append(f'--add-data={src};{dst}')

    # 添加隐含导入
    hidden_imports = [
        'PyQt6',
        'qt_material',
        'telethon',
        'tweepy',
        'sqlite3',
        'utils.common',
        'core',
        'models',
        'config'
    ]
    for imp in hidden_imports:
        build_args.append(f'--hidden-import={imp}')

    try:
        PyInstaller.__main__.run(build_args)
        return True
    except Exception as e:
        print(f"构建失败: {str(e)}")
        return False

def copy_additional_files():
    """复制额外文件到dist目录"""
    print("复制额外文件...")
    dist_dir = os.path.join('build', 'dist', 'TGForward')
    
    # 创建必要的目录
    directories = ['logs', 'data', 'sessions', 'config']
    for directory in directories:
        os.makedirs(os.path.join(dist_dir, directory), exist_ok=True)
    
    # 复制配置文件
    if os.path.exists('config/settings.py'):
        shutil.copy2('config/settings.py', os.path.join(dist_dir, 'config'))
    
    print("额外文件复制完成")

def main():
    start_time = datetime.now()
    
    try:
        # 初始化项目结构
        init_project_structure()
        
        # 创建应用图标
        if not create_app_icon():
            print("警告: 图标创建失败，将使用默认图标")
        
        # 清理旧的构建文件
        clean_build()
        
        # 构建可执行文件
        if not build_executable():
            print("构建失败！")
            return 1
        
        # 复制额外文件
        copy_additional_files()
        
        # 清理临时文件
        if os.path.exists('version_info.txt'):
            os.remove('version_info.txt')
        
        duration = (datetime.now() - start_time).total_seconds()
        print(f"\n构建完成！耗时: {duration:.2f} 秒")
        print("可执行文件位置: dist/TGForward/TGForward.exe")
        
    except Exception as e:
        print(f"构建过程中出错: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())