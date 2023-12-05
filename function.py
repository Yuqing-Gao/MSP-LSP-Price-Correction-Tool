import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
import seaborn as sns

labels = ['<500', '500-1000', '1000-2000', '2000-5000', '5000-7500', '7500-20000', '>20000']
thrds = [0.25, 0.2, 0.15, 0.1, 0.06, 0.05, 0.04]  # 定义偏离阈值


def piecewise(df):
    # 定义分段区间
    bins = [0, 500, 1000, 2000, 5000, 7500, 20000, float('inf')]
    # 定义分段标签
    df['Category'] = pd.cut(df['Price CP (E,C)'], bins=bins, labels=labels, right=False)
    return df


def check_difference(df, before0_or_after1):  # 改价前价格则输入0，改价后价格则输入1
    # 检查各价格段真数与目标值的差距情况
    df = piecewise(df)  # 分段
    result_dict = {}

    for label in labels:
        result_dict[label] = {}  # 初始化内部字典
        index = labels.index(label)
        # 计算偏离百分比
        category_df = df[df['Category'] == label]



        price_cp_column = None
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

        # target_price_values = category_df['Target Price']
        # percentage_diff = (price_cp_values - target_price_values) / target_price_values

        # 标记出需要改价的数据
        reprice_mark = np.where(abs(percentage_diff) - thrds[index] >= 0, 1, 0)

        # 将 percentage_diff 和 remark 写回 df
        df.loc[df['Category'] == label, 'Percentage Diff'] = percentage_diff
        df.loc[df['Category'] == label, 're-price mark'] = reprice_mark
        # 计数
        result_dict[label][f'<{100 * thrds[index]}%'] = len(percentage_diff[abs(percentage_diff) < thrds[index]])
        result_dict[label][f'>={100 * thrds[index]}%'] = len(percentage_diff[abs(percentage_diff) >= thrds[index]])


    # 打印结果
    print("data = {")
    for outer_key, inner_dict in result_dict.items():
        print(f"'{outer_key}': {{")
        for inner_key, value in inner_dict.items():
            print(f"    '{inner_key}': {value},")

        print("},")
    print("}")
    return df


def overall_check(df):
    # 检查是否所有 outlet item 都在 all item data 中有目标值
    for index, row in df.iterrows():
        if pd.isna(row['Target Price']):
            raise ValueError("Some outlet-items do not have target price.")
    print("All outlet-items have target price.")
    check_difference(df, 0)


def find_new_price(df):
    df = check_difference(df, 0)
    for index, row in df.iterrows():
        if row['re-price mark'] == 0:
            df.at[index, 'New Price CP (E,C)'] = row['Price CP (E,C)']
        elif row['re-price mark'] == 1:
            category = row['Category']
            percentage_diff = row['Percentage Diff']

            # 根据 category 获取对应的 thrds
            thrds_index = labels.index(category)
            thrds_value = thrds[thrds_index]

            # 根据 percentage_diff 的正负进行不同的更新
            if percentage_diff > 0:
                new_price = round(row['Target Price'] * (1 + 0.8*thrds_value) - random.uniform(1, 10), 2)
            elif percentage_diff < 0:
                new_price = round(row['Target Price'] * (1 - 0.8*thrds_value) + random.uniform(1, 10), 2)

            # 更新 New Price 列
            df.at[index, 'New Price CP (E,C)'] = new_price

    check_difference(df, before0_or_after1=1)
    return df


def check_plot(df, fontsize, legend_fontsize, ticklabel_size):
    # 设置Seaborn风格
    sns.set(style="whitegrid")

    # 获取不同的category
    categories = df['Category'].unique()

    # 计算子图的行数和列数
    num_rows = (len(categories) + 1) // 2  # 向上取整
    num_cols = 2

    # 创建子图
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(12, 6 * num_rows))

    # 展平子图数组，以便于遍历
    axes = axes.flatten()


    # 根据不同的category画子图
    for i, category in enumerate(categories):
        ax = axes[i]
        category_df = df[df['Category'] == category]

        # 画出0，+thrds，-thrds三条线
        ax.axhline(0, color='black', linestyle='--', label='0')
        ax.axhline(thrds[labels.index(category)], color='red', linestyle='--',
                   label=f'+{thrds[labels.index(category)]}')
        ax.axhline(-thrds[labels.index(category)], color='blue', linestyle='--',
                   label=f'-{thrds[labels.index(category)]}')

        # 标记Percentage Diff列数据
        sns.scatterplot(x=category_df.index, y='Percentage Diff', data=category_df, label='Percentage Diff', ax=ax)

        # 设置图形标题和标签
        ax.set_title(f'Percentage Diff for {category} Category', fontsize=fontsize)
        ax.set_xlabel('Index', fontsize=fontsize)
        ax.set_ylabel('Percentage Diff', fontsize=fontsize)

        # 设置图例的字号
        ax.legend(fontsize=legend_fontsize)

        # 设置坐标轴的字号
        ax.tick_params(axis='both', which='major', labelsize=ticklabel_size)

    # 调整子图之间的间距
    plt.tight_layout()

    # 显示图形
    plt.show()


