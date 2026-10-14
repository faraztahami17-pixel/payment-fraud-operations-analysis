"""metrics.py — confusion-matrix helpers used by evaluation and tests."""
from __future__ import annotations


def confusion_metrics(tp: int, fp: int, fn: int, tn: int, fraud_value_tp=None, fraud_value_total=None):
    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    fpr = fp / (fp + tn) if (fp + tn) > 0 else None
    alert_rate = (tp + fp) / (tp + fp + fn + tn) if (tp + fp + fn + tn) > 0 else None
    reviews_per_fraud = (tp + fp) / tp if tp > 0 else None
    fraud_value_recall = fraud_value_tp / fraud_value_total if fraud_value_total else None
    return precision, recall, fpr, alert_rate, reviews_per_fraud, fraud_value_recall
