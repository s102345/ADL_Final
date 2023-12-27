import json
import re
import matplotlib.pyplot as plt
from collections import Counter

import numpy as np

train = json.load(open('./data/train.json'))
test = json.load(open('./data/test.json'))

data = train + test

data_text = [d['text'] for d in data]

def extract_title_content(text):
    # Regex pattern to match the format "標題：[title] 內容：[content]"
    pattern = r"標題：(.*?) 內容：(.*?)$"
    match = re.search(pattern, text, re.DOTALL)
    
    if match:
        return match.group(1).strip(), match.group(2).strip()
    else:
        return "", ""
    
data_title = []
data_content = []
line, ptt, youtube, baha = 0, 0, 0, 0
c_line, c_ptt, c_youtube, c_baha = 0, 0, 0, 0
unknown = 0
titles = json.load(open('./titles.json', 'r'))
s = set()
for text in data_text:
    title, comment = extract_title_content(text)

    if title in titles:
        if titles[title] == "Line":
            if title not in s:
                line += 1
            c_line += 1
        elif titles[title] == "PTT":
            if title not in s:
                ptt += 1
            c_ptt += 1
        elif titles[title] == "Youtube":
            if title not in s:
                youtube += 1
            c_youtube += 1
        elif titles[title] == "Baha":
            if title not in s:
                baha += 1   
            c_baha += 1
    else:
        unknown += 1
    s.add(title)
    data_title.append(title)
    data_content.append(comment)

print(len(data_content))
print("POST")
print("Line", line, "PTT", ptt, "Youtube", youtube, "Baha", baha, "Total", line + ptt + youtube + baha, "Unknown", unknown)
print("COMMENT")
print("Line", c_line, "PTT", c_ptt, "Youtube", c_youtube, "Baha", c_baha, "Total", c_line + c_ptt + c_youtube + c_baha, "Unknown", unknown)

def plot_string_lengths_histogram_combined(strings, bin_width=5, combine_threshold=100):
    """
    Function to plot a histogram of string lengths in an array using matplotlib,
    combining all lengths greater than a specified threshold into a single bin.

    Args:
    strings (list of str): The array of strings to be analyzed.
    bin_width (int): The width of each bin in the histogram.
    combine_threshold (int): The threshold above which string lengths are combined.

    Returns:
    None: This function plots the histogram.
    """
    # Calculate lengths of each string
    lengths = [len(s) for s in strings]

    # Adjusting lengths to combine those greater than the threshold
    adjusted_lengths = [length if length <= combine_threshold else combine_threshold + bin_width for length in lengths]

    # Create bins for the histogram
    max_length = max(adjusted_lengths)
    bins = np.arange(0, max_length + bin_width, bin_width)

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.hist(adjusted_lengths, bins=bins, color='skyblue', edgecolor='black', align='left')
    plt.xlabel('Length of String')
    plt.ylabel('Count of Strings')
    plt.title('Histogram of String Lengths (Combining Lengths > {})'.format(combine_threshold))
    # Adjust x-ticks to include the combined bin
    plt.xticks(bins[:-1], [str(bin) if bin <= combine_threshold else f'>{combine_threshold}' for bin in bins[:-1]])
    plt.show()

# Example usage
plot_string_lengths_histogram_combined(data_content, bin_width=5, combine_threshold=100) # Combining lengths > 100

