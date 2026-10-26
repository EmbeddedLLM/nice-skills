#!/usr/bin/env python3
"""Run a test command with owned local servers (POSIX only).

License: Apache-2.0.
Includes process-group cleanup, inherited logs, occupied-port rejection,
early-exit detection, finite timeouts, and signal handling. See ../SOURCES.md.
"""

import argparse
import math
import os
import signal
import socket
import subprocess
import sys
import time


def listening(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return True
    except OSError:
        return False


def stop_groups(processes):
    # Shell commands can leave children alive after the shell has exited.
    for proc in reversed(processes):
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.monotonic() + 2
    for proc in processes:
        try:
            proc.wait(timeout=max(0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            pass
    for proc in reversed(processes):
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", action="append", required=True,
                        help="Trusted shell command; repeat for multiple servers")
    parser.add_argument("--port", action="append", required=True, type=int,
                        help="Corresponding server's IPv4 localhost port")
    parser.add_argument("--timeout", type=float, default=30,
                        help="Readiness timeout per server in seconds (default: 30)")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if os.name != "posix":
        parser.error("This helper requires POSIX process groups (Linux/macOS)")
    if not command or len(args.server) != len(args.port):
        parser.error("Provide one --port per --server and a command after --")
    if len(set(args.port)) != len(args.port) or any(not 1 <= p <= 65535 for p in args.port):
        parser.error("Ports must be distinct integers from 1 to 65535")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be finite and positive")
    if any(listening(port) for port in args.port):
        parser.error("A requested port is already in use; reuse that server separately")

    processes = []

    def interrupted(signum, frame):
        raise KeyboardInterrupt

    previous_handlers = {sig: signal.signal(sig, interrupted)
                         for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        for server, port in zip(args.server, args.port):
            print(f"Starting server on port {port}", flush=True)
            # Inherit logs so noisy children cannot fill an unread PIPE.
            proc = subprocess.Popen(server, shell=True, start_new_session=True)
            processes.append(proc)
            deadline = time.monotonic() + args.timeout
            while True:
                if any(item.poll() is not None for item in processes):
                    raise RuntimeError("A server exited before readiness")
                if listening(port):
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"Server on port {port} did not become ready")
                time.sleep(0.05)
        test = subprocess.Popen(command, start_new_session=True)
        processes.append(test)
        result = test.wait()
        return result if result >= 0 else 128 - result
    except KeyboardInterrupt:
        return 130
    except (OSError, RuntimeError) as exc:
        print(f"with_server: {exc}", file=sys.stderr)
        return 1
    finally:
        # A second signal must not interrupt process cleanup.
        for sig in previous_handlers:
            signal.signal(sig, signal.SIG_IGN)
        stop_groups(processes)
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)


if __name__ == "__main__":
    sys.exit(main())
