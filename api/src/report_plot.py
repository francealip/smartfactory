import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re

def create_combined_object(data):
    """
    Support function that allows to combine bindings and extra requests into a single object from
    which is easly to create all graphs.

    Args:
        data (str): The data string containing the bindings and extra requests, separated by _SEPARATOR_.

    Returns:
        list: list of dictionaries containing the combined data.
    """
    report_bindings_str, extra_requests_str = data.split("_SEPARATOR_")
    extra_requests_str = extra_requests_str.replace('”', '"').replace('“', '"')
    # Parse the input strings into Python objects
    report_bindings = json.loads(report_bindings_str)
    extra_requests = json.loads(extra_requests_str)
    
    print(report_bindings)

    # Create a mapping of machine and KPI to the relevant dates
    period_data = [request["Date_Start"] for request in extra_requests]
    period_data = list(set(period_data))
    
    start_date = datetime.strptime(min(period_data), '%Y-%m-%d')
    end_date = datetime.strptime(max(period_data), '%Y-%m-%d')
    
    print(start_date, end_date)
    
    # Combine the data into the desired structure
    combined_objects = []
    for binding in report_bindings:
        machine = binding["machine"]
        kpi = binding["kpi"]
        graphical_el = binding["graphical_el"]

        # Fetch periods and values if available
        values = []
        i = start_date        
        while i <= end_date:           
            for result in extra_requests:
                if result["Machine_Name"] == machine and result["KPI_Name"] == kpi and result["Date_Start"] == i.strftime('%Y-%m-%d'):
                    try:
                        values.append(float(result["Value"]))
                    except:
                        values.append(-1)
                    break
            i += timedelta(days=1)
        
        
        periods = [int(period.split('-')[2]) for period in period_data]
        periods.sort()

        # Create the combined object
        combined_objects.append({
            "machine": machine,
            "kpi": kpi,
            "graphical_el": graphical_el,
            "period": periods,
            "values": values
        })

    return combined_objects

def parse_report_for_computed_kpis(report):
    """Extracts calculated KPIs for each machine from the report text, removes units, 
    and converts values to float.
    
    Args:
        report (str): The report text containing computed KPIs for each machine.
        
    Returns:
        list: A list of dictionaries containing the machine name and computed KPIs.
    """
    
    machine_sections = re.split(r'-- MACHINE: ', report)[1:]
    
    kpi_list = []

    for section in machine_sections:
        machine_name = section.split("\n")[0].strip()
        
        computed_kpis_section = re.search(r'Computed KPIs:\n(.*?)\n\nForecasted KPIs:', section, re.DOTALL)
        if computed_kpis_section:
            computed_kpis = computed_kpis_section.group(1).strip().splitlines()

            kpi_dict = {'machine': machine_name.replace(" --", "")}
            
            for kpi in computed_kpis:
                print(kpi)
                kpi_name, kpi_value = kpi.split(":")
                try:
                    kpi_value = float(re.sub(r'[^\d.]', '', kpi_value.strip()))
                except ValueError:
                    kpi_value = 0.0
                kpi_dict[kpi_name.strip()] = kpi_value

            kpi_list.append(kpi_dict)

    return kpi_list

def save_plot(filename):
    """Save the current plot as an image file in a predefined directory."""
    output_dir = "report_img"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, bbox_inches="tight")
    plt.close()
    
def plot_kpi_comparison(kpi_data):
    """Create a pie plot for comparing KPI values between different machines."""
    
    # Get the list of all KPIs (all keys except 'machine')
    kpi_names = [key for key in kpi_data[0].keys() if key != 'machine']
    machine_names = [entry['machine'].replace(" ", "\n") for entry in kpi_data]
    
    # Loop through each KPI and create a pie plot
    for kpi_name in kpi_names:
        # Extracting machine names and their corresponding KPI values
        kpi_values = [entry[kpi_name] for entry in kpi_data]

        # Check if there is a value diverse from 0 in kpi values
        if any(value != 0 for value in kpi_values):
            # Create a pie plot
            fig, ax = plt.subplots(figsize=(6, 6))
            wedges, texts, autotexts = ax.pie(kpi_values, labels=machine_names, autopct='%1.1f%%', startangle=90)

            ax.set_title(f'{kpi_name} Comparison', fontsize=17)
            plt.savefig(f'report_img/{kpi_name}_comparison.png')
        else:
            kpi_names.remove(kpi_name)
        
    return kpi_names
    
def plot_line(data, x, y, title="", **kwargs):
    """Create a line plot for the given data."""
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=data, x=x, y=y, **kwargs)
    plt.grid(True)  
    plt.xlabel(x, fontsize=16)  
    plt.ylabel(y, fontsize=16)
    title_plot = title.replace("_", " ").title()
    plt.title(f"Line Chart- {title_plot}", fontsize=17)
    save_plot(f"line_chart_{title}.png")

def plot_area(data, x, y, title="", **kwargs):
    """Create an area plot for the given data."""
    plt.figure(figsize=(10, 6))
    plt.fill_between(data[x], data[y], alpha=0.4, **kwargs)
    plt.plot(data[x], data[y], **kwargs)
    plt.grid(True)  
    plt.xlabel(x, fontsize=16)  
    plt.ylabel(y, fontsize=16)
    title_plot = title.replace("_", " ").title()
    plt.title(f"Area Chart- {title_plot}", fontsize=17)
    save_plot(f"area_chart_{title}.png")

def plot_barv(data, x, y, title="", **kwargs):
    """Create a vertical bar plot for the given data."""
    plt.figure(figsize=(10, 6))
    sns.barplot(data=data, x=x, y=y, **kwargs)
    plt.grid(axis='y')  
    plt.xlabel(x, fontsize=16)  
    plt.ylabel(y, fontsize=16)
    title_plot = title.replace("_", " ").title()
    plt.title(f"Vertical Bar Chart- {title_plot}", fontsize=17)
    save_plot(f"barv_chart_{title}.png")

def plot_barh(data, x, y, title="", **kwargs):
    """Create a horizontal bar plot for the given data."""
    plt.figure(figsize=(10, 6))
    sns.barplot(data=data, x=y, y=x, orient='h', **kwargs)
    plt.grid(axis='x') 
    plt.xlabel(y, fontsize=16)
    plt.ylabel(x, fontsize=16)
    title_plot = title.replace("_", " ").title()
    plt.title(f"Horizontal Bar Chart- {title_plot}", fontsize=17)
    save_plot(f"barh_chart_{title}.png")

def plot_pie(data, x, y, title="", **kwargs):
    """Create a pie plot for the given data."""
    plt.figure(figsize=(8, 8))
    wedges, texts, autotexts = plt.pie(
        data[y], 
        labels=data[x], 
        autopct='%1.1f%%', 
        pctdistance=0.85,  
        labeldistance=1.1,  
        **kwargs
    )
    
    for i, text in enumerate(texts):
        text.set_fontsize(10)
        if i % 2 == 0:
            text.set_position((text.get_position()[0] * 1.1, text.get_position()[1] * 1.1))  
        else:
            text.set_position((text.get_position()[0] * 0.9, text.get_position()[1] * 0.9))  

    for autotext in autotexts:
        autotext.set_fontsize(10)
        autotext.set_color("white")
    title_plot = title.replace("_", " ").title()
    plt.title(f"Pie Chart- {title_plot}", fontsize=17)
    save_plot(f"pie_chart_{title}.png")

def plot_donut(data, x, y, title="", **kwargs):
    """Create a donut plot for the given data."""
    plt.figure(figsize=(8, 8))
    wedges, texts, autotexts = plt.pie(
        data[y], 
        labels=data[x], 
        autopct='%1.1f%%', 
        pctdistance=0.85, 
        labeldistance=1.1,  
        **kwargs
    )
    
    for i, text in enumerate(texts):
        text.set_fontsize(10)
        if i % 2 == 0:
            text.set_position((text.get_position()[0] * 1.1, text.get_position()[1] * 1.1))  
        else:
            text.set_position((text.get_position()[0] * 0.9, text.get_position()[1] * 0.9))  
    
    for autotext in autotexts:
        autotext.set_fontsize(10)
        autotext.set_color("white")
    
    plt.gca().add_artist(plt.Circle((0, 0), 0.70, fc='white'))
    title_plot = title.replace("_", " ").title()
    plt.title(f"Donut Chart- {title_plot}", fontsize=17)
    save_plot(f"donut_chart_{title}.png")

def plot_scatter(data, x, y, title="", **kwargs):
    """Create a scatter plot for the given data."""
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=data, x=x, y=y, **kwargs)
    plt.grid(True)  
    plt.xlabel(x, fontsize=16)  
    plt.ylabel(y, fontsize=16)
    title_plot = title.replace("_", " ").title()
    plt.title(f"Scatter Plot- {title_plot}", fontsize=17)
    save_plot(f"scatter_chart_{title}.png")


def plot_chart(chart_id, data, title="", **kwargs):
    chart_mapping = {
        "line": plot_line,
        "area": plot_area,
        "barv": plot_barv,
        "barh": plot_barh,
        "pie": plot_pie,
        "donut": plot_donut,
        "scatter": plot_scatter,
    }

    # Default Case Is Area Chart
    if chart_id not in chart_mapping:
        chart_id = "area"

    chart_mapping[chart_id](data, title=title, **kwargs)
