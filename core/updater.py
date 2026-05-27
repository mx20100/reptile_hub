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
    """Pull the latest code and reboot the Pi."""
    try:
        # Launch the update script detached so Flask can return a response
        # before the Pi reboots. stdout/stderr go to /tmp/reptile_update.log.
        log = open('/tmp/reptile_update.log', 'w')
        subprocess.Popen(
            ['sudo', UPDATE_SCRIPT],
            stdout=log, stderr=log,
            cwd=PROJECT_DIR,
            close_fds=True
        )
        return jsonify({'success': True, 'message': 'Updating and rebooting...'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500