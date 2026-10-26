#!/usr/bin/env python3
"""Accept revisions through LibreOffice in an isolated temporary copy.

Requires LibreOffice Writer; uses its revision engine and may alter formatting.
Timeout is failure. Inspect/render the resulting document before delivery.
"""
import argparse
from pathlib import Path
import shutil
import tempfile
import zipfile
import defusedxml.ElementTree as ET
from office.soffice import run_soffice

ACCEPT_CHANGES_MACRO = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">
<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Module1" script:language="StarBasic">
    Sub AcceptAllTrackedChanges()
        Dim document As Object
        Dim dispatcher As Object

        document = ThisComponent.CurrentController.Frame
        dispatcher = createUnoService("com.sun.star.frame.DispatchHelper")

        dispatcher.executeDispatch(document, ".uno:AcceptAllTrackedChanges", "", 0, Array())
        ThisComponent.store()
        ThisComponent.close(True)
    End Sub
</script:module>"""



def accept_changes(source, output, timeout=60):
    source, output = Path(source), Path(output)
    if source.suffix.lower() != '.docx' or output.suffix.lower() != '.docx':
        raise ValueError('Input and output must be .docx')
    if output.exists() or output.is_symlink():
        raise ValueError('Choose a new output path')
    with tempfile.TemporaryDirectory(prefix='docx-accept-') as tmp:
        work = Path(tmp)
        staged = work/'document.docx'
        shutil.copyfile(source, staged)
        profile = work/'profile'
        env_arg = f'-env:UserInstallation={profile.as_uri()}'
        run_soffice([env_arg, '--headless', '--terminate_after_init'],
                    timeout=timeout, check=True)
        macro_dir = profile/'user/basic/Standard'
        if not macro_dir.is_dir():
            raise RuntimeError('LibreOffice did not initialize its Basic library')
        (macro_dir/'Module1.xba').write_text(ACCEPT_CHANGES_MACRO, encoding='utf-8')
        run_soffice([env_arg, '--headless', '--norestore', str(staged),
                    'vnd.sun.star.script:Standard.Module1.AcceptAllTrackedChanges?language=Basic&location=application'],
                    timeout=timeout, check=True)
        w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        revision_tags = {w+n for n in ('ins','del','moveFrom','moveTo','moveFromRangeStart',
            'moveFromRangeEnd','moveToRangeStart','moveToRangeEnd','cellIns','cellDel','cellMerge')}
        with zipfile.ZipFile(staged) as archive:
            for name in archive.namelist():
                if name.startswith('word/') and name.endswith('.xml'):
                    root = ET.fromstring(archive.read(name))
                    if any(e.tag in revision_tags or (e.tag.startswith(w) and e.tag.endswith('PrChange')) for e in root.iter()):
                        raise RuntimeError(f'Revisions remain in {name}; output not published')
        with output.open('xb') as target, staged.open('rb') as stream:
            shutil.copyfileobj(stream, target)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--timeout', type=float, default=60)
    a = p.parse_args()
    import math
    if not math.isfinite(a.timeout) or a.timeout <= 0:
        p.error('--timeout must be finite and positive')
    try:
        accept_changes(a.input, a.output, a.timeout)
    except Exception as exc:
        p.exit(1, f'Error: {exc}\n')
    print(f'Accepted revisions: {a.output}')


if __name__ == '__main__':
    main()
