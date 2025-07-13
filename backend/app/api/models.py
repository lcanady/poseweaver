from flask import Blueprint, jsonify
from app.services.model_config import ModelConfig

models_bp = Blueprint('models', __name__)


@models_bp.route('/presets', methods=['GET'])
def get_model_presets():
    """Get all available model presets."""
    try:
        presets = ModelConfig.get_model_presets()
        return jsonify(presets), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@models_bp.route('/available', methods=['GET'])
def get_available_models():
    """Get list of available models."""
    try:
        models = ModelConfig.get_available_models()
        return jsonify({'models': models}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@models_bp.route('/config/<model_name>', methods=['GET'])
def get_model_config(model_name):
    """Get configuration for a specific model."""
    try:
        config = ModelConfig.get_model_config(model_name)
        return jsonify(config), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500 