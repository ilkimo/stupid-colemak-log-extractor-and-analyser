import re
from bs4 import BeautifulSoup
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.dates import MonthLocator, DateFormatter, DayLocator
from collections import defaultdict
import os

pattern = r"\{layout=colemak_DH,wpm=(\d+(?:\.\d)?),accuracy=(\d+(?:\.\d)?%)\}"
filtered_data = []

def print_colored(text, color):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "end": "\033[0m"
    }
    print(f"{colors[color]}{text}{colors['end']}")

def parse_html(file_path):
    match_count = 0
    with open(file_path, 'r', encoding="utf8") as file:
        soup = BeautifulSoup(file.read(), 'html.parser')
        for message in soup.find_all('div', class_='text'):
            matches = re.search(pattern, message.get_text())
            if matches:
                print_colored(f"Matched: {message.get_text().strip()}", "green")
                match_count += 1

                # Find parent message div
                parent_message = message.find_parent('div', class_='message')

                if parent_message:
                    # Within this parent message, find the date element
                    date_element = parent_message.find('div', class_='pull_right date details')

                    if date_element and 'title' in date_element.attrs:
                        date_str = date_element['title'].split(" UTC")[0]
                        full_date = datetime.strptime(date_str, '%d.%m.%Y %H:%M:%S')
                        
                        wpm = float(matches.group(1))
                        accuracy = float(matches.group(2).rstrip('%'))
                        filtered_data.append((full_date, wpm, accuracy))
                else:
                    print_colored(f"No parent message div found for: {message.get_text()}", "red")
            else:
                print_colored(f"No match: {message.get_text().strip()}", "red")
    return match_count


def plot_data():
    if not filtered_data:
        print("No data points found to plot.")
        return
    
    dates, wpm_values, accuracy_values = zip(*filtered_data)
    
    # Plotting WPM
    plt.figure(figsize=(10, 6))
    plt.plot(dates, wpm_values, marker='o', linestyle='-', markersize=2)
    plt.title('WPM Over Time')
    plt.xlabel('Date')
    plt.ylabel('WPM')
    plt.yticks(range(0, 101, 5))  # setting y-axis ticks from 0 to 100, in increments of 5
    plt.ylim(0, 100)

    # Formatting x-axis to display months
    month_locator = MonthLocator()  # every month
    month_fmt = DateFormatter('%b')  # e.g., Jan, Feb, ...
    ax = plt.gca()
    ax.xaxis.set_major_locator(month_locator)
    ax.xaxis.set_major_formatter(month_fmt)

    plt.grid(True, which="both", ls="--")
    plt.tight_layout()
    plt.savefig('macro_wpm.png')
    
    # Plotting Accuracy
    plt.figure(figsize=(10, 6))
    plt.plot(dates, accuracy_values, marker='o', linestyle='-', markersize=2)
    plt.title('Accuracy Over Time')
    plt.xlabel('Date')
    plt.ylabel('Accuracy (%)')

    min_accuracy = min(accuracy_values)
    tick_spacing = 2  # Define the desired tick spacing here
    starting_tick = tick_spacing * (min_accuracy // tick_spacing)
    y_ticks = [tick for tick in range(int(starting_tick), 101, tick_spacing)]
    
    plt.yticks(y_ticks)
    plt.ylim(min_accuracy, 100)

    # Formatting x-axis to display months
    ax = plt.gca()
    ax.xaxis.set_major_locator(month_locator)
    ax.xaxis.set_major_formatter(month_fmt)

    plt.grid(True, which="both", ls="--")
    plt.tight_layout()
    plt.savefig('macro_accuracy.png')

    # Aggregate WPM values by day
    wpm_by_day = defaultdict(list)
    for date, wpm in zip(dates, wpm_values):
        day = date.date()
        wpm_by_day[day].append(wpm)
    
    days = list(wpm_by_day.keys())
    max_wpm_values = [max(wpm_list) for wpm_list in wpm_by_day.values()]
    min_wpm_values = [min(wpm_list) for wpm_list in wpm_by_day.values()]
    median_wpm_values = [sorted(wpm_list)[len(wpm_list)//2] for wpm_list in wpm_by_day.values()]

    # Plotting Max, Min and Median WPM with connected lines
    plt.figure(figsize=(10, 6))
    plt.plot(days, max_wpm_values, color='blue', label='Max WPM', marker='o', markersize=2)
    plt.plot(days, min_wpm_values, color='red', label='Min WPM', marker='o', markersize=2)
    plt.plot(days, median_wpm_values, color='black', label='Median WPM', marker='o', markersize=2)

    plt.title('WPM Statistics Over Time')
    plt.xlabel('Date')
    plt.ylabel('WPM')
    plt.yticks(range(0, 101, 5))
    plt.ylim(0, 100)

    # Formatting x-axis to display months
    ax = plt.gca()
    ax.xaxis.set_major_locator(month_locator)
    ax.xaxis.set_major_formatter(month_fmt)

    plt.legend(loc='upper left')  # Displaying the legend
    plt.grid(True, which="both", ls="--")
    plt.tight_layout()
    plt.savefig('macro_wpm_stats.png')

    # Compute 7-day rolling averages
    sorted_days = sorted(wpm_by_day.keys())
    rolling_avg_values = []
    for i, day in enumerate(sorted_days):
        last_7_days = sorted_days[max(0, i-6):i+1]  # Get the last 7 days including the current day
        last_7_wpm = [sum(wpm_by_day[d])/len(wpm_by_day[d]) for d in last_7_days]  # Averages for each of the last 7 days
        avg_wpm = sum(last_7_wpm) / len(last_7_wpm)  # Average over the 7 days
        rolling_avg_values.append(avg_wpm)

    # Plotting 7-day Rolling Averages
    plt.figure(figsize=(10, 6))
    plt.plot(sorted_days, rolling_avg_values, color='green', label='7-day Avg WPM', marker='o', markersize=2)
    plt.title('7-day Rolling Average WPM Over Time')
    plt.xlabel('Date')
    plt.ylabel('WPM')
    plt.yticks(range(0, 101, 5))
    plt.ylim(0, 100)

    # Formatting x-axis to display months
    ax = plt.gca()
    ax.xaxis.set_major_locator(month_locator)
    ax.xaxis.set_major_formatter(month_fmt)

    plt.legend(loc='upper left')
    plt.grid(True, which="both", ls="--")
    plt.tight_layout()
    plt.savefig('macro_wpm_rolling_avg.png')

# Parsing multiple message files
file_num = 1
match_counts = []

file_name = f"messages.html"  # Starting with the first file

while os.path.exists(file_name):  # Loop while the file exists
    print(f"--------------Matching file {file_name}--------------")
    
    matches = parse_html(file_name)
    match_counts.append((file_name, matches))
    
    print(f"------------------------------------------------------")
    
    file_num += 1
    file_name = f"messages{file_num}.html"  # Move on to the next file

# Print out the number of matches for each file
for file_name, count in match_counts:
    print(f"Extracted {count} data points from {file_name}")

# Generate plots
plot_data()