"""Time-weighted native decision metrics, kept separate from historical samples."""
import math

COUNTERS = ['DecisionSampleCount', 'DecisionDuration', 'DecisionAbsoluteIntegral',
            'DecisionSquaredIntegral', 'DecisionSignedIntegral', 'DecisionWithin5Time',
            'DecisionExtremeTime', 'DecisionMaximumAbsoluteH', 'DecisionOutOfBandTime',
            'DecisionRecoveryCount', 'DecisionRecoveryTimeSum']

def summarize(counters):
    if any(not math.isfinite(float(counters[k])) for k in COUNTERS):
        raise ValueError('Non-finite native decision counter')
    n, duration = counters['DecisionSampleCount'], counters['DecisionDuration']
    if n < 1 or duration <= 0 or n != int(n):
        raise ValueError('Incomplete native decision sampling')
    count = counters['DecisionRecoveryCount']
    return dict(decision_samples=int(n), duration_seconds=duration,
                time_mae=counters['DecisionAbsoluteIntegral']/duration,
                time_rmse=math.sqrt(counters['DecisionSquaredIntegral']/duration),
                time_mean_signed=counters['DecisionSignedIntegral']/duration,
                fraction_within_5=counters['DecisionWithin5Time']/duration,
                fraction_above_100=counters['DecisionExtremeTime']/duration,
                maximum_absolute_h=counters['DecisionMaximumAbsoluteH'],
                completed_recoveries=int(count),
                mean_completed_excursion_seconds=counters['DecisionRecoveryTimeSum']/count if count else None,
                censored_excursion_seconds=counters['DecisionOutOfBandTime'])
