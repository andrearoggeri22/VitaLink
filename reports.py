import os
import logging
from datetime import datetime, timedelta
from io import BytesIO
import tempfile
import json
from flask import session

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
            'observations': 'Osservazioni',
            'no_observations': 'Nessuna osservazione registrata per questo parametro.',
            'summary': 'Resoconto',
            'complete_report': 'Rapporto Completo',
            'specific_report': 'Rapporto Specifico',
            
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
            'consult_doctor': 'Si prega di consultare il medico per discutere questi risultati. Questo rapporto è generato automaticamente e deve essere interpretato da un professionista medico qualificato.',
            
            # Time periods
            'one_day': '1 Giorno',
            'seven_days': '7 Giorni',
            'one_month': '1 Mese',
            'three_months': '3 Mesi',
            'one_year': '1 Anno'
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
            'observations': 'Observations',
            'no_observations': 'No observations recorded for this parameter.',
            'summary': 'Summary',
            'complete_report': 'Complete Report',
            'specific_report': 'Specific Report',
            
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
            'consult_doctor': 'Please consult with your healthcare provider to discuss these results. This report is generated automatically and should be interpreted by a qualified medical professional.',
            
            # Time periods
            'one_day': '1 Day',
            'seven_days': '7 Days',
            'one_month': '1 Month',
            'three_months': '3 Months',
            'one_year': '1 Year'
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


def generate_complete_report(patient, doctor, notes, observations, summary=None, language=None):
    """
    Generate a complete PDF report with all patient data, vital signs, and observations
    
    Args:
        patient: Patient object
        doctor: Doctor object
        notes: List of Note objects
        observations: List of VitalObservation objects
        summary: Optional summary text provided by the doctor (not saved to database)
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
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
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
    content.append(Paragraph(t['complete_report'], styles['Heading1Center']))
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
    
    # Optional Summary if provided
    if summary:
        content.append(Paragraph(t['summary'], styles['Heading2']))
        content.append(Spacer(1, 6))
        content.append(Paragraph(summary, styles['Normal']))
        content.append(Spacer(1, 18))
    
    # Notes Section
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
    
    content.append(PageBreak())
    
    # Vital Signs Section with Charts and Observations
    content.append(Paragraph(t['vital_signs'], styles['Heading2']))
    content.append(Spacer(1, 12))
    
    # Health Platform Connection Status
    if patient.connected_platform:
        content.append(Paragraph(f"Health Platform Connection: {patient.connected_platform.value} (Active)", styles['Normal-Bold']))
        content.append(Spacer(1, 12))
    
    # Time periods for charts
    time_periods = [
        {'name': t['one_day'], 'days': 1},
        {'name': t['seven_days'], 'days': 7},
        {'name': t['one_month'], 'days': 30},
        {'name': t['three_months'], 'days': 90},
        {'name': t['one_year'], 'days': 365}
    ]
    
    # Vital sign types to include with their display names
    vital_types = {
        VitalSignType.HEART_RATE: "Heart Rate",
        VitalSignType.STEPS: "Steps",
        VitalSignType.WEIGHT: "Weight",
        VitalSignType.OXYGEN_SATURATION: "Oxygen Saturation",
        VitalSignType.TEMPERATURE: "Temperature",
        VitalSignType.RESPIRATORY_RATE: "Respiratory Rate",
        VitalSignType.GLUCOSE: "Glucose",
        VitalSignType.ACTIVE_MINUTES: "Active Minutes",
        VitalSignType.CALORIES: "Calories",
        VitalSignType.DISTANCE: "Distance",
        VitalSignType.SLEEP_DURATION: "Sleep Duration",
        VitalSignType.FLOORS_CLIMBED: "Floors Climbed"
    }
    
    # For each vital type, create charts for all time periods and include observations
    for vital_enum, vital_name in vital_types.items():
        vital_type = vital_enum.value
        
        # Section for this vital type
        content.append(Paragraph(f"{vital_name}", styles['Heading3']))
        content.append(Spacer(1, 6))
        
        vital_observations = [obs for obs in observations if obs.vital_type == vital_enum]
        
        # Add charts for each time period
        for period in time_periods:
            days = period['days']
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Fetch data from health platform
            if patient.connected_platform:
                try:
                    vitals_data = health_platforms.get_vitals_data(
                        patient, 
                        vital_type,
                        start_date.strftime('%Y-%m-%d'),
                        end_date.strftime('%Y-%m-%d')
                    )
                    
                    if vitals_data and len(vitals_data) > 0:
                        # Add period header
                        content.append(Paragraph(f"{period['name']}", styles['Heading4']))
                        
                        # Generate and add chart
                        chart = create_vital_chart(vitals_data, period['name'], vital_type)
                        content.append(chart)
                        content.append(Spacer(1, 12))
                except Exception as e:
                    logger.error(f"Error generating chart for {vital_type}, period {days} days: {str(e)}")
                    content.append(Paragraph(f"{t['no_vital_data']} ({period['name']})", styles['Normal']))
                    content.append(Spacer(1, 6))
            else:
                content.append(Paragraph(f"{t['no_vital_data']}", styles['Normal']))
                content.append(Spacer(1, 6))
        
        # Add observations for this vital type
        content.append(Paragraph(f"{t['observations']} - {vital_name}", styles['Heading4']))
        content.append(Spacer(1, 6))
        
        if vital_observations:
            for obs in vital_observations:
                # Format the observation header with date range
                obs_period = f"{obs.start_date.strftime('%Y-%m-%d')} - {obs.end_date.strftime('%Y-%m-%d')}"
                doctor_name = f"Dr. {obs.doctor.first_name} {obs.doctor.last_name}"
                obs_header = f"{obs_period} ({doctor_name})"
                
                content.append(Paragraph(obs_header, styles['Normal-Bold']))
                content.append(Paragraph(obs.content, styles['Normal']))
                content.append(Spacer(1, 8))
        else:
            content.append(Paragraph(f"{t['no_observations']}", styles['Normal']))
        
        content.append(Spacer(1, 18))
        
        # Add page break after each vital type except the last one
        content.append(PageBreak())
    
    # Add recommendations
    content.append(Paragraph(t['recommendations'], styles['Heading3']))
    content.append(Spacer(1, 6))
    content.append(Paragraph(t['consult_doctor'], styles['Normal']))
    
    # Build the PDF
    doc.build(content)
    buffer.seek(0)
    
    return buffer

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
    
    # Get translations
    t = get_report_translations(language)
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
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
    content.append(Paragraph(t['specific_report'], styles['Heading1Center']))
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
    
    # Optional Summary if provided
    if summary:
        content.append(Paragraph(t['summary'], styles['Heading2']))
        content.append(Spacer(1, 6))
        content.append(Paragraph(summary, styles['Normal']))
        content.append(Spacer(1, 18))
    
    # Selected Notes
    if selected_notes:
        content.append(Paragraph(t['clinical_notes'], styles['Heading2']))
        content.append(Spacer(1, 6))
        
        for note in selected_notes:
            doctor_name = f"Dr. {note.doctor.first_name} {note.doctor.last_name}"
            note_header = f"{note.created_at.strftime('%Y-%m-%d %H:%M')} - {doctor_name}"
            content.append(Paragraph(note_header, styles['Heading4']))
            content.append(Paragraph(note.content, styles['Normal']))
            content.append(Spacer(1, 12))
        
        content.append(PageBreak())
    
    # Selected Vital Signs with Charts and Observations
    if selected_vital_types:
        content.append(Paragraph(t['vital_signs'], styles['Heading2']))
        content.append(Spacer(1, 12))
        
        # Health Platform Connection Status
        if patient.connected_platform:
            content.append(Paragraph(f"Health Platform Connection: {patient.connected_platform.value} (Active)", styles['Normal-Bold']))
            content.append(Spacer(1, 12))
        
        # Time periods for charts
        time_periods = {
            1: t['one_day'],
            7: t['seven_days'],
            30: t['one_month'],
            90: t['three_months'],
            365: t['one_year']
        }
        
        # For each selected vital type
        for vital_enum in selected_vital_types:
            vital_type = vital_enum.value
            vital_name = vital_enum.value.replace('_', ' ').title()
            
            # Section for this vital type
            content.append(Paragraph(f"{vital_name}", styles['Heading3']))
            content.append(Spacer(1, 6))
            
            # Get selected charts for this vital type
            selected_periods = selected_charts.get(vital_type, [])
            
            # Add charts for selected time periods
            for days in selected_periods:
                period_name = time_periods[days]
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                # Fetch data from health platform
                if patient.connected_platform:
                    try:
                        vitals_data = health_platforms.get_vitals_data(
                            patient, 
                            vital_type,
                            start_date.strftime('%Y-%m-%d'),
                            end_date.strftime('%Y-%m-%d')
                        )
                        
                        if vitals_data and len(vitals_data) > 0:
                            # Add period header
                            content.append(Paragraph(f"{period_name}", styles['Heading4']))
                            
                            # Generate and add chart
                            chart = create_vital_chart(vitals_data, period_name, vital_type)
                            content.append(chart)
                            content.append(Spacer(1, 12))
                    except Exception as e:
                        logger.error(f"Error generating chart for {vital_type}, period {days} days: {str(e)}")
                        content.append(Paragraph(f"{t['no_vital_data']} ({period_name})", styles['Normal']))
                        content.append(Spacer(1, 6))
                else:
                    content.append(Paragraph(f"{t['no_vital_data']}", styles['Normal']))
                    content.append(Spacer(1, 6))
            
            # Add selected observations for this vital type
            vital_observations = [obs for obs in selected_observations if obs.vital_type == vital_enum]
            
            if vital_observations:
                content.append(Paragraph(f"{t['observations']} - {vital_name}", styles['Heading4']))
                content.append(Spacer(1, 6))
                
                for obs in vital_observations:
                    # Format the observation header with date range
                    obs_period = f"{obs.start_date.strftime('%Y-%m-%d')} - {obs.end_date.strftime('%Y-%m-%d')}"
                    doctor_name = f"Dr. {obs.doctor.first_name} {obs.doctor.last_name}"
                    obs_header = f"{obs_period} ({doctor_name})"
                    
                    content.append(Paragraph(obs_header, styles['Normal-Bold']))
                    content.append(Paragraph(obs.content, styles['Normal']))
                    content.append(Spacer(1, 8))
            
            content.append(Spacer(1, 18))
            
            # Add page break after each vital type except the last one
            if vital_enum != selected_vital_types[-1]:
                content.append(PageBreak())
    
    # Add recommendations
    content.append(Paragraph(t['recommendations'], styles['Heading3']))
    content.append(Spacer(1, 6))
    content.append(Paragraph(t['consult_doctor'], styles['Normal']))
    
    # Build the PDF
    doc.build(content)
    buffer.seek(0)
    
    return buffer

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