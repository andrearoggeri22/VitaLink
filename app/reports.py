import logging
from datetime import datetime, timedelta
from io import BytesIO
from flask_babel import gettext as _

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.legends import Legend


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
                dates.append(dt.strftime('%d/%m'))
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
    drawing = Drawing(500, 220)
      # Define chart colors based on vital type
    chart_colors = {
    'heart_rate': colors.red,
    'oxygen_saturation': colors.blue,
    'breathing_rate': colors.cyan,
    'weight': colors.green,
    'temperature_core': colors.orange,
    'temperature_skin': colors.orange,
    'steps': colors.teal,
    'calories': colors.orange,  # <-- ADDED
    'sleep_duration': colors.navy,
    'distance': colors.green,
    'active_minutes': colors.purple,
    'floors_climbed': colors.saddlebrown,
    'elevation': colors.brown,
    'activity_calories': colors.orange,
    'calories_bmr': colors.orange,
    'minutes_sedentary': colors.gray,
    'minutes_lightly_active': colors.lightgreen,
    'minutes_fairly_active': colors.yellow,
    'calories_in': colors.red,
    'water': colors.blue
}

    
    chart_color = chart_colors.get(vital_type, colors.blueviolet)
    
    chart = HorizontalLineChart()
    chart.width = 450
    chart.height = 170
    chart.x = 25
    chart.y = 20
    
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
        chart.lines[0].strokeWidth = 2.5
        chart.lines[0].strokeColor = chart_color
        
        # Enhance chart appearance
        chart.categoryAxis.labels.angle = 30
        chart.categoryAxis.labels.boxAnchor = 'ne'
        chart.categoryAxis.labels.fontName = 'Helvetica'
        chart.categoryAxis.labels.fontSize = 7
        chart.valueAxis.labels.fontName = 'Helvetica'
        chart.valueAxis.labels.fontSize = 8
        
        # Configurazione griglia
        chart.categoryAxis.strokeWidth = 0.5
        chart.valueAxis.strokeWidth = 0.5
        chart.valueAxis.gridStrokeWidth = 0.25
        chart.valueAxis.gridStrokeColor = colors.lightgrey
        
        # Add title
        vital_name = vital_type.replace('_', ' ').title()
        title = f"{vital_name} - {period_name}"
        
        drawing.add(chart)
        
        # Add legend with title
        legend = Legend()
        legend.alignment = 'right'
        legend.x = 25
        legend.y = 200
        legend.columnMaximum = 1
        legend.fontName = 'Helvetica-Bold'
        legend.fontSize = 9
        legend.dxTextSpace = 5
        legend.dy = 5
        legend.dx = 10
        legend.deltay = 10
        legend.colorNamePairs = [(chart_color, title)]
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
        rightMargin=54,  # 3/4 inch margins for more modern look
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Add custom styles for modern look
    styles.add(ParagraphStyle(
        name='Heading1Center',
        parent=styles['Heading1'],
        alignment=1,  # 0=left, 1=center, 2=right
        fontName='Helvetica-Bold',
        fontSize=16,
        spaceAfter=12,
        textColor=colors.darkblue
    ))
    
    styles.add(ParagraphStyle(
        name='Heading2Modern',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        spaceAfter=6,
        textColor=colors.darkblue
    ))
    
    styles.add(ParagraphStyle(
        name='Heading3Modern',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        spaceAfter=6,
        textColor=colors.navy
    ))
    
    styles.add(ParagraphStyle(
        name='Normal-Center',
        parent=styles['Normal'],
        alignment=1,
        fontSize=10
    ))
    
    styles.add(ParagraphStyle(
        name='Normal-Bold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10
    ))
    
    styles.add(ParagraphStyle(
        name='Normal-Italic',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10
    ))
    
    styles.add(ParagraphStyle(
        name='ObservationTitle',
        parent=styles['Normal-Bold'],
        fontSize=10,
        textColor=colors.darkblue
    ))
    
    styles.add(ParagraphStyle(
        name='ObservationContent',
        parent=styles['Normal'],
        fontSize=10,
        leftIndent=15
    ))
    
    styles.add(ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey
    ))
    
    # Build content
    content = []
    
    # Report Header with modern style
    content.append(Paragraph(_('Specific Report'), styles['Heading1Center']))
    content.append(Spacer(1, 6))
    
    # Date of report
    content.append(Paragraph(f"{_('Generated on')}: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal-Center']))
    content.append(Spacer(1, 24))
    
    # Define a modern table style with rounded corners using background colors
    modern_table_style = [
        ('BACKGROUND', (0, 0), (0, -1), colors.lavender),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.grey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]
    
    # Patient Information with modern styling
    content.append(Paragraph(_('Patient Information'), styles['Heading2Modern']))
    content.append(Spacer(1, 6))
    
    patient_data = [
        [f"{_('Name')}:", f"{patient.first_name} {patient.last_name}"],
        [f"{_('Date of Birth')}:", patient.date_of_birth.strftime('%d/%m/%Y')],
        [f"{_('Gender')}:", patient.gender or _('Not specified')],
        [f"{_('Contact')}:", patient.contact_number or _('Not provided')]
    ]
    
    patient_table = Table(patient_data, colWidths=[1.5*inch, 4*inch])
    patient_table.setStyle(TableStyle(modern_table_style))
    
    content.append(patient_table)
    content.append(Spacer(1, 18))
    
    # Doctor Information
    content.append(Paragraph(_('Attending Physician'), styles['Heading2Modern']))
    content.append(Spacer(1, 6))
    
    doctor_data = [
        [f"{_('Name')}:", f"Dr. {doctor.first_name} {doctor.last_name}"],
        [f"{_('Specialty')}:", doctor.specialty or _('General Practice')],
        [f"{_('Email')}:", doctor.email]
    ]
    
    doctor_table = Table(doctor_data, colWidths=[1.5*inch, 4*inch])
    doctor_table.setStyle(TableStyle(modern_table_style))
    
    content.append(doctor_table)
    content.append(Spacer(1, 36)) # More spacing for clearer separation
    
    # Summary section (if provided)
    if summary:
        content.append(Paragraph(_('Summary'), styles['Heading2Modern']))
        content.append(Spacer(1, 6))
        content.append(Paragraph(summary, styles['Normal']))
        content.append(Spacer(1, 24))
    
    # Selected notes section
    if selected_notes:
        content.append(Paragraph(_('Clinical Notes'), styles['Heading2Modern']))
        content.append(Spacer(1, 8))
        
        for i, note in enumerate(selected_notes):
            date_str = note.created_at.strftime('%d/%m/%Y %H:%M')
            doctor_name = f"Dr. {note.doctor.first_name} {note.doctor.last_name}"
            content.append(Paragraph(f"<b>{date_str} - {doctor_name}</b>", styles['Normal-Bold']))
            content.append(Paragraph(note.content, styles['ObservationContent']))
            content.append(Spacer(1, 8))
            
            # Add a divider between notes except for the last one
            if i < len(selected_notes) - 1:
                content.append(Spacer(1, 3))
                content.append(Paragraph("<hr width='100%' color='#e0e0e0' />", styles['Normal-Center']))
                content.append(Spacer(1, 8))
        
        content.append(Spacer(1, 24))
    
    # Group observations by vital type for later use
    obs_by_type = {}
    if selected_observations:
        for obs in selected_observations:
            vital_type = obs.vital_type.value
            if vital_type not in obs_by_type:
                obs_by_type[vital_type] = []
            obs_by_type[vital_type].append(obs)
    
    # Selected vital signs section with integrated observations
    if selected_vital_types and selected_charts:
        content.append(Paragraph(_('Vital Signs'), styles['Heading2Modern']))
        content.append(Spacer(1, 8))
        
        from .health_platforms import get_vitals_data
        
        # Define colors for each vital type
        vital_colors = {
        'heart_rate': colors.red,
        'steps': colors.teal,
        'calories': colors.orange,
        'distance': colors.green,
        'active_minutes': colors.purple,
        'sleep_duration': colors.navy,
        'floors_climbed': colors.saddlebrown,
        'elevation': colors.brown,
        'weight': colors.green,
        'activity_calories': colors.orange,
        'calories_bmr': colors.orange,
        'minutes_sedentary': colors.gray,
        'minutes_lightly_active': colors.lightgreen,
        'minutes_fairly_active': colors.yellow,
        'calories_in': colors.red,
        'water': colors.blue,
        'breathing_rate': colors.cyan,
        'oxygen_saturation': colors.blue,
        'temperature_core': colors.orange,
        'temperature_skin': colors.orange
        }

        
        for vital_type in selected_vital_types:
            vital_type_value = vital_type.value
            color = vital_colors.get(vital_type_value, colors.darkblue)
            
            # Create a paragraph style with the specific vital color
            styles.add(ParagraphStyle(
                name=f'Heading3-{vital_type_value}',
                parent=styles['Heading3Modern'],
                textColor=color
            ))
            
            content.append(Paragraph(f"{vital_type_value.replace('_', ' ').title()}", styles[f'Heading3-{vital_type_value}']))
            content.append(Spacer(1, 6))
            
            has_data = False
            
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
                        period_name = f"{period_days} {_('days')}"
                    
                    # Calculate date range
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=period_days)
                    
                    # Display date range in an elegant way
                    date_range_text = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
                    content.append(Paragraph(f"<i>{date_range_text}</i>", styles['Normal-Italic']))
                    content.append(Spacer(1, 6))
                    
                    try:
                        # Try to get data from health platform
                        vitals_data = get_vitals_data(
                            patient,
                            vital_type_value,
                            start_date.strftime('%Y-%m-%d'),
                            end_date.strftime('%Y-%m-%d')
                        )
                        
                        if vitals_data and len(vitals_data) > 0:
                            has_data = True
                            # Create chart
                            chart = create_vital_chart(vitals_data, period_name, vital_type_value)
                            content.append(chart)
                            content.append(Spacer(1, 12))
                            
                        else:
                            content.append(Paragraph(f"{period_name}: {_('No vital data available for this period.')}", styles['Normal-Italic']))
                            content.append(Spacer(1, 6))
                            
                    except Exception as e:
                        logger.error(f"Error getting data for {vital_type_value}: {str(e)}")
                        content.append(Paragraph(f"{period_name}: {_('No vital data available for this period.')}", styles['Normal-Italic']))
                        content.append(Spacer(1, 6))
            else:
                content.append(Paragraph(_('No vital data available for this period.'), styles['Normal-Italic']))
            
            # Add observations for this vital type immediately after its charts
            if vital_type_value in obs_by_type and obs_by_type[vital_type_value]:
                if has_data:
                    content.append(Spacer(1, 12))
                
                # Add a subheading for observations
                content.append(Paragraph(_('Observations'), styles['ObservationTitle']))
                content.append(Spacer(1, 6))
                
                obs_list = obs_by_type[vital_type_value]
                for i, obs in enumerate(obs_list):
                    # Format the date range
                    date_range = f"{obs.start_date.strftime('%d/%m/%Y')} - {obs.end_date.strftime('%d/%m/%Y')}"
                    doctor_name = f"Dr. {obs.doctor.first_name} {obs.doctor.last_name}"
                    
                    # Use a box with soft background for each observation
                    obs_table = Table([[Paragraph(f"<b>{date_range}</b> - {doctor_name}", styles['Normal-Bold'])], 
                                       [Paragraph(obs.content, styles['Normal'])]], 
                                      colWidths=[5.5*inch])
                    
                    obs_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lavender),
                        ('BACKGROUND', (0, 1), (-1, 1), colors.white),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('LEFTPADDING', (0, 0), (-1, -1), 12),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey)
                    ]))
                    
                    content.append(obs_table)
                    
                    # Add a divider between observations except for the last one
                    if i < len(obs_list) - 1:
                        content.append(Spacer(1, 8))
                
                content.append(Spacer(1, 12))
            
            # Add spacing between different vital types
            content.append(Spacer(1, 24))
    
    # Footer with page numbers
    def add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        
        # Draw a thin line above the footer
        page_width = doc.pagesize[0]
        canvas.line(54, 40, page_width-54, 40)
        
        # Add page number
        page_num = f"{_('Page')} {doc.page} / {doc.page}"
        canvas.drawRightString(page_width-54, 25, page_num)
        
        # Add timestamp
        timestamp = f"VitaLink - {datetime.now().strftime('%d/%m/%Y')}"
        canvas.drawString(54, 25, timestamp)
        canvas.restoreState()
    
    # Build PDF with page numbers
    doc.build(content, onFirstPage=add_page_number, onLaterPages=add_page_number)
    buffer.seek(0)
    return buffer