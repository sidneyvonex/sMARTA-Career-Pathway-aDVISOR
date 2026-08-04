"""Backward-compatible import for the PDF package.

New code should import builders from ``reports.pdf``.
"""

from .pdf import build_student_report

__all__ = ['build_student_report']
