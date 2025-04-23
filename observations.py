import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from flask_babel import gettext as _
from app import db
from models import Patient, VitalObservation, VitalSignType
from audit import log_observation_creation, log_observation_update, log_observation_delete

observations_bp = Blueprint('observations', __name__)
logger = logging.getLogger(__name__)

@observations_bp.route('/web/observations/<int:patient_id>', methods=['GET'])
@login_required
def get_web_observations(patient_id):
    """Ottiene le osservazioni per un paziente specifico."""
    # Trova il paziente
    patient = Patient.query.get_or_404(patient_id)
    
    # Verifica che il medico sia associato a questo paziente
    if patient not in current_user.patients.all():
        return jsonify({"error": _("Non sei autorizzato ad accedere a questo paziente")}), 403
    
    # Ottieni parametri di query per il filtraggio
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    vital_type = request.args.get('vital_type')
    
    # Crea query
    query = VitalObservation.query.filter_by(patient_id=patient_id)
    
    # Applica filtri
    if start_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            query = query.filter(VitalObservation.start_date >= start_date)
        except ValueError:
            return jsonify({"error": _("Formato data inizio non valido. Usa il formato ISO (YYYY-MM-DD)")}), 400
    
    if end_date_str:
        try:
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            query = query.filter(VitalObservation.end_date <= end_date)
        except ValueError:
            return jsonify({"error": _("Formato data fine non valido. Usa il formato ISO (YYYY-MM-DD)")}), 400
    
    if vital_type:
        try:
            vital_type_enum = VitalSignType(vital_type)
            query = query.filter_by(vital_type=vital_type_enum)
        except ValueError:
            return jsonify({
                "error": _("Tipo di parametro vitale non valido. Deve essere uno tra: %(types)s") % {
                    "types": ", ".join(t.value for t in VitalSignType)
                }
            }), 400
    
    # Esegui query
    observations = query.order_by(VitalObservation.created_at.desc()).all()
    
    return jsonify([obs.to_dict() for obs in observations]), 200

@observations_bp.route('/web/observations', methods=['POST'])
@login_required
def add_web_observation():
    """Aggiunge una nuova osservazione."""
    # Valida i dati della richiesta
    if not request.is_json:
        return jsonify({"error": _("Dati JSON mancanti nella richiesta")}), 400
    
    data = request.json
    logger.debug(f"Dati ricevuti per la nuova osservazione: {data}")
    
    # Valida i campi obbligatori
    required_fields = ['patient_id', 'vital_type', 'content', 'start_date', 'end_date']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": _("Campo obbligatorio mancante: {field}").format(field=field)}), 400
    
    # Trova il paziente
    patient_id = data['patient_id']
    patient = Patient.query.get(patient_id)
    
    if not patient:
        return jsonify({"error": _("Paziente non trovato")}), 404
    
    # Verifica che il medico sia associato a questo paziente
    if patient not in current_user.patients.all():
        return jsonify({"error": _("Non sei autorizzato ad accedere a questo paziente")}), 403
    
    # Valida il tipo di parametro vitale
    try:
        logger.debug(f"Tipo di parametro vitale ricevuto: {data['vital_type']}")
        logger.debug(f"Tipi di parametri vitali disponibili: {[t.value for t in VitalSignType]}")
        vital_type = VitalSignType(data['vital_type'])
    except ValueError as e:
        logger.error(f"Tipo di parametro vitale non valido: {data['vital_type']}, errore: {str(e)}")
        return jsonify({
            "error": _("Tipo di parametro vitale non valido. Deve essere uno tra: %(types)s") % {
                "types": ", ".join(t.value for t in VitalSignType)
            }
        }), 400
    
    # Analizza le date
    try:
        start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({"error": _("Formato data inizio non valido. Usa il formato ISO (YYYY-MM-DD)")}), 400
    
    try:
        end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({"error": _("Formato data fine non valido. Usa il formato ISO (YYYY-MM-DD)")}), 400
    
    # Verifica che la data di inizio sia precedente alla data di fine
    if start_date >= end_date:
        return jsonify({"error": _("La data di inizio deve essere precedente alla data di fine")}), 400
    
    # Crea l'osservazione
    try:
        observation = VitalObservation(
            patient_id=patient_id,
            doctor_id=current_user.id,
            vital_type=vital_type,
            content=data['content'],
            start_date=start_date,
            end_date=end_date
        )
        
        db.session.add(observation)
        db.session.commit()
        
        logger.info(f"Osservazione aggiunta per il paziente {patient_id} dal medico {current_user.id}")
        
        return jsonify({
            "message": _("Osservazione aggiunta con successo"),
            "observation": observation.to_dict()
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Errore durante l'aggiunta dell'osservazione: {str(e)}")
        return jsonify({"error": _("Si è verificato un errore durante l'aggiunta dell'osservazione")}), 500

@observations_bp.route('/web/observations/<int:observation_id>', methods=['PUT'])
@login_required
def update_web_observation(observation_id):
    """Aggiorna un'osservazione esistente."""
    # Trova l'osservazione
    observation = VitalObservation.query.get_or_404(observation_id)
    
    # Verifica che il medico sia il creatore dell'osservazione
    if observation.doctor_id != current_user.id:
        return jsonify({"error": _("Non sei autorizzato a modificare questa osservazione")}), 403
    
    # Valida i dati della richiesta
    if not request.is_json:
        return jsonify({"error": _("Dati JSON mancanti nella richiesta")}), 400
    
    data = request.json
    
    # Aggiorna il tipo di parametro vitale se fornito
    if 'vital_type' in data:
        try:
            observation.vital_type = VitalSignType(data['vital_type'])
        except ValueError:
            return jsonify({
                "error": _("Tipo di parametro vitale non valido. Deve essere uno tra: %(types)s") % {
                    "types": ", ".join(t.value for t in VitalSignType)
                }
            }), 400
    
    # Aggiorna il contenuto se fornito
    if 'content' in data:
        observation.content = data['content']
    
    # Aggiorna la data di inizio se fornita
    if 'start_date' in data:
        try:
            observation.start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": _("Formato data inizio non valido. Usa il formato ISO (YYYY-MM-DD)")}), 400
    
    # Aggiorna la data di fine se fornita
    if 'end_date' in data:
        try:
            observation.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": _("Formato data fine non valido. Usa il formato ISO (YYYY-MM-DD)")}), 400
    
    # Verifica che la data di inizio sia precedente alla data di fine
    if observation.start_date >= observation.end_date:
        return jsonify({"error": _("La data di inizio deve essere precedente alla data di fine")}), 400
    
    # Salva le modifiche
    try:
        observation.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Osservazione {observation_id} aggiornata dal medico {current_user.id}")
        
        return jsonify({
            "message": _("Osservazione aggiornata con successo"),
            "observation": observation.to_dict()
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Errore durante l'aggiornamento dell'osservazione: {str(e)}")
        return jsonify({"error": _("Si è verificato un errore durante l'aggiornamento dell'osservazione")}), 500

@observations_bp.route('/web/observations/<int:observation_id>', methods=['DELETE'])
@login_required
def delete_web_observation(observation_id):
    """Elimina un'osservazione."""
    # Trova l'osservazione
    observation = VitalObservation.query.get_or_404(observation_id)
    
    # Verifica che il medico sia il creatore dell'osservazione
    if observation.doctor_id != current_user.id:
        return jsonify({"error": _("Non sei autorizzato a eliminare questa osservazione")}), 403
    
    # Elimina l'osservazione
    try:
        db.session.delete(observation)
        db.session.commit()
        
        logger.info(f"Osservazione {observation_id} eliminata dal medico {current_user.id}")
        
        return jsonify({
            "message": _("Osservazione eliminata con successo")
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Errore durante l'eliminazione dell'osservazione: {str(e)}")
        return jsonify({"error": _("Si è verificato un errore durante l'eliminazione dell'osservazione")}), 500