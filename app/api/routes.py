from flask import Blueprint, jsonify, request
from app.services.wireguard_service import WireguardService
import base64
import urllib.parse

bp = Blueprint('wireguard', __name__)
wg_service = WireguardService()

@bp.route('/peer', methods=['POST'])
def create_peer():
    try:
        result = wg_service.create_peer()
        return jsonify({
            'status': 'success',
            'data': result
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/peer/<string:encoded_key>', methods=['GET'])
def get_peer(encoded_key):
    try:
        # URL decode and then base64 decode if needed
        public_key = urllib.parse.unquote(encoded_key)

        peer = wg_service.get_peer(public_key)
        if peer:
            return jsonify({
                'status': 'success',
                'data': peer.to_dict()
            })
        return jsonify({
            'status': 'error',
            'message': 'Peer not found'
        }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/peers', methods=['GET'])
def get_all_peers():
    try:
        peers = wg_service.get_all_peers()
        return jsonify({
            'status': 'success',
            'data': [peer.to_dict() for peer in peers]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/peer/<string:encoded_key>', methods=['DELETE'])
def delete_peer(encoded_key):
    try:
        # URL decode and then base64 decode if needed
        public_key = urllib.parse.unquote(encoded_key)

        if wg_service.delete_peer(public_key):
            return jsonify({
                'status': 'success',
                'message': 'Peer deleted successfully'
            })
        return jsonify({
            'status': 'error',
            'message': 'Peer not found'
        }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
