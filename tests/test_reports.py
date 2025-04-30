"""
Test module for VitaLink reports functionality.
"""
import io
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.models import Patient, Doctor, Note, VitalObservation, VitalSignType
from app.reports import generate_specific_report, create_vital_chart, PERIOD_DAYS


class TestReports:
    """Test cases for report generation functionality."""
    
    def test_create_vital_chart(self):
        """Test creating a vital sign chart."""
        # Create sample vital data
        vitals_data = [
            {
                'timestamp': (datetime.utcnow() - timedelta(days=6)).isoformat(),
                'value': '70'
            },
            {
                'timestamp': (datetime.utcnow() - timedelta(days=5)).isoformat(),
                'value': '72'
            },
            {
                'timestamp': (datetime.utcnow() - timedelta(days=4)).isoformat(),
                'value': '75'
            },
            {
                'timestamp': (datetime.utcnow() - timedelta(days=3)).isoformat(),
                'value': '71'
            },
            {
                'timestamp': (datetime.utcnow() - timedelta(days=2)).isoformat(),
                'value': '73'
            },
            {
                'timestamp': (datetime.utcnow() - timedelta(days=1)).isoformat(),
                'value': '74'
            },
            {
                'timestamp': datetime.utcnow().isoformat(),
                'value': '72'
            }
        ]
        
        # Create a chart
        chart = create_vital_chart(vitals_data, '7 Days', 'heart_rate')
        
        # Check that the chart was created successfully
        assert chart is not None
        assert hasattr(chart, 'width')
        assert hasattr(chart, 'height')
        assert len(chart.contents) > 0  # Chart should have at least one item
    
    @patch('app.reports.get_vitals_data')
    def test_generate_specific_report(self, mock_get_vitals_data, session):
        """Test generating a specific report."""
        # Create necessary objects for testing
        doctor = Doctor(
            email="test_doctor@example.com",
            first_name="Test",
            last_name="Doctor",
            specialty="Cardiology"
        )
        doctor.set_password("password")
        
        patient = Patient(
            first_name="Test",
            last_name="Patient",
            date_of_birth=datetime(1990, 1, 1),
            gender="Male",
            contact_number="123-456-7890"
        )
        
        # Add the doctor and patient to the database
        session.add(doctor)
        session.add(patient)
        session.commit()
        
        # Create a note
        note = Note(
            patient_id=patient.id,
            doctor_id=doctor.id,
            content="Test note content"
        )
        session.add(note)
        session.commit()
        
        # Create a vital observation
        vital_observation = VitalObservation(
            patient_id=patient.id,
            doctor_id=doctor.id,
            vital_type=VitalSignType.HEART_RATE,
            content="Test heart rate observation",
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow()
        )
        session.add(vital_observation)
        session.commit()
        
        # Mock the get_vitals_data function to return test data
        mock_get_vitals_data.return_value = [
            {
                'timestamp': (datetime.utcnow() - timedelta(days=6)).isoformat(),
                'value': '70'
            },
            {
                'timestamp': (datetime.utcnow() - timedelta(days=3)).isoformat(),
                'value': '72'
            },
            {
                'timestamp': datetime.utcnow().isoformat(),
                'value': '75'
            }
        ]
        
        # Ensure the doctor instance is attached to the session
        session.refresh(doctor)
        
        # Generate a report
        with session.begin_nested():
            # This ensures the doctor remains attached to the session
            report_buffer = generate_specific_report(
                patient=patient,
                doctor=doctor,
                selected_notes=[note],
                selected_vital_types=[VitalSignType.HEART_RATE],
                selected_charts={'heart_rate': ['7d']},
                selected_observations=[vital_observation],
                summary="Test summary"
            )
        
        # Check that the report was generated successfully
        assert isinstance(report_buffer, io.BytesIO)
        assert report_buffer.getvalue()
        assert len(report_buffer.getvalue()) > 0  # Report should not be empty
    
    @patch('app.reports.get_vitals_data')
    def test_reports_page(self, mock_get_vitals_data, logged_in_client, doctor_with_patient, patient):
        """Test the reports page."""
        # Mock the get_vitals_data function
        mock_get_vitals_data.return_value = []
        
        # Access the reports page
        response = logged_in_client.get(f"/patient/{patient.id}/reports")
        
        # Check if the page loaded successfully
        assert response.status_code == 200
        assert b"Reports" in response.data
        assert bytes(patient.first_name, 'utf-8') in response.data
        assert bytes(patient.last_name, 'utf-8') in response.data
    
    @patch('app.reports.get_vitals_data')
    def test_generate_report_with_explicit_session(self, mock_get_vitals_data, session):
        """Test generating a report with an explicitly managed session."""
        # Create necessary objects for testing
        doctor = Doctor(
            email="doctor_reports@example.com",
            first_name="Reports",
            last_name="Doctor",
            specialty="Neurology"
        )
        doctor.set_password("password")
        
        patient = Patient(
            first_name="Reports",
            last_name="Patient",
            date_of_birth=datetime(1985, 5, 15),
            gender="Female",
            contact_number="555-123-4567"
        )
        
        # Add the doctor and patient to the database
        session.add(doctor)
        session.add(patient)
        session.flush()  # Flush to get IDs but stay in transaction
        
        # Create a note and vital observation
        note = Note(
            patient_id=patient.id,
            doctor_id=doctor.id,
            content="Patient shows normal vital signs."
        )
        
        vital_observation = VitalObservation(
            patient_id=patient.id,
            doctor_id=doctor.id,
            vital_type=VitalSignType.HEART_RATE,
            content="Heart rate is within normal range.",
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow()
        )
        
        session.add(note)
        session.add(vital_observation)
        session.commit()
        
        # Mock vital data
        mock_get_vitals_data.return_value = [
            {'timestamp': (datetime.utcnow() - timedelta(days=7)).isoformat(), 'value': '65'},
            {'timestamp': datetime.utcnow().isoformat(), 'value': '70'}
        ]
        
        # Ensure the doctor is fully loaded with all relationships before generating report
        session.refresh(doctor)
        
        # Generate report within an explicit transaction to prevent DetachedInstanceError
        with session.begin_nested():
            # Keep the doctor attached to the session throughout the report generation
            report_buffer = generate_specific_report(
                patient=patient,
                doctor=doctor,
                selected_notes=[note],
                selected_vital_types=[VitalSignType.HEART_RATE],
                selected_charts={'heart_rate': ['7d']},
                selected_observations=[vital_observation]
            )
        
        # Verify report was created successfully
        assert report_buffer is not None
        assert isinstance(report_buffer, io.BytesIO)
        assert len(report_buffer.getvalue()) > 0
        
    def test_period_days_constants(self):
        """Test the PERIOD_DAYS constants."""
        # Check that all period constants are defined correctly
        assert PERIOD_DAYS['1d'] == 1
        assert PERIOD_DAYS['7d'] == 7
        assert PERIOD_DAYS['1m'] == 30
        assert PERIOD_DAYS['3m'] == 90
        assert PERIOD_DAYS['1y'] == 365
