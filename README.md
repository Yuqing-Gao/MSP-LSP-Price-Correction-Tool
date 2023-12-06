# MSP-LSP-Price-Correction-Tool

This tool is designed to facilitate price adjustments for outlet items based on certain algorithms. It includes functionality for preprocessing Excel files, checking price differences, and generating bulk files.

### Prerequisites

- Python 3.x
- Required Python packages can be installed using:
  ```bash
  pip install -r requirements.txt
  
### Usage

1. Clone the repository:
2. Place the required files in the current directory in the specified format
3. Follow the on-screen instructions to process folders and perform price adjustments.

## Functionality

1. Preprocessing
The pre_process_folder function processes Excel files in a folder, merging tables, and producing a DataFrame for further analysis.

2. Price Adjustment
The PriceProcessor class handles the overall price adjustment process. It checks price differences, finds new prices, and generates bulk files.

3. Folder Processing
The FolderProcessor class processes all folders in the current directory. It utilizes the above functionalities to adjust prices for items in each folder.

