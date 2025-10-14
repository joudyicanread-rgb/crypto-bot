from flask import Flask, request, jsonify
import requests
from datetime import datetime
import logging

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

class TradingViewAlertBot:
    def __init__(self):
        self.bot_token = "8275480138:AAF0L6gXbJs9bJbD1VGGI0u1GYxztEtGFsU"
        self.chat_id = "1038277398"
    
    def process_alert_data(self, data):
        """معالجة بيانات التنبيه من TradingView"""
        try:
            # استخراج البيانات الأساسية
            symbol = data.get('symbol', data.get('ticker', 'Unknown'))
            price = data.get('price', data.get('close', 'N/A'))
            alert_message = data.get('message', data.get('alert_name', 'ALGOX Signal'))
            timeframe = data.get('timeframe', '5m')
            
            # كشف نوع الإشارة
            signal_type = self.detect_signal_type(alert_message)
            
            return {
                'symbol': symbol,
                'price': price,
                'message': alert_message,
                'signal_type': signal_type,
                'timeframe': timeframe
            }
        except Exception as e:
            logging.error(f"Error processing alert data: {e}")
            return None
    
    def detect_signal_type(self, message):
        """كشف نوع الإشارة من النص"""
        message_lower = str(message).lower()
        
        if any(word in message_lower for word in ['long', 'buy', 'شراء', 'صاعد', '🚀']):
            return "LONG"
        elif any(word in message_lower for word in ['short', 'sell', 'بيع', 'هابط', '⚠️']):
            return "SHORT"
        elif any(word in message_lower for word in ['cloud', 'سحابة', '☁️']):
            return "CLOUD"
        else:
            return "GENERIC"
    
    def create_telegram_message(self, alert_data):
        """إنشاء رسالة التليجرام"""
        symbol = alert_data['symbol']
        price = alert_data['price']
        signal_type = alert_data['signal_type']
        original_message = alert_data['message']
        timeframe = alert_data['timeframe']
        
        if signal_type == "LONG":
            emoji = "🚀"
            title = "إشارة شراء - LONG"
            color = "🟢"
            action = "شراء"
        elif signal_type == "SHORT":
            emoji = "⚠️" 
            title = "إشارة بيع - SHORT"
            color = "🔴"
            action = "بيع"
        else:
            emoji = "📊"
            title = "تنبيه ALGOX"
            color = "🔵"
            action = "مراقبة"
        
        message = f"""
{emoji} **{title}**

🏷️ **العملة**: `{symbol}`
💰 **السعر**: `{price}`
⏰ **الإطار الزمني**: `{timeframe}`
🕒 **الوقت**: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

📝 **التفاصيل**:
{original_message}

🎯 **الإجراء المقترح**: {action} {color}

🔔 **مصدر الإشارة**: TradingView ALGOX
"""
        return message
    
    def send_telegram_alert(self, message):
        """إرسال التنبيه إلى التليجرام"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logging.info("✅ تم إرسال التنبيه إلى التليجرام بنجاح")
                return True
            else:
                logging.error(f"❌ فشل إرسال التنبيه: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في إرسال التليجرام: {e}")
            return False

# إنشاء كائن البوت
alert_bot = TradingViewAlertBot()

@app.route('/webhook/algo-x', methods=['POST'])
def tradingview_webhook():
    """مسار ويب هوك رئيسي لاستقبال تنبيهات TradingView"""
    try:
        # تسجيل وصول الطلب
        logging.info("📥 تم استقبال طلب ويب هوك جديد")
        
        # الحصول على البيانات من TradingView
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        logging.info(f"📊 البيانات المستلمة: {data}")
        
        # معالجة البيانات
        alert_data = alert_bot.process_alert_data(data)
        
        if not alert_data:
            return jsonify({"status": "error", "message": "Failed to process alert data"}), 400
        
        # إنشاء رسالة التليجرام
        telegram_message = alert_bot.create_telegram_message(alert_data)
        
        # إرسال إلى التليجرام
        success = alert_bot.send_telegram_alert(telegram_message)
        
        if success:
            logging.info(f"✅ تم معالجة إشارة {alert_data['signal_type']} لـ {alert_data['symbol']}")
            return jsonify({
                "status": "success", 
                "message": "Alert processed and sent to Telegram",
                "symbol": alert_data['symbol'],
                "signal_type": alert_data['signal_type']
            }), 200
        else:
            return jsonify({"status": "error", "message": "Failed to send Telegram alert"}), 500
            
    except Exception as e:
        logging.error(f"❌ خطأ في معالجة ويب هوك: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/webhook/simple', methods=['POST'])
def simple_webhook():
    """مسار ويب هوك مبسط للاختبار"""
    try:
        data = request.get_json() or request.form.to_dict()
        
        # رسالة مبسطة للاختبار
        symbol = data.get('symbol', 'TEST')
        price = data.get('price', '100')
        
        message = f"""
🔔 **تنبيه اختبار**

🏷️ **العملة**: `{symbol}`
💰 **السعر**: `{price}`
🕒 **الوقت**: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

✅ هذا تنبيه اختبار من نظام ALGOX
"""
        
        success = alert_bot.send_telegram_alert(message)
        
        if success:
            return jsonify({"status": "success", "message": "Test alert sent"})
        else:
            return jsonify({"status": "error", "message": "Failed to send test alert"})
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """فحص صحة السيرفر"""
    return jsonify({
        "status": "healthy", 
        "service": "TradingView Webhook Server",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "main_webhook": "/webhook/algo-x",
            "test_webhook": "/webhook/simple",
            "health_check": "/health"
        }
    })

@app.route('/', methods=['GET'])
def home():
    """الصفحة الرئيسية"""
    return """
    <html>
        <head>
            <title>TradingView Webhook Server</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .endpoint { background: #f5f5f5; padding: 20px; margin: 10px 0; border-radius: 5px; }
                code { background: #eee; padding: 2px 5px; }
            </style>
        </head>
        <body>
            <h1>🚀 TradingView Webhook Server</h1>
            <p>هذا السيرفر يستقبل تنبيهات من TradingView ويرسلها إلى التليجرام.</p>
            
            <div class="endpoint">
                <h3>📊 المسارات المتاحة:</h3>
                <ul>
                    <li><code>POST /webhook/algo-x</code> - لتنبيهات ALGOX الرئيسية</li>
                    <li><code>POST /webhook/simple</code> - لتنبيهات الاختبار</li>
                    <li><code>GET /health</code> - فحص صحة السيرفر</li>
                </ul>
            </div>
            
            <div class="endpoint">
                <h3>🔧 كيفية الإعداد في TradingView:</h3>
                <ol>
                    <li>أنشئ تنبيه جديد في TradingView</li>
                    <li>اختر "Webhook URL" في الإشعارات</li>
                    <li>أدخل الرابط: <code>https://your-domain.com/webhook/algo-x</code></li>
                    <li>في حقل الرسالة، استخدم التنسيق التالي:</li>
                </ol>
                <pre>
{
    "symbol": "{{ticker}}",
    "price": "{{close}}",
    "message": "إشارة {{strategy.order.action}} من ALGOX",
    "timeframe": "{{timeframe}}"
}
                </pre>
            </div>
        </body>
    </html>
    """

if __name__ == '__main__':
    # تشغيل السيرفر
    logging.info("🚀 بدء تشغيل سيرفر ويب هوك TradingView...")
    logging.info(f"📞 المسار الرئيسي: POST /webhook/algo-x")
    logging.info(f"🔧 مسار الاختبار: POST /webhook/simple")
    logging.info(f"❤️  فحص الصحة: GET /health")
    
    app.run(host='0.0.0.0', port=5000, debug=False)