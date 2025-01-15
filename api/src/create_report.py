from fpdf import FPDF
import json
import glob
import os
import sys
from report_plot import create_combined_object, plot_chart, plot_kpi_comparison, parse_report_for_computed_kpis
from datetime import datetime

def parse_report(report):
    """Parse the report into metadata (contents), machine KPIs, and summary."""
    sections = report.split("-- ")
    metadata = sections[0].strip()
    machines = {}
    summary = ""

    for section in sections[1:]:
        if section.startswith("MACHINE: "):
            machine_name = section.split("--")[0].split(": ")[1].strip()
            content = section.split("Computed KPIs:")[1]
            computed_kpis = content.split("Forecasted KPIs:")[0].strip()
            forecasted_kpis = content.split("Forecasted KPIs:")[1].strip()
            
            machines[machine_name] = {
                "computed_kpis": computed_kpis,
                "forecasted_kpis": forecasted_kpis,
            }
        elif section.startswith("SUMMARY --"):
            summary = section.split("SUMMARY --")[1].strip()

    return metadata, machines, summary

def add_kpis_to_pdf(pdf, machine_name, kpis, x_offset=10, y_start=40):
    """Add KPIs to the PDF, returning final position (y)"""
    # Add Machine Name
    pdf.set_font("Arial", size=15, style='B')
    pdf.set_xy(x_offset, y_start)
    pdf.cell(0, 10, f"Machine: {machine_name}", ln=True)

    # Add Computed KPIs
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, "Computed KPIs:", ln=True)
    pdf.set_font("Arial", size=12)
    for line in kpis['computed_kpis'].splitlines():
        pdf.cell(0, 8, "  " + line.strip(), ln=True)
    
    # Add forecasted KPIs
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(0, 10, "Forecasted KPIs:", ln=True)
    pdf.set_font("Arial", size=12)
    for line in kpis['forecasted_kpis'].splitlines():
        if line.strip().startswith("-"):
            line = "     " + line.strip()
        else:
            line = "  " + line.strip()  
        pdf.cell(0, 8, line, ln=True)
    
    pdf.ln(5)
    y_forecasted_kpis = pdf.get_y()
    
    # Return the final y position
    return y_forecasted_kpis

def name_to_id(name):
    """Convert a name to a valid ID."""
    return name.lower().replace(" ", "_")
    
def create_pdf_with_images(text, appendix, data, path):
    """Generate the report pdf starting from the text and the extra data for images."""
    class PDF(FPDF):
        """Class to automatically add footer to each page."""
        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", size=10)
            self.set_text_color(0, 0, 0)
            
            # Add the current date on the left
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_date = f"Generated on: {current_date}"            
            self.cell(0, 10, current_date, align='L')

            # Add the page number on the right
            page_width = self.w
            self.set_x(page_width - 20)
            self.cell(0, 10, f"Page {self.page_no()}", align='R')
            
    data_for_imgs = create_combined_object(data)
    
    # Parse the report
    metadata, machines, summary = parse_report(text)
    title, description = metadata.split("Description:")
    
    pdf = PDF()
    try:
        pdf.set_auto_page_break(auto=True, margin=17)
        pdf.add_page()
        
        # Add title
        pdf.set_font("Arial", size=18, style='B')
        pdf.cell(0, 10, title, ln=True, align='C')
        pdf.ln(10)

        # Add description
        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(25, 5, "Description: ", ln=False)

        pdf.set_font("Arial", style="", size=12)
        pdf.multi_cell(0, 5, description)

        pdf.ln(4)

        # Add a line
        left_margin = pdf.l_margin
        right_margin = pdf.w - pdf.r_margin
        y_position = pdf.get_y()  

        pdf.line(left_margin, y_position, right_margin, y_position)
        
        y_start = pdf.get_y() #starting position of first machine
        
        for machine_name, kpis in machines.items():
            for obj in data_for_imgs:
                if obj["machine"] == machine_name:
                    plot_chart(
                        obj["graphical_el"], 
                        obj, 
                        x="period", 
                        y="values", 
                        title=f"{name_to_id(obj['machine'])}_{obj['kpi']}"
                    )
                    image_path = f"report_img/{obj['graphical_el']}_chart_{name_to_id(obj['machine'])}_{obj['kpi']}.png"
                
                    # Insert the image aligned with the corresponding machine name
                    pdf.image(image_path, x=110, y=y_start, w=90)
            # Add KPIs of the machine to the PDF        
            y_start = add_kpis_to_pdf(pdf, machine_name, kpis, y_start=y_start)
        
        # Manage Summary Section
        pdf.add_page()
        pdf.set_font("Arial", size=15, style='B')
        pdf.cell(0, 10, "Summary", ln=True, align='C')
        pdf.ln(10)
            
        comparisons, rest = summary.split("Predicted Values Insights:")
        insight, suggestions = rest.split("Suggestions:")

        # Machine comparisons subsection
        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(0, 5, "Machine Comparisons:", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 5, comparisons.split("Machine Comparisons:")[1])
        pdf.ln(5)

        # Add the machine comparison KPI plots
        kpi_data = parse_report_for_computed_kpis(text)
        kpi_names = plot_kpi_comparison(kpi_data)

        # Support variables for image positioning
        x_offset = 10
        y_offset = pdf.get_y() + 5  
        image_width = 80
        image_height = 80
        images_per_row = 2
        page_width = 210  

        # Add the KPI comparison images
        for i, kpi_name in enumerate(kpi_names):
            image_path = f"report_img/{kpi_name}_comparison.png"
            kpi_display_name = kpi_name.replace("_", " ").title()
            
            # Position the images in a grid (2 images per row)
            if i % images_per_row == 0 and i != 0:
                y_offset += image_height + 10  
                if y_offset + image_height > 290:
                    pdf.add_page()
                    y_offset = 10
                x_offset = 10  
                
            # Calculate the x offset for the image
            x_offset = (page_width - image_width * images_per_row - 10 * (images_per_row - 1)) / 2 + (i % images_per_row) * (image_width + 10)

            pdf.set_xy(x_offset, y_offset)
            pdf.set_font("Arial", size=10, style='B')
            pdf.cell(image_width, 10, kpi_display_name, ln=True, align='C')
            
            # Add the image to the PDF and update the x offset
            pdf.image(image_path, x=x_offset, y=y_offset + 10, w=image_width, h=image_height)
            x_offset += image_width + 10

        # Insights subsection
        pdf.ln(y_offset + image_height + 10)  
        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(0, 5, "Predicted Values Insights:", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 5, insight)
        pdf.ln(5)

        # Suggestions subsection
        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(0, 5, "Suggestions:", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 5, suggestions)
        
        # Appendix Section
        pdf.add_page()
        pdf.set_font('Arial', 'B', 15)
        pdf.cell(0, 10, 'Appendix', 0, 1, 'C')
        pdf.set_font('Arial', size=12)
        appendix = json.loads(appendix)
        for obj in appendix:
            if obj.get("context", None) is not None and obj.get("reference_number", None) is not None and obj.get("source_name", None) is not None:
                pdf.set_font("Arial", "B", 12)
                pdf.cell(190, 5, f"Reference Number: [{str(obj['reference_number'])}]", ln=True, align='L')
                pdf.set_font("Arial", "", 10)
                
                # Add the context of the reference
                pdf.cell(190, 5, "Context:", ln=True, align='L')
                lines = obj["context"].split("\n")
                for line in lines:
                    if len(line) > 0:
                        pdf.multi_cell(190, 5, line)
                    else:
                        pdf.ln()
                
                pdf.ln(2) 
                
                # Print the source name
                pdf.set_text_color(0, 0, 255)
                pdf.cell(190, 5, f"Source: {str(obj['source_name'])}", ln=True, align='L')
                pdf.set_text_color(0, 0, 0)
                
                pdf.ln(3) 

                # Add a separator line
                pdf.set_draw_color(0, 0, 0)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y()) 
                pdf.ln(3)  
        
        # Remove all images in the report_img directory to avoid duplicates in the next reports
        files = glob.glob('report_img/*')
        for f in files:
            os.remove(f)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
    pdf.output(name=path, dest="F")