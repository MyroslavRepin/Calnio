from datetime import datetime, timezone
import pytz

iat_timestamp = 1753731145
exp_timestamp = 1753732045.543738

# UTC время
iat_utc = datetime.fromtimestamp(iat_timestamp, tz=timezone.utc)
exp_utc = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

# Часовой пояс Эдмонтона (Mountain Time)
mountain_tz = pytz.timezone('Canada/Mountain')

iat_mt = iat_utc.astimezone(mountain_tz)
exp_mt = exp_utc.astimezone(mountain_tz)

print("Created at (MT):", iat_mt.strftime('%Y-%m-%d %H:%M:%S %Z'))
print("Expires at (MT):", exp_mt.strftime('%Y-%m-%d %H:%M:%S %Z'))
