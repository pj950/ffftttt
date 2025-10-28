import os
import requests
from typing import Dict


class ServerChanNotifier:
    """
    Send notifications via Server酱 (ServerChan) to WeChat.
    
    API: https://sctapi.ftqq.com/{SENDKEY}.send
    """
    
    def __init__(self, send_key: str = None):
        self.send_key = send_key or os.getenv("SERVERCHAN_KEY")
        self.api_url = f"https://sctapi.ftqq.com/{self.send_key}.send"
    
    def send_signal(self, signal: Dict, config: Dict = None) -> bool:
        """
        Send a trading signal notification.
        
        Args:
            signal: Signal dictionary with timestamp, symbol, timeframe, side, price, confidence, reason
            config: Notification config with title_template and message_template
            
        Returns:
            True if successful, False otherwise
        """
        if not self.send_key or self.send_key == "your_serverchan_key_here":
            return False
        
        if config is None:
            config = {}
        
        title_template = config.get("title_template", "{side} {symbol} [{timeframe}]")
        message_template = config.get(
            "message_template",
            "Signal: {side}\nSymbol: {symbol}\nTimeframe: {timeframe}\nPrice: {price:.2f}\nConfidence: {confidence:.2f}\nReason: {reason}\nTime: {timestamp}"
        )
        
        title = title_template.format(**signal)
        message = message_template.format(**signal)
        
        return self.send(title, message)
    
    def send(self, title: str, message: str) -> bool:
        """
        Send a generic notification.
        
        Args:
            title: Notification title
            message: Notification message (supports Markdown)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.send_key or self.send_key == "your_serverchan_key_here":
            return False
        
        try:
            data = {
                "title": title,
                "desp": message,
            }
            
            response = requests.post(self.api_url, data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    return True
                else:
                    return False
            else:
                return False
                
        except Exception as e:
            return False
