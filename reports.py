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
from utils import get_vital_reference_range, get_vital_sign_unit

# Setup logger
logger = logging.getLogger(__name__)

def get_report_translations():
    """
    Get translations for report text based on the selected language.
    
    Returns:
        dict: Dictionary of translated strings
    """
    language = session.get('language', 'en')
    
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
    
    # Get translations
    t = get_report_translations()
    
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
    
    # Vital Signs
    content.append(Paragraph(t['vital_signs'], styles['Heading2']))
    content.append(Spacer(1, 6))
    
    if vitals:
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
                range_text = t['normal_range'].format(reference['min'], reference['max'], unit)
                content.append(Paragraph(range_text, styles['Normal']))
                content.append(Spacer(1, 6))
            
            # Table header
            vitals_data = [[t['datetime'], t['value'], t['status']]]
            
            # Add data rows
            for vital in sorted(type_vitals, key=lambda v: v.recorded_at, reverse=True):
                # Determine status
                status = t['normal']
                status_color = colors.black
                
                if vital_type == 'blood_pressure':
                    # Special case for blood pressure
                    value_display = vital.value
                else:
                    value_display = f"{vital.value} {unit}"
                    # Check if value is outside normal range
                    if reference['min'] is not None and reference['max'] is not None:
                        if vital.value < reference['min']:
                            status = t['low']
                            status_color = colors.blue
                        elif vital.value > reference['max']:
                            status = t['high']
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
                if vitals_data[i][2] == t['high']:
                    vitals_table.setStyle(TableStyle([
                        ('TEXTCOLOR', (2, i), (2, i), colors.red),
                        ('FONTNAME', (2, i), (2, i), 'Helvetica-Bold')
                    ]))
                elif vitals_data[i][2] == t['low']:
                    vitals_table.setStyle(TableStyle([
                        ('TEXTCOLOR', (2, i), (2, i), colors.blue),
                        ('FONTNAME', (2, i), (2, i), 'Helvetica-Bold')
                    ]))
            
            content.append(vitals_table)
            content.append(Spacer(1, 18))
    else:
        content.append(Paragraph(t['no_vitals'], styles['Normal']))
        content.append(Spacer(1, 12))
    
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
    
    # Get translations
    t = get_report_translations()
    
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
    content.append(Paragraph(f"{reference['name']} {t['trend_analysis']}", styles['Heading1Center']))
    content.append(Spacer(1, 12))
    
    # Patient info
    content.append(Paragraph(f"{t['patient']}: {patient.first_name} {patient.last_name}", styles['Heading3']))
    content.append(Paragraph(f"{t['period']}: {period_desc}", styles['Normal']))
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
        
        # Assicuriamoci che i valori min e max siano float
        chart.valueAxis.valueMin = float(chart.valueAxis.valueMin)
        chart.valueAxis.valueMax = float(chart.valueAxis.valueMax)
        
        # Add reference lines if available
        if reference['min'] is not None:
            chart.valueAxis.valueMin = min(chart.valueAxis.valueMin, reference['min'] * 0.9)
            # Inizializza valueSteps se non esiste
            if not hasattr(chart.valueAxis, 'valueSteps'):
                chart.valueAxis.valueSteps = []
            chart.valueAxis.valueSteps.append(reference['min'])
        
        if reference['max'] is not None:
            chart.valueAxis.valueMax = max(chart.valueAxis.valueMax, reference['max'] * 1.1)
            # Inizializza valueSteps se non esiste
            if not hasattr(chart.valueAxis, 'valueSteps'):
                chart.valueAxis.valueSteps = []
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
        content.append(Paragraph(t['statistics'], styles['Heading3']))
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
            [t['average'], f"{avg_value:.1f} {unit}"],
            [t['minimum'], f"{min_value} {unit}"],
            [t['maximum'], f"{max_value} {unit}"],
            [t['normal_readings'], f"{normal_count} ({normal_count/len(values)*100:.1f}%)"],
            [t['high_readings'], f"{high_count} ({high_count/len(values)*100:.1f}%)"],
            [t['low_readings'], f"{low_count} ({low_count/len(values)*100:.1f}%)"]
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
        readings_data = [[t['datetime'], t['value'], t['status']]]
        
        # Add data rows
        for vital in sorted_vitals:
            # Determine status
            status = t['normal']
            
            if reference['min'] is not None and reference['max'] is not None:
                if vital.value < reference['min']:
                    status = t['low']
                elif vital.value > reference['max']:
                    status = t['high']
            
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
            if readings_data[i][2] == t['high']:
                readings_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (2, i), (2, i), colors.red),
                    ('FONTNAME', (2, i), (2, i), 'Helvetica-Bold')
                ]))
            elif readings_data[i][2] == t['low']:
                readings_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (2, i), (2, i), colors.blue),
                    ('FONTNAME', (2, i), (2, i), 'Helvetica-Bold')
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