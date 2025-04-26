import os
import logging
from datetime import datetime, timedelta
from io import BytesIO
import tempfile
import json
from flask import session
from flask_babel import gettext as _

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.legends import Legend

from models import VitalSignType, VitalObservation
import health_platforms

# Setup logger
logger = logging.getLogger(__name__)

# Define days for each period string
PERIOD_DAYS = {
    '1d': 1,
    '7d': 7,
    '1m': 30,
    '3m': 90,
    '1y': 365
}

def create_vital_chart(vitals_data, period_name, vital_type):
    """
    Create a chart drawing for a specific vital sign and time period
    
    Args:
        vitals_data: List of data points
        period_name: Name of the time period for the chart title
        vital_type: Type of vital sign
        
    Returns:
        Drawing: ReportLab Drawing object containing the chart
    """
    # Sort data by timestamp
    sorted_data = sorted(vitals_data, key=lambda v: v.get('timestamp', ''))
    
    # Extract values and dates for chart
    values = [float(v.get('value', 0)) for v in sorted_data]
    timestamps = [v.get('timestamp', '') for v in sorted_data]
    
    # Format dates for display
    dates = []
    for ts in timestamps:
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                dates.append(dt.strftime('%m/%d'))
            except (ValueError, AttributeError):
                dates.append('')
        else:
            dates.append('')
    
    # Limit number of data points to make chart readable
    max_points = 20
    if len(values) > max_points:
        step = len(values) // max_points
        values = values[::step]
        dates = dates[::step]
    
    # Create drawing and chart
    drawing = Drawing(450, 200)
    
    chart = HorizontalLineChart()
    chart.width = 400
    chart.height = 150
    chart.x = 25
    chart.y = 25
    
    # Set data
    if values:
        chart.data = [values]
        chart.categoryAxis.categoryNames = dates
        chart.valueAxis.valueMin = min(values) * 0.9 if values else 0
        chart.valueAxis.valueMax = max(values) * 1.1 if values else 100
        
        # Ensure min and max are float
        chart.valueAxis.valueMin = float(chart.valueAxis.valueMin)
        chart.valueAxis.valueMax = float(chart.valueAxis.valueMax)
        
        # Style the chart
        chart.lines[0].strokeWidth = 2
        chart.lines[0].strokeColor = colors.blue
        
        # Add title
        vital_name = vital_type.replace('_', ' ').title()
        title = f"{vital_name} - {period_name}"
        
        drawing.add(chart)
        
        # Add legend with title
        legend = Legend()
        legend.alignment = 'right'
        legend.x = 25
        legend.y = 180
        legend.columnMaximum = 1
        legend.fontName = 'Helvetica'
        legend.fontSize = 8
        legend.dxTextSpace = 5
        legend.dy = 5
        legend.dx = 10
        legend.deltay = 10
        legend.colorNamePairs = [(colors.blue, title)]
        drawing.add(legend)
    
    return drawing

def generate_specific_report(patient, doctor, selected_notes, selected_vital_types, selected_charts, selected_observations, summary=None, language=None):
    """
    Generate a specific PDF report with only selected data
    
    Args:
        patient: Patient object
        doctor: Doctor object
        selected_notes: List of selected Note objects
        selected_vital_types: List of selected vital types
        selected_charts: Dict mapping vital type to list of selected time periods
        selected_observations: List of selected VitalObservation objects
        summary: Optional summary text provided by the doctor (not saved to database)
        language: Optional language code override (it/en)
        
    Returns:
        BytesIO: PDF file as a binary stream
    """
    buffer = BytesIO()
    
    # Set language if provided (Flask-Babel handles this automatically if None)
    if language:
        # Qui potrebbe essere necessario un meccanismo per impostare la lingua temporaneamente
        pass
    
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
    styles.add(ParagraphStyle(
        name='Normal-Bold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold'
    ))
    
    # Build content
    content = []
    
    # Report Header
    content.append(Paragraph(_('Specific Report'), styles['Heading1Center']))
    content.append(Spacer(1, 12))
    
    # Date of report
    content.append(Paragraph(f"{_('Generated on')}: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal-Center']))
    content.append(Spacer(1, 24))
    
    # Patient Information
    content.append(Paragraph(_('Patient Information'), styles['Heading2']))
    content.append(Spacer(1, 6))
    
    patient_data = [
        [f"{_('Name')}:", f"{patient.first_name} {patient.last_name}"],
        [f"{_('Date of Birth')}:", patient.date_of_birth.strftime('%Y-%m-%d')],
        [f"{_('Gender')}:", patient.gender or _('Not specified')],
        [f"{_('Contact')}:", patient.contact_number or _('Not provided')]
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
    content.append(Paragraph(_('Attending Physician'), styles['Heading2']))
    content.append(Spacer(1, 6))
    
    doctor_data = [
        [f"{_('Name')}:", f"Dr. {doctor.first_name} {doctor.last_name}"],
        [f"{_('Specialty')}:", doctor.specialty or _('General Practice')],
        [f"{_('Email')}:", doctor.email]
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
    
    # Summary section (if provided)
    if summary:
        content.append(Paragraph(_('Summary'), styles['Heading2']))
        content.append(Spacer(1, 6))
        content.append(Paragraph(summary, styles['Normal']))
        content.append(Spacer(1, 24))
    
    # Selected notes section
    if selected_notes:
        content.append(Paragraph(_('Clinical Notes'), styles['Heading2']))
        content.append(Spacer(1, 6))
        
        for i, note in enumerate(selected_notes):
            date_str = note.created_at.strftime('%Y-%m-%d %H:%M')
            doctor_name = f"Dr. {note.doctor.first_name} {note.doctor.last_name}"
            content.append(Paragraph(f"<b>{date_str} - {doctor_name}</b>", styles['Normal']))
            content.append(Paragraph(note.content, styles['Normal']))
            content.append(Spacer(1, 6))
            
            # Add a divider between notes except for the last one
            if i < len(selected_notes) - 1:
                content.append(Spacer(1, 6))
                content.append(Paragraph("_" * 80, styles['Normal']))
                content.append(Spacer(1, 6))
        
        content.append(Spacer(1, 24))
    
    # Selected vital signs section
    if selected_vital_types and selected_charts:
        content.append(Paragraph(_('Vital Signs'), styles['Heading2']))
        content.append(Spacer(1, 6))
        
        from health_platforms import get_vitals_data
          # Map period strings to days and display names
        period_display = {
            '1d': (1, _('1 Day')),
            '7d': (7, _('7 Days')),
            '1m': (30, _('1 Month')),
            '3m': (90, _('3 Months'))
        }
        
        for vital_type in selected_vital_types:
            vital_type_value = vital_type.value
            content.append(Paragraph(f"{vital_type_value.replace('_', ' ').title()}", styles['Heading3']))
            content.append(Spacer(1, 6))
            
            # Check if this vital type has selected charts
            if vital_type_value in selected_charts and selected_charts[vital_type_value]:
                periods = selected_charts[vital_type_value]
                
                for period_days in periods:
                    # Get period display name
                    if period_days == 1:
                        period_name = _('1 Day')
                    elif period_days == 7:
                        period_name = _('7 Days')
                    elif period_days == 30:
                        period_name = _('1 Month')
                    elif period_days == 90:
                        period_name = _('3 Months')
                    else:
                        period_name = f"{period_days} days"
                    
                    # Calculate date range
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=period_days)
                    
                    try:
                        # Try to get data from health platform
                        vitals_data = get_vitals_data(
                            patient,
                            vital_type_value,
                            start_date.strftime('%Y-%m-%d'),
                            end_date.strftime('%Y-%m-%d')
                        )
                        
                        if vitals_data and len(vitals_data) > 0:
                            # Create chart
                            chart = create_vital_chart(vitals_data, period_name, vital_type_value)
                            content.append(chart)
                            content.append(Spacer(1, 12))
                            
                        else:
                            content.append(Paragraph(f"{period_name}: {_('No vital data available for this period.')}", styles['Normal']))
                            content.append(Spacer(1, 6))
                            
                    except Exception as e:
                        logger.error(f"Error getting data for {vital_type_value}: {str(e)}")
                        content.append(Paragraph(f"{period_name}: {_('No vital data available for this period.')}", styles['Normal']))
                        content.append(Spacer(1, 6))
            else:
                content.append(Paragraph(_('No vital data available for this period.'), styles['Normal']))
                
            content.append(Spacer(1, 18))
    
    # Selected observations section
    if selected_observations:
        content.append(PageBreak())
        content.append(Paragraph(_('Observations'), styles['Heading2']))
        content.append(Spacer(1, 6))
        
        # Group observations by vital type
        obs_by_type = {}
        for obs in selected_observations:
            vital_type = obs.vital_type.value
            if vital_type not in obs_by_type:
                obs_by_type[vital_type] = []
            obs_by_type[vital_type].append(obs)
        
        # Add observations for each vital type
        for vital_type, obs_list in obs_by_type.items():
            content.append(Paragraph(f"{vital_type.replace('_', ' ').title()}", styles['Heading3']))
            content.append(Spacer(1, 6))
            
            for i, obs in enumerate(obs_list):
                # Format the date range
                date_range = f"{obs.start_date.strftime('%Y-%m-%d')} - {obs.end_date.strftime('%Y-%m-%d')}"
                doctor_name = f"Dr. {obs.doctor.first_name} {obs.doctor.last_name}"
                
                content.append(Paragraph(f"<b>{date_range} - {doctor_name}</b>", styles['Normal']))
                content.append(Paragraph(obs.content, styles['Normal']))
                content.append(Spacer(1, 6))
                
                # Add a divider between observations except for the last one
                if i < len(obs_list) - 1:
                    content.append(Spacer(1, 3))
                    content.append(Paragraph("_" * 40, styles['Normal']))
                    content.append(Spacer(1, 3))
            
            content.append(Spacer(1, 12))
    
    # Build PDF
    doc.build(content)
    buffer.seek(0)
    return buffer

def generate_vital_trends_report(patient, doctor, vital_type, period='1m'):
    """
    Generate a trend analysis report for a specific vital sign
    
    Args:
        patient: Patient object
        doctor: Doctor object
        vital_type: Type of vital sign
        period: Time period to analyze (1d, 7d, 1m, 3m, 1y)
        
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
    content.append(Paragraph(_('Trend Analysis'), styles['Heading1Center']))
    content.append(Spacer(1, 12))
    
    # Date of report
    content.append(Paragraph(f"{_('Generated on')}: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal-Center']))
    content.append(Spacer(1, 24))
    
    # Patient Information
    content.append(Paragraph(_('Patient'), styles['Heading2']))
    content.append(Spacer(1, 6))
    
    patient_data = [
        [f"{_('Name')}:", f"{patient.first_name} {patient.last_name}"],
        [f"{_('Date of Birth')}:", patient.date_of_birth.strftime('%Y-%m-%d')]
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
    
    # Vital Sign Information
    days = PERIOD_DAYS.get(period, 30)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Mapping of vital types to names
    vital_names = {
        'heart_rate': _('Heart Rate'),
        'blood_pressure': _('Blood Pressure'),
        'temperature': _('Temperature'),
        'respiratory_rate': _('Respiratory Rate'),
        'oxygen_saturation': _('Oxygen Saturation'),
        'weight': _('Weight'),
        'steps': _('Steps'),
        'sleep_duration': _('Sleep Duration'),
    }
    
    # Mapping of vital types to units
    vital_units = {
        'heart_rate': 'bpm',
        'blood_pressure': 'mmHg',
        'temperature': '°C',
        'respiratory_rate': 'breaths/min',
        'oxygen_saturation': '%',
        'weight': 'kg',
        'steps': 'steps',
        'sleep_duration': 'hours',
    }
    
    vital_name = vital_names.get(vital_type, vital_type.replace('_', ' ').title())
    vital_unit = vital_units.get(vital_type, '')
    
    content.append(Paragraph(f"{vital_name} - {_('Period')}: {days} {_('days')}", styles['Heading2']))
    content.append(Spacer(1, 6))
    
    content.append(Paragraph(f"{_('period_from_to').format(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))}", styles['Normal']))
    content.append(Spacer(1, 12))
    
    # Try to get data from health platforms
    from health_platforms import get_vitals_data
    
    try:
        vitals_data = get_vitals_data(
            patient,
            vital_type,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        if not vitals_data or len(vitals_data) == 0:
            content.append(Paragraph(_('No vital data available for this period.'), styles['Normal']))
        else:
            # Create chart
            period_name = {
                '1d': _('One Day'),
                '7d': _('Seven Days'),
                '1m': _('One Month'),
                '3m': _('Three Months'),
                '1y': _('One Year')
            }.get(period, str(days) + ' ' + _('days'))
            
            chart = create_vital_chart(vitals_data, period_name, vital_type)
            content.append(chart)
            content.append(Spacer(1, 24))
            
            # Statistics section
            content.append(Paragraph(_('Statistics'), styles['Heading2']))
            content.append(Spacer(1, 6))
            
            # Calculate statistics
            values = [float(v.get('value', 0)) for v in vitals_data]
            
            if values:
                avg_value = sum(values) / len(values)
                min_value = min(values)
                max_value = max(values)
                
                # Get normal ranges
                normal_ranges = {
                    'heart_rate': (60, 100),
                    'blood_pressure_systolic': (90, 120),
                    'blood_pressure_diastolic': (60, 80),
                    'temperature': (36.1, 37.2),
                    'respiratory_rate': (12, 20),
                    'oxygen_saturation': (95, 100),
                }
                
                # Count readings in each range
                normal_range = normal_ranges.get(vital_type, (0, 0))
                normal_count = sum(1 for v in values if normal_range[0] <= v <= normal_range[1])
                high_count = sum(1 for v in values if v > normal_range[1])
                low_count = sum(1 for v in values if v < normal_range[0])
                
                # Create statistics table
                stats_data = [
                    [_('Average'), f"{avg_value:.1f} {vital_unit}"],
                    [_('Minimum'), f"{min_value:.1f} {vital_unit}"],
                    [_('Maximum'), f"{max_value:.1f} {vital_unit}"],
                    [_('Normal Readings'), f"{normal_count} ({normal_count/len(values)*100:.1f}%)"],
                    [_('High Readings'), f"{high_count} ({high_count/len(values)*100:.1f}%)"],
                    [_('Low Readings'), f"{low_count} ({low_count/len(values)*100:.1f}%)"],
                ]
                
                stats_table = Table(stats_data, colWidths=[2*inch, 2*inch])
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
                content.append(Spacer(1, 24))
                
                # Detailed readings section
                content.append(Paragraph(_('Detailed Readings'), styles['Heading2']))
                content.append(Spacer(1, 6))
                
                # Limit to the most recent 20 readings if there are many
                display_data = vitals_data
                if len(display_data) > 20:
                    display_data = sorted(vitals_data, key=lambda v: v.get('timestamp', ''), reverse=True)[:20]
                    content.append(Paragraph(_('Showing the 20 most recent readings'), styles['Normal']))
                    content.append(Spacer(1, 6))
                
                # Create table headers
                readings_data = [[_('Date/Time'), _('Value'), _('Status')]]
                
                # Add each reading
                for v in sorted(display_data, key=lambda v: v.get('timestamp', ''), reverse=True):
                    timestamp = v.get('timestamp', '')
                    value = float(v.get('value', 0))
                    
                    # Format date
                    date_str = ""
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            date_str = dt.strftime('%Y-%m-%d %H:%M')
                        except (ValueError, AttributeError):
                            date_str = timestamp
                    
                    # Determine status
                    status = _('Normal')
                    status_color = colors.green
                    if value > normal_range[1]:
                        status = _('High')
                        status_color = colors.red
                    elif value < normal_range[0]:
                        status = _('Low')
                        status_color = colors.orange
                    
                    readings_data.append([date_str, f"{value:.1f} {vital_unit}", status])
                
                readings_table = Table(readings_data, colWidths=[2*inch, 1.5*inch, 1*inch])
                
                # Create table style with colors
                table_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]
                
                readings_table.setStyle(TableStyle(table_style))
                
                content.append(readings_table)
                content.append(Spacer(1, 24))
            
            # Recommendations
            content.append(Paragraph(_('Recommendations'), styles['Heading2']))
            content.append(Spacer(1, 6))
            content.append(Paragraph(_('Consult your doctor to discuss these results. This report is generated automatically and should be interpreted by a qualified medical professional.'), styles['Normal']))
    except Exception as e:
        logger.error(f"Error generating vital trend report: {str(e)}")
        content.append(Paragraph(f"{_('Error generating report')}: {str(e)}", styles['Normal']))
    
    # Build PDF
    doc.build(content)
    buffer.seek(0)
    return buffer
