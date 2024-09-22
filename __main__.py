import base64
import json
from pathlib import Path
from typing import Dict, List

CURRENT_PATH = Path(__file__).parent
node_count = 0

def decode_vmess(node: str) -> Dict:
    global node_count
    node_count += 1
    try:
        node_data = base64.b64decode(node.replace("vmess://", "")).decode()
        node_dict: Dict = json.loads(node_data)
        
        result = {
            "name": f"{node_dict['ps']}☯{node_count}",
            "type": "vmess",
            "server": node_dict["add"],
            "port": int(node_dict["port"]),
            "sni": "",
            "uuid": node_dict["id"],
            "cipher": "auto",
            "network": "ws",
            "skip-cert-verify": True,
            "ws-opts": {
                "path": node_dict.get("path", ""),
                "headers": {
                    "host": node_dict.get("host", "")
                }
            },
            "alterId": 0
        }

        if node_dict.get("type", "tcp") == "ws":
            result["transport"] = {
                "network": "ws",
                "path": node_dict.get("path", ""),
                "headers": {"Host": node_dict.get("host", "")},
            }
        elif node_dict.get("type", "tcp") == "tcp":
            result["packet_encoding"] = "xudp"

        if node_dict.get("tls") == "tls":
            result["tls"] = {
                "enabled": True,
                "server_name": node_dict.get("host", ""),
                "insecure": False,
            }
        return result

    except (json.JSONDecodeError, base64.binascii.Error) as e:
        print(f"Error decoding node: {e}")
        return {}

def read_node() -> List[Dict]:
    node_info: List[Dict] = []
    try:
        with open(CURRENT_PATH / "nodes.txt", "r", encoding="utf-8") as f:
            node_info = [decode_vmess(item) for item in f if item.startswith("vmess://")]
    except FileNotFoundError:
        print("nodes.txt 文件未找到")
    return [node for node in node_info if node]  # 过滤掉解码失败的节点

def set_node_name_list(node_info: List[Dict]) -> List[str]:
    node_name_list = [item['name'] for item in node_info if 'name' in item and item['name']]
    for item in node_info:
        if 'name' not in item or not item['name']:
            print(f"Warning: 'name' key not found or item is empty: {item}")
    return node_name_list

if __name__ == "__main__":
    node_info = read_node()
    node_name_list = set_node_name_list(node_info)

    try:
        with open(CURRENT_PATH / "config", "r", encoding="utf-8") as f:
            config_content = f.read()
    except FileNotFoundError:
        print("config 文件未找到")
        config_content = ""

    node_name_list_str = "\n".join(f"  - {str(item)}" for item in node_name_list)
    config_content = config_content.replace('node_name_list', node_name_list_str + "\n")
    
    node_info_str = "\n".join(f"  - {str(item).replace("'", '')}" for item in node_info)
    config_content = config_content.replace('node_info', node_info_str + "\n")

    with open(CURRENT_PATH / "clash.yaml", "w", encoding="utf-8") as f:
        f.write(config_content)

    print(f">>>>>>>>> 总共生成{len(node_info)}个节点，当前目录已新增配置文件./clash.yaml。")
