import re
from bs4 import BeautifulSoup
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.dates import MonthLocator, DateFormatter, DayLocator
from collections import defaultdict
import os
import numpy as np
import imageio
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd

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
    
    # Ensure build directory exists
    if not os.path.exists("build"):
        os.makedirs("build")
    
    dates, wpm_values, accuracy_values = zip(*filtered_data)
    
    # Plotting WPM
    plt.figure(figsize=(10, 6))
    plt.plot(dates, wpm_values, marker='o', linestyle='-', markersize=2)
    plt.title('WPM Over Time')
    plt.xlabel('Date')
    plt.ylabel('WPM')
    plt.yticks(range(0, 121, 5))  # setting y-axis ticks from 0 to 100, in increments of 5
    plt.ylim(0, 120)

    # Add secondary y-axis on the right
    ax2 = plt.twinx()
    ax2.spines['right'].set_visible(False)
    ax2.yaxis.set_ticks_position('none')
    ax2.set_yticks(range(0, 121, 5))
    ax2.set_ylim(0, 120)

    # Formatting x-axis to display months
    month_locator = MonthLocator()  # every month
    month_fmt = DateFormatter('%b')  # e.g., Jan, Feb, ...
    ax = plt.gca()
    ax.xaxis.set_major_locator(month_locator)
    ax.xaxis.set_major_formatter(month_fmt)

    plt.grid(True, which="both", ls="--")
    plt.tight_layout()
    plt.savefig(os.path.join('build', 'macro_wpm.png'))
    
    # Plotting Accuracy
    plt.figure(figsize=(10, 6))
    plt.plot(dates, accuracy_values, marker='o', linestyle='-', markersize=2)
    plt.title('Accuracy Over Time')
    plt.xlabel('Date')
    plt.ylabel('Accuracy (%)')

    min_accuracy = min(accuracy_values)
    tick_spacing = 2  # Define the desired tick spacing here
    starting_tick = tick_spacing * (min_accuracy // tick_spacing)
    y_ticks = [tick for tick in range(int(starting_tick), 121, tick_spacing)]
    
    plt.yticks(y_ticks)
    plt.ylim(min_accuracy, 100)

    # Formatting x-axis to display months
    ax = plt.gca()
    ax.xaxis.set_major_locator(month_locator)
    ax.xaxis.set_major_formatter(month_fmt)

    plt.grid(True, which="both", ls="--")
    plt.tight_layout()
    plt.savefig(os.path.join('build', 'macro_accuracy.png'))

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
    plt.title('WPM Statistics Over Time')
    plt.xlabel('Date')
    plt.ylabel('WPM')
    plt.yticks(range(0, 121, 5))
    plt.ylim(0, 120)

     # Add secondary y-axis on the right
    ax2 = plt.twinx()
    ax2.spines['right'].set_visible(False)
    ax2.yaxis.set_ticks_position('none')
    ax2.set_yticks(range(0, 121, 5))
    ax2.set_ylim(0, 120)

    plt.plot(days, max_wpm_values, color='blue', label='Max WPM', marker='o', markersize=2)
    plt.plot(days, min_wpm_values, color='red', label='Min WPM', marker='o', markersize=2)
    plt.plot(days, median_wpm_values, color='black', label='Median WPM', marker='o', markersize=2)

    # Formatting x-axis to display months
    ax = plt.gca()
    ax.xaxis.set_major_locator(month_locator)
    ax.xaxis.set_major_formatter(month_fmt)

    plt.legend(loc='upper left')  # Displaying the legend
    plt.grid(True, which="both", ls="--")
    plt.tight_layout()
    plt.savefig(os.path.join('build', 'macro_wpm_stats.png'))

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
    plt.title('7-day Rolling Average WPM Over Time')
    plt.xlabel('Date')
    plt.ylabel('WPM')
    plt.yticks(range(0, 121, 5))
    plt.ylim(0, 120)

     # Add secondary y-axis on the right
    ax2 = plt.twinx()
    ax2.spines['right'].set_visible(False)
    ax2.yaxis.set_ticks_position('none')
    ax2.set_yticks(range(0, 121, 5))
    ax2.set_ylim(0, 120)
    plt.plot(sorted_days, rolling_avg_values, color='green', label='7-day Avg WPM', marker='o', markersize=2)


    # Formatting x-axis to display months
    ax = plt.gca()
    ax.xaxis.set_major_locator(month_locator)
    ax.xaxis.set_major_formatter(month_fmt)

    plt.legend(loc='upper left')
    plt.grid(True, which="both", ls="--")
    plt.tight_layout()
    plt.savefig(os.path.join('build', 'macro_wpm_rolling_avg.png'))

    # Compute rolling WPM average of the last 100 records
    rolling_100_avg_values = [
        sum(wpm_values[max(0, i-99):i+1]) / len(wpm_values[max(0, i-99):i+1]) 
        for i in range(len(wpm_values))
    ]

    # Plotting Rolling Average of Last 100 records
    plt.figure(figsize=(10, 6))
    plt.title('100-Record Rolling Average WPM')
    plt.xlabel('Number of Records')
    plt.ylabel('WPM')
    plt.yticks(range(0, 121, 5))
    plt.ylim(0, 120)

     # Add secondary y-axis on the right
    ax2 = plt.twinx()
    ax2.spines['right'].set_visible(False)
    ax2.yaxis.set_ticks_position('none')
    ax2.set_yticks(range(0, 121, 5))
    ax2.set_ylim(0, 120)
    plt.plot(range(len(wpm_values)), rolling_100_avg_values, color='purple', label='100-Record Avg WPM', marker='o', markersize=2)

    plt.legend(loc='upper left')
    plt.grid(True, which="both", ls="--")
    plt.tight_layout()
    plt.savefig(os.path.join('build', 'macro_wpm_rolling_100_avg.png'))

    # Curve fitting using a degree 2 polynomial (quadratic fit)
    x_values = np.array(range(len(rolling_100_avg_values)))
    coeffs = np.polyfit(x_values, rolling_100_avg_values, 2)
    polynomial = np.poly1d(coeffs)
    y_fit = polynomial(x_values)

    # Plotting Rolling Average of Last 100 records with curve fit
    plt.figure(figsize=(10, 6))
    plt.xlabel('Number of Records')
    plt.ylabel('WPM')
    plt.yticks(range(0, 121, 5))
    plt.ylim(0, 120)

     # Add secondary y-axis on the right
    ax2 = plt.twinx()
    ax2.spines['right'].set_visible(False)
    ax2.yaxis.set_ticks_position('none')
    ax2.set_yticks(range(0, 121, 5))
    ax2.set_ylim(0, 120)
    plt.title('100-Record Rolling Average WPM with Curve Fit')

    plt.plot(x_values, rolling_100_avg_values, color='purple', label='100-Record Avg WPM', marker='o', markersize=2)
    plt.plot(x_values, y_fit, color='orange', label='Fitted Curve', linewidth=2)
    plt.legend(loc='upper left')
    plt.grid(True, which="both", ls="--")
    plt.tight_layout()
    plt.savefig(os.path.join('build', 'macro_wpm_rolling_100_avg_fit.png'))

    #rotating_3d_video(dates, wpm_values)

def rolling_avg_wpm_over_days(dates, wpm_values, max_days=122):
    result = []
    for num_days in range(1, max_days + 1):
        rolling_avg_values = []
        for i in range(len(dates)):
            last_days = wpm_values[max(0, i-num_days+1):i+1]
            avg_wpm = sum(last_days) / len(last_days)
            rolling_avg_values.append(avg_wpm)
        result.append(rolling_avg_values)
    return np.array(result)

def rotating_3d_video(dates, wpm_values, duration=8, rotation_degrees=360):
    # Determine the new figure size
    default_figsize = plt.rcParams["figure.figsize"]
    new_figsize = (2.50 * default_figsize[0], 2.50 * default_figsize[1])

    # Create the figure with the increased size
    fig = plt.figure(figsize=new_figsize)
    ax = fig.add_subplot(111, projection='3d')
    
    Z = rolling_avg_wpm_over_days(dates, wpm_values)
    date_diffs = [(date - dates[0]).days for date in dates]
    X, Y = np.meshgrid(date_diffs, np.arange(1, Z.shape[0] + 1, dtype=float))
    
    ax.set_xlabel('Time')
    ax.set_ylabel('Rolling Average Days')
    ax.set_zlabel('WPM')
    
    # Set the z-axis (WPM axis) limits
    ax.set_zlim(min(wpm_values), max(wpm_values))
    ax.set_ylim(1, 120)
    
    # Generate the list of the first of the month dates
    start_date = dates[0].replace(day=1)
    end_date = dates[-1].replace(day=1) + pd.DateOffset(months=1)
    first_of_month_dates = pd.date_range(start_date, end_date, freq='MS')
    
    month_ticks = [(date - dates[0]).days for date in first_of_month_dates]
    
    # Sort the list of first_of_month_dates
    sorted_dates = sorted(first_of_month_dates)

    # Construct the month_names list
    month_names = [date.strftime('%b') for date in sorted_dates]

    # Modify the first and last elements to include the year
    month_names[0] = sorted_dates[0].strftime('%b %Y')
    month_names[-1] = sorted_dates[-1].strftime('%b %Y')

    ax.set_xticks(month_ticks)
    ax.set_xticklabels(month_names, rotation=45)  # Adding rotation to the labels for better readability
    
    # Color the surface based on the WPM values with the 'twilight' colormap
    wframe = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap='twilight', shade=True, vmin=min(wpm_values), vmax=max(wpm_values))
    fig.colorbar(wframe, ax=ax, label='WPM')  # Adding a colorbar to the side of the plot for reference

    # Ensure directory exists
    video_dir = os.path.join("build", "video")
    if not os.path.exists(video_dir):
        os.makedirs(video_dir)

    ax.view_init(elev=30)
    
    filenames = []
    num_frames = duration * 35  # 35 FPS
    for i in range(num_frames):
        ax.view_init(elev=30, azim=i*(rotation_degrees/num_frames))
        filename = os.path.join(video_dir, f"tmp_frame_{i}.png")
        plt.savefig(filename)
        filenames.append(filename)
        
        # Print percentage progress
        progress = (i + 1) / num_frames * 100
        print(f"Rendering progress: {progress:.2f}%")

    # Create video using imageio
    with imageio.get_writer(os.path.join(video_dir, '3d_rotation_video.mp4'), fps=35) as writer:
        for filename in filenames:
            image = imageio.imread(filename)
            writer.append_data(image)
            
    # Remove temporary files
    for filename in filenames:
        os.remove(filename)



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

