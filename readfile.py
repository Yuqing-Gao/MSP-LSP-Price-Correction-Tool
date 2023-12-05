import os
import pandas as pd


class FolderProcessor:
    def __init__(self):
        self.current_directory = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
        self.processed_folders = []

    def process_all_folders(self):
        # 遍历当前工作目录下的所有文件夹
        for folder_name in os.listdir(self.current_directory):
            folder_path = os.path.join(self.current_directory, folder_name)

            # 检查当前路径是否是文件夹
            if os.path.isdir(folder_path):
                # 调用处理文件夹的方法
                self.process_folder(folder_path)
            else:
                continue

    def process_folder(self, folder_path):
        # 处理单个文件夹的逻辑
        all_item_file_path = None
        outlet_item_file_path = None
        processed_df = None
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.xlsx') and 'all_item' in file_name:
                all_item_file_path = os.path.join(folder_path, file_name)
            elif file_name.endswith('.xlsx') and 'outlet_item' in file_name:
                outlet_item_file_path = os.path.join(folder_path, file_name)
        if all_item_file_path is not None and outlet_item_file_path is not None:
            try:
                # 实例化 ItemMerger 类
                merger = ItemMerger(all_item_file_path, outlet_item_file_path)
                # 调用 merge_tables 方法
                processed_df = merger.merge_tables()
            except Exception as e:
                print(f"An error occurred: {e}")

        self.processed_folders.append({
            'folder_path': folder_path,
            'processed_df': processed_df
        })


class ItemMerger:
    def __init__(self, all_item_path, outlet_item_path):
        self.all_item_path = all_item_path
        self.outlet_item_path = outlet_item_path

    def _all_item_init(self):
        all_item = pd.read_excel(self.all_item_path, header=18)
        all_item1 = all_item.copy().fillna(0)
        for index, row in all_item1.iterrows():
            if row['Price R1 (E,C)'] == 0 and row['Price CP (E,C)'] == 0:
                all_item1 = all_item1.drop(index)
            elif row['Price R1 (E,C)'] == 0:
                all_item1.at[index, 'Price R1 (E,C)'] = row['Price CP (E,C)']
        all_item1.reset_index(drop=True, inplace=True)
        return all_item1

    def _outlet_item_init(self):
        outlet_item = pd.read_excel(self.outlet_item_path, header=18)
        outlet_item1 = outlet_item.copy().fillna(0)
        outlet_item1 = outlet_item1.rename(columns={'id': 'ItemID'})
        if 'Productgroup' in outlet_item1:
            outlet_item1 = outlet_item1.drop(columns="Productgroup")



        # 手动输入 PG ID 和 QC ID
        pg_id = input("please enter PG ID:")
        qc_id = input("please enter QC ID:")
        outlet_item1.insert(0, 'PG ID', pg_id)
        outlet_item1.insert(0, 'QC ID', qc_id)
        return outlet_item1


    def merge_tables(self):
        all_item = self._all_item_init()
        outlet_item = self._outlet_item_init()
        outlet_item['Target Price'] = ''
        outlet_item['New Price CP (E,C)'] = ''


        for index, row in outlet_item.iterrows():
            item_id = row['ItemID']
            match_index = all_item.index[all_item['ItemID'] == item_id].tolist()
            if match_index:
                outlet_item.at[index, 'Target Price'] = all_item.at[match_index[0], 'Price R1 (E,C)']
        return outlet_item


# def all_item_init(file_path):
#     """
#     根据传入的 path 初始化 all_item 文件
#     """
#     all_item = pd.read_excel(file_path, header=18)
#     all_item1 = all_item.copy()
#     for index, row in all_item1.iterrows():
#         if row['Price R1 (E,C)'] == 0 and row['Price CP (E,C)'] == 0:
#             # 删除整行
#             all_item1 = all_item1.drop(index)
#         elif row['Price R1 (E,C)'] == 0:
#             # 用 Price CP (E,C)列的值替代 Price R1 (E,C)
#             all_item1.at[index, 'Price R1 (E,C)'] = row['Price CP (E,C)']
#     # 重置索引
#     all_item1.reset_index(drop=True)
#     return all_item1
#
#
# def outlet_item_init(file_path):
#     """
#     根据传入的 path 初始化 outlet_item 文件
#     """
#     outlet_item = pd.read_excel(file_path, header=18)  # 表格前 18 行为空
#     outlet_item1 = outlet_item.copy()
#     outlet_item1 = outlet_item1.rename(columns={'id': 'ItemID'})  # 修改列名使其和 all_item 的 key 一致
#     outlet_item1 = outlet_item1.drop(columns="Productgroup")  # 删除不需要的列
#     pg_id = input("please enter PG ID:")
#     qc_id = input("please enter QC ID:")
#     outlet_item1.insert(0, 'PG ID', pg_id)  # 37532
#     outlet_item1.insert(0, 'QC ID', qc_id)  # 178058
#     return outlet_item1
#
#
# def merge_table(file_path1, file_path2):
#     all_item = all_item_init(file_path1)
#     outlet_item = outlet_item_init(file_path2)
#     outlet_item['Target Price'] = ''
#     outlet_item['New Price CP (E,C)'] = ''
#
#     for index, row in outlet_item.iterrows():
#         item_id = row['ItemID']
#
#         # 查找匹配的 "ItemID" 在 all_item 中的索引
#         match_index = all_item.index[all_item['ItemID'] == item_id].tolist()
#
#         # 如果找到匹配，将 "Price R1 (E,C)" 填入 "New Price CP (E,C)"
#         if match_index:
#             outlet_item.at[index, 'Target Price'] = all_item.at[match_index[0], 'Price R1 (E,C)']
#
#     return outlet_item


def check_files(all_item_files, outlet_item_files):
    pass


if __name__ == "__main__":
    folder_processor = FolderProcessor()
    folder_processor.process_all_folders()

    # 获取所有处理结果
    # .xlsx 为空的情况：
    # Folder: D:\RealStudyfile\gfk实习\gaijia\v1\MSP_offline_extend
    # Empty DataFrame
    # Columns: [QC ID, PG ID, Target Price, New Price CP (E,C)]
    # Index: []
    # 文件夹为空的情况：
    # Folder: D:\RealStudyfile\gfk实习\gaijia\v1\.idea
    # None
    for result in folder_processor.processed_folders:
        print(f"Folder: {result['folder_path']}")
        print(result['processed_df'])

