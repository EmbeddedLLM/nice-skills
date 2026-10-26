"""Run local LibreOffice with bounded process lifetime; no environment shim."""
import os
import signal
import subprocess
import tempfile
from pathlib import Path


def run_soffice(args, timeout=60, **kwargs):
    # Caller may supply a profile for a multi-step operation such as a macro.
    with tempfile.TemporaryDirectory(prefix='office-profile-') as tmp:
        command = ['soffice', *map(str, args)]
        if not any(a.startswith('-env:UserInstallation=') for a in command):
            command.insert(1, f'-env:UserInstallation={Path(tmp).as_uri()}')
        kwargs.pop('capture_output', None)
        check = kwargs.pop('check', False)
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                start_new_session=(os.name == 'posix'), **kwargs)
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            if os.name == 'posix':
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                proc.kill()
            proc.communicate()
            raise
        result = subprocess.CompletedProcess(command, proc.returncode, stdout, stderr)
        if check:
            result.check_returncode()
        return result
