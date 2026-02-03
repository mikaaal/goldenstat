from flask import Blueprint, request, jsonify

tracking_bp = Blueprint('tracking', __name__)


def _get_usage_logger():
    from app import usage_logger
    return usage_logger


@tracking_bp.route('/api/track-tab', methods=['POST'])
def track_tab_click():
    """Log tab clicks for usage analytics"""
    try:
        data = request.get_json()
        tab = data.get('tab', 'unknown')
        context = data.get('context', '')
        league = request.args.get('league', '')

        # Get client info
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')[:100]

        _get_usage_logger().info(f"TAB | {tab} | league={league or 'stockholm'} | context={context} | ip={ip} | ua={user_agent}")

        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tracking_bp.route('/api/track-click', methods=['POST'])
def track_click():
    """Track click events for analytics"""
    try:
        data = request.get_json()
        event_name = data.get('event', 'unknown')
        league = request.args.get('league', '')

        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')[:100]

        _get_usage_logger().info(f"CLICK | {event_name} | league={league or 'stockholm'} | ip={ip} | ua={user_agent}")

        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tracking_bp.route('/api/track-pageview', methods=['POST'])
def track_pageview():
    """Track page views for analytics"""
    try:
        data = request.get_json()
        page_name = data.get('page', 'unknown')
        context = data.get('context', '')
        league = request.args.get('league', '')

        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')[:100]

        source = context or league or 'stockholm'
        _get_usage_logger().info(f"PAGEVIEW | {page_name} | league={source} | ip={ip} | ua={user_agent}")

        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@tracking_bp.route('/api/track-search', methods=['POST'])
def track_search():
    """Track player searches for analytics"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        context = data.get('context', '')
        league = request.args.get('league', '')

        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')[:100]

        source = context or league or 'stockholm'
        _get_usage_logger().info(f"SEARCH | {query} | league={source} | ip={ip} | ua={user_agent}")

        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
