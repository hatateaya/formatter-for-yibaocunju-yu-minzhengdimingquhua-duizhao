import json
import os
import sys

# 尝试导入 PyYAML，如果不存在则提示用户安装
try:
    import yaml
except ImportError:
    print("错误: 缺少必要的库 'PyYAML'。")
    print("请运行以下命令进行安装: pip install pyyaml")
    sys.exit(1)

INPUT_FILENAME = 'input.json'
OUTPUT_FILENAME = 'output.yaml'

def process_data():
    # 检查输入文件是否存在
    if not os.path.exists(INPUT_FILENAME):
        print(f"错误: 未找到 {INPUT_FILENAME} 文件。请确保文件在当前目录下。")
        return

    # 0. 从 input.json 读入数据
    try:
        with open(INPUT_FILENAME, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except json.JSONDecodeError:
        print(f"错误: {INPUT_FILENAME} 文件格式不正确，请检查是否为有效的JSON。")
        return

    # 1. 数据清洗与初步提取
    cleaned_items = []
    for item in raw_data:
        cleaned_items.append({
            "行政区划代码": item["MinZhengQuHuaXinXiQuHuaDaiMa"],
            "行政区划名称": item["MinZhengQuHuaXinXiQuHuaMingCheng"]
        })

    # 先按代码排序
    cleaned_items.sort(key=lambda x: x["行政区划代码"])

    # 2. 按照规则分组
    # 根节点: 结尾是 000000 (例如 370403000000 薛城区)
    # 一级组(街道/乡镇): 结尾是 000 (例如 370403001000 临城街道)
    # 二级项(社区/村): 其余项

    result_structure = {} 
    
    # 临时存储：当前处理的区/县列表引用
    current_district_list = None 
    
    # 第一次遍历：找到根（区/县）
    root_item = next((item for item in cleaned_items if item["行政区划代码"].endswith("000000")), None)
    
    if not root_item:
        print("错误：未在数据中找到以 '000000' 结尾的顶级行政区划。")
        return

    root_name = root_item["行政区划名称"]
    result_structure[root_name] = [] # 初始化区的列表
    current_district_list = result_structure[root_name]

    # 第二次遍历：处理子级分组和叶子节点
    
    current_group_children = None # 指向当前一级组下叶子列表的引用

    for item in cleaned_items:
        code = item["行政区划代码"]
        name = item["行政区划名称"]

        # 跳过根节点本身
        if code.endswith("000000"):
            continue

        # 判断是否是一级分组（街道/乡镇）：
        # 数据示例: 370403001000 (临城街道) -> 末尾是 000
        # 如果使用 endswith("00000") 会失败，因为倒数第4位是1
        if code.endswith("000"):
            # 这是一个新的一级分组
            # 创建结构: { "分组名": [ ...子节点... ] }
            new_group = {name: []}
            
            # 添加到区的列表中
            current_district_list.append(new_group)
            
            # 更新当前列表引用
            current_group_children = new_group[name]
        
        else:
            # 这是一个二级项（社区/村）
            # 把它添加到当前最近的一个分组列表中
            if current_group_children is not None:
                # 直接加入名称字符串
                current_group_children.append(name)
            else:
                # 如果没有找到归属的分组（例如社区出现在街道之前），可以选择忽略或记录
                pass

    # 3. 输出到 output.yaml
    print(f"正在写入 {OUTPUT_FILENAME} ...")
    with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
        yaml.dump(result_structure, f, allow_unicode=True, sort_keys=False, indent=2)

    print("处理完成！")

if __name__ == "__main__":
    process_data()
