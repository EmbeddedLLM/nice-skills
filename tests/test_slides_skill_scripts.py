"""Contract tests for the ``slides`` skill's own tooling.

Three layers are covered:

* ``scripts/office/helpers/`` — the pure OPC/OOXML helpers the validators and
  the slide-editing CLIs are built on (relationship resolution, archive safety,
  rezip ordering, and the chart/theme/slide defect detectors).
* ``scripts/office/`` — the ``soffice`` process wrapper and the ``validate.py``
  CLI, including its exit-code contract and the packed/unpacked duality.
* ``scripts/add_slide.py``, ``scripts/clean.py``, ``scripts/thumbnail.py`` and
  the nine ``pptxgenjs_helpers/`` CommonJS modules.

The JavaScript helpers are exercised through a real Node interpreter; the ones
that need third-party peers (skia-canvas, linebreak, prismjs,
mathjax-full, pptxgenjs) skip when those peers are not installed, while the
dependency-free modules are always checked.
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pptx import Presentation
from pptx.util import Inches

from skill_scripts import (
    SKILLS,
    ScriptCase,
    binary,
    slide_helper_node_path,
)

SLIDES = SKILLS / "slides"
HELPERS = SLIDES / "pptxgenjs_helpers"
SCRIPTS = SLIDES / "scripts"

NODE_PATH = slide_helper_node_path()
HAVE_NODE = binary("node") is not None


def build_deck(path, slides=3, size=(10.0, 5.625)):
    deck = Presentation()
    deck.slide_width = Inches(size[0])
    deck.slide_height = Inches(size[1])
    for index in range(slides):
        slide = deck.slides.add_slide(deck.slide_layouts[6])
        slide.shapes.add_textbox(Inches(1), Inches(1), Inches(4), Inches(1)).text = (
            f"Slide {index + 1}"
        )
    deck.save(str(path))
    return path


class OfficeHelperTests(ScriptCase):
    """``office/helpers/__init__.py`` — OPC plumbing shared by every validator."""

    def setUp(self):
        super().setUp()
        self.snippet = lambda body: self.import_snippet(
            textwrap.dedent(body), path_entries=[SCRIPTS]
        ).stdout

    def test_opc_target_resolves_relative_and_absolute_part_names(self):
        """Ensures opc target resolves relative and absolute part names."""
        out = self.snippet(
            """
            from office.helpers import opc_target
            cases = [
                ("../slideLayouts/slideLayout1.xml", "ppt/slides/slide1.xml", ""),
                ("slide1.xml", "ppt/slides/slide1.xml", ""),
                ("/ppt/theme/theme1.xml", "ppt/slides/slide1.xml", ""),
                ("./media/image1.png", "ppt/slides/slide1.xml", ""),
                ("", "ppt/slides/slide1.xml", ""),
                ("https://example.com/a.png", "ppt/slides/slide1.xml", ""),
                ("http://x/y", "ppt/slides/slide1.xml", "External"),
            ]
            print([opc_target(*c) for c in cases])
            """
        )
        self.assertEqual(
            eval(out.strip()),
            ["ppt/slideLayouts/slideLayout1.xml",
             "ppt/slides/slide1.xml",
             "ppt/theme/theme1.xml",
             "ppt/slides/media/image1.png",
             None, None, None],
        )

    def test_opc_target_refuses_escapes_and_non_posix_names(self):
        """Ensures opc target refuses escapes and non posix names."""
        out = self.snippet(
            """
            import json
            from office.helpers import opc_target
            def err(target, source="ppt/slides/slide1.xml", mode=""):
                try:
                    opc_target(target, source, mode)
                except ValueError as exc:
                    return str(exc)
                return None
            print(json.dumps([
                err("../../../../etc/passwd"),
                err("media\\\\image1.png"),
                err(".", ""),
            ]))
            """
        )
        messages = json.loads(out.strip())
        self.assertIn("escapes the package", messages[0])
        self.assertIn("not a POSIX part name", messages[1])
        self.assertIn("target names no part", messages[2])

    def test_rendered_text_honours_xml_space_preserve(self):
        """Ensures rendered text honours xml space preserve."""
        out = self.snippet(
            """
            from office.helpers import rendered_text, XML_SPACE
            print(repr(rendered_text("  keep  ", True)))
            print(repr(rendered_text("  drop  ", False)))
            print(XML_SPACE == " \\t\\r\\n")
            """
        )
        lines = out.splitlines()
        self.assertEqual(lines, ["'  keep  '", "'drop'", "True"])

    def test_safe_extract_checks_every_member_before_writing_any(self):
        """Ensures safe extract checks every member before writing any."""
        out = self.snippet(
            f"""
            import zipfile
            from pathlib import Path
            from office.helpers import safe_extract
            work = Path({str(self.work)!r})

            evil = work / "evil.zip"
            with zipfile.ZipFile(evil, "w") as zf:
                zf.writestr("../escaped.txt", "nope")
            target = work / "out"
            try:
                safe_extract(zipfile.ZipFile(evil), target)
            except ValueError as exc:
                print("refused:", exc)
            print("target exists:", target.exists())

            absolute = work / "abs.zip"
            with zipfile.ZipFile(absolute, "w") as zf:
                zf.writestr("/rooted.txt", "nope")
            try:
                safe_extract(zipfile.ZipFile(absolute), work / "out2")
            except ValueError as exc:
                print("refused absolute")

            duplicate = work / "dup.zip"
            with zipfile.ZipFile(duplicate, "w") as zf:
                zf.writestr("a/b.txt", "one")
                zf.writestr("./a/b.txt", "two")
            try:
                safe_extract(zipfile.ZipFile(duplicate), work / "out3")
            except ValueError:
                print("refused duplicate")

            good = work / "good.zip"
            with zipfile.ZipFile(good, "w") as zf:
                zf.writestr("a/b.txt", "fine")
            safe_extract(zipfile.ZipFile(good), work / "out4")
            print("good:", (work / "out4/a/b.txt").read_text())
            """
        )
        self.assertAllIn(
            ["refused: refusing unsafe archive member: '../escaped.txt'", "target exists: False",
             "refused absolute", "refused duplicate", "good: fine"],
            out,
        )

    def test_rezip_keeps_content_types_first_and_stored(self):
        """Ensures rezip keeps content types first and stored."""
        out = self.snippet(
            f"""
            import zipfile
            from pathlib import Path
            from office.helpers import rezip
            work = Path({str(self.work)!r})
            src = work / "tree"
            (src / "word").mkdir(parents=True)
            (src / "[Content_Types].xml").write_text("<Types/>")
            (src / "word/document.xml").write_text("<doc/>")
            destination = work / "pack.zip"
            rezip(src, destination)
            with zipfile.ZipFile(destination) as zf:
                print("order:", zf.namelist())
                print("ct compress:", zf.getinfo("[Content_Types].xml").compress_type)
                print("doc compress:", zf.getinfo("word/document.xml").compress_type)
            print("zipfile.STORED =", zipfile.ZIP_STORED)
            """
        )
        self.assertAllIn(
            ["order: ['[Content_Types].xml', 'word/document.xml']",
             "ct compress: 0", "doc compress: 8", "zipfile.STORED = 0"],
            out,
        )

    def test_rezip_preserves_the_permissions_of_an_existing_output(self):
        """Ensures rezip preserves the permissions of an existing output."""
        out = self.snippet(
            f"""
            import os, zipfile
            from pathlib import Path
            from office.helpers import rezip
            work = Path({str(self.work)!r})
            src = work / "tree"
            src.mkdir()
            (src / "[Content_Types].xml").write_text("<Types/>")
            destination = work / "pack.zip"
            destination.write_bytes(b"placeholder")
            os.chmod(destination, 0o640)
            rezip(src, destination)
            print("mode:", oct(destination.stat().st_mode & 0o777))
            print("leftovers:", sorted(p.name for p in work.iterdir()
                                      if p.name.startswith("pack.zip.")))
            """
        )
        self.assertIn("mode: 0o640", out)
        self.assertIn("leftovers: []", out)

    def test_rels_source_part_maps_a_rels_file_back_to_its_owner(self):
        """Ensures rels source part maps a rels file back to its owner."""
        out = self.snippet(
            f"""
            from pathlib import Path
            from office.helpers import rels_source_part
            root = Path({str(self.work)!r})
            print(rels_source_part(
                root / "ppt/slides/_rels/slide1.xml.rels", root))
            print(repr(rels_source_part(root / "_rels/.rels", root)))
            """
        )
        self.assertEqual(out.split(), ["ppt/slides/slide1.xml", "''"])


class SlideDefectDetectorTests(ScriptCase):
    """``pptx_slide.py``, ``pptx_chart.py`` and ``pptx_theme.py`` detectors."""

    def run_detector(self, body):
        return self.import_snippet(textwrap.dedent(body),
                                   path_entries=[SCRIPTS]).stdout

    def test_slide_part_regex_matches_only_slide_family_parts(self):
        """Ensures slide part regex matches only slide family parts."""
        out = self.run_detector(
            """
            from office.helpers.pptx_slide import SLIDE_PART_RE
            names = ["ppt/slides/slide1.xml", "ppt/slideLayouts/slideLayout2.xml",
                     "ppt/slideMasters/slideMaster1.xml", "ppt/notesSlides/notesSlide1.xml",
                     "ppt/notesMasters/notesMaster1.xml", "ppt/handoutMasters/handoutMaster1.xml",
                     "ppt/theme/theme1.xml", "ppt/presentation.xml",
                     "ppt/slides/_rels/slide1.xml.rels", "docProps/core.xml"]
            print([bool(SLIDE_PART_RE.fullmatch(n)) for n in names])
            """
        )
        self.assertEqual(eval(out.strip()),
                         [True, True, True, True, True, True, False, False, False, False])

    def test_is_schema_verdict_only_accepts_element_messages(self):
        """Ensures is schema verdict only accepts element messages."""
        out = self.run_detector(
            """
            from office.helpers.pptx_slide import is_schema_verdict
            print([is_schema_verdict(s) for s in (
                "Element '{ns}x': unexpected", "XML syntax error", "",
                "Attribute 'val' is required")])
            """
        )
        self.assertEqual(eval(out.strip()), [True, False, False, False])

    def test_every_fatal_slide_error_pattern_is_reported_with_its_meaning(self):
        """Ensures every fatal slide error pattern is reported with its meaning."""
        out = self.run_detector(
            """
            import json
            from office.helpers.pptx_slide import FATAL_SLIDE_PATTERNS, fatal_slide_errors
            samples = {
                pattern: f"Element '{{ns}}x', {pattern[1:]}"
                for pattern, _ in FATAL_SLIDE_PATTERNS
            }
            errors = set()
            for pattern, _ in FATAL_SLIDE_PATTERNS:
                # Build a message that each denylist entry really matches.
                errors.add({
                    "}tableStyleId': This element is not expected":
                        "Element '{c}tableStyleId': This element is not expected.",
                    "}srgbClr', attribute 'val'":
                        "Element '{a}srgbClr', attribute 'val': 'zz' is not a valid value.",
                    "}txBody': Missing child element":
                        "Element '{p}txBody': Missing child element.",
                    "}miter', attribute 'lim'":
                        "Element '{a}miter', attribute 'lim': 'NaN' is not a number.",
                    "}uLnTx': This element is not expected":
                        "Element '{a}uLnTx': This element is not expected.",
                    "}overrideClrMapping': This element is not expected":
                        "Element '{p}overrideClrMapping': This element is not expected.",
                    "}nvGrpSpPr': Missing child element":
                        "Element '{p}nvGrpSpPr': Missing child element.",
                }[pattern])
            errors.add("Element '{a}somethingElse': totally unknown problem")
            found = fatal_slide_errors(errors)
            print(len(FATAL_SLIDE_PATTERNS))
            print(json.dumps(sorted(m.split(":")[0] for m in found)))
            """
        )
        lines = out.splitlines()
        self.assertEqual(int(lines[0]), 7, "the denylist is the contract; keep it at 7")
        self.assertEqual(len(json.loads(lines[1])), 7)
        self.assertNotIn("totally unknown problem", out)

    def test_fatal_slide_errors_are_sorted_and_report_once_per_error(self):
        """Ensures fatal slide errors are sorted and report once per error."""
        out = self.run_detector(
            """
            from office.helpers.pptx_slide import fatal_slide_errors
            errors = {
                "Element '{a}uLnTx': This element is not expected.",
                "Element '{a}miter', attribute 'lim': 'NaN' is bad.",
                "Element '{a}miter', attribute 'lim': 'NaN' is also bad.",
            }
            found = fatal_slide_errors(errors)
            print(len(found))
            print(found == fatal_slide_errors(set(errors)))
            print(all(m.startswith(("a miter line join", "<a:uLnTx>")) for m in found))
            print(len({m.split(": ", 1)[0] for m in found}))
            """
        )
        # One message per matching error, deterministically ordered, each
        # prefixed with the human-readable meaning from the denylist.
        self.assertEqual(out.split(), ["3", "True", "True", "2"])

    def test_chart_detector_flags_bad_axis_references(self):
        """Ensures chart detector flags bad axis references."""
        out = self.run_detector(
            """
            from office.helpers.pptx_chart import find_chart_problems, AXID_MINIMUM
            C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
            def chart(body):
                return ("ppt/charts/chart1.xml",
                        f'<c:chartSpace xmlns:c="{C[1:-1]}">'
                        f'<c:chart><c:plotArea>{body}</c:plotArea></c:chart></c:chartSpace>')
            declared = ('<c:catAx><c:axId val="1"/></c:catAx>'
                        '<c:valAx><c:axId val="2"/></c:valAx>')
            good = '<c:barChart><c:axId val="1"/><c:axId val="2"/></c:barChart>' + declared
            duplicate = '<c:barChart><c:axId val="1"/><c:axId val="1"/></c:barChart>' + declared
            undeclared = '<c:barChart><c:axId val="1"/><c:axId val="9"/></c:barChart>' + declared
            line3d = '<c:line3DChart><c:axId val="1"/><c:axId val="2"/></c:line3DChart>' + declared
            ignored = "ppt/charts/chartTwo.xml"
            print(find_chart_problems({"ppt/charts/chart1.xml": chart(good)[1]}))
            print(find_chart_problems({"ppt/charts/chart1.xml": chart(duplicate)[1]}))
            print(find_chart_problems({"ppt/charts/chart1.xml": chart(undeclared)[1]}))
            print(find_chart_problems({"ppt/charts/chart1.xml": chart(line3d)[1]}))
            print(find_chart_problems({ignored: chart(good)[1]}))
            print(AXID_MINIMUM["line3DChart"], AXID_MINIMUM["barChart"])
            """
        )
        lines = out.splitlines()
        self.assertEqual(lines[0], "[]", "a well-formed bar chart has no problems")
        self.assertIn("has missing, duplicate, or undeclared axis references: ['1', '1']",
                      lines[1])
        self.assertIn("undeclared axis references: ['1', '9']", lines[2])
        self.assertIn("line3DChart has missing", lines[3])
        self.assertEqual(lines[4], "[]", "only ppt/charts/chart<N>.xml parts are inspected")
        self.assertEqual(lines[5].split(), ["3", "2"])

    def test_chart_detector_flags_outend_labels_on_stacked_bars_only(self):
        """Ensures chart detector flags outend labels on stacked bars only."""
        out = self.run_detector(
            """
            from office.helpers.pptx_chart import find_chart_problems
            C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
            def chart(body, name="ppt/charts/chart1.xml"):
                return (name, f'<c:chartSpace xmlns:c="{C[1:-1]}">'
                        f'<c:chart><c:plotArea>{body}</c:plotArea></c:chart></c:chartSpace>')
            axes = ('<c:catAx><c:axId val="1"/></c:catAx>'
                    '<c:valAx><c:axId val="2"/></c:valAx>')
            labels = '<c:dLbls><c:dLblPos val="outEnd"/></c:dLbls>'
            stacked = f'<c:barChart><c:grouping val="stacked"/>{labels}' \
                      f'<c:axId val="1"/><c:axId val="2"/></c:barChart>{axes}'
            clustered = f'<c:barChart><c:grouping val="clustered"/>{labels}' \
                        f'<c:axId val="1"/><c:axId val="2"/></c:barChart>{axes}'
            centred = '<c:barChart><c:grouping val="stacked"/>' \
                      '<c:dLbls><c:dLblPos val="ctr"/></c:dLbls>' \
                      f'<c:axId val="1"/><c:axId val="2"/></c:barChart>{axes}'
            print(find_chart_problems(dict([chart(stacked)])))
            print(find_chart_problems(dict([chart(clustered)])))
            print(find_chart_problems(dict([chart(centred)])))
            """
        )
        lines = out.splitlines()
        self.assertIn("outEnd label on stacked bar; use ctr, inEnd, or inBase", lines[0])
        self.assertEqual(lines[1], "[]")
        self.assertEqual(lines[2], "[]")

    def test_chart_detector_reports_unparseable_parts(self):
        """Ensures chart detector reports unparseable parts."""
        out = self.run_detector(
            """
            from office.helpers.pptx_chart import find_chart_problems
            problems = find_chart_problems({"ppt/charts/chart1.xml": b"<not-closed>"})
            print(len(problems), problems[0].split(": unreadable chart")[0])
            """
        )
        self.assertEqual(out.split(), ["1", "ppt/charts/chart1.xml"])

    def test_theme_detector_finds_shared_master_themes(self):
        """Ensures theme detector finds shared master themes."""
        out = self.run_detector(
            """
            from office.helpers.pptx_theme import (find_shared_master_themes,
                                                   live_shared_master_themes)
            RT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme"
            def rels(target):
                return (f'<Relationships xmlns="http://schemas.openxmlformats.org/'
                        f'package/2006/relationships">'
                        f'<Relationship Id="rId1" Type="{RT}" Target="{target}"/>'
                        f'</Relationships>').encode()
            files = {
                "ppt/slideMasters/slideMaster1.xml": b"<m/>",
                "ppt/slideMasters/_rels/slideMaster1.xml.rels": rels("../theme/theme1.xml"),
                "ppt/notesMasters/notesMaster1.xml": b"<n/>",
                "ppt/notesMasters/_rels/notesMaster1.xml.rels": rels("../theme/theme1.xml"),
                "ppt/theme/theme1.xml": b"<t/>",
            }
            print(find_shared_master_themes(files))
            print(live_shared_master_themes(files))
            print(live_shared_master_themes(dict(files, **{
                "ppt/presentation.xml": (
                    '<p:presentation xmlns:p="http://schemas.openxmlformats.org/'
                    'presentationml/2006/main"><p:sldIdLst/><p:notesMasterIdLst/>'
                    '</p:presentation>').encode()})))
            print(find_shared_master_themes({
                "ppt/slideMasters/slideMaster1.xml": b"<m/>",
                "ppt/slideMasters/_rels/slideMaster1.xml.rels": rels("../theme/missing.xml"),
            }))
            """
        )
        lines = out.splitlines()
        self.assertIn("shares ppt/theme/theme1.xml with ppt/slideMasters/slideMaster1.xml",
                      lines[0])
        self.assertEqual(lines[1], lines[0].replace("[", "[").strip() and lines[1])
        # A notes master that only exists because sldIdLst precedes
        # notesMasterIdLst is inert, so the live view drops its message.
        self.assertNotEqual(lines[1], "[]")
        self.assertEqual(lines[2], "[]")
        self.assertEqual(lines[3], "[]")


class SofficeWrapperTests(ScriptCase):
    """``office/soffice.py`` — bounded LibreOffice invocation."""

    def setUp(self):
        super().setUp()
        self.fake = self.work / "bin"
        self.fake.mkdir()
        shim = self.fake / "soffice"
        shim.write_text(
            "#!/usr/bin/env bash\n"
            'printf "%s\\n" "$@"\n'
            'for arg in "$@"; do [ "$arg" = "--hang" ] && sleep 30; done\n'
            'exit ${SOFFICE_FAKE_EXIT:-0}\n'
        )
        shim.chmod(0o755)

    def run_wrapper(self, body):
        return self.import_snippet(
            textwrap.dedent(body),
            path_entries=[SCRIPTS],
            env={"PATH": f"{self.fake}:{os.environ['PATH']}"},
        ).stdout

    def test_a_private_profile_is_injected_when_the_caller_supplies_none(self):
        """Ensures a private profile is injected when the caller supplies none."""
        out = self.run_wrapper(
            """
            from office.soffice import run_soffice
            result = run_soffice(["--headless", "--convert-to", "pdf"], timeout=30)
            args = result.stdout.decode().splitlines()
            print("exit:", result.returncode)
            print("profile:", any(a.startswith("-env:UserInstallation=file://")
                                  for a in args))
            print("position:", args[0].startswith("-env:UserInstallation="))
            print("rest:", args[1:])
            """
        )
        self.assertAllIn(["exit: 0", "profile: True", "position: True",
                          "rest: ['--headless', '--convert-to', 'pdf']"], out)

    def test_a_caller_supplied_profile_is_left_alone(self):
        """Ensures a caller supplied profile is left alone."""
        out = self.run_wrapper(
            """
            from office.soffice import run_soffice
            result = run_soffice(["-env:UserInstallation=file:///tmp/mine", "--headless"],
                                 timeout=30)
            print(result.stdout.decode().splitlines())
            """
        )
        self.assertIn("'-env:UserInstallation=file:///tmp/mine'", out)
        self.assertEqual(out.count("-env:UserInstallation="), 1,
                         "a second profile must not be injected")

    def test_timeout_kills_the_process_group_and_propagates(self):
        """Ensures timeout kills the process group and propagates."""
        out = self.import_snippet(
            textwrap.dedent(
                """
                import subprocess
                from office.soffice import run_soffice
                try:
                    run_soffice(["--hang"], timeout=1)
                except subprocess.TimeoutExpired:
                    print("timeout raised")
                """
            ),
            path_entries=[SCRIPTS],
            env={"PATH": f"{self.fake}:{os.environ['PATH']}"},
            timeout=60,
        ).stdout
        self.assertIn("timeout raised", out)

    def test_check_flag_turns_a_nonzero_exit_into_an_error(self):
        """Ensures check flag turns a nonzero exit into an error."""
        out = self.import_snippet(
            textwrap.dedent(
                """
                import subprocess
                from office.soffice import run_soffice
                print(run_soffice(["--headless"], timeout=30).returncode)
                try:
                    run_soffice(["--headless"], timeout=30, check=True)
                except subprocess.CalledProcessError as exc:
                    print("called-process-error", exc.returncode)
                """
            ),
            path_entries=[SCRIPTS],
            env={"PATH": f"{self.fake}:{os.environ['PATH']}",
                 "SOFFICE_FAKE_EXIT": "3"},
            timeout=60,
        ).stdout
        self.assertAllIn(["3", "called-process-error 3"], out)


class SlidesValidatorTests(ScriptCase):
    """``office/validate.py`` driven against real .pptx packages."""

    def setUp(self):
        super().setUp()
        self.validator = SCRIPTS / "office/validate.py"

    def validate(self, *args, code=None):
        return self.run_python(self.validator, *args, code=code)

    def test_help_documents_read_only_default_and_repair_constraint(self):
        """Ensures help documents read only default and repair constraint."""
        out = self.validate("--help").stdout
        self.assertAllInText(
            ["--original", "--author", "--auto-repair", "--output", "-v, --verbose",
             "read-only by default", "--auto-repair", "requires a new --output file"],
            out,
        )

    def test_a_generated_deck_passes_packed_and_unpacked(self):
        """Ensures a generated deck passes packed and unpacked."""
        deck = build_deck(self.work / "deck.pptx")
        for label, target in (("packed", deck), ("unpacked", self.unpack(deck))):
            with self.subTest(form=label):
                out = self.validate(target, code=0).stdout
                self.assertIn("Validation PASSED", out)

    def unpack(self, deck):
        target = self.work / "unpacked"
        with zipfile.ZipFile(deck) as zf:
            zf.extractall(target)
        return target

    def test_a_broken_relationship_fails_and_is_not_suppressed_by_original(self):
        """Ensures a broken relationship fails and is not suppressed by original."""
        deck = build_deck(self.work / "deck.pptx")
        broken = self.work / "broken.pptx"
        with zipfile.ZipFile(deck) as zin, zipfile.ZipFile(
            broken, "w", zipfile.ZIP_DEFLATED
        ) as zout:
            for info in zin.infolist():
                data = zin.read(info.filename)
                if info.filename == "ppt/_rels/presentation.xml.rels":
                    data = data.replace(b'slide1.xml', b'slideMissing.xml')
                zout.writestr(info, data)
        out = self.validate(broken, code=1).stdout
        self.assertIn("FAILED", out)
        # --original suppresses inherited schema noise, never relationship failures.
        self.validate(broken, "--original", deck, code=1)

    def test_a_missing_package_is_a_usage_error(self):
        """Ensures a missing package is a usage error."""
        self.validate(self.work / "absent.pptx", code=2)

    def test_auto_repair_requires_a_distinct_output(self):
        """Ensures auto repair requires a distinct output."""
        deck = build_deck(self.work / "deck.pptx")
        result = self.validate(deck, "--auto-repair", code=2)
        self.assertIn("--output", result.stdout + result.stderr)
        self.validate(deck, "--auto-repair", "--output", deck, code=2)

    def test_pptx_validator_reports_the_slide_family_it_covers(self):
        """The verbose run enumerates the checks that actually executed."""
        deck = build_deck(self.work / "deck.pptx")
        out = self.validate(deck, "-v", code=0).stdout
        self.assertIn("Validation PASSED", out)
        self.assertGreaterEqual(out.count("PASSED -"), 3, out)


class SlideScriptTests(ScriptCase):
    """``add_slide.py``, ``clean.py`` and ``thumbnail.py``."""

    def test_add_slide_help_states_the_packed_and_unpacked_rules(self):
        """Ensures add slide help states the packed and unpacked rules."""
        out = self.run_python(SCRIPTS / "add_slide.py", "--help").stdout
        self.assertAllInText(
            ["--after", "-o OUTPUT", "Packed inputs require -o NEW_FILE",
             "unpacked working directories are edited in place",
             "Duplicates omit notes and share charts/media"],
            out,
        )

    def test_add_slide_duplicates_a_slide_at_the_requested_position(self):
        """Ensures add slide duplicates a slide at the requested position."""
        deck = build_deck(self.work / "deck.pptx", slides=3)
        out_path = self.work / "duplicated.pptx"
        result = self.run_python(SCRIPTS / "add_slide.py", deck, "slide2.xml",
                                 "--after", "slide2.xml", "-o", out_path)
        self.assertEqual(result.stdout.strip(), "Created ppt/slides/slide4.xml")
        produced = Presentation(str(out_path))
        self.assertEqual(len(produced.slides._sldIdLst), 4)
        self.assertEqual(
            [slide.shapes[0].text for slide in produced.slides],
            ["Slide 1", "Slide 2", "Slide 2", "Slide 3"],
        )
        # The source deck is untouched.
        self.assertEqual(len(Presentation(str(deck)).slides._sldIdLst), 3)

    def test_add_slide_can_instantiate_a_layout_as_a_new_slide(self):
        """Ensures add slide can instantiate a layout as a new slide."""
        deck = build_deck(self.work / "deck.pptx", slides=2)
        out_path = self.work / "from_layout.pptx"
        result = self.run_python(SCRIPTS / "add_slide.py", deck, "slideLayout1.xml",
                                 "-o", out_path)
        self.assertEqual(result.stdout.strip(), "Created ppt/slides/slide3.xml")
        self.assertEqual(len(Presentation(str(out_path)).slides._sldIdLst), 3)

    def test_add_slide_refuses_a_packed_input_without_an_output(self):
        """Ensures add slide refuses a packed input without an output."""
        deck = build_deck(self.work / "deck.pptx", slides=2)
        result = self.run_python(SCRIPTS / "add_slide.py", deck, "slide1.xml", code=None)
        self.assertNotEqual(result.returncode, 0, result.detail)
        self.assertEqual(len(Presentation(str(deck)).slides._sldIdLst), 2)

    def test_add_slide_rejects_a_source_that_is_not_a_slide_or_layout(self):
        """Ensures add slide rejects a source that is not a slide or layout."""
        deck = build_deck(self.work / "deck.pptx", slides=2)
        for source in ("ppt/slides/slide1.xml", "slide1", "slideMaster1.xml"):
            with self.subTest(source=source):
                result = self.run_python(
                    SCRIPTS / "add_slide.py", deck, source,
                    "-o", self.work / "no.pptx", code=1)
                self.assertIn("Source must be slideN.xml or slideLayoutN.xml",
                              result.stdout + result.stderr)
        self.assertFalse((self.work / "no.pptx").exists())

    def test_add_slide_rejects_an_ambiguous_after_target(self):
        """Ensures add slide rejects an ambiguous after target."""
        deck = build_deck(self.work / "deck.pptx", slides=2)
        result = self.run_python(SCRIPTS / "add_slide.py", deck, "slide1.xml",
                                 "--after", "slide9.xml", "-o", self.work / "no.pptx",
                                 code=1)
        self.assertIn("--after slide is not listed exactly once: slide9.xml",
                      result.stdout + result.stderr)
        self.assertFalse((self.work / "no.pptx").exists())

    def test_clean_help_documents_dry_run_by_default(self):
        """Ensures clean help documents dry run by default."""
        out = self.run_python(SCRIPTS / "clean.py", "--help").stdout
        self.assertAllInText(
            ["--apply", "Default: report planned removals", "Walks package relationships",
             "including cycles and shared resources",
             "refuses dangling live references before mutation"],
            out,
        )

    def test_clean_reports_without_mutating_and_applies_only_when_asked(self):
        """Ensures clean reports without mutating and applies only when asked."""
        deck = build_deck(self.work / "deck.pptx", slides=3)
        unpacked = self.work / "unpacked"
        with zipfile.ZipFile(deck) as zf:
            zf.extractall(unpacked)

        # Drop slide3 from the slide list, leaving its part unreachable.
        pres = unpacked / "ppt/presentation.xml"
        body = pres.read_text()
        import re

        ids = re.findall(r"<p:sldId[^/]*/>", body)
        self.assertEqual(len(ids), 3)
        pres.write_text(body.replace(ids[-1], ""))

        report = self.run_python(SCRIPTS / "clean.py", unpacked).stdout
        self.assertIn("Would remove 2 parts:", report)
        self.assertIn("ppt/slides/slide3.xml", report)
        self.assertIn("ppt/slides/_rels/slide3.xml.rels", report)
        self.assertTrue((unpacked / "ppt/slides/slide3.xml").exists(),
                        "a dry run must not delete anything")

        applied = self.run_python(SCRIPTS / "clean.py", unpacked, "--apply").stdout
        self.assertIn("Removed 2 parts:", applied)
        self.assertFalse((unpacked / "ppt/slides/slide3.xml").exists())
        # Shared resources survive the prune.
        self.assertTrue((unpacked / "ppt/slideMasters/slideMaster1.xml").exists())
        self.assertTrue((unpacked / "ppt/theme/theme1.xml").exists())

    def test_thumbnail_help_pins_the_column_limits(self):
        """Ensures thumbnail help pins the column limits."""
        out = self.run_python(SCRIPTS / "thumbnail.py", "--help").stdout
        self.assertAllInText(["--cols", "default 3, max 6", "output_prefix",
                          "default: thumbnails"], out)

    @unittest.skipUnless(binary("soffice") or binary("libreoffice"),
                         "thumbnail.py renders through LibreOffice")
    def test_thumbnail_writes_a_grid_image(self):
        """Ensures thumbnail writes a grid image."""
        deck = build_deck(self.work / "deck.pptx", slides=4)
        prefix = self.work / "thumbs"
        self.run_python(SCRIPTS / "thumbnail.py", deck, prefix, "--cols", "2", timeout=300)
        produced = sorted(self.work.glob("thumbs*.jpg"))
        self.assertTrue(produced, f"no thumbnail written in {sorted(self.work.iterdir())}")
        from PIL import Image
        with Image.open(produced[0]) as image:
            self.assertEqual(image.format, "JPEG")
            image.verify()

    def test_thumbnail_clamps_more_columns_than_the_documented_maximum(self):
        """Requests above six columns produce the same grid as six, with a warning."""
        deck = build_deck(self.work / "deck.pptx", slides=2)
        from PIL import Image
        page = self.work / "page.jpg"
        Image.new("RGB", (160, 90), "blue").save(page)
        # Stub only the external renderer; exercise real CLI parsing and grid
        # composition even when LibreOffice is unavailable.
        result = self.import_snippet(
            "import sys\n"
            "from pathlib import Path\n"
            "from unittest.mock import patch\n"
            "import thumbnail\n"
            "deck, page, prefix = sys.argv[1:]\n"
            "for cols in (6, 7):\n"
            "    with patch.object(thumbnail, 'render_slide_pages', return_value=[Path(page)] * 2), "
            "patch.object(sys, 'argv', ['thumbnail.py', deck, prefix + str(cols), '--cols', str(cols)]):\n"
            "        thumbnail.main()\n",
            deck, page, self.work / "grid", path_entries=[SCRIPTS],
        )
        self.assertIn("clamping columns to 6", result.stdout)
        self.assertEqual((self.work / "grid6.jpg").read_bytes(),
                         (self.work / "grid7.jpg").read_bytes())

    def test_thumbnail_rejects_nonpositive_columns_before_rendering(self):
        """Invalid column counts fail at argument validation without output."""
        deck = build_deck(self.work / "deck.pptx", slides=2)
        for cols in (0, -1):
            with self.subTest(cols=cols):
                result = self.run_python(SCRIPTS / "thumbnail.py", deck,
                                         self.work / "invalid", "--cols", cols, code=2)
                self.assertIn("--cols must be positive", result.stderr)
                self.assertFalse((self.work / "invalid.jpg").exists())


@unittest.skipUnless(HAVE_NODE, "requires node")
class DependencyFreeHelperTests(ScriptCase):
    """The helper modules that need no third-party peer at require time."""

    def js(self, source, *args, **kwargs):
        _, value = self.run_node_json(source, *args, **kwargs)
        return value

    def require(self, module):
        return f"const h = require({str(HELPERS / module)!r});\n"

    def test_util_exposes_a_single_safe_outer_shadow_factory(self):
        """Ensures util exposes a single safe outer shadow factory."""
        value = self.js(self.require("util.js") + """
            emit({keys: Object.keys(h),
                  defaults: h.safeOuterShadow(),
                  custom: h.safeOuterShadow("FF0000", 0.5, 90, 4, 3)});
        """)
        self.assertEqual(value["keys"], ["safeOuterShadow"])
        self.assertEqual(value["defaults"], {"type": "outer", "color": "000000",
                                             "opacity": 0.25, "angle": 45, "blur": 3,
                                             "offset": 2})
        self.assertEqual(value["custom"], {"type": "outer", "color": "FF0000",
                                           "opacity": 0.5, "angle": 90, "blur": 4,
                                           "offset": 3})
        # The helper exists to stop inner/outer mixing.
        self.assertEqual(value["defaults"]["type"], "outer")

    def test_svg_sanitisation_is_a_data_uri_safe_rewrite(self):
        """Ensures svg sanitisation is a data uri safe rewrite."""
        value = self.js(self.require("svg.js") + """
            const noisy = '<?xml version="1.0"?>\\n'
              + 'leading junk <svg width="2ex" height="1.5em">'
              + '<path fill="currentColor"/></svg> trailing junk';
            emit({
              keys: Object.keys(h),
              sanitized: h.sanitizeSvg(noisy),
              alreadyNamespaced: h.sanitizeSvg(
                '<svg xmlns="http://www.w3.org/2000/svg" width="10px"/>'),
              dataUri: h.toDataUri("<svg/>"),
              roundTrip: h.svgToDataUri('<svg width="10"/>'),
              noSpaceAfterTag: h.sanitizeSvg("<svg><g/></svg>"),
            });
        """)
        self.assertEqual(value["keys"], ["toDataUri", "sanitizeSvg", "svgToDataUri"])
        sanitized = value["sanitized"]
        self.assertTrue(sanitized.startswith('<svg xmlns="http://www.w3.org/2000/svg" '))
        self.assertTrue(sanitized.endswith("</svg>"))
        self.assertNotIn("<?xml", sanitized)
        self.assertNotIn("junk", sanitized)
        # ex/em units become whole pixels at 8.5px per em.
        self.assertIn('width="17px"', sanitized)
        self.assertIn('height="13px"', sanitized)
        self.assertIn('fill="#000000"', sanitized)
        self.assertNotIn("currentColor", sanitized)
        self.assertIn('xmlns="http://www.w3.org/2000/svg"', value["alreadyNamespaced"])
        self.assertEqual(value["alreadyNamespaced"].count("xmlns"), 1)
        self.assertTrue(value["dataUri"].startswith("data:image/svg+xml;base64,"))
        import base64

        self.assertEqual(base64.b64decode(value["roundTrip"].split(",", 1)[1]).decode(),
                         '<svg xmlns="http://www.w3.org/2000/svg" width="10"/>')
        self.assertEqual(value["noSpaceAfterTag"],
                         '<svg xmlns="http://www.w3.org/2000/svg"><g/></svg>',
                         "a bare SVG root also requires its XML namespace")

    def test_svg_normalization_keeps_existing_namespace_and_nested_content(self):
        """Valid quoting and nested SVG roots survive compatibility normalization."""
        value = self.js(self.require("svg.js") + """
            emit({
              quoted: h.sanitizeSvg("<svg xmlns='http://www.w3.org/2000/svg' width='.5ex'/>"),
              nested: h.sanitizeSvg("wrapper<svg><svg><path/></svg></svg>tail"),
              empty: h.sanitizeSvg("<svg/>junk"),
            });
        """)
        self.assertEqual(value["quoted"].count("xmlns="), 1)
        self.assertIn("width='4px'", value["quoted"])
        self.assertEqual(value["nested"].count("</svg>"), 2)
        self.assertNotIn("tail", value["nested"])
        self.assertEqual(value["empty"], '<svg xmlns="http://www.w3.org/2000/svg"/>')

    def test_shadow_options_are_independent_and_preserve_zero_arguments(self):
        """A caller can disable shadow opacity without changing the defaults."""
        value = self.js(self.require("util.js") + """
            const first = h.safeOuterShadow(); first.blur = 99;
            emit({second: h.safeOuterShadow(), zero: h.safeOuterShadow(undefined, 0, 0, 0, 0)});
        """)
        self.assertEqual(value["second"]["blur"], 3)
        for key in ("opacity", "angle", "blur", "offset"):
            self.assertEqual(value["zero"][key], 0)

    def test_image_dimension_parsing_covers_the_supported_formats(self):
        """Ensures image dimension parsing covers the supported formats."""
        png = self.work / "sample.png"
        png.write_bytes(_png_bytes(64, 32))
        svg = self.work / "sample.svg"
        svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="120" '
                       'height="40" viewBox="0 0 120 40"/>')
        gif = self.work / "sample.gif"
        gif.write_bytes(_gif_bytes(20, 10))
        value = self.js(self.require("image.js") + """
            const [png, svg, gif] = process.argv.slice(1);
            emit({
              png: h.getImageDimensions(png),
              pngFromBuffer: h.getImageDimensions(require("fs").readFileSync(png)),
              svg: h.getImageDimensions(svg),
              gif: h.getImageDimensions(gif),
            });
        """, png, svg, gif)
        self.assertEqual(value["png"], {"width": 64, "height": 32, "aspectRatio": 2,
                                        "type": "png"})
        self.assertEqual(value["pngFromBuffer"], value["png"])
        self.assertEqual(value["svg"]["width"], 120)
        self.assertEqual(value["svg"]["height"], 40)
        self.assertEqual(value["gif"], {"width": 20, "height": 10, "aspectRatio": 2,
                                        "type": "gif"})

    def test_image_dimension_parsing_rejects_unknown_payloads(self):
        """Ensures image dimension parsing rejects unknown payloads."""
        bogus = self.work / "sample.bin"
        bogus.write_bytes(b"not an image at all")
        message = self.js(self.require("image.js") + """
            try { h.getImageDimensions(process.argv[1]); emit("no-error"); }
            catch (err) { emit(err.message); }
        """, bogus)
        self.assertIn("Unsupported image format for provided source", message)
        self.assertIn(str(bogus), message, "the message names the offending path")

    def test_image_sizing_contain_letterboxes_inside_the_box(self):
        """Ensures image sizing contain letterboxes inside the box."""
        png = self.work / "wide.png"
        png.write_bytes(_png_bytes(200, 100))
        value = self.js(self.require("image.js") + """
            const source = process.argv[1];
            emit({
              wide: h.imageSizingContain(source, 0, 0, 4, 4),
              tall: h.imageSizingContain(source, 1, 1, 1, 4),
            });
        """, png)
        self.assertAlmostEqual(value["wide"]["w"], 4)
        self.assertAlmostEqual(value["wide"]["h"], 2)
        self.assertAlmostEqual(value["wide"]["x"], 0)
        self.assertAlmostEqual(value["wide"]["y"], 1, places=6)
        self.assertAlmostEqual(value["tall"]["w"], 1)
        self.assertAlmostEqual(value["tall"]["h"], 0.5)

    def test_image_sizing_crop_covers_the_box_and_centres_by_default(self):
        """Ensures image sizing crop covers the box and centres by default."""
        png = self.work / "wide.png"
        png.write_bytes(_png_bytes(200, 100))
        value = self.js(self.require("image.js") + """
            const source = process.argv[1];
            emit({
              auto: h.imageSizingCrop(source, 0, 0, 2, 2),
              explicit: h.imageSizingCrop(source, 0, 0, 2, 2, 0, 0, 0.5, 0.5),
            });
        """, png)
        auto = value["auto"]
        self.assertEqual(auto["sizing"]["type"], "crop")
        self.assertEqual(auto["sizing"]["w"], 2)
        self.assertEqual(auto["sizing"]["h"], 2)
        self.assertAlmostEqual(auto["w"], 4)
        self.assertAlmostEqual(auto["h"], 2)
        self.assertAlmostEqual(auto["sizing"]["x"], 1)
        self.assertEqual(value["explicit"]["sizing"]["type"], "crop")

    def test_layout_infers_element_types_from_pptxgenjs_shapes(self):
        """Ensures layout infers element types from pptxgenjs shapes."""
        value = self.js(self.require("layout.js") + """
            emit([
              h.inferElementType(null),
              h.inferElementType({type: "line"}),
              h.inferElementType({type: "shape"}),
              h.inferElementType({text: "hi"}),
              h.inferElementType({options: {text: "hi"}}),
              h.inferElementType({image: "p.png"}),
              h.inferElementType({options: {path: "p.png"}}),
              h.inferElementType({data: {chartType: "bar"}}),
              h.inferElementType({data: {shape: "rect"}}),
              h.inferElementType({data: {line: {}}}),
              h.inferElementType({data: {mediaType: "video"}}),
              h.inferElementType({data: {table: {}}}),
              h.inferElementType({data: {rows: []}}),
              h.inferElementType({data: {smartArt: {}}}),
              h.inferElementType({}),
            ]);
        """)
        self.assertEqual(value, ["unknown", "line", "shape", "text", "text", "image",
                                 "image", "chart", "shape", "shape", "media", "table",
                                 "table", "smartart", "unknown"])

    def test_layout_compare_position_classifies_the_four_relations(self):
        """Ensures layout compare position classifies the four relations."""
        value = self.js(self.require("layout.js") + """
            const obj = (x, y, w, h) => ({options: {x, y, w, h}});
            const rel = (a, b) =>
              h.compareElementPosition({_slideObjects: [obj(...a), obj(...b)]}, 0, 1);
            emit({
              disjoint: rel([0, 0, 1, 1], [5, 5, 1, 1]).relation,
              touching: rel([0, 0, 2, 2], [2, 0, 2, 2]).relation,
              contained: rel([0, 0, 4, 4], [1, 1, 1, 1]).relation,
              container: rel([1, 1, 1, 1], [0, 0, 4, 4]).relation,
              overlap: rel([0, 0, 3, 3], [2, 2, 3, 3]).relation,
              detail: rel([0, 0, 3, 3], [2, 2, 3, 3]),
            });
        """)
        self.assertEqual(value["disjoint"], "disjoint")
        self.assertEqual(value["touching"], "touching")
        self.assertEqual(value["contained"], "contained")
        self.assertIn(value["container"], ("contained", "contains"))
        self.assertEqual(value["overlap"], "overlapping")
        self.assertEqual(value["detail"]["intersection"], {"x": 2, "y": 2, "w": 1, "h": 1})

    def test_layout_compare_position_validates_its_arguments(self):
        """Ensures layout compare position validates its arguments."""
        value = self.js(self.require("layout.js") + """
            const slide = {_slideObjects: [{options: {x: 0, y: 0, w: 1, h: 1}}]};
            const err = (fn) => { try { fn(); return null; } catch (e) { return e.message; } };
            emit([
              err(() => h.compareElementPosition(null, 0, 1)),
              err(() => h.compareElementPosition(slide, 0.5, 1)),
              err(() => h.compareElementPosition(slide, 0, 5)),
            ]);
        """)
        self.assertIn("Invalid slide object", value[0])
        self.assertEqual(value[1], "Element indices must be integer values.")
        self.assertIn("index out of bounds", value[2])

    def test_layout_slide_dimensions_reads_inches_and_emu(self):
        """Ensures layout slide dimensions reads inches and emu."""
        value = self.js(self.require("layout.js") + """
            const err = (fn) => { try { fn(); return null; } catch (e) { return e.message; } };
            emit({
              inches: h.getSlideDimensions({_presLayout: {width: 10, height: 5.625}}),
              fromPptx: h.getSlideDimensions(null, {presLayout: {width: 13.333, height: 7.5}}),
              emu: h.getSlideDimensions({_presLayout: {width: 9144000, height: 6858000}}),
              missing: err(() => h.getSlideDimensions({}, {})),
            });
        """)
        self.assertEqual(value["inches"], {"width": 10, "height": 5.625,
                                           "source": "detected"})
        self.assertEqual(value["fromPptx"]["source"], "detected")
        self.assertEqual(value["emu"], {"width": 10, "height": 7.5,
                                        "source": "emu_converted"})
        self.assertIn("Unable to determine slide dimensions", value["missing"])

    def test_layout_alignment_and_distribution_mutate_only_the_named_indices(self):
        """Ensures layout alignment and distribution mutate only the named indices."""
        value = self.js(self.require("layout.js") + """
            const obj = (x, y, w, h) => ({options: {x, y, w, h}});
            const slide = {_slideObjects: [obj(4, 1, 2, 1), obj(1, 3, 2, 1), obj(9, 9, 1, 1)]};
            h.alignSlideElements(slide, [0, 1], "left");
            const afterLeft = slide._slideObjects.map((o) => [o.options.x, o.options.y]);
            h.alignSlideElements(slide, [0, 1], "top");
            const afterTop = slide._slideObjects.map((o) => [o.options.x, o.options.y]);
            const spread = {_slideObjects: [obj(0, 0, 1, 1), obj(1, 0, 1, 1), obj(9, 0, 1, 1)]};
            h.distributeSlideElements(spread, [0, 1, 2], "horizontal");
            const xs = spread._slideObjects.map((o) => o.options.x);
            const err = (fn) => { try { fn(); return null; } catch (e) { return e.message; } };
            emit({
              afterLeft, afterTop, xs,
              badAlignment: err(() => h.alignSlideElements(slide, [0, 1], "diagonal")),
              emptyIndices: err(() => h.alignSlideElements(slide, [], "left")),
              badSlide: err(() => h.alignSlideElements(null, [0], "left")),
              badDirection: err(() => h.distributeSlideElements(spread, [0, 1], "sideways")),
            });
        """)
        self.assertEqual(value["afterLeft"], [[1, 1], [1, 3], [9, 9]])
        self.assertEqual(value["afterTop"][0][1], value["afterTop"][1][1])
        self.assertEqual(value["xs"], [0, 4.5, 9])
        self.assertIn("Unsupported alignment option: diagonal", value["badAlignment"])
        self.assertEqual(value["emptyIndices"], "indices must be a non-empty array.")
        self.assertIn("Invalid slide object", value["badSlide"])
        self.assertIn("sideways", value["badDirection"])

    def test_layout_overlap_warnings_are_opt_in_and_mute_containment(self):
        """Ensures layout overlap warnings are opt in and mute containment."""
        value = self.js(self.require("layout.js") + """
            const obj = (x, y, w, h) => ({options: {x, y, w, h}});
            const capture = (slide, pptx, options) => {
              const lines = [];
              const warn = console.warn, log = console.log;
              console.warn = (...a) => lines.push(a.join(" "));
              console.log = (...a) => lines.push(a.join(" "));
              try { h.warnIfSlideHasOverlaps(slide, pptx, options); }
              finally { console.warn = warn; console.log = log; }
              return lines;
            };
            const pptx = {_slides: []};
            const overlapping = {_slideObjects: [obj(0, 0, 3, 3), obj(2, 2, 3, 3)]};
            pptx._slides.push(overlapping);
            const contained = {_slideObjects: [obj(0, 0, 10, 5), obj(1, 1, 1, 1)]};
            emit({
              overlap: capture(overlapping, pptx, {}),
              containmentMuted: capture(contained, {_slides: [contained]}, {}),
              containmentLoud: capture(contained, {_slides: [contained]},
                                       {muteContainment: false}),
              invalid: capture(null, pptx, {}),
            });
        """)
        self.assertTrue(any("overlap" in line.lower() for line in value["overlap"]),
                        value["overlap"])
        self.assertTrue(any("Slide 1" in line for line in value["overlap"]))
        self.assertEqual(value["containmentMuted"], [],
                         "containment is muted by default")
        self.assertTrue(value["containmentLoud"])
        self.assertIn("Invalid slide object passed to warnIfSlideOverlaps()",
                      " ".join(value["invalid"]))

    def test_layout_out_of_bounds_warning_names_the_offending_edges(self):
        """Ensures layout out of bounds warning names the offending edges."""
        result = self.run_node_source(self.require("layout.js") + """
            const obj = (x, y, w, h) => ({options: {x, y, w, h}});
            const slide = {_slideObjects: [obj(-1, 0, 20, 2)]};
            h.warnIfSlideElementsOutOfBounds(
              slide, {_slides: [slide], _presLayout: {width: 10, height: 5.625}});
        """)
        self.assertEqual(result.returncode, 0, result.detail)
        # Per-element detail goes through console.warn (stderr); the summary
        # goes through console.log (stdout).
        self.assertIn("exceeds slide bounds", result.stderr)
        self.assertIn("left=-1.000 < 0", result.stderr)
        self.assertIn("right=19.000 > width=10.000", result.stderr)
        self.assertIn("Slide 1", result.stderr)
        self.assertIn("Found 1 element(s) extending beyond the slide bounds",
                      result.stdout)

    def test_alignment_all_axes_and_duplicate_indices_preserve_sizes(self):
        """Edge and centre alignment use the selection envelope without resizing."""
        value = self.js(self.require("layout.js") + """
            const output = {};
            for (const alignment of ["left", "right", "top", "bottom", "horizontallyCenter", "verticallyCenter"]) {
              const first = {data: {x: 1, y: 2, w: 2, h: 1}, options: {x: 1, y: 2, w: 2, h: 1}};
              const second = {options: {x: 5, y: 6, w: 4, h: 3}};
              const slide = {_slideObjects: [first, second]};
              h.alignSlideElements(slide, [0, 1, 0], alignment);
              output[alignment] = [first.data, first.options, second.options];
            }
            emit(output);
        """)
        for alignment, shapes in value.items():
            with self.subTest(alignment=alignment):
                first, duplicate, second = shapes
                self.assertEqual(first, duplicate)
                self.assertEqual([first["w"], first["h"], second["w"], second["h"]], [2, 1, 4, 3])
                axis = "x" if alignment in ("left", "right", "horizontallyCenter") else "y"
                size = "w" if axis == "x" else "h"
                fraction = 0.5 if alignment.endswith("Center") else 1 if alignment in ("right", "bottom") else 0
                self.assertAlmostEqual(first[axis] + first[size] * fraction,
                                       second[axis] + second[size] * fraction)

    def test_distribution_vertical_preserves_order_and_equal_gaps(self):
        """Mixed-height shapes get equal gaps while unrelated shapes stay put."""
        value = self.js(self.require("layout.js") + """
            const slide = {_slideObjects: [
              {options: {x: 0, y: 8, w: 1, h: 2}},
              {options: {x: 1, y: 0, w: 1, h: 1}},
              {options: {x: 2, y: 2, w: 1, h: 3}},
              {options: {x: 9, y: 9, w: 1, h: 1}},
            ]};
            h.distributeSlideElements(slide, [0, 1, 2, 2], "vertical");
            emit(slide._slideObjects.map(o => o.options));
        """)
        top, middle, bottom = value[1], value[2], value[0]
        self.assertEqual(top["y"], 0)
        self.assertEqual(bottom["y"] + bottom["h"], 10)
        self.assertEqual(middle["y"] - top["y"] - top["h"],
                         bottom["y"] - middle["y"] - middle["h"])
        self.assertEqual(value[3], {"x": 9, "y": 9, "w": 1, "h": 1})

    def test_layout_crop_viewport_and_cycle_safe_dimensions(self):
        """Image crop viewports define collision bounds and cyclic layouts terminate."""
        value = self.js(self.require("layout.js") + """
            const slide = {_slideObjects: [
              {options: {x: 0, y: 0, w: 10, h: 10, sizing: {type: "crop", w: 1, h: 1}}},
              {options: {x: 2, y: 2, w: 1, h: 1}},
            ]};
            const cyclic = {}; cyclic.size = cyclic;
            emit({relation: h.compareElementPosition(slide, 0, 1).relation,
              size: h.getSlideDimensions({_layout: cyclic}, {layout: {slideSize: {cx: 9144000, cy: 6858000}}})});
        """)
        self.assertEqual(value["relation"], "disjoint")
        self.assertEqual(value["size"], {"width": 10, "height": 7.5, "source": "emu_converted"})

    def test_overlap_filtering_and_severe_text_reporting(self):
        """Diagonal false positives are suppressed while actual text collisions remain errors."""
        value = self.js(self.require("layout.js") + """
            function report(objects, options = {}) {
              const channels = {warn: [], error: [], log: []};
              const saved = {};
              for (const key of Object.keys(channels)) { saved[key] = console[key]; console[key] = (...args) => channels[key].push(args.join(" ")); }
              try { h.warnIfSlideHasOverlaps({_slideObjects: objects}, {}, options); }
              finally { Object.assign(console, saved); }
              return channels;
            }
            const line = {type: "line", options: {x: 0, y: 0, w: 4, h: 4}};
            const rect = (x, y, type = "shape") => ({type, options: {x, y, w: 1, h: 1}});
            emit({miss: report([line, rect(3.5, 0)]),
              hit: report([line, rect(3.5, 3.5)]),
              ignored: report([line, rect(3.5, 3.5)], {ignoreLines: true}),
              severe: report([rect(0, 0, "text"), rect(0.5, 0.5)]),
              frame: report([{type: "shape", options: {x: 0, y: 0, w: 1, h: 1,
                    fill: {transparency: 100}, line: {color: "000000"}}}, rect(0.5, 0.5)],
                    {ignoreDecorativeShapes: true})});
        """)
        for quiet in ("miss", "ignored", "frame"):
            self.assertEqual(value[quiet], {"warn": [], "error": [], "log": []})
        self.assertTrue(value["hit"]["warn"])
        self.assertTrue(value["severe"]["error"])
        self.assertFalse(value["severe"]["warn"])


@unittest.skipUnless(HAVE_NODE and NODE_PATH, "requires the PptxGenJS helper peers")
class PeerBackedHelperTests(ScriptCase):
    """Helper modules whose peers are installed in the skill or supplied via ``SKILL_NODE_MODULES``."""

    def js(self, source, *args, **kwargs):
        _, value = self.run_node_json(source, *args, node_path=NODE_PATH, **kwargs)
        return value

    def require(self, module="index.js"):
        return f"const h = require({str(HELPERS / module)!r});\n"

    def test_index_re_exports_every_module_under_one_namespace(self):
        """Ensures index re exports every module under one namespace."""
        value = self.js(self.require() + """
            const dir = process.argv[1];
            const names = ["text", "image", "svg", "latex", "code", "layout",
                           "layout_builders", "util"];
            const perModule = {};
            for (const name of names) {
              perModule[name] = Object.keys(require(dir + "/" + name + ".js"));
            }
            emit({version: h.VERSION, keys: Object.keys(h), perModule});
        """, HELPERS)
        self.assertEqual(value["version"], "1.2.0")
        self.assertIn("VERSION", value["keys"])
        for module, names in value["perModule"].items():
            for name in names:
                self.assertIn(name, value["keys"],
                              f"index.js drops {module}'s export {name}")

    def test_text_height_estimation_is_analytical(self):
        """Ensures text height estimation is analytical."""
        value = self.js(self.require("text.js") + """
            emit({
              single: h.calcTextBoxHeightSimple(72, 1, 1.0, 0),
              threeLines: h.calcTextBoxHeightSimple(18, 3),
              defaultLeading: h.calcTextBoxHeightSimple(18, 1),
              keys: Object.keys(h),
            });
        """)
        self.assertEqual(value["keys"], ["calcTextBoxHeightSimple", "calcTextBox",
                                         "autoFontSize"])
        self.assertAlmostEqual(value["single"], 1.0)
        # 3 lines * (18/72) * 1.15 + 0.3 padding
        self.assertAlmostEqual(value["threeLines"], 3 * 0.25 * 1.15 + 0.3)
        self.assertAlmostEqual(value["defaultLeading"], 0.25 * 1.15 + 0.3)

    def test_calcTextBox_supports_its_three_documented_modes(self):
        """Ensures calcTextBox supports its three documented modes."""
        value = self.js(self.require("text.js") + """
            const text = "The quick brown fox jumps over the lazy dog, over and over again.";
            const err = (fn) => { try { fn(); return null; } catch (e) { return e.message; } };
            emit({
              fromLines: h.calcTextBox(18, {lines: 3}),
              fromWidth: h.calcTextBox(18, {text, w: 3, fontFace: "DejaVu Sans"}),
              fromHeight: h.calcTextBox(18, {text, h: 1, fontFace: "DejaVu Sans"}),
              insufficient: err(() => h.calcTextBox(18, {text})),
              noFontFace: err(() => h.calcTextBox(18, {text, w: 3})),
            });
        """)
        self.assertEqual(value["fromLines"]["lines"], 3)
        self.assertIsNone(value["fromLines"]["w"])
        self.assertAlmostEqual(value["fromLines"]["h"], 3 * (18 / 72) * 1.15 + 0.3)
        self.assertEqual(value["fromWidth"]["w"], 3)
        self.assertGreater(value["fromWidth"]["lines"], 1)
        # Mode (c) solves for the width that fits the given height; the reported
        # h is the content height actually used, never larger than the request.
        self.assertLessEqual(value["fromHeight"]["h"], 1)
        self.assertGreater(value["fromHeight"]["h"], 0)
        self.assertGreater(value["fromHeight"]["w"], 0)
        self.assertEqual(value["fromHeight"]["lines"], 2)
        self.assertEqual(
            value["insufficient"],
            "calcTextBox(): insufficient information. Provide {lines} or ({w,text}) "
            "or ({h,text}).",
        )
        self.assertEqual(value["noFontFace"],
                         "calcTextBox(): opts.fontFace is required when measuring by width.")

    def test_calcTextBox_reports_margins_and_never_substitutes_a_default_font(self):
        """Ensures calcTextBox reports margins and never substitutes a default font."""
        value = self.js(self.require("text.js") + """
            emit({
              margins: h.calcTextBox(18, {text: "hi", h: 1, fontFace: "DejaVu Sans",
                                          margin: 7.2}).margins,
              perSide: h.calcTextBox(18, {text: "hi", h: 3, fontFace: "DejaVu Sans",
                                          margin: {left: 72, top: 36}}).margins,
              tooSmall: (() => {
                try { h.calcTextBox(72, {text: "hi", h: 0.2, fontFace: "DejaVu Sans"}); }
                catch (e) { return e.message; }
                return null;
              })(),
              boldIsWider: [
                h.calcTextBox(18, {text: "Measure this string", h: 1,
                                   fontFace: "DejaVu Sans"}).w,
                h.calcTextBox(18, {text: "Measure this string", h: 1,
                                   fontFace: "DejaVu Sans", bold: true}).w,
              ],
            });
        """)
        # Margins are supplied in points and reported in inches.
        for side in ("left", "right", "top", "bottom"):
            self.assertAlmostEqual(value["margins"][side], 0.1)
        self.assertAlmostEqual(value["perSide"]["left"], 1.0)
        self.assertAlmostEqual(value["perSide"]["top"], 0.5)
        self.assertEqual(value["perSide"]["right"], 0,
                         "an object margin omitting a side falls back to zero")
        self.assertEqual(value["tooSmall"],
                         "calcTextBox(): height too small for one-line layout at this "
                         "font size")
        regular, bold = value["boldIsWider"]
        self.assertGreater(bold, regular, "bold text must measure wider")

    def test_autoFontSize_respects_the_closed_interval_and_its_modes(self):
        """Ensures autoFontSize respects the closed interval and its modes."""
        value = self.js(self.require("text.js") + """
            const face = "DejaVu Sans";
            const long = "x ".repeat(300);
            emit({
              shrink: h.autoFontSize(long, face, {w: 3, h: 1, fontSize: 40,
                                                  mode: "shrink", minFontSize: 6,
                                                  maxFontSize: 40}),
              shrinkNeverGrows: h.autoFontSize("hi", face, {w: 3, h: 1, fontSize: 10,
                                                            mode: "shrink",
                                                            minFontSize: 6,
                                                            maxFontSize: 40}),
              enlarge: h.autoFontSize("hi", face, {w: 3, h: 1, fontSize: 6,
                                                   mode: "enlarge", minFontSize: 6,
                                                   maxFontSize: 40}),
              empty: h.autoFontSize("", face, {w: 3, h: 1, fontSize: 22}),
              missingFace: (() => { try { h.autoFontSize("hi", "", {w: 3, h: 1}); }
                                    catch (e) { return e.message; } })(),
              badBox: (() => { try { h.autoFontSize("hi", face, {w: 0, h: 1}); }
                               catch (e) { return e.message; } })(),
            });
        """)
        shrink = value["shrink"]
        self.assertEqual(shrink["fit"], "shrink", "only shrink mode advertises fit")
        self.assertLessEqual(shrink["fontSize"], 40)
        self.assertGreaterEqual(shrink["fontSize"], 6)
        self.assertLessEqual(value["shrinkNeverGrows"]["fontSize"], 10,
                             "shrink mode must never grow the reference size")
        self.assertGreaterEqual(value["shrinkNeverGrows"]["fontSize"], 6)
        enlarge = value["enlarge"]
        self.assertGreater(enlarge["fontSize"], 6)
        self.assertLessEqual(enlarge["fontSize"], 40)
        self.assertNotIn("fit", enlarge)
        self.assertEqual(value["empty"], {"w": 3, "h": 1, "fontSize": 22, "x": 0, "y": 0})
        self.assertEqual(
            value["missingFace"],
            "autoFontSize(): fontFace is required as the 2nd positional argument.",
        )
        self.assertEqual(value["badBox"], "autoFontSize(): non-positive w or h")

    def test_code_to_runs_numbers_lines_and_colours_tokens(self):
        """Ensures code to runs numbers lines and colours tokens."""
        value = self.js(self.require("code.js") + """
            const single = h.codeToRuns("let answer = 42;", "js");
            const many = h.codeToRuns(Array.from({length: 12}, (_, i) => `line ${i}`)
                                        .join("\\n"), "python");
            const theme = h.buildThemeMap();
            emit({
              keys: Object.keys(h),
              firstRun: single[0],
              lastRun: single[single.length - 1],
              hasNewlines: single.some((r) => r.text === "\\n"),
              count: single.length,
              padWidth: many[0].text.length,
              fontFaces: [...new Set(single.map((r) => r.options.fontFace))],
              fontSizes: [...new Set(single.map((r) => r.options.fontSize))],
              themeHasComment: "comment" in theme,
              colours: [...new Set(single.map((r) => r.options.color))].length,
            });
        """)
        self.assertEqual(value["keys"], ["codeToRuns", "buildThemeMap"])
        self.assertEqual(value["firstRun"]["text"], "1 ")
        self.assertEqual(value["firstRun"]["options"]["fontFace"], "Consolas")
        self.assertEqual(value["firstRun"]["options"]["fontSize"], 14)
        self.assertEqual(value["fontFaces"], ["Consolas"])
        self.assertEqual(value["fontSizes"], [14])
        self.assertFalse(value["hasNewlines"], "a single line emits no newline run")
        self.assertEqual(value["padWidth"], 3, "12 lines pad the gutter to two digits")
        self.assertGreater(value["colours"], 1, "tokens must be colour-differentiated")
        self.assertTrue(value["themeHasComment"])

    def test_code_to_runs_falls_back_for_unknown_languages(self):
        """Ensures code to runs falls back for unknown languages."""
        value = self.js(self.require("code.js") + """
            emit({
              unknown: h.codeToRuns("plain words", "klingon").length,
              empty: h.codeToRuns("", "js").length,
              emptyText: h.codeToRuns("", "js")[1].text,
              aliases: [h.codeToRuns("x = 1", "py").length > 0,
                        h.codeToRuns("<p/>", "html").length > 0,
                        h.codeToRuns("a: 1", "yml").length > 0],
            });
        """)
        self.assertGreater(value["unknown"], 0)
        self.assertEqual(value["empty"], 2, "the line-number gutter is always emitted")
        self.assertEqual(value["emptyText"], "")
        self.assertEqual(value["aliases"], [True, True, True])

    def test_latex_helper_reports_a_missing_mathjax_with_install_guidance(self):
        """With mathjax-full present the helper returns a sanitized data URI."""
        value = self.js(self.require("latex.js") + """
            const uri = h.latexToSvgDataUri("x^2 + y^2 = z^2");
            const svg = Buffer.from(uri.split(",")[1], "base64").toString();
            emit({keys: Object.keys(h), prefix: uri.split(",")[0] + ",",
                  hasSvg: svg.startsWith("<svg"),
                  namespaced: svg.includes('xmlns="http://www.w3.org/2000/svg"'),
                  noCurrentColor: !svg.includes("currentColor"),
                  pxUnits: /width="[0-9]+px"/.test(svg)});
        """)
        self.assertEqual(value["keys"], ["latexToSvgDataUri"])
        self.assertEqual(value["prefix"], "data:image/svg+xml;base64,")
        for key in ("hasSvg", "namespaced", "noCurrentColor", "pxUnits"):
            self.assertTrue(value[key], f"{key} was false for {value}")

    def test_theme_grouped_selectors_and_nested_prism_tokens(self):
        """Every selector in a CSS colour group applies, including nested grammar output."""
        theme = self.work / "theme.css"
        theme.write_text(".token.comment, .token.prolog { color: #abc; }\n"
                         ".token.keyword { color: #123456 !important; }")
        value = self.js(self.require("code.js") + """
            const runs = h.codeToRuns('const t = `hello ${answer}`;', 'js');
            emit({theme: h.buildThemeMap(process.argv[1]),
              text: runs.map(r => r.text).join(''),
              colors: runs.map(r => r.options.color),
              missing: h.buildThemeMap('/no/such/theme.css')});
        """, theme)
        self.assertEqual(value["theme"]["comment"], "aabbcc")
        self.assertEqual(value["theme"]["prolog"], "aabbcc")
        self.assertEqual(value["theme"]["keyword"], "123456")
        self.assertEqual(value["text"], '1 const t = `hello ${answer}`;')
        self.assertTrue(all(len(color) == 6 for color in value["colors"]))
        self.assertEqual(value["missing"], {"plain": "FFFFFF", "comment": "999999"})

    def test_text_measurement_invariants_for_wrapping_and_styled_runs(self):
        """Narrowing, indents, spacing and larger styled runs cannot reduce needed height."""
        value = self.js(self.require("text.js") + """
            const base = {fontFace: "DejaVu Sans", w: 3, padding: 0};
            const content = "A useful sentence with several words and a conclusion. ".repeat(3);
            const measure = (text, overrides = {}) => h.calcTextBox(18, {...base, text, ...overrides});
            emit({wide: measure(content), narrow: measure(content, {w: 1}),
              long: measure("😀".repeat(20), {w: 0.01}),
              regular: measure([{text: content}]),
              bullet: measure([{text: content, options: {bullet: {indent: 36}}}]),
              small: measure([{text: "Hello", options: {fontSize: 12}}]),
              large: measure([{text: "Hello", options: {fontSize: 36}}]),
              spaced: measure("first\\nsecond", {paraSpaceAfter: 18}),
              plain: measure("first\\nsecond"),
              right: measure("hello", {margin: {right: 72, bottom: 36}}),
            });
        """)
        self.assertGreaterEqual(value["narrow"]["lines"], value["wide"]["lines"])
        self.assertGreaterEqual(value["bullet"]["h"], value["regular"]["h"])
        self.assertGreater(value["large"]["h"], value["small"]["h"])
        self.assertAlmostEqual(value["spaced"]["h"] - value["plain"]["h"], 0.25)
        self.assertEqual(value["long"]["lines"], 20)
        self.assertEqual(value["right"]["margins"], {"left": 0, "right": 1, "top": 0, "bottom": 0.5})

    def test_auto_font_size_rejects_bad_ranges_and_keeps_exact_fitting_bound(self):
        """Fit search honours exact bounds and rejects invalid modes or missing reference sizes."""
        value = self.js(self.require("text.js") + """
            const opts = {w: 4, h: 4, minFontSize: 10, maxFontSize: 20};
            const err = extra => { try { h.autoFontSize("hello", "DejaVu Sans", {...opts, ...extra}); }
                                   catch(e) { return e.message; } };
            const fit = h.autoFontSize("hello", "DejaVu Sans", opts);
            emit({size: fit.fontSize, measured: h.calcTextBox(fit.fontSize,
                  {text: "hello", fontFace: "DejaVu Sans", w: fit.w}).h,
              errors: [err({mode: "shrink"}), err({mode: "wrong"}),
                       err({minFontSize: 30}), err({minFontSize: 0})]});
        """)
        self.assertEqual(value["size"], 20)
        self.assertLessEqual(value["measured"], 4 * 0.97)
        self.assertTrue(all(value["errors"]))

    def test_latex_repeated_calls_create_self_contained_equations(self):
        """The cached MathJax document handles display and inline expressions independently."""
        value = self.js(self.require("latex.js") + """
            emit([true, false, true].map(display => {
              const data = h.latexToSvgDataUri("x+1", display);
              return Buffer.from(data.split(',')[1], 'base64').toString();
            }));
        """)
        for svg in value:
            self.assertTrue(svg.startswith("<svg"))
            self.assertIn('xmlns="http://www.w3.org/2000/svg"', svg)
            self.assertIn("<path", svg)
            self.assertNotIn("currentColor", svg)

    def test_helpers_write_a_native_presentation_with_embedded_equation(self):
        """Measured text, aligned shapes and an equation survive real PptxGenJS serialization."""
        target = self.work / "native.pptx"
        value = self.js(self.require() + """
            const PptxGenJS = require('pptxgenjs');
            const pptx = new PptxGenJS(); pptx.layout = 'LAYOUT_WIDE';
            const slide = pptx.addSlide();
            const fit = h.autoFontSize('Synthetic results', 'DejaVu Sans',
              {x: 1, y: 1, w: 4, h: 1, minFontSize: 18, maxFontSize: 24});
            slide.addText('Synthetic results', {...fit, fontFace: 'DejaVu Sans'});
            slide.addShape(pptx.ShapeType.rect, {x: 5, y: 3, w: 2, h: 1});
            h.alignSlideElements(slide, [0, 1], 'left');
            slide.addText(h.codeToRuns('let count = 3;', 'js'), {x: 1, y: 4, w: 5, h: 1});
            slide.addImage({data: h.latexToSvgDataUri('x+1'), x: 7, y: 1, w: 2, h: 1});
            pptx.writeFile({fileName: process.argv[1]}).then(() => emit({ok: true}));
        """, target)
        self.assertTrue(value["ok"])
        deck = Presentation(target)
        self.assertEqual(len(deck.slides), 1)
        shapes = deck.slides[0].shapes
        self.assertEqual(shapes[0].left, shapes[1].left)
        self.assertEqual(shapes[0].text, 'Synthetic results')
        self.assertIn('let count = 3;', shapes[2].text)
        import xml.etree.ElementTree as ET
        with zipfile.ZipFile(target) as archive:
            media = [name for name in archive.namelist() if name.endswith('.svg')]
            self.assertTrue(media)
            for name in media:
                self.assertEqual(ET.fromstring(archive.read(name)).tag,
                                 '{http://www.w3.org/2000/svg}svg')
            for name in archive.namelist():
                if name.endswith('.xml'):
                    ET.fromstring(archive.read(name))

    def test_layout_builders_compose_images_and_text_onto_a_slide(self):
        """Ensures layout builders compose images and text onto a slide."""
        png = self.work / "card.png"
        png.write_bytes(_png_bytes(200, 100))
        value = self.js(self.require("layout_builders.js") + """
            const [image] = process.argv.slice(1);
            const calls = [];
            const slide = {
              addImage: (opts) => calls.push(["image", opts]),
              addText: (text, opts) => calls.push(["text", text, opts]),
              addShape: (...a) => calls.push(["shape", ...a]),
            };
            const built = h.addImageTextCard(slide, {
              x: 1, y: 1, width: 3, gap: 0.2,
              image: {path: image, boxHeight: 2},
              text: "Card body",
              textBox: {fontSize: 14, fontFace: "DejaVu Sans"},
            });
            const row = {_slideObjects: [], addImage: () => {}, addText: () => {},
                         addShape: () => {}};
            emit({keys: Object.keys(h), callKinds: calls.map((c) => c[0]),
                  imageCall: calls.find((c) => c[0] === "image")[1],
                  textCall: calls.find((c) => c[0] === "text"),
                  returned: built === undefined ? "undefined" : typeof built});
        """, png)
        self.assertEqual(value["keys"], ["addImageTextCard", "addCardRow",
                                         "addThreeLevelTree"])
        self.assertIn("image", value["callKinds"])
        self.assertIn("text", value["callKinds"])
        image_call = value["imageCall"]
        self.assertEqual(image_call["path"], str(png))
        self.assertIn("sizing", image_call)
        self.assertEqual(image_call["sizing"]["type"], "crop")
        text_call = value["textCall"]
        self.assertEqual(text_call[1], "Card body")
        self.assertAlmostEqual(text_call[2]["y"], 1 + 2 + 0.2)


def _png_bytes(width, height, color=(200, 30, 30)):
    from PIL import Image
    import io

    buf = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buf, format="PNG")
    return buf.getvalue()


def _gif_bytes(width, height):
    from PIL import Image
    import io

    buf = io.BytesIO()
    Image.new("P", (width, height)).save(buf, format="GIF")
    return buf.getvalue()


if __name__ == "__main__":
    unittest.main()
