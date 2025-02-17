# app/api/routes.py
from flask import Blueprint, jsonify, request
from app.services.wireguard_service import WireguardService

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

@bp.route('/peer/<public_key>', methods=['GET'])
def get_peer(public_key):
    try:
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

@bp.route('/peer/<public_key>', methods=['DELETE'])
def delete_peer(public_key):
    try:
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

