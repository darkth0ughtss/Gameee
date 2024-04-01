import os
import telebot
import pymongo
import random
from config import BOT_TOKEN, MONGODB_URI

# Initialize Telebot client
bot_token = os.getenv("BOT_TOKEN") or BOT_TOKEN
bot = telebot.TeleBot(bot_token)

# Connect to MongoDB Atlas
mongo_uri = os.getenv("MONGODB_URI") or MONGODB_URI
client = pymongo.MongoClient(mongo_uri)
db = client.get_database("my_database")
users_collection = db.get_collection("users")

# Get the directory path of the script
current_directory = os.path.dirname(os.path.abspath(__file__))

# Function to handle /start command
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user_data = users_collection.find_one({"_id": user_id})
    if user_data is None:
        users_collection.insert_one({"_id": user_id, "balance": 10000})
        bot.send_message(user_id, "Welcome to the E-Coin trading bot! You have been credited with 10,000 E-Coins.")
    else:
        bot.send_message(user_id, "You have already started using the E-Coin trading bot.")

# Function to handle /info command
@bot.message_handler(commands=['info'])
def info_command(message):
    user_id = message.from_user.id
    user_data = users_collection.find_one({"_id": user_id})
    if user_data:
        balance = user_data["balance"]
        bot.reply_to(message, f"Your current balance: {balance} E-Coins")

# Function to handle /bet command and direct bet messages
@bot.message_handler(commands=['bet'])
@bot.message_handler(func=lambda message: message.text.startswith('Bbet '))
def bet_command(message):
    user_id = message.from_user.id

    # Extracting command arguments
    if message.text.startswith('/'):
        args = message.text.split()[1:]
    else:
        args = message.text[len('Bbet '):].split()

    if len(args) != 2:
        bot.reply_to(message, "Invalid command usage. Please use /bet {amount} heads/tails or Bbet {amount} heads/tails")
        return
    
    try:
        amount = int(args[0])
        if amount <= 0:
            raise ValueError
    except ValueError:
        bot.reply_to(message, "Invalid bet amount. Please enter a positive integer.")
        return

    choice = args[1].lower()
    if choice not in ["heads", "tails", "h", "t"]:
        bot.reply_to(message, "Invalid choice. Please choose either heads or tails.")
        return

    # Map short forms to full words
    if choice == "h":
        choice = "heads"
    elif choice == "t":
        choice = "tails"

    user_data = users_collection.find_one({"_id": user_id})
    if not user_data:
        bot.reply_to(message, "You haven't started using the E-Coin trading bot yet. Please use /start first.")
        return
    
    balance = user_data["balance"]
    if amount > balance:
        bot.reply_to(message, "Insufficient balance to place this bet.")
        return

    # Simulate a coin toss
    outcome = random.choice(["heads", "tails"])
    if choice == outcome:
        new_balance = balance + amount
        user_info = bot.get_chat(user_id)
        first_name = user_info.first_name
        reply_text = f"🎉 Congratulations {first_name}, the coin has landed on {outcome}. You have successfully won {amount} E-Coins.\n\n"
        reply_text += f"[✅](https://telegra.ph/file/aea4cd0e35149b70943fe.png) {amount} E-Coins have been credited to your balance."
    else:
        new_balance = balance - amount
        user_info = bot.get_chat(user_id)
        first_name = user_info.first_name
        reply_text = f"😕 Oh no {first_name}, the coin has landed on {outcome}. You have lost {amount} E-Coins.\n\n"
        reply_text += f"[❌](https://telegra.ph/file/afe505073a3baa383015c.png) {amount} E-Coins have been deducted from your balance."
    
    # Update user's balance in the database
    users_collection.update_one({"_id": user_id}, {"$set": {"balance": new_balance}})
    
    # Send the bet result message
    bot.reply_to(message, reply_text, parse_mode="Markdown")



# Function to handle /leaderboard or /lb command
@bot.message_handler(commands=['leaderboard', 'lb'])
def leaderboard_command(message):
    # Retrieve all users' data from the database sorted by balance in descending order
    all_users = list(users_collection.find().sort("balance", pymongo.DESCENDING).limit(10))

    # If there are no users in the database, send a message
    if not all_users:
        bot.reply_to(message, "No users found in the database.")
        return

    # Create the leaderboard message
    leaderboard_message = "Leaderboard:\n"
    for index, user_data in enumerate(all_users, start=1):
        user_id = user_data["_id"]
        balance = user_data["balance"]
        
        # Get the user's first name using their user ID
        user_info = bot.get_chat(user_id)
        first_name = user_info.first_name

        # Create a clickable link to the user's profile
        user_profile_link = f"<a href='tg://user?id={user_id}'>{first_name}</a>"

        # Add the user's information to the leaderboard message
        leaderboard_message += f"{index}. {user_profile_link} - {balance} E-Coins\n"

    # Send the leaderboard message with HTML formatting
    bot.send_message(message.chat.id, leaderboard_message, parse_mode="HTML")


# Start the bot
bot.polling()
