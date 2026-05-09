#!/usr/bin/env python3
"""
Mihomo 代理配置生成脚本
支持 Base64 编码节点列表和 Clash/Mihomo YAML 格式订阅
"""

import os
import sys
import io
import base64
import json
import urllib.request
import urllib.parse
import ssl
from typing import List, Dict, Any, Optional

# 设置 UTF-8 编码（Windows 兼容）
# 使用标志避免重复设置
if sys.platform == 'win32' and not hasattr(sys.stdout, '_mihomo_encoded'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stdout._mihomo_encoded = True
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    sys.stderr._mihomo_encoded = True


def decode_base64(content: str) -> str:
    """Base64 解码，自动处理填充"""
    content = content.strip()
    # 自动添加填充
    padding = 4 - len(content) % 4
    if padding != 4:
        content += '=' * padding
    try:
        return base64.b64decode(content).decode('utf-8')
    except:
        return content


def is_base64_encoded(content: str) -> bool:
    """检查内容是否是 Base64 编码"""
    try:
        # 移除空白字符
        content = content.strip()
        # 尝试解码
        decoded = base64.b64decode(content)
        # 检查解码后是否是可读的文本（节点链接）
        decoded_str = decoded.decode('utf-8')
        # 如果包含常见的协议前缀，说明是 Base64 编码的节点列表
        return any(prefix in decoded_str for prefix in ['ss://', 'vmess://', 'trojan://', 'vless://'])
    except:
        return False


def is_yaml_format(content: str) -> bool:
    """检查内容是否是 YAML 格式（Clash/Mihomo 配置）"""
    content = content.strip().lower()
    # 检查是否包含 YAML 特有的关键字（必须是 YAML 结构的关键字）
    yaml_indicators = ['proxies:', 'proxy-groups:', 'mixed-port:', 'rules:']
    return any(indicator in content for indicator in yaml_indicators)


def parse_ss_node(line: str) -> Optional[Dict[str, Any]]:
    """解析 SS 节点"""
    try:
        if line.startswith('ss://'):
            line = line[5:]
            
            # 分离名称
            name = "SS节点"
            if '#' in line:
                line, name = line.rsplit('#', 1)
                name = urllib.parse.unquote(name)
            
            # 解析用户信息
            if '@' in line:
                user_info, server_info = line.split('@', 1)
                user_info = decode_base64(user_info)
                method, password = user_info.split(':', 1)
                
                # 解析服务器信息
                if ':' in server_info:
                    server, port_str = server_info.rsplit(':', 1)
                    port = int(port_str.split('#')[0].split('?')[0])
                    
                    return {
                        'name': name[:30],
                        'type': 'ss',
                        'server': server,
                        'port': port,
                        'cipher': method,
                        'password': password
                    }
    except Exception as e:
        print(f"解析 SS 节点失败: {e}")
    return None


def parse_vmess_node(line: str) -> Optional[Dict[str, Any]]:
    """解析 VMess 节点"""
    try:
        if line.startswith('vmess://'):
            line = line[8:]
            decoded = decode_base64(line)
            node = json.loads(decoded)
            
            return {
                'name': node.get('ps', 'VMess节点')[:30],
                'type': 'vmess',
                'server': node.get('add', ''),
                'port': int(node.get('port', 443)),
                'uuid': node.get('id', ''),
                'alterId': int(node.get('aid', 0)),
                'cipher': 'auto',
                'tls': node.get('tls', '') == 'tls',
                'network': node.get('net', 'tcp'),
                'ws-opts': {
                    'path': node.get('path', '/'),
                    'headers': {
                        'Host': node.get('host', node.get('add', ''))
                    }
                } if node.get('net') == 'ws' else None
            }
    except Exception as e:
        print(f"解析 VMess 节点失败: {e}")
    return None


def parse_trojan_node(line: str) -> Optional[Dict[str, Any]]:
    """解析 Trojan 节点"""
    try:
        if line.startswith('trojan://'):
            line = line[9:]
            
            # 分离名称
            name = "Trojan节点"
            if '#' in line:
                line, name = line.rsplit('#', 1)
                name = urllib.parse.unquote(name)
            
            # 解析密码和服务器
            if '@' in line:
                password, server_info = line.split('@', 1)
                password = urllib.parse.unquote(password)
                
                # 处理查询参数
                if '?' in server_info:
                    server_part, query = server_info.split('?', 1)
                else:
                    server_part = server_info
                    query = ""
                
                if ':' in server_part:
                    server, port_str = server_part.rsplit(':', 1)
                    port = int(port_str)
                    
                    node = {
                        'name': name[:30],
                        'type': 'trojan',
                        'server': server,
                        'port': port,
                        'password': password
                    }
                    
                    # 解析 sni
                    if 'sni=' in query:
                        for param in query.split('&'):
                            if param.startswith('sni='):
                                node['sni'] = urllib.parse.unquote(param[4:])
                                break
                    
                    return node
    except Exception as e:
        print(f"解析 Trojan 节点失败: {e}")
    return None


def parse_vless_node(line: str) -> Optional[Dict[str, Any]]:
    """解析 VLESS 节点"""
    try:
        if line.startswith('vless://'):
            line = line[8:]
            
            # 分离名称
            name = "VLESS节点"
            if '#' in line:
                line, name = line.rsplit('#', 1)
                name = urllib.parse.unquote(name)
            
            # 解析 UUID 和服务器
            if '@' in line:
                uuid, server_info = line.split('@', 1)
                
                # 处理查询参数
                if '?' in server_info:
                    server_part, query = server_info.split('?', 1)
                else:
                    server_part = server_info
                    query = ""
                
                if ':' in server_part:
                    server, port_str = server_part.rsplit(':', 1)
                    port = int(port_str)
                    
                    node = {
                        'name': name[:30],
                        'type': 'vless',
                        'server': server,
                        'port': port,
                        'uuid': uuid
                    }
                    
                    # 解析参数
                    params = {}
                    for param in query.split('&'):
                        if '=' in param:
                            k, v = param.split('=', 1)
                            params[k] = urllib.parse.unquote(v)
                    
                    if 'security' in params:
                        node['tls'] = params['security'] == 'tls'
                    if 'sni' in params:
                        node['servername'] = params['sni']
                    if 'type' in params:
                        node['network'] = params['type']
                    
                    return node
    except Exception as e:
        print(f"解析 VLESS 节点失败: {e}")
    return None


def parse_base64_subscription(content: str) -> List[Dict[str, Any]]:
    """解析 Base64 编码的节点列表"""
    proxies = []
    
    try:
        decoded = decode_base64(content)
        lines = decoded.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 尝试解析不同类型的节点
            node = None
            if line.startswith('ss://'):
                node = parse_ss_node(line)
            elif line.startswith('vmess://'):
                node = parse_vmess_node(line)
            elif line.startswith('trojan://'):
                node = parse_trojan_node(line)
            elif line.startswith('vless://'):
                node = parse_vless_node(line)
            
            if node:
                proxies.append(node)
                print(f"  解析节点: {node['name']} ({node['type']})")
    
    except Exception as e:
        print(f"解析 Base64 订阅失败: {e}")
    
    return proxies


def parse_yaml_subscription(content: str) -> List[Dict[str, Any]]:
    """解析 YAML 格式的订阅（Clash/Mihomo 配置）使用 PyYAML"""
    proxies = []
    
    try:
        import yaml
        
        # 解析 YAML 内容
        config = yaml.safe_load(content)
        
        if not isinstance(config, dict):
            print("YAML 内容格式不正确")
            return proxies
        
        # 提取 proxies 部分
        yaml_proxies = config.get('proxies', [])
        
        if not yaml_proxies:
            print("YAML 中没有找到 proxies 部分")
            return proxies
        
        for proxy in yaml_proxies:
            if not isinstance(proxy, dict):
                continue
            
            # 提取必要的字段
            node = {
                'name': str(proxy.get('name', 'Unknown')),
                'type': proxy.get('type', ''),
                'server': proxy.get('server', ''),
                'port': proxy.get('port', 0)
            }
            
            # 根据节点类型提取额外字段
            node_type = node['type'].lower()
            
            if node_type == 'ss':
                node['cipher'] = proxy.get('cipher', 'none')
                node['password'] = proxy.get('password', '')
            elif node_type == 'vmess':
                node['uuid'] = proxy.get('uuid', '')
                node['alterId'] = proxy.get('alterId', 0)
                node['cipher'] = proxy.get('cipher', 'auto')
                node['tls'] = proxy.get('tls', False)
                node['network'] = proxy.get('network', 'tcp')
                if 'ws-opts' in proxy:
                    node['ws-opts'] = proxy['ws-opts']
            elif node_type == 'trojan':
                node['password'] = proxy.get('password', '')
                if 'sni' in proxy:
                    node['sni'] = proxy['sni']
            elif node_type == 'vless':
                node['uuid'] = proxy.get('uuid', '')
                node['tls'] = proxy.get('tls', False)
                if 'servername' in proxy:
                    node['servername'] = proxy['servername']
                if 'network' in proxy:
                    node['network'] = proxy['network']
            elif node_type == 'ssr':
                node['cipher'] = proxy.get('cipher', 'none')
                node['password'] = proxy.get('password', '')
                node['protocol'] = proxy.get('protocol', 'origin')
                node['obfs'] = proxy.get('obfs', 'plain')
            elif node_type == 'http':
                node['username'] = proxy.get('username', '')
                node['password'] = proxy.get('password', '')
            elif node_type == 'socks5':
                node['username'] = proxy.get('username', '')
                node['password'] = proxy.get('password', '')
            
            # 保留原始配置中的所有其他字段
            for key, value in proxy.items():
                if key not in node:
                    node[key] = value
            
            proxies.append(node)
            print(f"  解析节点: {node['name']} ({node['type']})")
    
    except ImportError:
        print("警告: 未安装 PyYAML，尝试使用简单解析")
        return parse_yaml_subscription_simple(content)
    except Exception as e:
        print(f"解析 YAML 订阅失败: {e}")
        import traceback
        traceback.print_exc()
    
    return proxies


def parse_yaml_subscription_simple(content: str) -> List[Dict[str, Any]]:
    """简单解析 YAML 格式的订阅（备用方案）"""
    proxies = []
    
    try:
        lines = content.split('\n')
        in_proxies = False
        current_proxy = {}
        current_indent = 0
        
        for line in lines:
            stripped = line.strip()
            
            # 检测 proxies: 部分开始
            if stripped == 'proxies:':
                in_proxies = True
                current_indent = len(line) - len(line.lstrip())
                continue
            
            if not in_proxies:
                continue
            
            # 检测行缩进
            line_indent = len(line) - len(line.lstrip())
            
            # 检测其他顶级部分，结束 proxies 解析
            if stripped.endswith(':') and line_indent <= current_indent:
                if stripped in ['proxy-groups:', 'rules:', 'mode:', 'log-level:', 'dns:']:
                    break
            
            # 检测新的代理节点（以 - 开头，且缩进正确）
            if stripped.startswith('- '):
                # 保存上一个节点
                if current_proxy and 'name' in current_proxy:
                    proxies.append(current_proxy)
                    print(f"  解析节点: {current_proxy.get('name', 'Unknown')} ({current_proxy.get('type', 'unknown')})")
                
                # 开始新节点
                current_proxy = {}
                # 解析第一个属性
                key_val = stripped[2:].strip()  # 移除 '- '
                if ':' in key_val:
                    key, val = key_val.split(':', 1)
                    current_proxy[key.strip()] = val.strip().strip('"\'')
            
            # 解析节点的其他属性（必须是缩进的）
            elif ':' in stripped and current_proxy is not None and line_indent > current_indent:
                key, val = stripped.split(':', 1)
                key = key.strip()
                val = val.strip().strip('"\'')
                
                # 跳过嵌套对象（简单处理）
                if not val and stripped.endswith(':'):
                    continue
                
                # 转换类型
                if key in ['port', 'alterId']:
                    try:
                        val = int(val)
                    except:
                        pass
                elif key == 'tls':
                    val = val.lower() == 'true'
                
                if val or key not in current_proxy:
                    current_proxy[key] = val
        
        # 保存最后一个节点
        if current_proxy and 'name' in current_proxy:
            proxies.append(current_proxy)
            print(f"  解析节点: {current_proxy.get('name', 'Unknown')} ({current_proxy.get('type', 'unknown')})")
    
    except Exception as e:
        print(f"简单解析 YAML 订阅失败: {e}")
    
    return proxies


def fetch_subscription(url: str) -> List[Dict[str, Any]]:
    """从订阅链接获取节点列表，自动识别格式"""
    proxies = []
    
    try:
        # 创建 SSL 上下文（忽略证书验证）
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Clash',
                'Accept': '*/*'
            }
        )
        
        print(f"正在下载订阅: {url[:50]}...")
        
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            content = response.read().decode('utf-8')
        
        print(f"订阅内容大小: {len(content)} 字节")
        
        # 检测订阅格式 - 先检查是否是 Base64 编码（更严格的检测）
        if is_base64_encoded(content):
            print("检测到 Base64 编码订阅")
            proxies = parse_base64_subscription(content)
        elif is_yaml_format(content):
            print("检测到 YAML 格式订阅 (Clash/Mihomo)")
            proxies = parse_yaml_subscription(content)
        else:
            # 尝试作为纯文本节点列表解析
            print("尝试作为纯文本节点列表解析")
            proxies = parse_base64_subscription(content)
        
        print(f"\n共解析到 {len(proxies)} 个节点")
        
    except Exception as e:
        print(f"获取订阅失败: {e}")
        import traceback
        traceback.print_exc()
    
    return proxies


def generate_config(proxies: List[Dict[str, Any]], output_path: str = 'mihomo_config.yaml'):
    """生成 Mihomo 配置文件"""
    if not proxies:
        print("没有可用节点，无法生成配置")
        return False
    
    # 只取前 10 个节点，避免配置过大
    proxies = proxies[:10]
    
    proxy_names = [p['name'] for p in proxies]
    
    # 构建配置字典
    config = {
        'mixed-port': 7890,
        'socks-port': 7891,
        'redir-port': 0,
        'allow-lan': False,
        'mode': 'rule',
        'log-level': 'info',
        'external-controller': '127.0.0.1:9090',
        'proxies': [],
        'proxy-groups': [
            {
                'name': 'AutoSelect',
                'type': 'url-test',
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300,
                'tolerance': 50,
                'proxies': proxy_names
            },
            {
                'name': 'Manual',
                'type': 'select',
                'proxies': ['AutoSelect'] + proxy_names
            }
        ],
        'rules': ['MATCH,Manual']
    }
    
    # 清理节点数据，移除不必要的字段
    cleaned_proxies = []
    for p in proxies:
        cleaned = {}
        # 必须字段
        for key in ['name', 'type', 'server', 'port']:
            if key in p:
                cleaned[key] = p[key]
        
        # 根据类型添加特定字段
        node_type = p.get('type', '').lower()
        
        if node_type == 'ss':
            for key in ['cipher', 'password']:
                if key in p:
                    cleaned[key] = p[key]
        elif node_type == 'vmess':
            for key in ['uuid', 'alterId', 'cipher', 'tls', 'network', 'ws-opts', 'ws-path', 'ws-headers', 'skip-cert-verify']:
                if key in p:
                    cleaned[key] = p[key]
        elif node_type == 'trojan':
            for key in ['password', 'sni', 'skip-cert-verify']:
                if key in p:
                    cleaned[key] = p[key]
        elif node_type == 'vless':
            for key in ['uuid', 'tls', 'servername', 'network', 'flow', 'client-fingerprint']:
                if key in p:
                    cleaned[key] = p[key]
        elif node_type == 'ssr':
            for key in ['cipher', 'password', 'protocol', 'obfs', 'protocol-param', 'obfs-param']:
                if key in p:
                    cleaned[key] = p[key]
        elif node_type in ['http', 'socks5']:
            for key in ['username', 'password']:
                if key in p:
                    cleaned[key] = p[key]
        
        # 保留其他可能重要的字段
        for key, value in p.items():
            if key not in cleaned and value is not None and value != '':
                cleaned[key] = value
        
        cleaned_proxies.append(cleaned)
    
    config['proxies'] = cleaned_proxies
    
    try:
        import yaml
        # 使用 PyYAML 输出配置
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Mihomo 自动生成的配置文件\n")
            yaml.dump(config, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    except ImportError:
        # 如果没有 PyYAML，使用手动生成
        print("警告: 未安装 PyYAML，使用手动生成配置")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("""# Mihomo 自动生成的配置文件
mixed-port: 7890
socks-port: 7891
redir-port: 0
allow-lan: false
mode: rule
log-level: info
external-controller: 127.0.0.1:9090

proxies:
""")
            for p in cleaned_proxies:
                f.write(f"  - name: \"{p['name']}\"\n")
                f.write(f"    type: {p['type']}\n")
                f.write(f"    server: {p['server']}\n")
                f.write(f"    port: {p['port']}\n")
                
                for key, value in p.items():
                    if key not in ['name', 'type', 'server', 'port']:
                        if isinstance(value, bool):
                            f.write(f"    {key}: {str(value).lower()}\n")
                        elif isinstance(value, (int, float)):
                            f.write(f"    {key}: {value}\n")
                        elif isinstance(value, dict):
                            f.write(f"    {key}:\n")
                            for k, v in value.items():
                                if isinstance(v, dict):
                                    f.write(f"      {k}:\n")
                                    for kk, vv in v.items():
                                        f.write(f"        {kk}: {vv}\n")
                                else:
                                    f.write(f"      {k}: {v}\n")
                        else:
                            f.write(f"    {key}: \"{value}\"\n")
                f.write("\n")
            
            f.write("""proxy-groups:
  - name: AutoSelect
    type: url-test
    url: http://www.gstatic.com/generate_204
    interval: 300
    tolerance: 50
    proxies:
""")
            for name in proxy_names:
                f.write(f"      - \"{name}\"\n")
            
            f.write("""  - name: Manual
    type: select
    proxies:
      - AutoSelect
""")
            for name in proxy_names:
                f.write(f"      - \"{name}\"\n")
            
            f.write("""
rules:
  - MATCH,Manual
""")
    
    print(f"\n配置文件已生成: {output_path}")
    print(f"包含 {len(proxies)} 个节点")
    return True


def find_mihomo_binary() -> Optional[str]:
    """查找 Mihomo 可执行文件"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    possible_paths = [
        os.path.join(script_dir, 'mihomo.exe'),
        os.path.join(script_dir, 'mihomo-windows-amd64.exe'),
        os.path.join(script_dir, 'mihomo'),
        os.path.join(os.path.dirname(script_dir), 'mihomo.exe'),
        os.path.join(os.path.dirname(script_dir), 'mihomo-windows-amd64.exe'),
        'mihomo.exe',
        'mihomo',
        '/usr/local/bin/mihomo',
        '/usr/bin/mihomo',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"找到 Mihomo: {path}")
            return path
    
    return None


def main():
    subscribe_url = os.environ.get('SUBSCRIBE_URL')
    
    if not subscribe_url:
        print("错误: 未设置 SUBSCRIBE_URL 环境变量")
        sys.exit(1)
    
    print("="*60)
    print("Mihomo 配置生成工具")
    print("="*60)
    print()
    
    # 查找 Mihomo
    mihomo_path = find_mihomo_binary()
    if mihomo_path:
        print(f"Mihomo 路径: {mihomo_path}")
    else:
        print("警告: 未找到 Mihomo 可执行文件")
    
    print()
    
    # 获取订阅
    proxies = fetch_subscription(subscribe_url)
    
    if not proxies:
        print("\n错误: 未能获取到任何节点")
        sys.exit(1)
    
    # 生成配置
    if generate_config(proxies):
        print("\n" + "="*60)
        print("配置生成成功！")
        print("="*60)
        print("代理地址: http://127.0.0.1:7890")
        print("Socks5 地址: socks5://127.0.0.1:7891")
        print("外部控制器: http://127.0.0.1:9090")
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
