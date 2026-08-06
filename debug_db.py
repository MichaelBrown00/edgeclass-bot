from database import get_pending_predictions

rows = get_pending_predictions()

print(rows[0])