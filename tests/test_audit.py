"""
Test module for the audit functionality.

This module tests the audit logging functionality including:
- Audit log creation for various actions
- Audit log retrieval and filtering
- Audit stats generation
- Convenience functions for common audit operations
"""
import json
from datetime import datetime, timedelta

from app.models import (ActionType, EntityType, VitalSignType)
from app.audit import (
    log_action, log_patient_creation, log_patient_update, log_patient_delete,
    log_note_creation, log_report_generation, log_patient_view, log_patient_import,
    log_observation_creation, log_observation_update, log_observation_delete,
    log_health_link_creation, log_platform_connection, log_platform_disconnection,
    log_data_sync, log_vital_creation, log_note_delete
)


class TestAuditLogging:
    """Test class for audit logging functionality.
    
    This class tests all aspects of the audit logging system including:
    - Base logging functionality
    - Entity-specific logging functions
    - API endpoints for retrieving audit data
    - Statistics generation for audit logs
    """

    def test_log_action(self, doctor_factory, patient_factory):
        """Test log_action basic functionality.
        
        Verifies that the core log_action function correctly creates audit logs
        with the specified parameters, and that optional parameters are handled properly.
        
        Args:
            doctor_factory: Factory fixture to create Doctor instances
            patient_factory: Factory fixture to create Patient instances
        """
        doctor = doctor_factory()
        patient = patient_factory()
        details = {"test_key": "test_value"}
        
        # Create audit log
        audit_log = log_action(
            doctor_id=doctor.id,
            action_type=ActionType.CREATE,
            entity_type=EntityType.PATIENT,
            entity_id=patient.id,
            details=details,
            patient_id=patient.id
        )
          # Verify audit log creation and properties
        assert audit_log is not None
        assert audit_log.doctor_id == doctor.id
        assert audit_log.action_type == ActionType.CREATE
        assert audit_log.entity_type == EntityType.PATIENT
        assert audit_log.entity_id == patient.id
        assert audit_log.patient_id == patient.id
        
        # Check details were stored correctly
        stored_details = audit_log.get_details()
        assert stored_details['test_key'] == 'test_value'
        
        # Test with missing optional parameters
        audit_log = log_action(
            doctor_id=doctor.id,
            action_type=ActionType.VIEW,
            entity_type=EntityType.NOTE,
            entity_id=1
        )
        
        assert audit_log is not None
        assert audit_log.doctor_id == doctor.id
        assert audit_log.action_type == ActionType.VIEW
        assert audit_log.entity_type == EntityType.NOTE
        assert audit_log.entity_id == 1
        assert audit_log.patient_id is None
        assert audit_log.details is None

    def test_patient_audit_logs(self, doctor_factory, patient_factory):
        """Test patient-related audit logging functions.
        
        Verifies that all patient-related audit logging functions (creation, update,
        delete, view, and import) correctly create audit logs with appropriate action types,
        entity types, and details.
        
        Args:
            doctor_factory: Factory fixture to create Doctor instances
            patient_factory: Factory fixture to create Patient instances
        """
        doctor = doctor_factory()
        patient = patient_factory()
        
        # Test patient creation log
        creation_log = log_patient_creation(doctor.id, patient)
        assert creation_log is not None
        assert creation_log.action_type == ActionType.CREATE
        assert creation_log.entity_type == EntityType.PATIENT
        assert creation_log.entity_id == patient.id
        
        # Test patient update log
        old_data = patient.to_dict()
        patient.first_name = "Updated"
        update_log = log_patient_update(doctor.id, patient, old_data)
        assert update_log is not None
        assert update_log.action_type == ActionType.UPDATE
        assert update_log.entity_type == EntityType.PATIENT
        
        # Verify update details contain old and new values
        update_details = update_log.get_details()
        assert 'old' in update_details
        assert 'new' in update_details
        assert update_details['old']['first_name'] == old_data['first_name']
        assert update_details['new']['first_name'] == "Updated"
        
        # Test patient delete log
        delete_log = log_patient_delete(doctor.id, patient)
        assert delete_log is not None
        assert delete_log.action_type == ActionType.DELETE
        assert delete_log.entity_type == EntityType.PATIENT
        
        # Test patient view log
        view_log = log_patient_view(doctor.id, patient.id)
        assert view_log is not None
        assert view_log.action_type == ActionType.VIEW
        assert view_log.entity_type == EntityType.PATIENT
        
        # Test patient import log
        import_log = log_patient_import(doctor.id, patient)
        assert import_log is not None
        assert import_log.action_type == ActionType.IMPORT
        assert import_log.entity_type == EntityType.PATIENT
        assert import_log.entity_id == patient.id
        
        # Verify import details contain patient UUID
        import_details = import_log.get_details()
        assert 'patient_uuid' in import_details
        assert import_details['patient_uuid'] == patient.uuid

    def test_note_audit_logs(self, doctor_factory, patient_factory):
        """Test note-related audit logging functions.
        
        Verifies that note-related audit logging functions (creation and deletion)
        correctly create audit logs with appropriate action types, entity types, and details.
        Uses a mock Note object to simulate the database model.
        
        Args:
            doctor_factory: Factory fixture to create Doctor instances
            patient_factory: Factory fixture to create Patient instances
        """
        doctor = doctor_factory()
        patient = patient_factory()
        
        # Create a test note
        class MockNote:
            def __init__(self):
                self.id = 1
                self.doctor_id = doctor.id
                self.patient_id = patient.id
                self.content = 'Test note content'
                self.created_at = datetime.utcnow()
                self.updated_at = datetime.utcnow()
                
            def to_dict(self):
                return {
                    'id': self.id,
                    'doctor_id': self.doctor_id, 
                    'patient_id': self.patient_id,
                    'content': self.content,
                    'created_at': self.created_at.isoformat(),
                    'updated_at': self.updated_at.isoformat()
                }
                
        note = MockNote()
        
        # Test note creation log
        creation_log = log_note_creation(doctor.id, note)
        assert creation_log is not None
        assert creation_log.action_type == ActionType.CREATE
        assert creation_log.entity_type == EntityType.NOTE
        assert creation_log.entity_id == note.id
        assert creation_log.patient_id == patient.id
        
        # Test note deletion log
        delete_log = log_note_delete(doctor.id, note)
        assert delete_log is not None
        assert delete_log.action_type == ActionType.DELETE
        assert delete_log.entity_type == EntityType.NOTE
        assert delete_log.entity_id == note.id
        assert delete_log.patient_id == patient.id
        
        # Verify deletion details contain note content
        delete_details = delete_log.get_details()
        assert 'content' in delete_details
        assert delete_details['content'] == 'Test note content'

    def test_observation_audit_logs(self, doctor_factory, patient_factory):
        """Test observation-related audit logging functions.
        
        Verifies that observation-related audit logging functions (creation, update, 
        and deletion) correctly create audit logs with appropriate action types, 
        entity types, and details. Uses a mock Observation object to simulate
        the database model.
        
        Args:
            doctor_factory: Factory fixture to create Doctor instances
            patient_factory: Factory fixture to create Patient instances
        """
        doctor = doctor_factory()
        patient = patient_factory()
        
        # Create a test observation
        class MockObservation:
            def __init__(self):
                self.id = 1
                self.doctor_id = doctor.id
                self.patient_id = patient.id
                self.vital_type = VitalSignType.HEART_RATE
                self.content = 'Heart rate observation'
                self.start_date = datetime.utcnow() - timedelta(days=7)
                self.end_date = datetime.utcnow()
                self.created_at = datetime.utcnow()
                self.updated_at = datetime.utcnow()
                
            def to_dict(self):
                return {
                    'id': self.id,
                    'doctor_id': self.doctor_id,
                    'patient_id': self.patient_id,
                    'vital_type': self.vital_type.value,
                    'content': self.content,
                    'start_date': self.start_date.isoformat(),
                    'end_date': self.end_date.isoformat(),
                    'created_at': self.created_at.isoformat(),
                    'updated_at': self.updated_at.isoformat()
                }
        
        observation = MockObservation()
        
        # Test observation creation log
        creation_log = log_observation_creation(doctor.id, observation)
        assert creation_log is not None
        assert creation_log.action_type == ActionType.CREATE
        assert creation_log.entity_type == EntityType.OBSERVATION
        assert creation_log.entity_id == observation.id
        assert creation_log.patient_id == patient.id
        
        # Test observation update log
        old_data = {'content': 'Old content'}
        update_log = log_observation_update(doctor.id, observation, old_data)
        assert update_log is not None
        assert update_log.action_type == ActionType.UPDATE
        assert update_log.entity_type == EntityType.OBSERVATION
        assert update_log.entity_id == observation.id
        
        # Test observation delete log
        delete_log = log_observation_delete(doctor.id, observation)
        assert delete_log is not None
        assert delete_log.action_type == ActionType.DELETE
        assert delete_log.entity_type == EntityType.OBSERVATION
        assert delete_log.entity_id == observation.id

    def test_vital_sign_audit_logs(self, doctor_factory, patient_factory):
        """Test vital sign-related audit logging functions.
        
        Verifies that vital sign-related audit logging functions correctly 
        create audit logs with appropriate action types, entity types, and details.
        Uses a mock VitalSign object to simulate the database model.
        
        Args:
            doctor_factory: Factory fixture to create Doctor instances
            patient_factory: Factory fixture to create Patient instances
        """
        doctor = doctor_factory()
        patient = patient_factory()
        
        # Create a test vital sign
        class MockVitalSign:
            def __init__(self):
                self.id = 1
                self.patient_id = patient.id
                self.type = VitalSignType.HEART_RATE
                self.value = 72
                self.timestamp = datetime.utcnow()
                
            def to_dict(self):
                return {
                    'id': self.id,
                    'patient_id': self.patient_id,
                    'type': self.type.value,
                    'value': self.value,
                    'timestamp': self.timestamp.isoformat()
                }
        
        vital = MockVitalSign()
        
        # Test vital sign creation log
        creation_log = log_vital_creation(doctor.id, vital)
        assert creation_log is not None
        assert creation_log.action_type == ActionType.CREATE
        assert creation_log.entity_type == EntityType.VITAL_SIGN
        assert creation_log.entity_id == vital.id
        assert creation_log.patient_id == patient.id
        
        # Verify details contain vital type and value
        creation_details = creation_log.get_details()
        assert 'type' in creation_details
        assert 'value' in creation_details
        assert creation_details['type'] == 'heart_rate'
        assert creation_details['value'] == 72

    def test_report_generation_audit_log(self, doctor_factory, patient_factory):
        """Test report generation audit logging functions.
        
        Verifies that report generation audit logging function correctly creates
        audit logs with appropriate action types, entity types, and details including
        report parameters.
        
        Args:
            doctor_factory: Factory fixture to create Doctor instances
            patient_factory: Factory fixture to create Patient instances
        """
        doctor = doctor_factory()
        patient = patient_factory()
        report_params = {
            'period': '7d',
            'vital_types': ['heart_rate', 'steps']
        }
        
        # Test report generation log
        report_log = log_report_generation(doctor.id, patient.id, 'Health Report', report_params)
        assert report_log is not None
        assert report_log.action_type == ActionType.EXPORT
        assert report_log.entity_type == EntityType.REPORT
        assert report_log.patient_id == patient.id
        
        # Verify details contain report type and parameters
        report_details = report_log.get_details()
        assert 'report_type' in report_details
        assert 'params' in report_details
        assert report_details['report_type'] == 'Health Report'
        assert report_details['params'] == report_params

    def test_health_platform_audit_logs(self, doctor_factory, patient_factory):
        """Test health platform-related audit logging functions.
        
        Verifies that health platform-related audit logging functions (link generation,
        connection, disconnection, and data syncing) correctly create audit logs
        with appropriate action types, entity types, and details.
        
        Args:
            doctor_factory: Factory fixture to create Doctor instances
            patient_factory: Factory fixture to create Patient instances
        """
        doctor = doctor_factory()
        patient = patient_factory()
        platform_name = "fitbit"
          # Create a mock health platform link using dynamic class
        link = type('HealthPlatformLink', (), {
            'id': 1,
            'patient_id': patient.id,
            'doctor_id': doctor.id,
            'platform': 'fitbit',
            'uuid': 'test-uuid',
            'expires_at': datetime.utcnow() + timedelta(hours=24)
        })
        
        # Test health link creation log
        link_log = log_health_link_creation(doctor.id, link)
        assert link_log is not None
        assert link_log.action_type == ActionType.GENERATE_LINK
        assert link_log.entity_type == EntityType.HEALTH_LINK
        assert link_log.entity_id == link.id
        assert link_log.patient_id == patient.id
        
        # Test platform connection log
        connection_log = log_platform_connection(doctor.id, patient, platform_name)
        assert connection_log is not None
        assert connection_log.action_type == ActionType.CONNECT
        assert connection_log.entity_type == EntityType.HEALTH_PLATFORM
        assert connection_log.patient_id == patient.id
        
        # Test platform disconnection log
        disconnection_log = log_platform_disconnection(doctor.id, patient, platform_name)
        assert disconnection_log is not None
        assert disconnection_log.action_type == ActionType.DISCONNECT
        assert disconnection_log.entity_type == EntityType.HEALTH_PLATFORM
        assert disconnection_log.patient_id == patient.id
        
        # Test data sync log
        result_summary = {
            'records': 150,
            'timespan': '7 days',
            'success': True
        }
          # Define data type and platform as strings
        data_type = 'heart_rate'        
        platform_name = 'fitbit'
        sync_log = log_data_sync(doctor.id, patient, platform_name, data_type, result_summary)
        assert sync_log is not None
        assert sync_log.action_type == ActionType.SYNC
        assert sync_log.entity_type == EntityType.HEALTH_PLATFORM
        assert sync_log.patient_id == patient.id
        
        # Verify sync details
        sync_details = sync_log.get_details()
        assert 'platform' in sync_details
        assert 'data_type' in sync_details
        assert 'result' in sync_details
        assert sync_details['platform'] == platform_name
        assert sync_details['data_type'] == 'heart_rate'
        assert sync_details['result'] == result_summary

    def test_audit_logs_api_endpoint(self, client, authenticated_doctor):
        """Test the API endpoint for retrieving audit logs.
        
        Verifies that the audit logs API endpoint correctly returns audit logs
        with various filters (action type, entity type, date range) and in different
        formats (JSON, HTML).
        
        Args:
            client: Flask test client
            authenticated_doctor: Fixture providing an authenticated doctor
        """
        doctor = authenticated_doctor
        
        # Create some audit logs
        for i in range(5):
            log_action(
                doctor_id=doctor.id,
                action_type=ActionType.VIEW,
                entity_type=EntityType.PATIENT,
                entity_id=i+1
            )
            
        # Test without filters, specifying JSON format and filtering by doctor_id
        response = client.get(f'/audit/logs?format=json&doctor_id={doctor.id}')
        
        # Verify the endpoint is accessible
        assert response.status_code == 200, "Audit logs endpoint not accessible"
        data = json.loads(response.data)
        # There should be exactly 5 logs created by the current doctor
        assert len(data['logs']) == 5
        
        # Test with action_type filter
        log_action(
            doctor_id=doctor.id,
            action_type=ActionType.CREATE,
            entity_type=EntityType.NOTE,
            entity_id=1
        )
        
        # Filter by both action type and doctor ID
        response = client.get(f'/audit/logs?action_type=CREATE&doctor_id={doctor.id}&format=json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['logs']) == 1
        assert data['logs'][0]['action_type'] == 'CREATE'
        
        # Test with entity_type filter
        response = client.get(f'/audit/logs?entity_type=note&doctor_id={doctor.id}&format=json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['logs']) == 1
        assert data['logs'][0]['entity_type'] == 'note'
        
        # Test with date range filter
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        response = client.get(f'/audit/logs?start_date={yesterday}&end_date={tomorrow}&doctor_id={doctor.id}&format=json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['logs']) == 6  # Verify that all created logs are within the date range
        
        # Test HTML format vs JSON format
        response = client.get('/audit/logs?format=html')
        assert response.status_code == 200
        assert response.content_type.startswith('text/html')
        
        response = client.get('/audit/logs?format=json')
        assert response.status_code == 200
        assert response.content_type.startswith('application/json')

    def test_audit_stats_api_endpoint(self, client, authenticated_doctor, patient_factory):
        """Test the API endpoint for retrieving audit statistics.
        
        Verifies that the audit statistics API endpoint correctly returns
        statistics about audit logs, including counts by action type, entity type,
        and timeline data.
        
        Args:
            client: Flask test client
            authenticated_doctor: Fixture providing an authenticated doctor
            patient_factory: Factory fixture to create Patient instances
        """
        doctor = authenticated_doctor
        patient = patient_factory()
        
        # Create diverse audit logs
        action_types = [
            ActionType.CREATE, ActionType.UPDATE, ActionType.VIEW, 
            ActionType.DELETE, ActionType.EXPORT
        ]
        
        entity_types = [
            EntityType.PATIENT, EntityType.NOTE, EntityType.OBSERVATION,
            EntityType.REPORT, EntityType.VITAL_SIGN
        ]
        
        for action in action_types:
            for entity in entity_types:
                log_action(
                    doctor_id=doctor.id,
                    action_type=action,
                    entity_type=entity,
                    entity_id=1,
                    patient_id=patient.id if entity != EntityType.PATIENT else None
                )
        
        # Test stats endpoint
        response = client.get('/audit/logs/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify presence of action_stats and entity_stats (updated structure)
        assert 'action_stats' in data
        assert 'entity_stats' in data
        assert 'timeline' in data
        
        # Check action counts - using action_stats instead of actions_by_type
        assert len(data['action_stats']) >= len(action_types)
        for action_type in action_types:
            found = False
            for item in data['action_stats']:
                if item['type'] == action_type.value:                    # Verify count is at least equal to the number of entity types we created
                    assert item['count'] >= len(entity_types)
                    found = True
                    break
            assert found, f"Action type {action_type.value} not found in results"
        
        # Check entity counts
        assert len(data['entity_stats']) >= len(entity_types)
        for entity_type in entity_types:
            found = False
            for item in data['entity_stats']:
                if item['type'] == entity_type.value.lower():
                    # The count may vary due to other tests
                    assert item['count'] >= len(action_types)
                    found = True
                    break
            assert found, f"Entity type {entity_type.value} not found in results"
        
        # Check timeline data (updated structure)
        assert 'timeline' in data
        assert 'counts' in data['timeline']
        assert 'labels' in data['timeline']
        assert len(data['timeline']['counts']) == len(data['timeline']['labels'])
