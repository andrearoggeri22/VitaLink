import os
import logging
from datetime import datetime
from io import BytesIO
import tempfile
from flask import session

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.legends import Legend

from models import VitalSignType

# Setup logger
logger = logging.getLogger(__name__)

def get_report_translations(lang=None):
    """
    Get translations for report text based on the selected language.
    
    Args:
        lang: Optional language code override. If not provided, uses session language.
    
    Returns:
        dict: Dictionary of translated strings
    """
    language = lang or session.get('language', 'en')
    logger.debug(f"Report language: {language}")
    
    if language == 'it':
        return {
            # Common terms
            'report_title': 'Rapporto di Monitoraggio Sanitario',
            'generated_on': 'Generato il',
            'patient_info': 'Informazioni sul Paziente',
            'attending_physician': 'Medico Curante',
            'vital_signs': 'Parametri Vitali',
            'clinical_notes': 'Note Cliniche',
            'no_vitals': 'Nessun parametro vitale registrato per questo periodo.',
            'no_notes': 'Nessuna nota clinica registrata per questo paziente.',
            
            # Patient/Doctor info
            'name': 'Nome',
            'date_of_birth': 'Data di Nascita',
            'gender': 'Genere',
            'contact': 'Contatto',
            'specialty': 'Specialità',
            'email': 'Email',
            'not_specified': 'Non specificato',
            'not_provided': 'Non fornito',
            'general_practice': 'Medicina Generale',
            
            # Vital signs
            'period_from_to': 'Periodo: Dal {} al {}',
            'period_from': 'Periodo: Dal {}',
            'period_until': 'Periodo: Fino al {}',
            'normal_range': 'Intervallo Normale: {} - {} {}',
            'datetime': 'Data e Ora',
            'value': 'Valore',
            'status': 'Stato',
            'normal': 'Normale',
            'high': 'Alto',
            'low': 'Basso',
            
            # Trend analysis
            'trend_analysis': 'Analisi dei Trend',
            'patient': 'Paziente',
            'period': 'Periodo',
            'statistics': 'Statistiche',
            'detailed_readings': 'Letture Dettagliate',
            'average': 'Media',
            'minimum': 'Minimo',
            'maximum': 'Massimo',
            'normal_readings': 'Letture Normali',
            'high_readings': 'Letture Alte',
            'low_readings': 'Letture Basse',
            'no_vital_data': 'Nessun dato vitale disponibile per questo periodo.',
            'recommendations': 'Raccomandazioni',
            'consult_doctor': 'Si prega di consultare il medico per discutere questi risultati. Questo rapporto è generato automaticamente e deve essere interpretato da un professionista medico qualificato.'
        }
    else:
        return {
            # Common terms
            'report_title': 'Healthcare Monitoring Report',
            'generated_on': 'Generated on',
            'patient_info': 'Patient Information',
            'attending_physician': 'Attending Physician',
            'vital_signs': 'Vital Signs',
            'clinical_notes': 'Clinical Notes',
            'no_vitals': 'No vital signs recorded for this period.',
            'no_notes': 'No clinical notes recorded for this patient.',
            
            # Patient/Doctor info
            'name': 'Name',
            'date_of_birth': 'Date of Birth',
            'gender': 'Gender',
            'contact': 'Contact',
            'specialty': 'Specialty',
            'email': 'Email',
            'not_specified': 'Not specified',
            'not_provided': 'Not provided',
            'general_practice': 'General Practice',
            
            # Vital signs
            'period_from_to': 'Period: From {} to {}',
            'period_from': 'Period: From {}',
            'period_until': 'Period: Until {}',
            'normal_range': 'Normal Range: {} - {} {}',
            'datetime': 'Date & Time',
            'value': 'Value',
            'status': 'Status',
            'normal': 'Normal',
            'high': 'High',
            'low': 'Low',
            
            # Trend analysis
            'trend_analysis': 'Trend Analysis',
            'patient': 'Patient',
            'period': 'Period',
            'statistics': 'Statistics',
            'detailed_readings': 'Detailed Readings',
            'average': 'Average',
            'minimum': 'Minimum',
            'maximum': 'Maximum',
            'normal_readings': 'Normal Readings',
            'high_readings': 'High Readings',
            'low_readings': 'Low Readings',
            'no_vital_data': 'No vital data available for this period.',
            'recommendations': 'Recommendations',
            'consult_doctor': 'Please consult with your healthcare provider to discuss these results. This report is generated automatically and should be interpreted by a qualified medical professional.'
        }

def generate_patient_report(patient, doctor, notes, has_health_connection=False, start_date=None, end_date=None, language=None):
    """
    Generate a PDF report for a patient's health data and notes
    
    Args:
        patient: Patient object
        doctor: Doctor object
        notes: List of Note objects
        has_health_connection: Whether the patient has a health platform connection
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        language: Optional language code override (it/en)
        
    Returns:
        BytesIO: PDF file as a binary stream
    """
    buffer = BytesIO()
    
    # Get translations
    t = get_report_translations(language)
    
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
    content.append(Paragraph(t['report_title'], styles['Heading1Center']))
    content.append(Spacer(1, 12))
    
    # Date of report
    content.append(Paragraph(f"{t['generated_on']}: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal-Center']))
    content.append(Spacer(1, 24))
    
    # Patient Information
    content.append(Paragraph(t['patient_info'], styles['Heading2']))
    content.append(Spacer(1, 6))
    
    patient_data = [
        [f"{t['name']}:", f"{patient.first_name} {patient.last_name}"],
        [f"{t['date_of_birth']}:", patient.date_of_birth.strftime('%Y-%m-%d')],
        [f"{t['gender']}:", patient.gender or t['not_specified']],
        [f"{t['contact']}:", patient.contact_number or t['not_provided']]
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
    content.append(Paragraph(t['attending_physician'], styles['Heading2']))
    content.append(Spacer(1, 6))
    
    doctor_data = [
        [f"{t['name']}:", f"Dr. {doctor.first_name} {doctor.last_name}"],
        [f"{t['specialty']}:", doctor.specialty or t['general_practice']],
        [f"{t['email']}:", doctor.email]
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
    
    # Health Data Section
    content.append(Paragraph(t['vital_signs'], styles['Heading2']))
    content.append(Spacer(1, 6))
    
    # Filter period explanation
    if start_date and end_date:
        period_text = t['period_from_to'].format(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        content.append(Paragraph(period_text, styles['Normal']))
    elif start_date:
        period_text = t['period_from'].format(start_date.strftime('%Y-%m-%d'))
        content.append(Paragraph(period_text, styles['Normal']))
    elif end_date:
        period_text = t['period_until'].format(end_date.strftime('%Y-%m-%d'))
        content.append(Paragraph(period_text, styles['Normal']))
        
    content.append(Spacer(1, 12))
    
    if has_health_connection:
        content.append(Paragraph("Health Platform Connection: Active", styles['Normal']))
        content.append(Paragraph("Data can be viewed through the VitaLink platform's web interface.", styles['Normal']))
        content.append(Spacer(1, 6))
        content.append(Paragraph("The patient is connected to an external health platform that provides real-time vital sign data. This report does not include the real-time data to ensure accuracy. Please consult the VitaLink web interface for the most up-to-date health information.", styles['Normal']))
    else:
        content.append(Paragraph("Health Platform Connection: Not Active", styles['Normal']))
        content.append(Paragraph("The patient is not currently connected to any health platform for automatic vital sign monitoring.", styles['Normal']))
    
    content.append(Spacer(1, 18))
    
    # Notes
    content.append(Paragraph(t['clinical_notes'], styles['Heading2']))
    content.append(Spacer(1, 6))
    
    if notes:
        for i, note in enumerate(notes):
            doctor_name = f"Dr. {note.doctor.first_name} {note.doctor.last_name}"
            note_header = f"{note.created_at.strftime('%Y-%m-%d %H:%M')} - {doctor_name}"
            content.append(Paragraph(note_header, styles['Heading4']))
            content.append(Paragraph(note.content, styles['Normal']))
            content.append(Spacer(1, 12))
    else:
        content.append(Paragraph(t['no_notes'], styles['Normal']))
    
    # Build the PDF
    doc.build(content)
    buffer.seek(0)
    
    return buffer


def generate_vital_trends_report(patient, vital_type, vitals, period_desc, language=None):
    """
    Generate a PDF report showing trends for a specific vital sign
    
    Args:
        patient: Patient object
        vital_type: Type of vital sign (string)
        vitals: List of data points from health platform
        period_desc: Description of the time period
        language: Optional language code override (it/en)
        
    Returns:
        BytesIO: PDF file as a binary stream
    """
    buffer = BytesIO()
    
    # Get translations
    t = get_report_translations(language)
    
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
    
    # Mappatura dei nomi di parametri vitali
    vital_names = {
        'heart_rate': 'Heart Rate',
        'steps': 'Steps',
        'weight': 'Weight',
        'sleep': 'Sleep',
        'activity': 'Activity',
        'distance': 'Distance'
    }
    
    # Mappatura delle unità di misura
    vital_units = {
        'heart_rate': 'bpm',
        'steps': 'steps',
        'weight': 'kg',
        'sleep': 'minutes',
        'activity': 'minutes',
        'distance': 'km'
    }
    
    # Get the vital name and unit
    vital_name = vital_names.get(vital_type, vital_type.replace('_', ' ').title())
    unit = vital_units.get(vital_type, '')
    
    # Build content
    content = []
    
    # Report Header
    content.append(Paragraph(f"{vital_name} {t['trend_analysis']}", styles['Heading1Center']))
    content.append(Spacer(1, 12))
    
    # Patient info
    content.append(Paragraph(f"{t['patient']}: {patient.first_name} {patient.last_name}", styles['Heading3']))
    content.append(Paragraph(f"{t['period']}: {period_desc}", styles['Normal']))
    content.append(Spacer(1, 24))
    
    if vitals:
        # Assume vitals è un elenco di dizionari con 'timestamp' e 'value'
        # Sort per data/ora
        sorted_vitals = sorted(vitals, key=lambda v: v['timestamp'])
        
        # Create a line chart for the vitals trend
        drawing = Drawing(400, 200)
        
        chart = HorizontalLineChart()
        chart.width = 350
        chart.height = 150
        chart.x = 25
        chart.y = 25
        
        # Prepare data
        # Estrai data in formato breve dal timestamp ISO
        dates = []
        for v in sorted_vitals:
            dt = datetime.fromisoformat(v['timestamp'].replace('Z', '+00:00'))
            dates.append(dt.strftime('%m/%d'))
        
        values = [float(v['value']) for v in sorted_vitals]
        
        chart.data = [values]
        chart.categoryAxis.categoryNames = dates
        chart.valueAxis.valueMin = min(values) * 0.9 if values else 0
        chart.valueAxis.valueMax = max(values) * 1.1 if values else 100
        
        # Assicuriamoci che i valori min e max siano float
        chart.valueAxis.valueMin = float(chart.valueAxis.valueMin)
        chart.valueAxis.valueMax = float(chart.valueAxis.valueMax)
        
        # Style the chart
        chart.lines[0].strokeWidth = 2
        chart.lines[0].strokeColor = colors.blue
        
        # Add the chart to the drawing
        drawing.add(chart)
        
        # Add drawing to content
        content.append(drawing)
        content.append(Spacer(1, 12))
        
        # Add a statistics table
        content.append(Paragraph(t['statistics'], styles['Heading3']))
        content.append(Spacer(1, 6))
        
        # Calculate statistics
        avg_value = sum(values) / len(values)
        min_value = min(values)
        max_value = max(values)
        
        # Create statistics table
        stats_data = [
            [t['average'], f"{avg_value:.1f} {unit}"],
            [t['minimum'], f"{min_value} {unit}"],
            [t['maximum'], f"{max_value} {unit}"]
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
        content.append(Paragraph(t['detailed_readings'], styles['Heading3']))
        content.append(Spacer(1, 6))
        
        # Table header
        readings_data = [[t['datetime'], t['value']]]
        
        # Add data rows
        for vital in sorted_vitals:
            # Parse datetime from ISO format
            dt = datetime.fromisoformat(vital['timestamp'].replace('Z', '+00:00'))
            
            readings_data.append([
                dt.strftime('%Y-%m-%d %H:%M'),
                f"{vital['value']} {unit}"
            ])
        
        # Create table
        readings_table = Table(readings_data, colWidths=[2.5*inch, 3*inch])
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
        
        content.append(readings_table)
    else:
        content.append(Paragraph(t['no_vital_data'], styles['Normal']))
    
    # Recommendations section - Now using prepared translations
    content.append(Spacer(1, 24))
    content.append(Paragraph(t['recommendations'], styles['Heading3']))
    content.append(Spacer(1, 6))
    content.append(Paragraph(t['consult_doctor'], styles['Normal']))
    
    # Build the PDF
    doc.build(content)
    buffer.seek(0)
    
    return buffer