import os
import logging
from datetime import datetime
from io import BytesIO
import tempfile

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.legends import Legend

from models import VitalSignType
from utils import get_vital_reference_range, get_vital_sign_unit

# Setup logger
logger = logging.getLogger(__name__)

def generate_patient_report(patient, doctor, vitals, notes, start_date=None, end_date=None):
    """
    Generate a PDF report for a patient's vital signs and notes
    
    Args:
        patient: Patient object
        doctor: Doctor object
        vitals: List of VitalSign objects
        notes: List of Note objects
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        
    Returns:
        BytesIO: PDF file as a binary stream
    """
    buffer = BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Heading1Center',
        parent=styles['Heading1'],
        alignment=1  # 0=left, 1=center, 2=right
    ))
    styles.add(ParagraphStyle(
        name='Normal-Center',
        parent=styles['Normal'],
        alignment=1
    ))
    
    # Build content
    content = []
    
    # Report Header
    content.append(Paragraph("Healthcare Monitoring Report", styles['Heading1Center']))
    content.append(Spacer(1, 12))
    
    # Date of report
    content.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal-Center']))
    content.append(Spacer(1, 24))
    
    # Patient Information
    content.append(Paragraph("Patient Information", styles['Heading2']))
    content.append(Spacer(1, 6))
    
    patient_data = [
        ["Name:", f"{patient.first_name} {patient.last_name}"],
        ["Date of Birth:", patient.date_of_birth.strftime('%Y-%m-%d')],
        ["Gender:", patient.gender or "Not specified"],
        ["Contact:", patient.contact_number or "Not provided"]
    ]
    
    patient_table = Table(patient_data, colWidths=[1.5*inch, 4*inch])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    content.append(patient_table)
    content.append(Spacer(1, 12))
    
    # Doctor Information
    content.append(Paragraph("Attending Physician", styles['Heading2']))
    content.append(Spacer(1, 6))
    
    doctor_data = [
        ["Name:", f"Dr. {doctor.first_name} {doctor.last_name}"],
        ["Specialty:", doctor.specialty or "General Practice"],
        ["Email:", doctor.email]
    ]
    
    doctor_table = Table(doctor_data, colWidths=[1.5*inch, 4*inch])
    doctor_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    content.append(doctor_table)
    content.append(Spacer(1, 24))
    
    # Vital Signs
    content.append(Paragraph("Vital Signs", styles['Heading2']))
    content.append(Spacer(1, 6))
    
    if vitals:
        # Filter period explanation
        if start_date and end_date:
            content.append(Paragraph(f"Period: From {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", styles['Normal']))
        elif start_date:
            content.append(Paragraph(f"Period: From {start_date.strftime('%Y-%m-%d')}", styles['Normal']))
        elif end_date:
            content.append(Paragraph(f"Period: Until {end_date.strftime('%Y-%m-%d')}", styles['Normal']))
            
        content.append(Spacer(1, 12))
        
        # Group vitals by type
        vitals_by_type = {}
        for vital in vitals:
            type_name = vital.type.value
            if type_name not in vitals_by_type:
                vitals_by_type[type_name] = []
            vitals_by_type[type_name].append(vital)
        
        # Create a table for each vital type
        for vital_type, type_vitals in vitals_by_type.items():
            # Get reference range
            reference = get_vital_reference_range(vital_type)
            unit = get_vital_sign_unit(vital_type)
            
            content.append(Paragraph(f"{reference['name']}", styles['Heading3']))
            content.append(Spacer(1, 3))
            
            # Reference range info
            if reference['min'] is not None and reference['max'] is not None:
                content.append(Paragraph(f"Normal Range: {reference['min']} - {reference['max']} {unit}", styles['Normal']))
                content.append(Spacer(1, 6))
            
            # Table header
            vitals_data = [["Date & Time", "Value", "Status"]]
            
            # Add data rows
            for vital in sorted(type_vitals, key=lambda v: v.recorded_at, reverse=True):
                # Determine status
                status = "Normal"
                status_color = colors.black
                
                if vital_type == 'blood_pressure':
                    # Special case for blood pressure
                    value_display = vital.value
                else:
                    value_display = f"{vital.value} {unit}"
                    # Check if value is outside normal range
                    value_str = str(vital.value)
                    if reference['min'] is not None and reference['max'] is not None:
                        if vital.value < reference['min']:
                            status = "Low"
                            status_color = colors.blue
                        elif vital.value > reference['max']:
                            status = "High"
                            status_color = colors.red
                
                vitals_data.append([
                    vital.recorded_at.strftime('%Y-%m-%d %H:%M'),
                    value_display,
                    status
                ])
            
            # Create table
            vitals_table = Table(vitals_data, colWidths=[2*inch, 2*inch, 1.5*inch])
            vitals_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            # Add status color coding
            for i in range(1, len(vitals_data)):
                if vitals_data[i][2] == "High":
                    vitals_table.setStyle(TableStyle([
                        ('TEXTCOLOR', (2, i), (2, i), colors.red),
                        ('FONTNAME', (2, i), (2, i), 'Helvetica-Bold')
                    ]))
                elif vitals_data[i][2] == "Low":
                    vitals_table.setStyle(TableStyle([
                        ('TEXTCOLOR', (2, i), (2, i), colors.blue),
                        ('FONTNAME', (2, i), (2, i), 'Helvetica-Bold')
                    ]))
            
            content.append(vitals_table)
            content.append(Spacer(1, 18))
    else:
        content.append(Paragraph("No vital signs recorded for this period.", styles['Normal']))
        content.append(Spacer(1, 12))
    
    # Notes
    content.append(Paragraph("Clinical Notes", styles['Heading2']))
    content.append(Spacer(1, 6))
    
    if notes:
        for i, note in enumerate(notes):
            doctor_name = f"Dr. {note.doctor.first_name} {note.doctor.last_name}"
            note_header = f"{note.created_at.strftime('%Y-%m-%d %H:%M')} - {doctor_name}"
            content.append(Paragraph(note_header, styles['Heading4']))
            content.append(Paragraph(note.content, styles['Normal']))
            content.append(Spacer(1, 12))
    else:
        content.append(Paragraph("No clinical notes recorded for this patient.", styles['Normal']))
    
    # Build the PDF
    doc.build(content)
    buffer.seek(0)
    
    return buffer


def generate_vital_trends_report(patient, vital_type, vitals, period_desc):
    """
    Generate a PDF report showing trends for a specific vital sign
    
    Args:
        patient: Patient object
        vital_type: Type of vital sign (string)
        vitals: List of VitalSign objects
        period_desc: Description of the time period
        
    Returns:
        BytesIO: PDF file as a binary stream
    """
    buffer = BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Heading1Center',
        parent=styles['Heading1'],
        alignment=1
    ))
    
    # Get reference range and unit
    reference = get_vital_reference_range(vital_type)
    unit = get_vital_sign_unit(vital_type)
    
    # Build content
    content = []
    
    # Report Header
    content.append(Paragraph(f"{reference['name']} Trend Analysis", styles['Heading1Center']))
    content.append(Spacer(1, 12))
    
    # Patient info
    content.append(Paragraph(f"Patient: {patient.first_name} {patient.last_name}", styles['Heading3']))
    content.append(Paragraph(f"Period: {period_desc}", styles['Normal']))
    content.append(Spacer(1, 24))
    
    if vitals:
        # Sort vitals by date
        sorted_vitals = sorted(vitals, key=lambda v: v.recorded_at)
        
        # Create a line chart for the vitals trend
        drawing = Drawing(400, 200)
        
        chart = HorizontalLineChart()
        chart.width = 350
        chart.height = 150
        chart.x = 25
        chart.y = 25
        
        # Prepare data
        dates = [v.recorded_at.strftime('%m/%d') for v in sorted_vitals]
        values = [v.value for v in sorted_vitals]
        
        chart.data = [values]
        chart.categoryAxis.categoryNames = dates
        chart.valueAxis.valueMin = min(values) * 0.9 if values else 0
        chart.valueAxis.valueMax = max(values) * 1.1 if values else 100
        
        # Add reference lines if available
        if reference['min'] is not None:
            chart.valueAxis.valueMin = min(chart.valueAxis.valueMin, reference['min'] * 0.9)
            chart.valueAxis.valueSteps.append(reference['min'])
        
        if reference['max'] is not None:
            chart.valueAxis.valueMax = max(chart.valueAxis.valueMax, reference['max'] * 1.1)
            chart.valueAxis.valueSteps.append(reference['max'])
        
        # Style the chart
        chart.lines[0].strokeWidth = 2
        chart.lines[0].strokeColor = colors.blue
        
        # Add the chart to the drawing
        drawing.add(chart)
        
        # Add drawing to content
        content.append(drawing)
        content.append(Spacer(1, 12))
        
        # Add a statistics table
        content.append(Paragraph("Statistics", styles['Heading3']))
        content.append(Spacer(1, 6))
        
        # Calculate statistics
        avg_value = sum(values) / len(values)
        min_value = min(values)
        max_value = max(values)
        
        # Count abnormal readings
        high_count = sum(1 for v in values if reference['max'] is not None and v > reference['max'])
        low_count = sum(1 for v in values if reference['min'] is not None and v < reference['min'])
        normal_count = len(values) - high_count - low_count
        
        # Create statistics table
        stats_data = [
            ["Average", f"{avg_value:.1f} {unit}"],
            ["Minimum", f"{min_value} {unit}"],
            ["Maximum", f"{max_value} {unit}"],
            ["Normal Readings", f"{normal_count} ({normal_count/len(values)*100:.1f}%)"],
            ["High Readings", f"{high_count} ({high_count/len(values)*100:.1f}%)"],
            ["Low Readings", f"{low_count} ({low_count/len(values)*100:.1f}%)"]
        ]
        
        stats_table = Table(stats_data, colWidths=[2*inch, 3*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(stats_table)
        content.append(Spacer(1, 18))
        
        # Detailed readings
        content.append(Paragraph("Detailed Readings", styles['Heading3']))
        content.append(Spacer(1, 6))
        
        # Table header
        readings_data = [["Date & Time", "Value", "Status"]]
        
        # Add data rows
        for vital in sorted_vitals:
            # Determine status
            status = "Normal"
            
            if reference['min'] is not None and reference['max'] is not None:
                if vital.value < reference['min']:
                    status = "Low"
                elif vital.value > reference['max']:
                    status = "High"
            
            readings_data.append([
                vital.recorded_at.strftime('%Y-%m-%d %H:%M'),
                f"{vital.value} {unit}",
                status
            ])
        
        # Create table
        readings_table = Table(readings_data, colWidths=[2*inch, 2*inch, 1.5*inch])
        readings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        # Add status color coding
        for i in range(1, len(readings_data)):
            if readings_data[i][2] == "High":
                readings_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (2, i), (2, i), colors.red),
                    ('FONTNAME', (2, i), (2, i), 'Helvetica-Bold')
                ]))
            elif readings_data[i][2] == "Low":
                readings_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (2, i), (2, i), colors.blue),
                    ('FONTNAME', (2, i), (2, i), 'Helvetica-Bold')
                ]))
        
        content.append(readings_table)
    else:
        content.append(Paragraph("No vital data available for this period.", styles['Normal']))
    
    # Recommendations section
    content.append(Spacer(1, 24))
    content.append(Paragraph("Recommendations", styles['Heading3']))
    content.append(Spacer(1, 6))
    content.append(Paragraph(
        "Please consult with your healthcare provider to discuss these results. This report is generated "
        "automatically and should be interpreted by a qualified medical professional.",
        styles['Normal']))
    
    # Build the PDF
    doc.build(content)
    buffer.seek(0)
    
    return buffer