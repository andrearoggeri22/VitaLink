"""
Test module for VitaLink audit log functionality.
"""
import pytest
import json
from datetime import datetime, timedelta

from app.models import AuditLog, ActionType, EntityType


class TestAuditLogging:
    """Test cases for audit logging functionality."""
    
    def test_audit_log_creation(self, doctor, patient, session):
        """Test creating audit log entries."""
        # Create an audit log entry
        audit_log = AuditLog(
            doctor_id=doctor.id,
            action_type=ActionType.VIEW,
            entity_type=EntityType.PATIENT,
            entity_id=patient.id,
            details={"source": "test"},
            patient_id=patient.id,
            ip_address="127.0.0.1"
        )
        
        # Add the audit log to the database
        session.add(audit_log)
        session.commit()
        
        # Retrieve the audit log from the database
        saved_log = session.query(AuditLog).first()
        
        # Check the audit log's attributes
        assert saved_log is not None
        assert saved_log.doctor_id == doctor.id
        assert saved_log.action_type == ActionType.VIEW
        assert saved_log.entity_type == EntityType.PATIENT
        assert saved_log.entity_id == patient.id
        assert saved_log.patient_id == patient.id
        assert saved_log.ip_address == "127.0.0.1"
        
        # Check the details
        details = saved_log.get_details()
        assert details == {"source": "test"}
    
    def test_to_dict_method(self, doctor, patient, session):
        """Test the to_dict method of the AuditLog model."""
        # Create an audit log entry
        audit_log = AuditLog(
            doctor_id=doctor.id,
            action_type=ActionType.CREATE,
            entity_type=EntityType.NOTE,
            entity_id=1,
            details={"content": "Test note"},
            patient_id=patient.id,
            ip_address="127.0.0.1"
        )
        
        # Add the audit log to the database
        session.add(audit_log)
        session.commit()
        
        # Convert the audit log to a dictionary
        log_dict = audit_log.to_dict()
        
        # Check the dictionary keys
        assert "id" in log_dict
        assert "doctor_id" in log_dict
        assert "doctor_name" in log_dict
        assert "timestamp" in log_dict
        assert "action_type" in log_dict
        assert "entity_type" in log_dict
        assert "entity_id" in log_dict
        assert "details" in log_dict
        assert "patient_id" in log_dict
        assert "patient_name" in log_dict
        assert "ip_address" in log_dict
        
        # Check the dictionary values
        assert log_dict["doctor_id"] == doctor.id
        assert log_dict["doctor_name"] == f"{doctor.first_name} {doctor.last_name}"
        assert log_dict["action_type"] == ActionType.CREATE.value
        assert log_dict["entity_type"] == EntityType.NOTE.value
        assert log_dict["entity_id"] == 1
        assert log_dict["details"] == {"content": "Test note"}
        assert log_dict["patient_id"] == patient.id
        assert log_dict["patient_name"] == f"{patient.first_name} {patient.last_name}"
        assert log_dict["ip_address"] == "127.0.0.1"


class TestAuditViews:
    """Test cases for audit log views."""
    
    def test_audit_logs_view(self, logged_in_client, doctor, patient, session):
        """Test viewing audit logs."""
        # Create some audit log entries
        log1 = AuditLog(
            doctor_id=doctor.id,
            action_type=ActionType.CREATE,
            entity_type=EntityType.PATIENT,
            entity_id=patient.id,
            patient_id=patient.id,
            ip_address="127.0.0.1"
        )
        
        log2 = AuditLog(
            doctor_id=doctor.id,
            action_type=ActionType.UPDATE,
            entity_type=EntityType.PATIENT,
            entity_id=patient.id,
            patient_id=patient.id,
            ip_address="127.0.0.1"
        )
        
        # Add the audit logs to the database
        session.add(log1)
        session.add(log2)
        session.commit()
        
        # Access the audit logs page
        response = logged_in_client.get("/audit/logs")
        
        # Check if the page loaded successfully
        assert response.status_code == 200
        assert b"Audit" in response.data
        assert b"History" in response.data
        
        # Check if the audit logs are displayed
        assert bytes(doctor.first_name, 'utf-8') in response.data
        assert bytes(patient.first_name, 'utf-8') in response.data
        assert b"CREATE" in response.data
        assert b"UPDATE" in response.data
    
    def test_filtered_audit_logs_view(self, logged_in_client, doctor, patient, session):
        """Test viewing filtered audit logs."""
        # Create some audit log entries
        log1 = AuditLog(
            doctor_id=doctor.id,
            action_type=ActionType.CREATE,
            entity_type=EntityType.PATIENT,
            entity_id=patient.id,
            patient_id=patient.id,
            ip_address="127.0.0.1"
        )
        
        log2 = AuditLog(
            doctor_id=doctor.id,
            action_type=ActionType.VIEW,
            entity_type=EntityType.NOTE,
            entity_id=1,
            patient_id=patient.id,
            ip_address="127.0.0.1"
        )
        
        # Add the audit logs to the database
        session.add(log1)
        session.add(log2)
        session.commit()
        
        # Access the audit logs page with filters
        response = logged_in_client.get("/audit/logs?action_type=CREATE&entity_type=PATIENT")
        
        # Check if the page loaded successfully
        assert response.status_code == 200
        
        # The CREATE PATIENT action should be visible but not the VIEW NOTE action
        assert b"CREATE" in response.data
        assert b"PATIENT" in response.data
        assert b"VIEW" not in response.data
        assert b"NOTE" not in response.data
    
    def test_audit_logs_api(self, logged_in_client, doctor, patient, session):
        """Test retrieving audit logs via API."""
        # Create some audit log entries
        log1 = AuditLog(
            doctor_id=doctor.id,
            action_type=ActionType.CREATE,
            entity_type=EntityType.PATIENT,
            entity_id=patient.id,
            patient_id=patient.id,
            ip_address="127.0.0.1"
        )
        
        log2 = AuditLog(
            doctor_id=doctor.id,
            action_type=ActionType.UPDATE,
            entity_type=EntityType.PATIENT,
            entity_id=patient.id,
            patient_id=patient.id,
            ip_address="127.0.0.1"
        )
        
        # Add the audit logs to the database
        session.add(log1)
        session.add(log2)
        session.commit()
        
        # Send a GET request to the audit logs API
        response = logged_in_client.get("/audit/logs/stats")
        
        # Check if the request was successful
        assert response.status_code == 200
        
        # Parse the JSON response
        data = json.loads(response.data)
        
        # Check if the response contains audit statistics
        assert "status" in data
        assert data["status"] == "success"
        assert "action_stats" in data
        assert "entity_stats" in data
        assert "timeline" in data
        
        # Check if the action stats contain our test actions
        action_types = [action["type"] for action in data["action_stats"]]
        assert "CREATE" in action_types
        assert "UPDATE" in action_types
        
        # Check if the entity stats contain our test entity types
        entity_types = [entity["type"] for entity in data["entity_stats"]]
        assert "patient" in entity_types
