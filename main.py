import os
import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
import seaborn as sns


def pre_process_folder(folder_path):
    # 预处理（.xlsx -> df）单个文件夹的逻辑
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
            merger = ItemMerger(all_item_file_path, outlet_item_file_path, folder_path)
            # 调用 merge_tables 方法得到可以继续进行改价处理的 dataframe
            processed_df = merger.merge_tables()
        except Exception as e:
            print(f"An error occurred: {e}")

    return processed_df


def make_bulk_file(df, folder_path, foldername):
    df.to_excel(f"{folder_path}/{foldername}_bulk.xlsx", index=False)


class PriceProcessor:
    def __init__(self, df, folder_path):
        self.labels = ['<500', '500-1000', '1000-2000', '2000-5000', '5000-7500', '7500-20000', '>20000']  # 价格分类标签
        self.thrds = [0.25, 0.2, 0.15, 0.1, 0.06, 0.05, 0.04]  # 偏离阈值
        self.folder_path = folder_path
        self.df = df
        self.piecewise()  # 调用 piecewise 方法在初始化时直接分段

    def piecewise(self):  # 给 df 加分段标签
        bins = [0, 500, 1000, 2000, 5000, 7500, 20000, float('inf')]
        self.df['Category'] = pd.cut(self.df['Price CP (E,C)'], bins=bins, labels=self.labels, right=False)

    def check_difference(self, before0_or_after1):
        result_dict = {}
        for label in self.labels:
            result_dict[label] = {}  # 初始化内部字典
            index = self.labels.index(label)
            # 计算偏离百分比
            category_df = self.df[self.df['Category'] == label]

            if before0_or_after1 == 0:
                price_cp_column = 'Price CP (E,C)'
            elif before0_or_after1 == 1:
                price_cp_column = 'New Price CP (E,C)'
            else:
                raise ValueError("Invalid value for before0_or_after1. Must be 0 or 1.")

            # 确保列是数值类型
            category_df = category_df.copy()
            category_df[price_cp_column] = pd.to_numeric(category_df[price_cp_column], errors='coerce')
            category_df['Target Price'] = pd.to_numeric(category_df['Target Price'], errors='coerce')

            # 进行安全的除法运算
            price_cp_values = category_df[price_cp_column]
            target_price_values = category_df['Target Price']
            percentage_diff = np.where(target_price_values != 0,
                                       (price_cp_values - target_price_values) / target_price_values, 0)
            # 标记出需要改价的数据
            reprice_mark = np.where(abs(percentage_diff) - self.thrds[index] >= 0, 1, 0)
            # 将 percentage_diff 和 remark 写回 df
            self.df.loc[self.df['Category'] == label, 'Percentage Diff'] = percentage_diff
            self.df.loc[self.df['Category'] == label, 're-price mark'] = reprice_mark
            # 计数
            result_dict[label][f'<{100 * self.thrds[index]}%'] = len(
                percentage_diff[abs(percentage_diff) < self.thrds[index]])
            result_dict[label][f'>={100 * self.thrds[index]}%'] = len(
                percentage_diff[abs(percentage_diff) >= self.thrds[index]])

        print("data = {")
        for outer_key, inner_dict in result_dict.items():
            print(f"'{outer_key}': {{")

            for inner_key, value in inner_dict.items():
                print(f"    '{inner_key}': {value},")
            print("},")
        print("}")

    def overall_check(self):
        for index, row in self.df.iterrows():
            if pd.isna(row['Target Price']):
                raise ValueError("Some outlet-items do not have target price.")
        print("All outlet-items have target price.")
        self.check_difference(0)
        self.check_plot("before correction")  # 改价前图片

    def find_new_price(self):
        for index, row in self.df.iterrows():
            if row['re-price mark'] == 0:
                self.df.at[index, 'New Price CP (E,C)'] = row['Price CP (E,C)']
            elif row['re-price mark'] == 1:
                category = row['Category']
                percentage_diff = row['Percentage Diff']
                # 根据 category 获取对应的 thrds
                thrds_index = self.labels.index(category)
                thrds_value = self.thrds[thrds_index]

                new_price = None  # 初始化 new_price
                # 将偏离其目标值对应阈值的价格调回正常范围
                if percentage_diff > 0:
                    new_price = round(row['Target Price'] * (1 + 0.8 * thrds_value) - random.uniform(1, 10), 2)
                elif percentage_diff < 0:
                    new_price = round(row['Target Price'] * (1 - 0.8 * thrds_value) + random.uniform(1, 10), 2)
                self.df.at[index, 'New Price CP (E,C)'] = new_price  # 改好的价格填入 New Price 列

        self.check_difference(1)
        self.check_plot("after correction")  # 改价后图片

    def check_plot(self, filename):
        sns.set(style="whitegrid")
        categories = self.df['Category'].unique()
        num_rows = (len(categories) + 1) // 2
        num_cols = 2
        fig, axes = plt.subplots(num_rows, num_cols, figsize=(12, 6 * num_rows))
        axes = axes.flatten()

        for i, category in enumerate(categories):
            ax = axes[i]
            category_df = self.df[self.df['Category'] == category]
            ax.axhline(0, color='black', linestyle='--', label='0')
            ax.axhline(self.thrds[self.labels.index(category)], color='red', linestyle='--',
                       label=f'+{self.thrds[self.labels.index(category)]}')
            ax.axhline(-self.thrds[self.labels.index(category)], color='blue', linestyle='--',
                       label=f'-{self.thrds[self.labels.index(category)]}')

            sns.scatterplot(x=category_df.index, y='Percentage Diff', data=category_df, label='Percentage Diff', ax=ax)

            ax.set_title(f'Percentage Diff for {category} Category', fontsize=6)
            ax.set_xlabel('Index', fontsize=6)
            ax.set_ylabel('Percentage Diff', fontsize=6)

            ax.legend(fontsize=6)
            ax.tick_params(axis='both', which='major', labelsize=6)

        plt.tight_layout()
        plt.savefig(f"{self.folder_path}/{filename}.png")  # 保存图像
        plt.close()  # 关闭图形窗口


class FolderProcessor:
    # 将 PriceProcessor 的全部 methods 加入 FolderProcessor ，以实现完整地遍历处理单个文件夹的功能
    def __init__(self):
        self.current_directory = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

    def process_all_folders(self):
        # 遍历并处理当前工作目录下的所有文件夹
        for folder_name in os.listdir(self.current_directory):
            folder_path = os.path.join(self.current_directory, folder_name)

            # 检查当前路径是否是文件夹
            if os.path.isdir(folder_path):
                # 调用处理文件夹的方法

                # pre-process the raw files (.xlsx to dataframe)
                df = pre_process_folder(folder_path)
                if df is None or df.empty:  # 若预处理后得到的 dataframe 为空或没有得到 dataframe，continue
                    continue

                # process current dataframe using certain algorithms
                price_processor = PriceProcessor(df, folder_path)
                price_processor.overall_check()
                price_processor.find_new_price()
                df_after = price_processor.df

                # turn df_after to the bulk file needed (dataframe to .xlsx)
                make_bulk_file(df_after, folder_path, folder_name)

            else:
                continue


class ItemMerger:
    def __init__(self, all_item_path, outlet_item_path, folder_path):
        self.all_item_path = all_item_path
        self.outlet_item_path = outlet_item_path
        self.folder_path = folder_path

    def _all_item_init(self):
        # 读取，预处理 all item 文件
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
        # 读取，预处理 outlet item 文件
        outlet_item = pd.read_excel(self.outlet_item_path, header=18)  # 从第 19 行开始是表头
        outlet_item1 = outlet_item.copy().fillna(0)  # 将 nan 填充为 0
        outlet_item1 = outlet_item1.rename(columns={'id': 'ItemID'})  # 改名从而使两张表的 key 相同

        # 去除不需要的列
        if 'Productgroup' in outlet_item1:
            outlet_item1 = outlet_item1.drop(columns="Productgroup")

        # 手动输入 PG ID 和 QC ID
        print(f"Processing {self.folder_path} now...")  # 通过当前路径得知 PG ID 和 QC ID
        pg_id = input("please enter PG ID:")
        qc_id = input("please enter QC ID:")
        outlet_item1.insert(0, 'PG ID', pg_id)
        outlet_item1.insert(0, 'QC ID', qc_id)
        return outlet_item1

    def merge_tables(self):
        # 将 outlet item 以 all item 为基准查找目标值，最终返回修改后的 outlet item
        all_item = self._all_item_init()
        outlet_item = self._outlet_item_init()
        outlet_item['Target Price'] = ''
        outlet_item['New Price CP (E,C)'] = ''
        # 找目标值，填充到 outlet item 表中
        for index, row in outlet_item.iterrows():
            item_id = row['ItemID']
            match_index = all_item.index[all_item['ItemID'] == item_id].tolist()
            if match_index:
                outlet_item.at[index, 'Target Price'] = all_item.at[match_index[0], 'Price R1 (E,C)']
        return outlet_item


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
    # for result in folder_processor.processed_folders:
    #     print(f"Folder: {result['folder_path']}")
    #     print(result['processed_df'])
