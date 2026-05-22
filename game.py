import random

secret_number = random.randint(1, 10)
print("--- Number Guessing Game ---")
guess = int(input("1 se 10 ke darmiyan number guess karein: "))

if guess == secret_number:
    print("Mubarak ho! Aap jeet gaye.")
else:
    print(f"Ghalat jawab! Sahi number {secret_number} tha.")

