"""Exercise owned server groups through the public with_server command line.

Fixtures use ephemeral loopback ports and synthetic local processes only.
"""

import os
import shlex
import signal
import socket
import subprocess
import sys
import time
import unittest

from skill_scripts import SKILLS, ScriptCase


@unittest.skipUnless(os.name == 'posix', 'server process groups require POSIX')
class ServerLifecycleTests(ScriptCase):
    script_path = SKILLS / 'webapp-testing/scripts/with_server.py'

    def setUp(self):
        super().setUp()
        self.processes = []
        self.group_files = []
        self.log = (self.work / 'process.log').open('w+')
        self.addCleanup(self.log.close)
        self.addCleanup(self.stop_processes)
        self.server_script = self.write('listener.py', '''
import os, pathlib, socket, sys
port, group_file, noisy = sys.argv[1:]
pathlib.Path(group_file).write_text(str(os.getpgrp()))
if noisy == 'yes':
    sys.stdout.write('output' * 100000)
    sys.stdout.flush()
    sys.stderr.write('errors' * 100000)
    sys.stderr.flush()
with socket.socket() as listener:
    listener.bind(('127.0.0.1', int(port)))
    listener.listen()
    while True:
        connection, _ = listener.accept()
        connection.close()
''')

    def stop_processes(self):
        for proc in self.processes:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
        # Also clean up fixtures if a regression prevented helper cleanup.
        for path in self.group_files:
            if path.exists() and path.read_text():
                try:
                    os.killpg(int(path.read_text()), signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def ports(self, count):
        sockets = []
        try:
            for _ in range(count):
                sock = socket.socket()
                sockets.append(sock)
                sock.bind(('127.0.0.1', 0))
            return [sock.getsockname()[1] for sock in sockets]
        finally:
            for sock in sockets:
                sock.close()

    def listener(self, port, noisy=False):
        group_file = self.work / f'group-{port}'
        self.group_files.append(group_file)
        args = [sys.executable, str(self.server_script), str(port), str(group_file),
                'yes' if noisy else 'no']
        # Keep a parent alive so cleanup must reach its listening descendant.
        return shlex.join([sys.executable, '-c',
                           f'import subprocess, time; subprocess.Popen({args!r}); time.sleep(60)'])

    def start(self, servers, command, timeout='3'):
        args = [sys.executable, str(self.script_path), '--timeout', timeout]
        for port, server in servers:
            args.extend(['--server', server, '--port', str(port)])
        args.extend(['--', sys.executable, '-c', command])
        proc = subprocess.Popen(args, cwd=self.work, stdout=self.log, stderr=self.log)
        self.processes.append(proc)
        return proc

    def assert_exit(self, proc, expected):
        result = proc.wait(timeout=12)
        self.log.flush()
        self.log.seek(0)
        self.assertEqual(result, expected, self.log.read()[-3000:])

    def wait_for(self, condition):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if condition():
                return
            time.sleep(0.02)
        self.fail('Timed out waiting for local fixture state')

    @staticmethod
    def listening(port):
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.1):
                return True
        except OSError:
            return False

    def test_multiple_servers_and_command_descendants_are_stopped(self):
        """Successful runs close every server and children left by the test command."""
        first, second, descendant = self.ports(3)
        child_group = self.work / 'command-descendant.group'
        self.group_files.append(child_group)
        child_args = [sys.executable, str(self.server_script), str(descendant), str(child_group), 'no']
        command = f'''
import socket, subprocess, time
for port in {[first, second]!r}:
    with socket.create_connection(('127.0.0.1', port), timeout=1):
        pass
subprocess.Popen({child_args!r})
for _ in range(100):
    try:
        with socket.create_connection(('127.0.0.1', {descendant}), timeout=0.1):
            break
    except OSError:
        time.sleep(0.02)
else:
    raise RuntimeError('command descendant did not start')
'''
        proc = self.start([(first, self.listener(first)), (second, self.listener(second))], command)
        self.assert_exit(proc, 0)
        self.wait_for(lambda: not any(self.listening(p) for p in (first, second, descendant)))

    def test_noisy_server_preserves_command_failure_code(self):
        """Large stdout and stderr do not block readiness or swallow a command failure."""
        port, = self.ports(1)
        proc = self.start([(port, self.listener(port, noisy=True))], 'raise SystemExit(23)')
        self.assert_exit(proc, 23)
        self.wait_for(lambda: not self.listening(port))

    def test_occupied_port_prevents_any_launch_and_preserves_listener(self):
        """Preflight rejects occupied ports before launching either server or command."""
        marker = self.work / 'unexpected'
        touch = f'from pathlib import Path; Path({str(marker)!r}).touch()'
        with socket.socket() as existing:
            existing.bind(('127.0.0.1', 0))
            existing.listen()
            port = existing.getsockname()[1]
            proc = self.start([(port, shlex.join([sys.executable, '-c', touch]))], touch)
            self.assert_exit(proc, 2)
            self.assertFalse(marker.exists())
            self.assertTrue(self.listening(port))

    def test_startup_failures_stop_already_started_servers(self):
        """Early exit and readiness timeout preserve the test command and clean earlier servers."""
        for failing_server in ('exit 17', shlex.join([sys.executable, '-c', 'import time; time.sleep(60)'])):
            with self.subTest(server=failing_server):
                ready, failing = self.ports(2)
                marker = self.work / 'unexpected'
                proc = self.start([(ready, self.listener(ready)), (failing, failing_server)],
                                  f'from pathlib import Path; Path({str(marker)!r}).touch()', timeout='2')
                self.assert_exit(proc, 1)
                self.log.seek(0)
                expected = ('A server exited before readiness' if failing_server == 'exit 17'
                            else f'Server on port {failing} did not become ready')
                self.assertIn(expected, self.log.read())
                self.assertFalse(marker.exists())
                self.wait_for(lambda: not self.listening(ready))

    def test_sigterm_stops_server_and_running_command(self):
        """Interrupting a ready run reaps the command and stops owned server descendants."""
        port, = self.ports(1)
        marker = self.work / 'command.pid'
        command = (f'import os, pathlib, time; pathlib.Path({str(marker)!r})'
                   '.write_text(str(os.getpid())); time.sleep(60)')
        proc = self.start([(port, self.listener(port))], command)
        self.wait_for(lambda: marker.exists() and bool(marker.read_text()))
        command_pid = int(marker.read_text())
        proc.send_signal(signal.SIGTERM)
        self.assert_exit(proc, 130)
        self.wait_for(lambda: not self.listening(port))
        with self.assertRaises(ProcessLookupError):
            os.kill(command_pid, 0)


if __name__ == '__main__':
    unittest.main()
