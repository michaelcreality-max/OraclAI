"""
Execution Safety Routes
API endpoints for safety status and mode control with safety validation.
"""

from flask import Blueprint, jsonify, request
from quant_ecosystem.api_key_manager import require_admin, require_user_or_admin, Role
from quant_ecosystem.execution_safety import execution_safety, SystemMode

safety_routes = Blueprint('safety_routes', __name__, url_prefix='/api')


@safety_routes.route('/safety/status', methods=['GET'])
@require_user_or_admin
def get_safety_status():
    """
    Get current execution safety status.
    Returns whether system is safe and execution is allowed.
    """
    status = execution_safety.get_safety_status()
    return jsonify(status)


@safety_routes.route('/mode/current', methods=['GET'])
@require_user_or_admin
def get_current_mode():
    """Get current system mode"""
    mode = execution_safety.get_current_mode()
    return jsonify({
        "mode": mode.value,
        "description": _get_mode_description(mode)
    })


@safety_routes.route('/mode/switch', methods=['POST'])
@require_admin
def switch_mode():
    """
    Switch system mode with safety validation.
    Requires all safety checks to pass before switching to execution mode.
    
    Request body:
        - mode: str - 'training', 'execution', or 'safe'
    """
    data = request.get_json() or {}
    mode_str = data.get('mode', '').lower()
    
    if not mode_str:
        return jsonify({"error": "Mode is required"}), 400
    
    try:
        target_mode = SystemMode(mode_str)
    except ValueError:
        return jsonify({
            "error": f"Invalid mode '{mode_str}'. Must be one of: training, execution, safe"
        }), 400
    
    # Attempt mode switch with safety validation
    success, message = execution_safety.set_mode(target_mode)
    
    if not success:
        return jsonify({
            "success": False,
            "error": message,
            "systemSafe": False,
            "executionAllowed": False
        }), 403
    
    return jsonify({
        "success": True,
        "message": message,
        "mode": target_mode.value,
        "systemSafe": execution_safety.get_safety_status()["systemSafe"],
        "executionAllowed": execution_safety.get_safety_status()["executionAllowed"]
    })


@safety_routes.route('/safety/record-validation', methods=['POST'])
@require_admin
def record_model_validation():
    """
    Record a model validation result.
    
    Request body:
        - model_id: str
        - model_name: str
        - validation_score: float
    """
    data = request.get_json() or {}
    
    model_id = data.get('model_id')
    model_name = data.get('model_name')
    validation_score = data.get('validation_score')
    
    if not all([model_id, model_name, validation_score is not None]):
        return jsonify({"error": "Missing required fields: model_id, model_name, validation_score"}), 400
    
    try:
        validation_score = float(validation_score)
    except (ValueError, TypeError):
        return jsonify({"error": "validation_score must be a number"}), 400
    
    success = execution_safety.record_model_validation(
        model_id=model_id,
        model_name=model_name,
        validation_score=validation_score
    )
    
    return jsonify({
        "success": success,
        "message": f"Model validation recorded for {model_name}"
    })


@safety_routes.route('/safety/record-backtest', methods=['POST'])
@require_admin
def record_backtest():
    """
    Record a completed backtest.
    
    Request body:
        - backtest_id: str
        - strategy_name: str
        - win_rate: float
        - profit_factor: float
        - max_drawdown: float
        - sharpe_ratio: float
    """
    data = request.get_json() or {}
    
    required_fields = ['backtest_id', 'strategy_name', 'win_rate', 
                       'profit_factor', 'max_drawdown', 'sharpe_ratio']
    
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    
    try:
        success = execution_safety.record_backtest(
            backtest_id=data['backtest_id'],
            strategy_name=data['strategy_name'],
            win_rate=float(data['win_rate']),
            profit_factor=float(data['profit_factor']),
            max_drawdown=float(data['max_drawdown']),
            sharpe_ratio=float(data['sharpe_ratio'])
        )
        
        return jsonify({
            "success": success,
            "message": f"Backtest recorded for {data['strategy_name']}"
        })
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid numeric values: {str(e)}"}), 400


@safety_routes.route('/safety/violations', methods=['GET'])
@require_admin
def get_safety_violations():
    """Get recent safety violations (admin only)"""
    import sqlite3
    from datetime import datetime, timedelta
    
    days = request.args.get('days', 7, type=int)
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    
    with sqlite3.connect(execution_safety.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, violation_type, description, severity
            FROM safety_violations
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        ''', (cutoff,))
        
        violations = [
            {
                "timestamp": row[0],
                "type": row[1],
                "description": row[2],
                "severity": row[3]
            }
            for row in cursor.fetchall()
        ]
    
    return jsonify({
        "count": len(violations),
        "violations": violations
    })


@safety_routes.route('/safety/reset-safe-mode', methods=['POST'])
@require_admin
def reset_from_safe_mode():
    """
    Reset system from safe mode back to training.
    Requires manual admin intervention.
    """
    success, message = execution_safety.set_mode(SystemMode.TRAINING)
    
    if success:
        return jsonify({
            "success": True,
            "message": "System reset to training mode",
            "mode": "training",
            "note": "Run safety checks before switching to execution mode"
        })
    else:
        return jsonify({"error": message}), 500


def _get_mode_description(mode: SystemMode) -> str:
    """Get human-readable mode description"""
    descriptions = {
        SystemMode.TRAINING: "Safe testing environment - no real trades",
        SystemMode.EXECUTION: "Live trading mode - real positions opened",
        SystemMode.SAFE: "HOLD mode only - auto-fallback due to anomalies"
    }
    return descriptions.get(mode, "Unknown mode")
