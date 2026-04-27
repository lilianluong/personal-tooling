#!/bin/sh
BRANCH=$(git -C "${GIT_DIR:-.}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
export BRANCH
cat | python3 -c "
import json, sys, os

data = json.load(sys.stdin)

model = (data.get('model') or {}).get('display_name') or 'unknown'
branch = os.environ.get('BRANCH', '')

cw = data.get('context_window') or {}
total_in = cw.get('total_input_tokens') or 0
total_out = cw.get('total_output_tokens') or 0
used_pct = cw.get('used_percentage')

total_tokens = total_in + total_out
if total_tokens >= 1_000_000:
    tokens_fmt = f'{total_tokens/1_000_000:.1f}M'
elif total_tokens >= 1_000:
    tokens_fmt = f'{total_tokens/1_000:.1f}k'
else:
    tokens_fmt = str(total_tokens)

cost = (data.get('cost') or {}).get('total_cost_usd')

status = f'{model}'
if branch:
    status += f' | {branch}'
status += f' | tokens: {tokens_fmt}'
if used_pct is not None:
    status += f' | ctx: {round(used_pct)}%'
if cost:
    status += f' | \${cost:.3f}'

rl = data.get('rate_limits') or {}
five = (rl.get('five_hour') or {}).get('used_percentage')
week = (rl.get('seven_day') or {}).get('used_percentage')
if five is not None or week is not None:
    parts = []
    if five is not None:
        parts.append(f'5h:{round(five)}%')
    if week is not None:
        parts.append(f'7d:{round(week)}%')
    status += ' | ' + ' '.join(parts)

print(status)
"
