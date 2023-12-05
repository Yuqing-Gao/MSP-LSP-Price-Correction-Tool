# from function_v2 import *
from function import *
from readfile import *


if __name__ == "__main__":
    # all_item_file_path, outlet_item_file_path = file_reader()
    # check_files(all_item_file_path, outlet_item_file_path)
    # for file_path1, file_path2 in all_item_file_path, outlet_item_file_path:
    #     df = merge_table(file_path1, file_path2)
    #
    #     overall_check(df)
    #     check_plot(df, fontsize=7, legend_fontsize=6, ticklabel_size=6)
    #     df_after = find_new_price(df)
    #     check_plot(df_after, fontsize=7, legend_fontsize=6, ticklabel_size=6)
    #     df_after.to_excel()
    folder_processor = FolderProcessor()
    folder_processor.process_all_folders()

    labels = ['<500', '500-1000', '1000-2000', '2000-5000', '5000-7500', '7500-20000', '>20000']
    thrds = [0.25, 0.2, 0.15, 0.1, 0.06, 0.05, 0.04]

    # price_processor = PriceProcessor(labels, thrds)

    for result in folder_processor.processed_folders:
        df = result['processed_df']
        if df is None or df.empty:
            continue
        overall_check(df)
        check_plot(df, fontsize=7, legend_fontsize=6, ticklabel_size=6)
        df_after = find_new_price(df)
        check_plot(df_after, fontsize=7, legend_fontsize=6, ticklabel_size=6)