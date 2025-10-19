#!/usr/bin/env python3
import csv
import json
import math
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Iterable, Optional

# Simple, dependency-free MVP for duplicate detection and feature tagging.
# - Exact duplicate clusters on normalized (subject, description)
# - Near-duplicate clustering based on subject using Jaccard over 3-grams
# - Feature request heuristic using keywords and patterns
# Outputs:
#   - outputs/duplicate_clusters.jsonl (one cluster per line)
#   - outputs/feature_requests.jsonl (one issue per line tagged as feature_request=true)


@dataclass
class Issue:
    id: str
    subject: str
    description: str
    author: str
    status: str
    related: str


def read_issues(csv_path: Path) -> List[Issue]:
    issues: List[Issue] = []
    with csv_path.open('r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            issues.append(
                Issue(
                    id=str(row.get('id', '')).strip(),
                    subject=row.get('subject', '') or '',
                    description=row.get('description', '') or '',
                    author=row.get('author', '') or '',
                    status=row.get('status', '') or '',
                    related=row.get('related issues', '') or '',
                )
            )
    return issues


_whitespace_re = re.compile(r"\s+")

# Python re does not support \p classes. Implement simple punctuation removal.
_punct_strip = re.compile(r"[^\w\s]+", re.UNICODE)


def normalize_text(s: str) -> str:
    s = s.strip().lower()
    s = _whitespace_re.sub(" ", s)
    return s


def normalize_for_match(s: str) -> str:
    s = normalize_text(s)
    s = _punct_strip.sub("", s)
    s = _whitespace_re.sub(" ", s).strip()
    return s


def make_exact_key(issue: Issue) -> Tuple[str, str]:
    return (normalize_for_match(issue.subject), normalize_for_match(issue.description))


# Shingle-based near-duplicate detection over subjects

def to_trigrams(text: str) -> set:
    t = normalize_for_match(text)
    if not t:
        return set()
    padded = f"  {t}  "
    return {padded[i:i+3] for i in range(len(padded)-2)}


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def cluster_near_duplicates_subject(issues: List[Issue], threshold: float = 0.92) -> List[List[Issue]]:
    # Greedy single-pass clustering by highest jaccard to first representative
    reps: List[Tuple[Issue, set]] = []
    clusters: List[List[Issue]] = []
    for issue in issues:
        grams = to_trigrams(issue.subject)
        best_idx = -1
        best_sim = -1.0
        for idx, (rep_issue, rep_grams) in enumerate(reps):
            sim = jaccard(grams, rep_grams)
            if sim > best_sim:
                best_sim = sim
                best_idx = idx
        if best_sim >= threshold and best_idx >= 0:
            clusters[best_idx].append(issue)
        else:
            reps.append((issue, grams))
            clusters.append([issue])
    # Keep only clusters with size >= 2
    return [c for c in clusters if len(c) >= 2]


# Feature request heuristic
FEATURE_PATTERNS = [
    r"\b(feature|enhancement|improvement|upgrade|add|support|ability to|allow|enable)\b",
    r"\b(it would be (nice|great|useful)|would like to|i would like|please add)\b",
    r"\bshould be able to\b",
    r"\bmake it possible to\b",
]
FEATURE_RE = re.compile("|".join(FEATURE_PATTERNS), re.I)


def is_feature_request(issue: Issue) -> bool:
    text = f"{issue.subject}\n{issue.description}"
    text = normalize_text(text)
    if FEATURE_RE.search(text):
        return True
    # Keywords that often indicate bug reports; if present without feature patterns, bias to False
    bug_bias = re.search(r"\b(error|exception|fail(ed|ure)?|crash|not working|doesn\'t|broken)\b", text)
    if bug_bias and not FEATURE_RE.search(text):
        return False
    # Fallback: subjects starting with verbs like add/allow/support
    if re.match(r"^(add|allow|support|enable|improve|upgrade|provide)\b", normalize_text(issue.subject)):
        return True
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: detect_dupes_and_features.py /path/to/all_issues_for_test.csv [near_dupe_threshold]", file=sys.stderr)
        sys.exit(2)
    csv_path = Path(sys.argv[1])
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.92

    issues = read_issues(csv_path)

    # Exact duplicate clusters
    exact_groups: Dict[Tuple[str, str], List[Issue]] = defaultdict(list)
    for issue in issues:
        exact_groups[make_exact_key(issue)].append(issue)
    exact_clusters = [grp for grp in exact_groups.values() if len(grp) >= 2]

    # Near duplicate clusters on subject
    near_clusters = cluster_near_duplicates_subject(issues, threshold=threshold)

    outputs_dir = Path('outputs')
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # Write duplicate clusters
    with (outputs_dir / 'duplicate_clusters.jsonl').open('w', encoding='utf-8') as out:
        # tag clusters as exact or near
        for grp in exact_clusters:
            out.write(json.dumps({
                'type': 'exact',
                'size': len(grp),
                'ids': [i.id for i in grp],
                'subjects': [i.subject for i in grp[:3]],
            }, ensure_ascii=False) + "\n")
        for grp in near_clusters:
            out.write(json.dumps({
                'type': 'near',
                'size': len(grp),
                'ids': [i.id for i in grp],
                'subjects': [i.subject for i in grp[:3]],
            }, ensure_ascii=False) + "\n")

    # Feature requests
    with (outputs_dir / 'feature_requests.jsonl').open('w', encoding='utf-8') as out:
        for i in issues:
            flag = is_feature_request(i)
            if flag:
                out.write(json.dumps({
                    'id': i.id,
                    'subject': i.subject,
                    'status': i.status,
                    'author': i.author,
                    'is_feature_request': True,
                }, ensure_ascii=False) + "\n")

    # Brief stats
    stats = {
        'total_issues': len(issues),
        'exact_duplicate_clusters': len(exact_clusters),
        'near_duplicate_clusters': len(near_clusters),
        'feature_request_count': sum(1 for i in issues if is_feature_request(i)),
        'near_threshold': threshold,
    }
    with (outputs_dir / 'detector_stats.json').open('w', encoding='utf-8') as out:
        json.dump(stats, out, ensure_ascii=False, indent=2)

    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
