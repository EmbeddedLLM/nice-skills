#!/usr/bin/env python3
"""Crash-safe, bounded provider lifecycle. Adapter protocol is in references/provider-lifecycle.md.

This module performs no network I/O itself. Adapters own credential handling and
must return only sanitized job IDs/status, never credentials or signed URLs.
"""
import fcntl
import hashlib
import json
import os
import tempfile
import uuid
from pathlib import Path


def save(path, data):
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.job-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(data, stream, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def advance(path, request, adapter, *, max_attempts, budget, cost_per_attempt):
    """Advance once: submit, recover, or poll. Never automatically retry a submission.

    Money is integer minor units (e.g. cents), reserved pessimistically even for
    failed/unknown jobs. The caller has already obtained authorization for this
    exact request and ceiling. Repeated calls with the same ledger resume it.
    """
    for value in (max_attempts, budget, cost_per_attempt):
        if type(value) is not int or value <= 0:
            raise ValueError('attempts and money limits must be positive integers')
    encoded = json.dumps(request, sort_keys=True, allow_nan=False).encode()
    fingerprint = hashlib.sha256(encoded).hexdigest()
    limits = dict(max_attempts=max_attempts, budget=budget, cost_per_attempt=cost_per_attempt)
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(path.suffix + '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = json.loads(path.read_text()) if path.exists() else {
            'version': 1, 'request_sha256': fingerprint, 'limits': limits, 'attempts': []}
        if data['request_sha256'] != fingerprint or data['limits'] != limits:
            raise ValueError('request or approved limits changed; reconcile the existing job first')
        attempts = data['attempts']
        current = attempts[-1] if attempts else None
        if current and current['status'] == 'succeeded':
            return data
        adapter.ensure_ready()  # missing credentials must not consume an attempt
        if current and current['status'] in ('submitting', 'unknown'):
            # A crash after a successful remote submit may precede saving the ID.
            # lookup must reconcile by the persisted idempotency key; None is NOT
            # evidence that resubmission is safe (eventual consistency).
            task_id = adapter.lookup(current['key'])
            if not task_id:
                current['status'] = 'unknown'
                save(path, data)
                raise RuntimeError('submission outcome unknown; reconcile with provider, do not resubmit')
            current.update(task_id=str(task_id), status='pending')
            save(path, data)
        if current and current['status'] == 'pending':
            status = adapter.poll(current['task_id'])
            if status not in ('pending', 'succeeded', 'failed'):
                raise ValueError('adapter returned an unsupported status')
            current['status'] = status
            save(path, data)
            return data
        if len(attempts) >= max_attempts or (len(attempts) + 1) * cost_per_attempt > budget:
            raise RuntimeError('approved attempt or budget ceiling reached')
        current = {'key': str(uuid.uuid4()), 'status': 'submitting', 'reserved_cost': cost_per_attempt}
        attempts.append(current)
        save(path, data)  # persisted BEFORE the potentially billable operation
        try:
            task_id = adapter.submit(request, current['key'])
            if not task_id:
                raise ValueError('provider returned no task ID')
        except BaseException:
            current['status'] = 'unknown'
            save(path, data)
            raise
        current.update(task_id=str(task_id), status='pending')
        save(path, data)
        return data
