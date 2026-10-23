"""Detect stacked-label and unresolved-axis defects from the supplied checks.

Namespace-aware, reports defects without guessing repairs. These checks cover
selected chart constraints, not full chart schema/application compatibility.
"""
import re
from defusedxml import ElementTree as ET

C = '{http://schemas.openxmlformats.org/drawingml/2006/chart}'
AXID_MINIMUM = {'barChart':2,'lineChart':2,'areaChart':2,'scatterChart':2,
    'bubbleChart':2,'radarChart':2,'stockChart':2,'bar3DChart':2,
    'area3DChart':2,'surfaceChart':2,'line3DChart':3,'surface3DChart':3}


def find_chart_problems(files):
    problems = []
    for part,data in sorted(files.items()):
        if not re.fullmatch(r'ppt/charts/chart\d+\.xml',part):
            continue
        try:
            root = ET.fromstring(data)
        except Exception as exc:
            problems.append(f'{part}: unreadable chart: {exc}'); continue
        for area in root.iter(C+'plotArea'):
            declared = {axis.find(C+'axId').get('val') for axis in area
                        if axis.tag in {C+x for x in ('catAx','valAx','serAx','dateAx')}
                        and axis.find(C+'axId') is not None}
            for group in area:
                kind = group.tag.removeprefix(C)
                if kind in AXID_MINIMUM:
                    ids = [e.get('val') for e in group.findall(C+'axId')]
                    if len(set(ids)) < AXID_MINIMUM[kind] or not set(ids) <= declared:
                        problems.append(f'{part}: {kind} has missing, duplicate, or undeclared axis references: {ids}')
                if kind in ('barChart','bar3DChart'):
                    grouping = group.find(C+'grouping')
                    if grouping is not None and grouping.get('val') in ('stacked','percentStacked'):
                        # Ignore extension namespaces; inspect actual chart labels.
                        parents = [group, *group.findall(C+'ser')]
                        for parent in parents:
                            labels = parent.find(C+'dLbls')
                            if labels is not None and any(e.get('val')=='outEnd' for e in labels.iter(C+'dLblPos')):
                                problems.append(f'{part}: outEnd label on stacked bar; use ctr, inEnd, or inBase')
    return problems
