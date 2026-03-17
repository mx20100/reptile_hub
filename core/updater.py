"""
Updater module - checks the public GitHub repo for new commits and
applies updates via git pull.

Endpoints
---------
GET  /api/update/check   - compare local HEAD against remote; return status
POST /api/update/apply   - pull latest code and restart the service
"""

from flask import Blueprint, jsonify
import subprocess
import os

update_bp = Blueprint('update_bp', __name__)

REPO_URL = "https://github.com/mx20100/reptile_hub.git"
# Resolve the project root (one level up from this file's directory)
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
UPDATE_SCRIPT = os.path.join(PROJECT_DIR, 'scripts', 'update.sh')


def _run(cmd, **kwargs):
    """Run a shell command inside the project directory and return stdout."""
    return subprocess.run(
        cmd, capture_output=True, text=True,
        cwd=PROJECT_DIR, timeout=30, **kwargs
    )


@update_bp.route('/api/update/check', methods=['GET'])
def check_update():
    """Compare local HEAD with the remote main branch."""
    try:
        # Get local commit hash
        local = _run(['git', 'rev-parse', 'HEAD'])
        local_hash = local.stdout.strip()

        # Fetch latest remote refs without downloading objects
        _run(['git', 'fetch', 'origin', 'main', '--quiet'])
        remote = _run(['git', 'rev-parse', 'origin/main'])
        remote_hash = remote.stdout.strip()

        if not local_hash or not remote_hash:
            return jsonify({'error': 'Could not read git hashes'}), 500

        update_available = local_hash != remote_hash

        return jsonify({
            'update_available': update_available,
            'local': local_hash[:8],
            'remote': remote_hash[:8]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@update_bp.route('/api/update/apply', methods=['POST'])
def apply_update():
    """Pull the latest code and restart the reptilehub service."""
    try:
        # Run the update script (it does git pull + service restart)
        result = subprocess.run(
            ['sudo', UPDATE_SCRIPT],
            capture_output=True, text=True,
            cwd=PROJECT_DIR, timeout=60
        )
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': result.stderr or 'Update script failed'
            }), 500

        return jsonify({'success': True, 'message': 'Update applied. Restarting...'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500