from database import get_engine_statistics

stats = get_engine_statistics()

print("\n==============================")
print(" EDGECLASS ENGINE LEADERBOARD ")
print("==============================\n")

if not stats:
    print("No engine statistics yet.")

for engine in stats:

    engine_name = engine[0]
    wins = engine[1]
    losses = engine[2]
    accuracy = engine[3]

    print(
        f"{engine_name:<12}"
        f" Wins:{wins:<4}"
        f" Losses:{losses:<4}"
        f" Accuracy:{accuracy}%"
    )