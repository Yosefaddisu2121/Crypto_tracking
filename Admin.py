import sqlite3
from telegram import Bot, Update
from telegram.ext import CommandHandler, Application, ContextTypes
import os

# Bot Token
BOT_TOKEN = '7970662601:AAEynrrZmd5ujvaErbpuaFmZ4659njYMU-8'
# Your Telegram ID (admin user)
ADMIN_USER_ID = "474803674"  # Replace with your actual Telegram ID

# Connect to SQLite Database
def get_db_connection():
    conn = sqlite3.connect('users.db')
    return conn

# Check if the user is an admin
def is_admin(user_id):
    return user_id == ADMIN_USER_ID

# Command to start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if is_admin(user_id):
        await update.message.reply_text("Welcome, Admin! You have full access.")
    else:
        await update.message.reply_text("Access Denied. You are not an admin.")

# Command to view all users
async def view_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Access Denied. Only the admin can view the database.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, telegram_id, subscription FROM users")
    users = cursor.fetchall()
    conn.close()

    if users:
        message = "Users in the database:\n\n"
        for user in users:
            message += f"User ID: {user[0]}, Telegram ID: {user[1]}, Subscription: {user[2]}\n"
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("No users found in the database.")

# Command to delete a user by user_id
async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Access Denied. Only the admin can delete users.")
        return

    try:
        user_to_delete = int(context.args[0])  # Get user_id from command argument
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_to_delete,))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"User with ID {user_to_delete} has been deleted.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /delete_user <user_id>")

# Command to promote a user to premium
async def promote_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Access Denied. Only the admin can promote users.")
        return

    try:
        user_to_promote = int(context.args[0])  # Get user_id from command argument
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET subscription = 'premium' WHERE user_id = ?", (user_to_promote,))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"User with ID {user_to_promote} has been promoted to premium.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /promote_user <user_id>")

# Command to send a message to all users (admin only)
async def send_message_to_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("Access Denied. Only the admin can send messages to all users.")
        return

    message = " ".join(context.args)  # The message that the admin wants to send
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM users")
    all_users = cursor.fetchall()
    conn.close()

    if all_users:
        for user in all_users:
            chat_id = user[0]
            try:
                await context.bot.send_message(chat_id=chat_id, text=message)
            except Exception as e:
                print(f"Error sending message to {chat_id}: {e}")
        await update.message.reply_text("Message sent to all users.")
    else:
        await update.message.reply_text("No users found.")

# Set up the bot with commands
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("view_users", view_users))
    application.add_handler(CommandHandler("delete_user", delete_user))
    application.add_handler(CommandHandler("promote_user", promote_user))
    application.add_handler(CommandHandler("send_message_to_all", send_message_to_all))

    # Start polling for updates
    application.run_polling()

if __name__ == "__main__":
    main()
