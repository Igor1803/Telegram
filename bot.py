import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_BOT_TOKEN
from llm_service import AIService
from storage import ConversationRepository
from models import Message

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ClientAssessmentBot:
    def __init__(self):
        self.ai_service = AIService()
        self.repository = ConversationRepository()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user_id = update.effective_user.id
        
        self.repository.reset_conversation(user_id)
        conversation = self.repository.create_conversation(user_id)
        
        initial_message = "Привет! Меня зовут Алексей, я ассистент руководителя. Расскажи, чем могу помочь?"
        
        self.repository.add_message(user_id, "assistant", initial_message)
        
        await update.message.reply_text(initial_message)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        user_message = update.message.text
        
        conversation = self.repository.get_conversation(user_id)
        
        if not conversation:
            await self.start_command(update, context)
            return
        
        if conversation.is_finished:
            await update.message.reply_text(
                "Спасибо за разговор! Если хочешь начать новый разговор, отправь /start"
            )
            return
        
        self.repository.add_message(user_id, "user", user_message)
        
        messages = conversation.messages
        response, is_finished, report = self.ai_service.create_reply(messages)
        
        self.repository.add_message(user_id, "assistant", response)
        
        if is_finished and report:
            self.repository.finalize_conversation(user_id, report)
            logger.info(f"Разговор завершён для пользователя {user_id}. Отчёт: {report}")
        
        await update.message.reply_text(response)
    
    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /reset для сброса разговора"""
        user_id = update.effective_user.id
        self.repository.reset_conversation(user_id)
        await update.message.reply_text("Разговор сброшен. Отправь /start для начала нового разговора.")
    
    def run(self):
        """Запускает бота"""
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("reset", self.reset_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("Бот запущен...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot = ClientAssessmentBot()
    bot.run()

