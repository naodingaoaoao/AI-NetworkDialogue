import uvicorn
import os
import sys
import socket
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def check_port_available(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("localhost", port))
            s.listen(1)
            return True
        except OSError:
            return False

if __name__ == "__main__":
    # 创建数据目录
    data_dir = current_dir / "data"
    data_dir.mkdir(exist_ok=True)
    print(f"数据目录: {data_dir}")
    start_port = 8100
    port = start_port
    
    while port < start_port + 20:  # 尝试20个端口
        if check_port_available(port):
            break
        port += 1
    else:
        print(f"错误: 无法找到可用端口（从 {start_port} 开始的20个端口都被占用）")
        sys.exit(1)
    
    if port != start_port:
        print(f"端口 {start_port} 被占用，使用端口 {port}")
    
    print("请确保你的LM Studio在本地运行并开放端口1234")
    print(f"访问地址: http://localhost:{port}")
    print(f"API文档: http://localhost:{port}/docs")
    print("按 Ctrl+C 停止服务")
    
    try:
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=port,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"启动失败！ {e}")
