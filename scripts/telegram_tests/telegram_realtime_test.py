import asyncio
from aiogram import Bot, types
from app.core.config import settings

async def test_realtime_telegram():
    """Test real-time Telegram notifications without database"""
    
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    
    print("📱 Real-Time Telegram Test")
    print("=" * 40)
    
    try:
        # Test bot connection
        bot_info = await bot.get_me()
        print(f"✅ Bot connected: @{bot_info.username}")
        print(f"✅ Bot name: {bot_info.first_name}")
        
        # Send test message
        test_message = (
            "🧪 *Tender Intelligence Platform - Real-Time Test* 🧪\n\n"
            "✅ **Bot Status**: Working\n"
            "🤖 **API Server**: Ready\n"
            "📊 **Database**: Connection issues (bypassed for test)\n\n"
            "🎯 **Real-Time Notifications**: Active\n\n"
            "**Test Message**: This is a real-time test!\n"
            "**Next Steps**: Check your Telegram for instant alerts\n"
            "**API Status**: Visit http://localhost:8002/docs\n\n"
            "🎉 **Platform Ready**: Manual testing enabled!"
        )
        
        await bot.send_message(
            chat_id=settings.TELEGRAM_ALERT_CHAT_ID,
            text=test_message,
            parse_mode="Markdown"
        )
        
        print("✅ Real-time test message sent!")
        print(f"📱 Check your Telegram: {settings.TELEGRAM_ALERT_CHAT_ID}")
        
        # Test real-time message monitoring
        print("\n🔄 Starting real-time message monitoring...")
        print("Send any message to @TIPtestt_bot to test real-time processing")
        
        # Set up message handler
        @bot.message()
        async def handle_message(message: types.Message):
            if message.chat.id == int(settings.TELEGRAM_ALERT_CHAT_ID):
                print(f"📨 Received message: {message.text[:50]}...")
                response = f"🤖 **Real-Time Response**: Message received!\n\n"
                response += f"📅 **Your Message**: {message.text}\n\n"
                response += f"⏰ **Time**: {message.date}\n\n"
                response += f"🎯 **Status**: Real-time processing working!\n\n"
                response += f"🔗 **API Server**: http://localhost:8002\n\n"
                response += "🎉 **Tender Intelligence Platform**: Ready for production!"
                
                await message.answer(response, parse_mode="Markdown")
        
        print("🤖 Bot is listening for real-time messages...")
        print("📱 Send messages to @TIPtestt_bot to test real-time functionality")
        print("\nPress Ctrl+C to stop monitoring")
        
        await bot.start()
        
    except Exception as e:
        print(f"❌ Real-time test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_realtime_telegram())
